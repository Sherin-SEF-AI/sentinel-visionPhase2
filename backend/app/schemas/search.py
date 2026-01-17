"""
Natural language search schemas.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.common import ConfidenceScore, LocationInfo
from app.schemas.frame import FrameWithAnalysis


class SearchRequest(BaseModel):
    """Natural language search request."""
    query: str = Field(..., min_length=1, description="Natural language search query")

    # Optional filters
    start_time: Optional[datetime] = Field(None, description="Start of time range")
    end_time: Optional[datetime] = Field(None, description="End of time range")
    camera_ids: Optional[List[int]] = Field(None, description="Filter by camera IDs")
    facility_zones: Optional[List[str]] = Field(None, description="Filter by facility zones")

    # Search parameters
    confidence_threshold: float = Field(default=0.40, ge=0.0, le=1.0)
    result_limit: int = Field(default=20, ge=1, le=100)

    # Result formatting
    include_video_clips: bool = Field(default=True, description="Generate video clips for results")
    clip_duration_seconds: int = Field(default=10, ge=5, le=60)


class QueryAnalysis(BaseModel):
    """Query understanding results."""
    intent: str
    entities: Dict[str, List[str]]
    implicit_requirements: Optional[List[str]]
    semantic_expansion: Optional[List[str]]
    temporal_references: Optional[Dict[str, Any]]


class SearchResult(BaseModel):
    """Individual search result."""
    frame_id: int
    frame: FrameWithAnalysis

    # Match information
    confidence: ConfidenceScore
    match_explanation: str
    matched_entities: List[str]

    # Video clip
    video_clip_url: Optional[str] = None
    clip_start_time: Optional[datetime] = None
    clip_end_time: Optional[datetime] = None

    # Context
    location: LocationInfo
    related_track_ids: Optional[List[str]] = None


class SearchResponse(BaseModel):
    """Natural language search response."""
    query_id: str
    query: str
    query_analysis: Optional[QueryAnalysis]

    # Results
    results: List[SearchResult]
    result_count: int

    # Execution metadata
    cameras_searched: int
    frames_evaluated: int
    time_range_coverage_hours: Optional[float]
    execution_time_ms: int

    # Follow-up suggestions
    suggestions: Optional[List[str]] = None

    # Direct answer (if applicable)
    direct_answer: Optional[str] = None


class SearchHistoryItem(BaseModel):
    """Search history entry."""
    query_id: str
    query: str
    result_count: int
    top_confidence: Optional[float]
    executed_at: datetime
    execution_time_ms: Optional[int]


class SearchHistoryResponse(BaseModel):
    """Search history response."""
    queries: List[SearchHistoryItem]
    total: int
    page: int
    page_size: int
