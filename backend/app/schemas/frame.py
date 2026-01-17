"""
Frame and frame analysis schemas.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.common import LocationInfo


class FrameBase(BaseModel):
    """Base frame schema."""
    frame_id: str
    camera_id: int
    captured_at: datetime


class FrameResponse(FrameBase):
    """Schema for frame response."""
    id: int
    video_id: Optional[str]

    hour_of_day: Optional[int]
    day_of_week: Optional[int]
    is_business_hours: bool

    motion_detected: bool
    motion_intensity: Optional[float]

    frame_quality: Optional[str]
    quality_score: Optional[float]

    frame_path: str
    thumbnail_path: Optional[str]

    processing_status: str
    processed_at: Optional[datetime]

    created_at: datetime

    class Config:
        from_attributes = True


class PersonProfile(BaseModel):
    """Person appearance profile."""
    person_id: int
    clothing_upper: Optional[str] = None
    clothing_lower: Optional[str] = None
    colors: Optional[List[str]] = None
    carried_objects: Optional[List[str]] = None
    physical_characteristics: Optional[str] = None
    distinctive_features: Optional[List[str]] = None
    position: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None


class ObjectDetection(BaseModel):
    """Detected object information."""
    object_type: str
    description: str
    confidence: float
    position: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None


class FrameAnalysisResponse(BaseModel):
    """Schema for frame analysis response."""
    id: int
    frame_id: int

    scene_description: Optional[str]
    location_context: Optional[str]
    facility_zone: Optional[str]
    location_type: Optional[str]
    access_level: Optional[str]

    activity_category: Optional[str]
    activity_description: Optional[str]
    activity_confidence: Optional[float]

    person_count: int
    person_profiles: Optional[List[PersonProfile]]

    objects_detected: Optional[List[ObjectDetection]]
    vehicles_detected: Optional[List[Dict[str, Any]]]
    carried_objects: Optional[List[Dict[str, Any]]]

    threat_level: str
    threat_confidence: Optional[float]
    threat_indicators: Optional[List[str]]

    searchable_phrases: Optional[List[str]]

    analysis_confidence: Optional[float]
    model_version: Optional[str]
    processing_time_ms: Optional[int]

    analyzed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class FrameWithAnalysis(FrameResponse):
    """Frame with its analysis data."""
    analysis: Optional[FrameAnalysisResponse] = None
    location: Optional[LocationInfo] = None


class FrameListResponse(BaseModel):
    """Response schema for frame list."""
    frames: List[FrameWithAnalysis]
    total: int
    page: int
    page_size: int
