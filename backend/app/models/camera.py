"""
Camera model for storing camera configuration and metadata.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Camera(Base):
    """Camera configuration and operational status."""

    __tablename__ = "cameras"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Camera identification
    name = Column(String(255), nullable=False, unique=True)
    camera_id = Column(String(100), nullable=False, unique=True, index=True)

    # Location information
    location = Column(String(500), nullable=False)
    facility_zone = Column(String(255), nullable=True, index=True)
    access_level = Column(String(100), nullable=True)
    location_type = Column(String(100), nullable=True)  # entrance, parking, hallway, etc.

    # Stream configuration
    stream_url = Column(Text, nullable=False)  # RTSP/RTMP/HLS URL
    stream_protocol = Column(String(50), default="rtsp")  # rtsp, rtmp, hls
    stream_username = Column(String(255), nullable=True)
    stream_password = Column(String(255), nullable=True)

    # Operational status
    is_active = Column(Boolean, default=True)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Processing configuration
    frame_extraction_fps = Column(Integer, default=1)
    motion_detection_enabled = Column(Boolean, default=True)
    motion_detection_fps = Column(Integer, default=5)
    motion_sensitivity = Column(Integer, default=50)  # 0-100

    # Additional metadata
    metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    frames = relationship("Frame", back_populates="camera", cascade="all, delete-orphan")
    threat_detections = relationship("ThreatDetection", back_populates="camera")

    def __repr__(self):
        return f"<Camera(id={self.id}, name='{self.name}', location='{self.location}')>"
