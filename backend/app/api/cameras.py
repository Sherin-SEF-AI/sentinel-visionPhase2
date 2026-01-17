"""
Camera management API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate, CameraResponse, CameraListResponse

router = APIRouter()


@router.post("/", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new camera."""
    # Check if camera_id already exists
    result = await db.execute(
        select(Camera).where(Camera.camera_id == camera_data.camera_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Camera with ID {camera_data.camera_id} already exists"
        )

    camera = Camera(**camera_data.model_dump())
    db.add(camera)
    await db.commit()
    await db.refresh(camera)

    return camera


@router.get("/", response_model=CameraListResponse)
async def list_cameras(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """List all cameras."""
    query = select(Camera)

    if active_only:
        query = query.where(Camera.is_active == True)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    cameras = list(result.scalars().all())

    # Get total count
    count_result = await db.execute(select(Camera))
    total = len(list(count_result.scalars().all()))

    return {
        "cameras": cameras,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit
    }


@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get camera by ID."""
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )

    return camera


@router.patch("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    camera_data: CameraUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update camera configuration."""
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )

    # Update fields
    update_data = camera_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camera, field, value)

    await db.commit()
    await db.refresh(camera)

    return camera


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete camera."""
    result = await db.execute(
        select(Camera).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()

    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Camera {camera_id} not found"
        )

    await db.delete(camera)
    await db.commit()
