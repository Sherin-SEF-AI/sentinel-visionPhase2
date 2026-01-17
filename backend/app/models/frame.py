"""
Frame model for storing extracted video frames and metadata.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Frame(Base):
    """Video frames extracted from camera streams."""

    __tablename__ = "frames"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Frame identification
    frame_id = Column(String(100), nullable=False, unique=True, index=True)

    # Source information
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(String(255), nullable=True, index=True)  # Source video file identifier

    # Temporal information
    captured_at = Column(DateTime(timezone=True), nullable=False, index=True)
    hour_of_day = Column(Integer, nullable=True)  # 0-23 for temporal queries
    day_of_week = Column(Integer, nullable=True)  # 0-6 for pattern analysis
    is_business_hours = Column(Boolean, default=True)

    # Motion detection
    motion_detected = Column(Boolean, default=False, index=True)
    motion_intensity = Column(Float, nullable=True)  # 0.0-1.0
    motion_regions = Column(Text, nullable=True)  # JSON string of bounding boxes

    # Frame quality assessment
    frame_quality = Column(String(50), nullable=True)  # excellent, good, fair, poor
    quality_score = Column(Float, nullable=True)  # 0.0-1.0
    blur_score = Column(Float, nullable=True)
    brightness_score = Column(Float, nullable=True)

    # Storage paths
    frame_path = Column(Text, nullable=False)
    thumbnail_path = Column(Text, nullable=True)

    # Processing status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    camera = relationship("Camera", back_populates="frames")
    analysis = relationship("FrameAnalysis", back_populates="frame", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Frame(id={self.id}, frame_id='{self.frame_id}', captured_at={self.captured_at})>"
