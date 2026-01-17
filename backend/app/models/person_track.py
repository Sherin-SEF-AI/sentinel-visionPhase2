"""
Person track model for maintaining identity continuity across frames.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Index
from sqlalchemy.sql import func

from app.database import Base


class PersonTrack(Base):
    """Person tracking records maintaining identity across frames and cameras."""

    __tablename__ = "person_tracks"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Track identification
    track_id = Column(String(100), nullable=False, unique=True, index=True)

    # Temporal span
    first_seen = Column(DateTime(timezone=True), nullable=False, index=True)
    last_seen = Column(DateTime(timezone=True), nullable=False, index=True)
    duration_seconds = Column(Integer, nullable=True)

    # Appearance signature
    appearance_signature = Column(JSON, nullable=False)  # Comprehensive appearance data
    clothing_description = Column(Text, nullable=True)
    physical_characteristics = Column(Text, nullable=True)
    distinctive_features = Column(JSON, nullable=True)

    # Movement data
    camera_ids = Column(JSON, nullable=False)  # Array of camera IDs where person was seen
    camera_names = Column(JSON, nullable=True)  # Array of camera names
    trajectory = Column(JSON, nullable=False)  # Array of {timestamp, camera_id, position, frame_id}
    zones_visited = Column(JSON, nullable=True)  # Array of facility zones

    # Tracking metrics
    frame_count = Column(Integer, default=0)
    confidence_score = Column(Float, nullable=True)  # Overall track confidence
    match_history = Column(JSON, nullable=True)  # History of appearance matches

    # Track status
    status = Column(String(50), default="active", index=True)  # active, inactive, archived
    is_person_of_interest = Column(Boolean, default=False, index=True)
    notes = Column(Text, nullable=True)

    # Associated data
    frame_ids = Column(JSON, nullable=False)  # Array of all frame IDs in this track
    detection_ids = Column(JSON, nullable=True)  # Array of threat detection IDs

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes for common queries
    __table_args__ = (
        Index("idx_track_temporal", "first_seen", "last_seen"),
        Index("idx_track_status_lastseen", "status", "last_seen"),
    )

    def __repr__(self):
        return f"<PersonTrack(id={self.id}, track_id='{self.track_id}', status='{self.status}')>"
