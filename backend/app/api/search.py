"""
Natural language search API endpoints.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search import get_search_service

router = APIRouter()


@router.post("/", response_model=SearchResponse)
async def search_videos(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute natural language video search.

    This endpoint enables conversational querying of video archives.
    The system understands natural language, extracts entities, performs
    semantic search, ranks results, and provides relevant video clips.

    Example queries:
    - "Show me anyone wearing a red jacket near the main entrance this morning"
    - "Find people carrying boxes in the loading dock yesterday afternoon"
    - "Who left the building between 5pm and 6pm last Friday?"
    - "Show suspicious activity in the parking lot last night"
    """
    try:
        search_service = get_search_service()

        result = await search_service.search(
            db=db,
            query=request.query,
            start_time=request.start_time,
            end_time=request.end_time,
            camera_ids=request.camera_ids,
            facility_zones=request.facility_zones,
            confidence_threshold=request.confidence_threshold,
            result_limit=request.result_limit,
            operator_id=None  # TODO: Get from auth context
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )
