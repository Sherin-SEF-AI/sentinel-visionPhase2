"""
Person tracking schemas.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class AppearanceSignature(BaseModel):
    """Person appearance signature."""
    clothing_upper: Optional[str] = None
    clothing_lower: Optional[str] = None
    colors: List[str] = []
    physical_characteristics: Optional[str] = None
    distinctive_features: List[str] = []
    hair_style: Optional[str] = None
    accessories: List[str] = []


class TrajectoryPoint(BaseModel):
    """Single point in person trajectory."""
    timestamp: datetime
    camera_id: int
    camera_name: Optional[str] = None
    frame_id: int
    position: Optional[Dict[str, Any]] = None
    facility_zone: Optional[str] = None


class PersonTrackResponse(BaseModel):
    """Schema for person track response."""
    id: int
    track_id: str

    first_seen: datetime
    last_seen: datetime
    duration_seconds: Optional[int]

    appearance_signature: AppearanceSignature
    clothing_description: Optional[str]
    physical_characteristics: Optional[str]
    distinctive_features: Optional[List[str]]

    camera_ids: List[int]
    camera_names: Optional[List[str]]
    trajectory: List[TrajectoryPoint]
    zones_visited: Optional[List[str]]

    frame_count: int
    confidence_score: Optional[float]

    status: str
    is_person_of_interest: bool
    notes: Optional[str]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class TrackingUpdate(BaseModel):
    """Schema for updating person track."""
    status: Optional[str] = Field(None, description="active, inactive, archived")
    is_person_of_interest: Optional[bool] = None
    notes: Optional[str] = None


class TrackMatchResult(BaseModel):
    """Result of track matching attempt."""
    matched: bool
    track_id: Optional[str] = None
    confidence: float
    match_factors: Dict[str, float]
    explanation: str


class ActiveTrackSummary(BaseModel):
    """Summary of active person track."""
    track_id: str
    current_camera: str
    current_location: str
    appearance_summary: str
    duration_seconds: int
    last_seen_seconds_ago: int


class TrackingStatistics(BaseModel):
    """Person tracking statistics."""
    active_tracks: int
    total_tracks_today: int
    average_track_duration_seconds: float
    unique_persons_detected: int
    cross_camera_transitions: int
    persons_of_interest: int
