"""
Threat detection model for storing detected threats and alerts.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ThreatDetection(Base):
    """Detected threats and security alerts."""

    __tablename__ = "threat_detections"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Detection identification
    detection_id = Column(String(100), nullable=False, unique=True, index=True)

    # Source references
    frame_id = Column(Integer, ForeignKey("frames.id", ondelete="CASCADE"), nullable=False, index=True)
    camera_id = Column(Integer, ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True, index=True)
    signature_id = Column(Integer, ForeignKey("threat_signatures.id", ondelete="SET NULL"), nullable=True, index=True)

    # Temporal information
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True)
    detection_timestamp = Column(DateTime(timezone=True), nullable=False)

    # Threat classification
    threat_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)  # critical, high, medium, low
    category = Column(String(100), nullable=True, index=True)

    # Confidence and evidence
    confidence_score = Column(Float, nullable=False, index=True)
    confidence_breakdown = Column(JSON, nullable=True)  # Component confidence scores
    evidence_summary = Column(Text, nullable=True)
    visual_evidence_path = Column(Text, nullable=True)

    # Contextual data
    context_data = Column(JSON, nullable=False)  # Data that triggered the signature
    location = Column(String(500), nullable=True)
    facility_zone = Column(String(255), nullable=True, index=True)
    environmental_context = Column(JSON, nullable=True)

    # Associated entities
    person_track_ids = Column(JSON, nullable=True)  # Array of related person tracks
    related_detection_ids = Column(JSON, nullable=True)  # Array of related detection IDs

    # Alert management
    alert_status = Column(String(50), default="pending", index=True)  # pending, acknowledged, investigating, resolved, false_positive
    alert_priority = Column(String(50), nullable=True)
    alert_message = Column(Text, nullable=True)

    # Operator response
    acknowledged_by = Column(String(255), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    response_actions = Column(JSON, nullable=True)  # Array of actions taken
    operator_notes = Column(Text, nullable=True)

    # Verification
    is_true_positive = Column(Boolean, nullable=True)
    verification_notes = Column(Text, nullable=True)
    verified_by = Column(String(255), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    signature = relationship("ThreatSignature", back_populates="detections")
    camera = relationship("Camera", back_populates="threat_detections")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_detection_temporal_severity", "detected_at", "severity"),
        Index("idx_detection_status_priority", "alert_status", "alert_priority"),
    )

    def __repr__(self):
        return f"<ThreatDetection(id={self.id}, type='{self.threat_type}', severity='{self.severity}')>"
