"""
Person tracking service for maintaining identity continuity across frames and cameras.
Implements cross-frame identity linking with appearance and spatiotemporal validation.
"""

import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.models.person_track import PersonTrack
from app.models.frame import Frame
from app.models.frame_analysis import FrameAnalysis
from app.models.camera import Camera
from app.database import get_redis
from app.services.gemini_client import get_gemini_client
from app.config import settings

logger = logging.getLogger(__name__)


class PersonTrackingService:
    """Service for person tracking across frames and cameras."""

    def __init__(self):
        """Initialize person tracking service."""
        self.gemini_client = get_gemini_client()

    async def process_frame_persons(
        self,
        db: AsyncSession,
        frame: Frame,
        frame_analysis: FrameAnalysis,
        camera: Camera
    ) -> List[Dict[str, Any]]:
        """
        Process person detections from a frame and assign to tracks.

        Args:
            db: Database session
            frame: Frame model instance
            frame_analysis: Analysis results containing person detections
            camera: Camera instance

        Returns:
            List of track assignments
        """
        try:
            if not frame_analysis.person_profiles:
                return []

            logger.info(f"Processing {len(frame_analysis.person_profiles)} persons from frame {frame.frame_id}")

            # Get active tracks from Redis
            active_tracks = await self._get_active_tracks()

            # Match persons to tracks using Gemini
            camera_info = {
                "name": camera.name,
                "location": camera.location,
                "facility_zone": camera.facility_zone,
                "camera_id": camera.id,
            }

            matches = self.gemini_client.match_person_tracks(
                current_persons=frame_analysis.person_profiles,
                active_tracks=active_tracks,
                camera_info=camera_info
            )

            # Process matches
            track_assignments = []

            for match in matches:
                if match["matched"] and match["track_id"]:
                    # Update existing track
                    track = await self._update_track(
                        db=db,
                        track_id=match["track_id"],
                        person_data=match,
                        frame=frame,
                        camera=camera
                    )
                else:
                    # Create new track
                    track = await self._create_track(
                        db=db,
                        person_data=match,
                        frame=frame,
                        camera=camera
                    )

                track_assignments.append({
                    "person_id": match["person_id"],
                    "track_id": track.track_id,
                    "confidence": match["confidence"],
                    "is_new_track": not match["matched"]
                })

            await db.commit()

            logger.info(f"Processed {len(track_assignments)} track assignments")
            return track_assignments

        except Exception as e:
            logger.error(f"Error processing frame persons: {e}")
            raise

    async def _get_active_tracks(self) -> List[Dict[str, Any]]:
        """
        Get active tracks from Redis (last 5 minutes).

        Returns:
            List of active track dictionaries
        """
        try:
            redis_client = await get_redis()

            # Get all active track keys
            track_keys = await redis_client.keys("track:*")

            active_tracks = []
            cutoff_time = datetime.utcnow() - timedelta(seconds=settings.TRACK_TTL_SECONDS)

            for key in track_keys:
                track_data = await redis_client.get(key)
                if track_data:
                    track = json.loads(track_data)

                    # Check if track is still active
                    last_seen = datetime.fromisoformat(track["last_seen"])
                    if last_seen > cutoff_time:
                        active_tracks.append(track)

            logger.debug(f"Retrieved {len(active_tracks)} active tracks from Redis")
            return active_tracks

        except Exception as e:
            logger.error(f"Error retrieving active tracks: {e}")
            return []

    async def _create_track(
        self,
        db: AsyncSession,
        person_data: Dict[str, Any],
        frame: Frame,
        camera: Camera
    ) -> PersonTrack:
        """
        Create new person track.

        Args:
            db: Database session
            person_data: Person detection data
            frame: Frame where person was detected
            camera: Camera instance

        Returns:
            New PersonTrack instance
        """
        try:
            track_id = f"track_{uuid.uuid4().hex[:12]}"

            # Extract appearance data
            person_profile = person_data.get("appearance", {})

            appearance_signature = {
                "clothing_upper": person_profile.get("clothing_upper"),
                "clothing_lower": person_profile.get("clothing_lower"),
                "colors": person_profile.get("dominant_colors", []),
                "physical_characteristics": person_profile.get("physical_characteristics"),
                "distinctive_features": person_profile.get("distinctive_features", []),
                "accessories": person_profile.get("accessories", []),
            }

            trajectory = [{
                "timestamp": frame.captured_at.isoformat(),
                "camera_id": camera.id,
                "camera_name": camera.name,
                "frame_id": frame.id,
                "position": person_profile.get("position"),
                "facility_zone": camera.facility_zone,
            }]

            # Create track record
            track = PersonTrack(
                track_id=track_id,
                first_seen=frame.captured_at,
                last_seen=frame.captured_at,
                duration_seconds=0,
                appearance_signature=appearance_signature,
                clothing_description=f"{person_profile.get('clothing_upper')} and {person_profile.get('clothing_lower')}",
                physical_characteristics=person_profile.get("physical_characteristics"),
                distinctive_features=person_profile.get("distinctive_features", []),
                camera_ids=[camera.id],
                camera_names=[camera.name],
                trajectory=trajectory,
                zones_visited=[camera.facility_zone] if camera.facility_zone else [],
                frame_count=1,
                confidence_score=person_data.get("confidence", 1.0),
                match_history=[],
                status="active",
                frame_ids=[frame.id],
            )

            db.add(track)
            await db.flush()

            # Store in Redis for real-time access
            await self._store_track_in_redis(track)

            logger.info(f"Created new track {track_id}")
            return track

        except Exception as e:
            logger.error(f"Error creating track: {e}")
            raise

    async def _update_track(
        self,
        db: AsyncSession,
        track_id: str,
        person_data: Dict[str, Any],
        frame: Frame,
        camera: Camera
    ) -> PersonTrack:
        """
        Update existing person track with new detection.

        Args:
            db: Database session
            track_id: Track identifier
            person_data: Person detection data
            frame: Frame where person was detected
            camera: Camera instance

        Returns:
            Updated PersonTrack instance
        """
        try:
            # Load track from database
            result = await db.execute(
                select(PersonTrack).where(PersonTrack.track_id == track_id)
            )
            track = result.scalar_one_or_none()

            if not track:
                logger.warning(f"Track {track_id} not found, creating new track")
                return await self._create_track(db, person_data, frame, camera)

            # Update temporal data
            track.last_seen = frame.captured_at
            track.duration_seconds = int((frame.captured_at - track.first_seen).total_seconds())

            # Update trajectory
            trajectory = track.trajectory or []
            person_profile = person_data.get("appearance", {})

            trajectory.append({
                "timestamp": frame.captured_at.isoformat(),
                "camera_id": camera.id,
                "camera_name": camera.name,
                "frame_id": frame.id,
                "position": person_profile.get("position"),
                "facility_zone": camera.facility_zone,
            })
            track.trajectory = trajectory

            # Update camera lists
            if camera.id not in track.camera_ids:
                track.camera_ids = track.camera_ids + [camera.id]
                track.camera_names = (track.camera_names or []) + [camera.name]

            # Update zones visited
            if camera.facility_zone and camera.facility_zone not in (track.zones_visited or []):
                track.zones_visited = (track.zones_visited or []) + [camera.facility_zone]

            # Update frame tracking
            track.frame_count += 1
            track.frame_ids = (track.frame_ids or []) + [frame.id]

            # Update match history
            match_history = track.match_history or []
            match_history.append({
                "timestamp": frame.captured_at.isoformat(),
                "frame_id": frame.id,
                "confidence": person_data.get("confidence"),
                "match_factors": person_data.get("match_factors", {}),
            })
            track.match_history = match_history

            # Update confidence score (running average)
            current_avg = track.confidence_score or 0.0
            new_confidence = person_data.get("confidence", 0.0)
            track.confidence_score = (current_avg * (track.frame_count - 1) + new_confidence) / track.frame_count

            # Store in Redis
            await self._store_track_in_redis(track)

            logger.debug(f"Updated track {track_id}")
            return track

        except Exception as e:
            logger.error(f"Error updating track {track_id}: {e}")
            raise

    async def _store_track_in_redis(self, track: PersonTrack):
        """
        Store track in Redis for real-time access.

        Args:
            track: PersonTrack instance
        """
        try:
            redis_client = await get_redis()

            track_data = {
                "track_id": track.track_id,
                "first_seen": track.first_seen.isoformat(),
                "last_seen": track.last_seen.isoformat(),
                "appearance_signature": track.appearance_signature,
                "camera_ids": track.camera_ids,
                "camera_names": track.camera_names,
                "trajectory": track.trajectory[-10:],  # Last 10 points
                "confidence_score": track.confidence_score,
                "status": track.status,
            }

            # Store with TTL
            await redis_client.setex(
                f"track:{track.track_id}",
                settings.TRACK_TTL_SECONDS,
                json.dumps(track_data, default=str)
            )

        except Exception as e:
            logger.error(f"Error storing track in Redis: {e}")
            # Don't raise - Redis is for optimization, not critical

    async def get_active_tracks(
        self,
        db: AsyncSession,
        limit: int = 100
    ) -> List[PersonTrack]:
        """
        Get currently active person tracks.

        Args:
            db: Database session
            limit: Maximum number of tracks to return

        Returns:
            List of active PersonTrack instances
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=settings.TRACK_TTL_SECONDS)

            result = await db.execute(
                select(PersonTrack)
                .where(
                    and_(
                        PersonTrack.status == "active",
                        PersonTrack.last_seen >= cutoff_time
                    )
                )
                .order_by(PersonTrack.last_seen.desc())
                .limit(limit)
            )

            tracks = result.scalars().all()
            return list(tracks)

        except Exception as e:
            logger.error(f"Error retrieving active tracks: {e}")
            raise

    async def archive_inactive_tracks(self, db: AsyncSession):
        """
        Archive tracks that haven't been seen recently.

        Args:
            db: Database session
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(seconds=settings.TRACK_TTL_SECONDS * 2)

            result = await db.execute(
                select(PersonTrack).where(
                    and_(
                        PersonTrack.status == "active",
                        PersonTrack.last_seen < cutoff_time
                    )
                )
            )

            tracks = result.scalars().all()

            for track in tracks:
                track.status = "archived"

            await db.commit()

            logger.info(f"Archived {len(tracks)} inactive tracks")

        except Exception as e:
            logger.error(f"Error archiving tracks: {e}")
            raise


# Global service instance
_person_tracking_service: Optional[PersonTrackingService] = None


def get_person_tracking_service() -> PersonTrackingService:
    """Get or create global person tracking service instance."""
    global _person_tracking_service
    if _person_tracking_service is None:
        _person_tracking_service = PersonTrackingService()
    return _person_tracking_service
