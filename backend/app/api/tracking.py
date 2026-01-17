"""
Person tracking API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.tracking import PersonTrackResponse
from app.services.person_tracking import get_person_tracking_service

router = APIRouter()


@router.get("/active", response_model=List[PersonTrackResponse])
async def get_active_tracks(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Get currently active person tracks.

    Returns persons who have been seen in the last 5 minutes across
    all cameras with their movement trajectories.
    """
    service = get_person_tracking_service()

    tracks = await service.get_active_tracks(db=db, limit=limit)

    return tracks
