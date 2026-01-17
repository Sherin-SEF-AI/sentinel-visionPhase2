"""
Threat detection and alert management API endpoints.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.threat_signature import ThreatSignature
from app.models.threat_detection import ThreatDetection
from app.schemas.threat import (
    ThreatSignatureCreate,
    ThreatSignatureResponse,
    ThreatDetectionResponse,
    ThreatDetectionUpdate,
    CustomSignatureRequest
)
from app.services.threat_detection import get_threat_detection_service

router = APIRouter()


# Signature Management

@router.get("/signatures", response_model=List[ThreatSignatureResponse])
async def list_signatures(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List threat signatures."""
    query = select(ThreatSignature)

    if active_only:
        query = query.where(ThreatSignature.is_active == True)

    if category:
        query = query.where(ThreatSignature.category == category)

    if severity:
        query = query.where(ThreatSignature.severity == severity)

    query = query.order_by(ThreatSignature.severity.desc(), ThreatSignature.name)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/signatures/custom", response_model=ThreatSignatureResponse)
async def create_custom_signature(
    request: CustomSignatureRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create custom threat signature from natural language description.

    Example: "Detect when someone is taking photos of security cameras
    or access control panels"
    """
    try:
        service = get_threat_detection_service()

        signature = await service.create_custom_signature(
            db=db,
            description=request.description,
            severity=request.severity,
            category=request.category,
            alert_priority=request.alert_priority,
            created_by=None  # TODO: Get from auth context
        )

        return signature

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create custom signature: {str(e)}"
        )


# Alert Management

@router.get("/alerts", response_model=List[ThreatDetectionResponse])
async def list_alerts(
    status: Optional[str] = Query(None, description="pending, acknowledged, investigating, resolved"),
    severity: Optional[str] = Query(None, description="critical, high, medium, low"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """List threat alerts."""
    service = get_threat_detection_service()

    alerts = await service.get_active_alerts(
        db=db,
        limit=limit,
        severity=severity
    )

    if status:
        alerts = [a for a in alerts if a.alert_status == status]

    return alerts


@router.patch("/alerts/{detection_id}", response_model=ThreatDetectionResponse)
async def update_alert(
    detection_id: str,
    update_data: ThreatDetectionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update threat alert status."""
    result = await db.execute(
        select(ThreatDetection).where(ThreatDetection.detection_id == detection_id)
    )
    detection = result.scalar_one_or_none()

    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {detection_id} not found"
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(detection, field, value)

    await db.commit()
    await db.refresh(detection)

    return detection


@router.post("/alerts/{detection_id}/acknowledge", response_model=ThreatDetectionResponse)
async def acknowledge_alert(
    detection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge a threat alert."""
    service = get_threat_detection_service()

    detection = await service.acknowledge_alert(
        db=db,
        detection_id=detection_id,
        acknowledged_by="operator"  # TODO: Get from auth context
    )

    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {detection_id} not found"
        )

    return detection
