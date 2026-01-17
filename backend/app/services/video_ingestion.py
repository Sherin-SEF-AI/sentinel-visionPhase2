"""
Video ingestion service for capturing frames from camera streams.
Supports RTSP, RTMP, and HLS protocols with motion detection.
"""

import logging
import cv2
import numpy as np
import asyncio
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading
from queue import Queue, Empty

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camera import Camera
from app.models.frame import Frame
from app.config import settings
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class CameraStreamHandler:
    """Handles individual camera stream processing."""

    def __init__(self, camera: Camera):
        """Initialize camera stream handler."""
        self.camera = camera
        self.stream_url = camera.stream_url
        self.capture: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.frame_count = 0
        self.last_frame_time = None
        self.motion_detector = MotionDetector()
        self.frame_queue = Queue(maxsize=50)

    def start(self):
        """Start capturing from camera stream."""
        try:
            logger.info(f"Starting stream for camera {self.camera.name}")

            # Open video capture
            self.capture = cv2.VideoCapture(self.stream_url)

            if not self.capture.isOpened():
                logger.error(f"Failed to open stream: {self.stream_url}")
                return

            self.is_running = True

            # Start capture thread
            capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            capture_thread.start()

            logger.info(f"Stream started successfully for {self.camera.name}")

        except Exception as e:
            logger.error(f"Error starting stream for {self.camera.name}: {e}")
            self.is_running = False

    def _capture_loop(self):
        """Main capture loop running in separate thread."""
        consecutive_failures = 0
        max_failures = 10

        while self.is_running:
            try:
                ret, frame = self.capture.read()

                if not ret:
                    consecutive_failures += 1
                    logger.warning(f"Failed to read frame from {self.camera.name} ({consecutive_failures}/{max_failures})")

                    if consecutive_failures >= max_failures:
                        logger.error(f"Max failures reached for {self.camera.name}, stopping stream")
                        self.stop()
                        break

                    # Try to reconnect
                    self._reconnect()
                    continue

                # Reset failure count on success
                consecutive_failures = 0

                # Check if we should process this frame
                current_time = datetime.utcnow()

                # Calculate time since last frame
                if self.last_frame_time:
                    time_since_last = (current_time - self.last_frame_time).total_seconds()

                    # Normal frame extraction rate
                    if time_since_last >= (1.0 / self.camera.frame_extraction_fps):
                        self._process_frame(frame, current_time, motion_detected=False)
                        self.last_frame_time = current_time
                else:
                    self.last_frame_time = current_time

                # Check for motion if enabled
                if self.camera.motion_detection_enabled:
                    motion_detected = self.motion_detector.detect_motion(frame)

                    if motion_detected:
                        # Higher frame rate during motion
                        self._process_frame(frame, current_time, motion_detected=True)

                # Small sleep to prevent CPU overload
                asyncio.sleep(0.01)

            except Exception as e:
                logger.error(f"Error in capture loop for {self.camera.name}: {e}")
                consecutive_failures += 1

    def _process_frame(self, frame: np.ndarray, timestamp: datetime, motion_detected: bool):
        """Process captured frame and queue for analysis."""
        try:
            # Quality assessment
            quality_score = self._assess_frame_quality(frame)

            if quality_score < 0.3:  # Skip very low quality frames
                return

            # Generate frame ID
            frame_id = f"frame_{self.camera.camera_id}_{uuid.uuid4().hex[:12]}"

            # Save frame to disk
            frame_path = self._save_frame(frame, frame_id)

            # Create thumbnail
            thumbnail_path = self._create_thumbnail(frame, frame_id)

            # Prepare frame data
            frame_data = {
                "frame_id": frame_id,
                "camera_id": self.camera.id,
                "captured_at": timestamp,
                "hour_of_day": timestamp.hour,
                "day_of_week": timestamp.weekday(),
                "is_business_hours": self._is_business_hours(timestamp),
                "motion_detected": motion_detected,
                "frame_quality": self._quality_label(quality_score),
                "quality_score": quality_score,
                "frame_path": frame_path,
                "thumbnail_path": thumbnail_path,
                "processing_status": "pending",
            }

            # Add to queue for database insertion
            if not self.frame_queue.full():
                self.frame_queue.put(frame_data)
                self.frame_count += 1
            else:
                logger.warning(f"Frame queue full for {self.camera.name}, dropping frame")

        except Exception as e:
            logger.error(f"Error processing frame for {self.camera.name}: {e}")

    def _save_frame(self, frame: np.ndarray, frame_id: str) -> str:
        """Save frame to disk."""
        frame_dir = Path(settings.FRAME_STORAGE_PATH)
        frame_dir.mkdir(parents=True, exist_ok=True)

        frame_path = frame_dir / f"{frame_id}.jpg"
        cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        return str(frame_path)

    def _create_thumbnail(self, frame: np.ndarray, frame_id: str) -> str:
        """Create thumbnail from frame."""
        thumbnail_dir = Path(settings.THUMBNAIL_STORAGE_PATH)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)

        # Resize to thumbnail
        height, width = frame.shape[:2]
        scale = 320.0 / width
        thumbnail = cv2.resize(frame, (320, int(height * scale)))

        thumbnail_path = thumbnail_dir / f"{frame_id}_thumb.jpg"
        cv2.imwrite(str(thumbnail_path), thumbnail, [cv2.IMWRITE_JPEG_QUALITY, 75])

        return str(thumbnail_path)

    def _assess_frame_quality(self, frame: np.ndarray) -> float:
        """Assess frame quality using blur detection."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

        # Normalize to 0-1 range (higher is better)
        # Typical values: >100 = good, 50-100 = acceptable, <50 = blurry
        quality = min(laplacian_var / 100.0, 1.0)

        return quality

    def _quality_label(self, score: float) -> str:
        """Convert quality score to label."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        else:
            return "poor"

    def _is_business_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is during business hours."""
        hour = timestamp.hour
        day = timestamp.weekday()

        # Monday-Friday, 7 AM - 7 PM
        return day < 5 and 7 <= hour < 19

    def _reconnect(self):
        """Attempt to reconnect to stream."""
        logger.info(f"Attempting to reconnect to {self.camera.name}")

        if self.capture:
            self.capture.release()

        # Wait before reconnecting
        asyncio.sleep(5)

        self.capture = cv2.VideoCapture(self.stream_url)

    def stop(self):
        """Stop capturing from camera stream."""
        logger.info(f"Stopping stream for camera {self.camera.name}")
        self.is_running = False

        if self.capture:
            self.capture.release()
            self.capture = None

    def get_queued_frames(self) -> List[Dict[str, Any]]:
        """Get all queued frames for database insertion."""
        frames = []

        while not self.frame_queue.empty():
            try:
                frames.append(self.frame_queue.get_nowait())
            except Empty:
                break

        return frames


class MotionDetector:
    """Simple motion detection using background subtraction."""

    def __init__(self):
        """Initialize motion detector."""
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500,
            varThreshold=16,
            detectShadows=True
        )
        self.min_motion_area = 1000  # Minimum pixels for motion

    def detect_motion(self, frame: np.ndarray) -> bool:
        """Detect if there is significant motion in frame."""
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)

        # Remove shadows
        fg_mask[fg_mask == 127] = 0

        # Find contours
        contours, _ = cv2.findContours(
            fg_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Check if any contour is large enough
        for contour in contours:
            if cv2.contourArea(contour) > self.min_motion_area:
                return True

        return False


class VideoIngestionService:
    """Service for managing multiple camera streams."""

    def __init__(self):
        """Initialize video ingestion service."""
        self.stream_handlers: Dict[int, CameraStreamHandler] = {}
        self.is_running = False

    async def start(self):
        """Start video ingestion for all active cameras."""
        logger.info("Starting video ingestion service")
        self.is_running = True

        # Start ingestion loop
        asyncio.create_task(self._ingestion_loop())

    async def _ingestion_loop(self):
        """Main ingestion loop."""
        while self.is_running:
            try:
                # Get active cameras
                async with AsyncSessionLocal() as db:
                    result = await db.execute(
                        select(Camera).where(Camera.is_active == True)
                    )
                    cameras = list(result.scalars().all())

                # Start streams for new cameras
                for camera in cameras:
                    if camera.id not in self.stream_handlers:
                        handler = CameraStreamHandler(camera)
                        handler.start()
                        self.stream_handlers[camera.id] = handler

                # Stop streams for removed cameras
                active_ids = {c.id for c in cameras}
                for camera_id in list(self.stream_handlers.keys()):
                    if camera_id not in active_ids:
                        self.stream_handlers[camera_id].stop()
                        del self.stream_handlers[camera_id]

                # Process queued frames
                await self._process_queued_frames()

                # Wait before next iteration
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Error in ingestion loop: {e}")
                await asyncio.sleep(30)

    async def _process_queued_frames(self):
        """Process queued frames from all handlers."""
        async with AsyncSessionLocal() as db:
            for handler in self.stream_handlers.values():
                frames_data = handler.get_queued_frames()

                for frame_data in frames_data:
                    try:
                        frame = Frame(**frame_data)
                        db.add(frame)
                    except Exception as e:
                        logger.error(f"Error adding frame to database: {e}")

            try:
                await db.commit()
            except Exception as e:
                logger.error(f"Error committing frames: {e}")
                await db.rollback()

    async def stop(self):
        """Stop video ingestion service."""
        logger.info("Stopping video ingestion service")
        self.is_running = False

        # Stop all stream handlers
        for handler in self.stream_handlers.values():
            handler.stop()

        self.stream_handlers.clear()

    async def add_camera_stream(self, camera_id: int):
        """Start stream for specific camera."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Camera).where(Camera.id == camera_id)
            )
            camera = result.scalar_one_or_none()

            if camera and camera.is_active:
                if camera_id not in self.stream_handlers:
                    handler = CameraStreamHandler(camera)
                    handler.start()
                    self.stream_handlers[camera_id] = handler
                    logger.info(f"Started stream for camera {camera.name}")

    async def remove_camera_stream(self, camera_id: int):
        """Stop stream for specific camera."""
        if camera_id in self.stream_handlers:
            self.stream_handlers[camera_id].stop()
            del self.stream_handlers[camera_id]
            logger.info(f"Stopped stream for camera ID {camera_id}")

    def get_stream_status(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all camera streams."""
        status = {}

        for camera_id, handler in self.stream_handlers.items():
            status[camera_id] = {
                "camera_name": handler.camera.name,
                "is_running": handler.is_running,
                "frames_captured": handler.frame_count,
                "queue_size": handler.frame_queue.qsize(),
            }

        return status


# Global service instance
_video_ingestion_service: Optional[VideoIngestionService] = None


def get_video_ingestion_service() -> VideoIngestionService:
    """Get or create global video ingestion service instance."""
    global _video_ingestion_service
    if _video_ingestion_service is None:
        _video_ingestion_service = VideoIngestionService()
    return _video_ingestion_service
