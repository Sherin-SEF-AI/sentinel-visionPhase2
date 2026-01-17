"""
Pydantic schemas for API request/response validation.
"""

from app.schemas.camera import CameraCreate, CameraUpdate, CameraResponse
from app.schemas.frame import FrameResponse, FrameAnalysisResponse
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.schemas.threat import ThreatDetectionResponse, ThreatSignatureCreate, ThreatSignatureResponse
from app.schemas.tracking import PersonTrackResponse, TrackingUpdate
from app.schemas.common import HealthResponse, PaginationParams, TimeRangeFilter

__all__ = [
    "CameraCreate",
    "CameraUpdate",
    "CameraResponse",
    "FrameResponse",
    "FrameAnalysisResponse",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    "ThreatDetectionResponse",
    "ThreatSignatureCreate",
    "ThreatSignatureResponse",
    "PersonTrackResponse",
    "TrackingUpdate",
    "HealthResponse",
    "PaginationParams",
    "TimeRangeFilter",
]
