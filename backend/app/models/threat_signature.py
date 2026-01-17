"""
Threat signature model for storing threat detection patterns.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class ThreatSignature(Base):
    """Threat signatures for pattern-based threat detection."""

    __tablename__ = "threat_signatures"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Signature identification
    signature_id = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Classification
    category = Column(String(100), nullable=False, index=True)  # high_severity, perimeter_control, etc.
    severity = Column(String(50), nullable=False, index=True)  # critical, high, medium, low
    threat_type = Column(String(100), nullable=True, index=True)

    # Signature definition
    trigger_conditions = Column(JSON, nullable=False)  # Conditions that trigger this signature
    differentiation_rules = Column(JSON, nullable=True)  # Rules to differentiate from similar signatures
    contextual_rules = Column(JSON, nullable=True)  # Context-based reclassification rules

    # Detection parameters
    confidence_threshold = Column(Float, default=0.60)
    temporal_window_seconds = Column(Integer, nullable=True)
    spatial_requirements = Column(JSON, nullable=True)
    environmental_factors = Column(JSON, nullable=True)

    # Response configuration
    alert_enabled = Column(Boolean, default=True)
    alert_priority = Column(String(50), default="medium")  # critical, high, medium, low
    recommended_actions = Column(JSON, nullable=True)  # Array of recommended response actions
    notification_targets = Column(JSON, nullable=True)  # Who should be notified

    # Custom signature
    is_custom = Column(Boolean, default=False, index=True)
    created_by = Column(String(255), nullable=True)
    natural_language_definition = Column(Text, nullable=True)  # Original NL description if custom

    # Usage statistics
    detection_count = Column(Integer, default=0)
    true_positive_count = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)
    last_detection_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    is_active = Column(Boolean, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    detections = relationship("ThreatDetection", back_populates="signature")

    def __repr__(self):
        return f"<ThreatSignature(id={self.id}, name='{self.name}', severity='{self.severity}')>"
