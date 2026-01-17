"""
Common schemas used across multiple endpoints.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    timestamp: datetime
    services: Dict[str, Dict[str, Any]]


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class TimeRangeFilter(BaseModel):
    """Time range filter for temporal queries."""
    start_time: Optional[datetime] = Field(default=None, description="Start of time range")
    end_time: Optional[datetime] = Field(default=None, description="End of time range")


class ConfidenceScore(BaseModel):
    """Confidence score with breakdown."""
    total: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    semantic_relevance: Optional[float] = Field(None, ge=0.0, le=1.0)
    entity_match: Optional[float] = Field(None, ge=0.0, le=1.0)
    temporal_relevance: Optional[float] = Field(None, ge=0.0, le=1.0)
    visual_quality: Optional[float] = Field(None, ge=0.0, le=1.0)


class LocationInfo(BaseModel):
    """Location information schema."""
    camera_id: Optional[int] = None
    camera_name: Optional[str] = None
    location: Optional[str] = None
    facility_zone: Optional[str] = None
    location_type: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: Dict[str, Any] = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "type": "validation_error",
                    "message": "Request validation failed",
                    "details": []
                }
            }
        }
