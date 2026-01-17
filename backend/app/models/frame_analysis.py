"""
Frame analysis model for storing Gemini vision analysis results.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class FrameAnalysis(Base):
    """Gemini vision analysis results for video frames."""

    __tablename__ = "frame_analysis"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Frame reference
    frame_id = Column(Integer, ForeignKey("frames.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Scene understanding
    scene_description = Column(Text, nullable=True)
    location_context = Column(String(255), nullable=True)
    facility_zone = Column(String(255), nullable=True, index=True)
    location_type = Column(String(100), nullable=True, index=True)
    access_level = Column(String(100), nullable=True)

    # Activity classification
    activity_category = Column(String(100), nullable=True, index=True)
    activity_description = Column(Text, nullable=True)
    activity_confidence = Column(Float, nullable=True)

    # Person detection
    person_count = Column(Integer, default=0, index=True)
    person_profiles = Column(JSON, nullable=True)  # Array of person appearance data

    # Object detection
    objects_detected = Column(JSON, nullable=True)  # Array of detected objects
    vehicles_detected = Column(JSON, nullable=True)  # Array of vehicle information
    carried_objects = Column(JSON, nullable=True)  # Array of carried items

    # Threat assessment
    threat_level = Column(String(50), default="none", index=True)  # none, low, medium, high, critical
    threat_confidence = Column(Float, nullable=True)
    threat_indicators = Column(JSON, nullable=True)  # Array of threat indicators

    # Searchable content
    searchable_phrases = Column(JSON, nullable=True)  # Array of natural language phrases
    embedding_text = Column(Text, nullable=True)  # Optimized text for embedding generation

    # Full analysis data
    full_analysis_json = Column(JSON, nullable=False)  # Complete Gemini response

    # Quality metrics
    analysis_confidence = Column(Float, nullable=True)
    model_version = Column(String(100), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Timestamps
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    frame = relationship("Frame", back_populates="analysis")

    def __repr__(self):
        return f"<FrameAnalysis(id={self.id}, frame_id={self.frame_id}, activity={self.activity_category})>"
