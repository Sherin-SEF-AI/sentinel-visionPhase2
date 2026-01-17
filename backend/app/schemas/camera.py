"""
Camera-related schemas for API validation.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class CameraBase(BaseModel):
    """Base camera schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="Camera name")
    location: str = Field(..., min_length=1, max_length=500, description="Camera location")
    facility_zone: Optional[str] = Field(None, max_length=255, description="Facility zone")
    access_level: Optional[str] = Field(None, max_length=100, description="Access level")
    location_type: Optional[str] = Field(None, max_length=100, description="Location type")


class CameraCreate(CameraBase):
    """Schema for creating a new camera."""
    camera_id: str = Field(..., min_length=1, max_length=100, description="Unique camera identifier")
    stream_url: str = Field(..., description="RTSP/RTMP/HLS stream URL")
    stream_protocol: str = Field(default="rtsp", description="Stream protocol")
    stream_username: Optional[str] = Field(None, max_length=255)
    stream_password: Optional[str] = Field(None, max_length=255)

    frame_extraction_fps: int = Field(default=1, ge=1, le=30)
    motion_detection_enabled: bool = Field(default=True)
    motion_detection_fps: int = Field(default=5, ge=1, le=30)
    motion_sensitivity: int = Field(default=50, ge=0, le=100)

    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class CameraUpdate(BaseModel):
    """Schema for updating camera configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    facility_zone: Optional[str] = Field(None, max_length=255)
    access_level: Optional[str] = Field(None, max_length=100)
    location_type: Optional[str] = Field(None, max_length=100)

    stream_url: Optional[str] = None
    stream_protocol: Optional[str] = None
    stream_username: Optional[str] = None
    stream_password: Optional[str] = None

    is_active: Optional[bool] = None

    frame_extraction_fps: Optional[int] = Field(None, ge=1, le=30)
    motion_detection_enabled: Optional[bool] = None
    motion_detection_fps: Optional[int] = Field(None, ge=1, le=30)
    motion_sensitivity: Optional[int] = Field(None, ge=0, le=100)

    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class CameraResponse(CameraBase):
    """Schema for camera response."""
    id: int
    camera_id: str
    stream_url: str
    stream_protocol: str

    is_active: bool
    is_online: bool
    last_seen: Optional[datetime]

    frame_extraction_fps: int
    motion_detection_enabled: bool
    motion_detection_fps: int
    motion_sensitivity: int

    metadata: Optional[Dict[str, Any]]
    notes: Optional[str]

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CameraStatus(BaseModel):
    """Camera operational status."""
    camera_id: str
    is_online: bool
    last_seen: Optional[datetime]
    frame_rate: Optional[float]
    frames_processed: Optional[int]
    processing_lag_ms: Optional[int]
    error_message: Optional[str]


class CameraListResponse(BaseModel):
    """Response schema for camera list."""
    cameras: list[CameraResponse]
    total: int
    page: int
    page_size: int
