"""
Frame analysis service for processing video frames with Gemini AI.
Handles frame analysis, embedding generation, and storage in Qdrant.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client.models import PointStruct

from app.models.frame import Frame
from app.models.frame_analysis import FrameAnalysis
from app.models.camera import Camera
from app.database import get_qdrant_client
from app.services.gemini_client import get_gemini_client
from app.config import settings

logger = logging.getLogger(__name__)


class FrameAnalysisService:
    """Service for analyzing video frames and storing results."""

    def __init__(self):
        """Initialize frame analysis service."""
        self.gemini_client = get_gemini_client()
        self.qdrant_client = get_qdrant_client()

    async def analyze_frame(
        self,
        db: AsyncSession,
        frame: Frame,
        camera: Optional[Camera] = None
    ) -> FrameAnalysis:
        """
        Analyze a video frame using Gemini and store results.

        Args:
            db: Database session
            frame: Frame model instance
            camera: Optional camera instance for context

        Returns:
            FrameAnalysis model instance
        """
        try:
            logger.info(f"Analyzing frame {frame.frame_id}")

            # Load camera if not provided
            if camera is None:
                result = await db.execute(
                    select(Camera).where(Camera.id == frame.camera_id)
                )
                camera = result.scalar_one_or_none()

            # Prepare camera context
            camera_info = None
            if camera:
                camera_info = {
                    "name": camera.name,
                    "location": camera.location,
                    "facility_zone": camera.facility_zone,
                    "access_level": camera.access_level,
                    "location_type": camera.location_type,
                }

            # Analyze frame with Gemini
            analysis_result = self.gemini_client.analyze_frame(
                image_path=frame.frame_path,
                camera_info=camera_info
            )

            # Extract fields from analysis
            metadata = analysis_result.get("metadata", {})
            location_context = analysis_result.get("location_context", {})
            activity = analysis_result.get("activity_classification", {})
            threat = analysis_result.get("threat_assessment", {})

            # Create frame analysis record
            frame_analysis = FrameAnalysis(
                frame_id=frame.id,
                scene_description=analysis_result.get("scene_description"),
                location_context=camera.location if camera else None,
                facility_zone=location_context.get("location_type"),
                location_type=location_context.get("location_type"),
                access_level=location_context.get("access_level"),
                activity_category=activity.get("primary_activity"),
                activity_description=activity.get("activity_description"),
                activity_confidence=activity.get("confidence"),
                person_count=metadata.get("person_count", 0),
                person_profiles=analysis_result.get("persons_detected"),
                objects_detected=analysis_result.get("objects_detected"),
                vehicles_detected=analysis_result.get("vehicles_detected"),
                carried_objects=None,  # Extract from persons if needed
                threat_level=threat.get("threat_level", "none"),
                threat_confidence=threat.get("confidence"),
                threat_indicators=threat.get("threat_indicators"),
                searchable_phrases=analysis_result.get("searchable_phrases"),
                embedding_text=None,  # Will be generated next
                full_analysis_json=analysis_result,
                analysis_confidence=metadata.get("analysis_confidence"),
                model_version=analysis_result.get("model_version"),
                processing_time_ms=analysis_result.get("processing_time_ms"),
            )

            # Generate embedding text
            embedding_text = self.gemini_client.generate_embedding_text(analysis_result)
            frame_analysis.embedding_text = embedding_text

            # Generate embedding vector
            embedding_vector = self.gemini_client.generate_embedding(embedding_text)

            # Store in database
            db.add(frame_analysis)
            await db.flush()

            # Store in Qdrant
            await self._store_embedding(
                frame=frame,
                frame_analysis=frame_analysis,
                embedding_vector=embedding_vector,
                camera=camera
            )

            # Update frame processing status
            frame.processing_status = "completed"
            frame.processed_at = datetime.utcnow()

            await db.commit()

            logger.info(f"Frame {frame.frame_id} analysis completed successfully")
            return frame_analysis

        except Exception as e:
            logger.error(f"Frame analysis error for {frame.frame_id}: {e}")
            frame.processing_status = "failed"
            frame.processing_error = str(e)
            await db.commit()
            raise

    async def _store_embedding(
        self,
        frame: Frame,
        frame_analysis: FrameAnalysis,
        embedding_vector: List[float],
        camera: Optional[Camera] = None
    ):
        """
        Store frame embedding in Qdrant with comprehensive metadata.

        Args:
            frame: Frame model instance
            frame_analysis: FrameAnalysis model instance
            embedding_vector: 768-dimensional embedding vector
            camera: Optional camera instance
        """
        try:
            # Prepare payload with comprehensive metadata
            payload = {
                "frame_id": frame.id,
                "frame_uuid": frame.frame_id,
                "video_id": frame.video_id,
                "camera_id": frame.camera_id,
                "camera_name": camera.name if camera else None,
                "timestamp": frame.captured_at.isoformat(),
                "timestamp_unix": int(frame.captured_at.timestamp()),
                "hour_of_day": frame.hour_of_day,
                "day_of_week": frame.day_of_week,
                "is_business_hours": frame.is_business_hours,
                "facility_zone": camera.facility_zone if camera else None,
                "location": camera.location if camera else None,
                "location_type": frame_analysis.location_type,
                "access_level": frame_analysis.access_level,
                "person_count": frame_analysis.person_count,
                "activity_category": frame_analysis.activity_category,
                "threat_level": frame_analysis.threat_level,
                "has_vehicles": bool(frame_analysis.vehicles_detected),
                "has_carried_objects": bool(frame_analysis.carried_objects),
                "analysis_confidence": frame_analysis.analysis_confidence,
                "frame_quality": frame.frame_quality,
                "scene_description": frame_analysis.scene_description,
                "embedding_text": frame_analysis.embedding_text,
                "searchable_phrases": frame_analysis.searchable_phrases,
            }

            # Create point for Qdrant
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding_vector,
                payload=payload
            )

            # Upsert to Qdrant
            self.qdrant_client.upsert(
                collection_name=settings.QDRANT_COLLECTION,
                points=[point]
            )

            logger.debug(f"Stored embedding for frame {frame.frame_id} in Qdrant")

        except Exception as e:
            logger.error(f"Qdrant storage error for frame {frame.frame_id}: {e}")
            raise

    async def get_frame_with_analysis(
        self,
        db: AsyncSession,
        frame_id: int
    ) -> Optional[tuple[Frame, Optional[FrameAnalysis]]]:
        """
        Retrieve frame with its analysis.

        Args:
            db: Database session
            frame_id: Frame ID

        Returns:
            Tuple of (Frame, FrameAnalysis) or None
        """
        try:
            # Query frame
            result = await db.execute(
                select(Frame).where(Frame.id == frame_id)
            )
            frame = result.scalar_one_or_none()

            if not frame:
                return None

            # Query analysis
            result = await db.execute(
                select(FrameAnalysis).where(FrameAnalysis.frame_id == frame_id)
            )
            analysis = result.scalar_one_or_none()

            return frame, analysis

        except Exception as e:
            logger.error(f"Error retrieving frame {frame_id}: {e}")
            raise

    async def batch_analyze_frames(
        self,
        db: AsyncSession,
        frame_ids: List[int]
    ) -> List[FrameAnalysis]:
        """
        Batch analyze multiple frames for efficiency.

        Args:
            db: Database session
            frame_ids: List of frame IDs to analyze

        Returns:
            List of FrameAnalysis instances
        """
        results = []

        for frame_id in frame_ids:
            try:
                result = await db.execute(
                    select(Frame).where(Frame.id == frame_id)
                )
                frame = result.scalar_one_or_none()

                if frame and frame.processing_status == "pending":
                    analysis = await self.analyze_frame(db, frame)
                    results.append(analysis)

            except Exception as e:
                logger.error(f"Batch analysis error for frame {frame_id}: {e}")
                continue

        return results


# Global service instance
_frame_analysis_service: Optional[FrameAnalysisService] = None


def get_frame_analysis_service() -> FrameAnalysisService:
    """Get or create global frame analysis service instance."""
    global _frame_analysis_service
    if _frame_analysis_service is None:
        _frame_analysis_service = FrameAnalysisService()
    return _frame_analysis_service
