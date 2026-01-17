"""
Threat detection and signature schemas.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.common import ConfidenceScore, LocationInfo


class ThreatSignatureBase(BaseModel):
    """Base threat signature schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str
    severity: str = Field(..., description="critical, high, medium, low")
    threat_type: Optional[str] = None


class ThreatSignatureCreate(ThreatSignatureBase):
    """Schema for creating a threat signature."""
    signature_id: str = Field(..., min_length=1, max_length=100)

    trigger_conditions: Dict[str, Any]
    differentiation_rules: Optional[Dict[str, Any]] = None
    contextual_rules: Optional[Dict[str, Any]] = None

    confidence_threshold: float = Field(default=0.60, ge=0.0, le=1.0)
    temporal_window_seconds: Optional[int] = None
    spatial_requirements: Optional[Dict[str, Any]] = None
    environmental_factors: Optional[Dict[str, Any]] = None

    alert_enabled: bool = Field(default=True)
    alert_priority: str = Field(default="medium")
    recommended_actions: Optional[List[str]] = None
    notification_targets: Optional[List[str]] = None

    is_custom: bool = Field(default=False)
    natural_language_definition: Optional[str] = None


class ThreatSignatureUpdate(BaseModel):
    """Schema for updating a threat signature."""
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None

    trigger_conditions: Optional[Dict[str, Any]] = None
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)

    alert_enabled: Optional[bool] = None
    alert_priority: Optional[str] = None
    recommended_actions: Optional[List[str]] = None

    is_active: Optional[bool] = None


class ThreatSignatureResponse(ThreatSignatureBase):
    """Schema for threat signature response."""
    id: int
    signature_id: str

    trigger_conditions: Dict[str, Any]
    differentiation_rules: Optional[Dict[str, Any]]
    contextual_rules: Optional[Dict[str, Any]]

    confidence_threshold: float
    temporal_window_seconds: Optional[int]

    alert_enabled: bool
    alert_priority: str
    recommended_actions: Optional[List[str]]

    is_custom: bool
    natural_language_definition: Optional[str]

    detection_count: int
    true_positive_count: int
    false_positive_count: int
    last_detection_at: Optional[datetime]

    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ThreatDetectionResponse(BaseModel):
    """Schema for threat detection response."""
    id: int
    detection_id: str

    frame_id: int
    camera_id: Optional[int]
    signature_id: Optional[int]

    detected_at: datetime
    detection_timestamp: datetime

    threat_type: str
    severity: str
    category: Optional[str]

    confidence_score: float
    confidence_breakdown: Optional[ConfidenceScore]
    evidence_summary: Optional[str]
    visual_evidence_path: Optional[str]

    context_data: Dict[str, Any]
    location: Optional[LocationInfo] = None

    person_track_ids: Optional[List[str]]
    related_detection_ids: Optional[List[str]]

    alert_status: str
    alert_priority: Optional[str]
    alert_message: Optional[str]

    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    response_actions: Optional[List[str]]
    operator_notes: Optional[str]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ThreatDetectionUpdate(BaseModel):
    """Schema for updating threat detection status."""
    alert_status: Optional[str] = Field(None, description="pending, acknowledged, investigating, resolved, false_positive")
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    response_actions: Optional[List[str]] = None
    operator_notes: Optional[str] = None
    is_true_positive: Optional[bool] = None
    verification_notes: Optional[str] = None


class ThreatAlertWebSocket(BaseModel):
    """Real-time threat alert for WebSocket."""
    detection_id: str
    threat_type: str
    severity: str
    confidence_score: float
    alert_message: str
    camera_id: Optional[int]
    camera_name: Optional[str]
    location: Optional[str]
    timestamp: datetime
    visual_evidence_url: Optional[str]
    recommended_actions: Optional[List[str]]


class ThreatStatistics(BaseModel):
    """Threat detection statistics."""
    total_detections: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]
    by_status: Dict[str, int]
    active_alerts: int
    resolved_today: int
    average_response_time_minutes: Optional[float]


class CustomSignatureRequest(BaseModel):
    """Request to create custom threat signature from natural language."""
    description: str = Field(..., min_length=10, description="Natural language threat description")
    severity: str = Field(..., description="critical, high, medium, low")
    category: str = Field(..., description="Threat category")
    alert_priority: str = Field(default="medium")
