"""
Threat detection service for evaluating frames against threat signature library.
Generates real-time alerts for detected threats.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.threat_signature import ThreatSignature
from app.models.threat_detection import ThreatDetection
from app.models.frame import Frame
from app.models.frame_analysis import FrameAnalysis
from app.models.camera import Camera
from app.services.gemini_client import get_gemini_client
from app.config import settings

logger = logging.getLogger(__name__)


class ThreatDetectionService:
    """Service for threat signature matching and alert generation."""

    def __init__(self):
        """Initialize threat detection service."""
        self.gemini_client = get_gemini_client()

    async def evaluate_frame_threats(
        self,
        db: AsyncSession,
        frame: Frame,
        frame_analysis: FrameAnalysis,
        camera: Optional[Camera] = None
    ) -> List[ThreatDetection]:
        """
        Evaluate frame against all active threat signatures.

        Args:
            db: Database session
            frame: Frame model instance
            frame_analysis: Frame analysis results
            camera: Optional camera instance

        Returns:
            List of ThreatDetection instances for matched signatures
        """
        try:
            logger.info(f"Evaluating threats for frame {frame.frame_id}")

            # Get active threat signatures
            signatures = await self._get_active_signatures(db)

            if not signatures:
                logger.warning("No active threat signatures found")
                return []

            # Prepare context
            context = await self._prepare_context(db, frame, camera)

            # Evaluate signatures using Gemini
            signature_dicts = [self._signature_to_dict(sig) for sig in signatures]

            matches = self.gemini_client.evaluate_threat_signatures(
                frame_analysis=frame_analysis.full_analysis_json,
                signatures=signature_dicts,
                context=context
            )

            # Create threat detection records for matches
            detections = []

            for match in matches:
                if match.get("matched") and match.get("confidence", 0) >= settings.ALERT_MEDIUM_SEVERITY_THRESHOLD:
                    detection = await self._create_threat_detection(
                        db=db,
                        frame=frame,
                        camera=camera,
                        match=match,
                        frame_analysis=frame_analysis
                    )
                    detections.append(detection)

            await db.commit()

            logger.info(f"Detected {len(detections)} threats in frame {frame.frame_id}")
            return detections

        except Exception as e:
            logger.error(f"Error evaluating frame threats: {e}")
            raise

    async def _get_active_signatures(self, db: AsyncSession) -> List[ThreatSignature]:
        """Get all active threat signatures."""
        try:
            result = await db.execute(
                select(ThreatSignature)
                .where(ThreatSignature.is_active == True)
                .order_by(ThreatSignature.severity.desc())
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error retrieving threat signatures: {e}")
            return []

    def _signature_to_dict(self, signature: ThreatSignature) -> Dict[str, Any]:
        """Convert ThreatSignature model to dictionary for Gemini."""
        return {
            "signature_id": signature.signature_id,
            "name": signature.name,
            "description": signature.description,
            "category": signature.category,
            "severity": signature.severity,
            "threat_type": signature.threat_type,
            "trigger_conditions": signature.trigger_conditions,
            "differentiation_rules": signature.differentiation_rules,
            "contextual_rules": signature.contextual_rules,
            "confidence_threshold": signature.confidence_threshold,
        }

    async def _prepare_context(
        self,
        db: AsyncSession,
        frame: Frame,
        camera: Optional[Camera]
    ) -> Dict[str, Any]:
        """Prepare contextual information for threat evaluation."""
        context = {
            "timestamp": frame.captured_at.isoformat(),
            "hour_of_day": frame.hour_of_day,
            "is_business_hours": frame.is_business_hours,
            "day_of_week": frame.day_of_week,
        }

        if camera:
            context.update({
                "camera_name": camera.name,
                "location": camera.location,
                "facility_zone": camera.facility_zone,
                "access_level": camera.access_level,
                "location_type": camera.location_type,
            })

        return context

    async def _create_threat_detection(
        self,
        db: AsyncSession,
        frame: Frame,
        camera: Optional[Camera],
        match: Dict[str, Any],
        frame_analysis: FrameAnalysis
    ) -> ThreatDetection:
        """Create threat detection record."""
        try:
            detection_id = f"det_{uuid.uuid4().hex[:12]}"

            # Get signature
            signature_id_str = match.get("signature_id")
            result = await db.execute(
                select(ThreatSignature).where(ThreatSignature.signature_id == signature_id_str)
            )
            signature = result.scalar_one_or_none()

            # Determine alert priority based on severity and confidence
            alert_priority = self._calculate_alert_priority(
                severity=match.get("severity"),
                confidence=match.get("confidence")
            )

            # Create detection
            detection = ThreatDetection(
                detection_id=detection_id,
                frame_id=frame.id,
                camera_id=camera.id if camera else None,
                signature_id=signature.id if signature else None,
                detected_at=datetime.utcnow(),
                detection_timestamp=frame.captured_at,
                threat_type=match.get("signature_name"),
                severity=match.get("severity"),
                category=signature.category if signature else None,
                confidence_score=match.get("confidence"),
                confidence_breakdown=match.get("confidence_factors"),
                evidence_summary=match.get("evidence_summary"),
                visual_evidence_path=frame.frame_path,
                context_data={
                    "frame_analysis": frame_analysis.full_analysis_json,
                    "match_details": match,
                },
                location=camera.location if camera else None,
                facility_zone=camera.facility_zone if camera else None,
                environmental_context={
                    "time_of_day": frame.hour_of_day,
                    "is_business_hours": frame.is_business_hours,
                },
                alert_status="pending",
                alert_priority=alert_priority,
                alert_message=self._generate_alert_message(match, camera),
            )

            db.add(detection)
            await db.flush()

            # Update signature statistics
            if signature:
                signature.detection_count += 1
                signature.last_detection_at = datetime.utcnow()

            logger.info(f"Created threat detection {detection_id} with severity {match.get('severity')}")
            return detection

        except Exception as e:
            logger.error(f"Error creating threat detection: {e}")
            raise

    def _calculate_alert_priority(self, severity: str, confidence: float) -> str:
        """Calculate alert priority based on severity and confidence."""
        if severity == "critical" and confidence >= 0.75:
            return "critical"
        elif severity in ["critical", "high"] and confidence >= 0.65:
            return "high"
        elif confidence >= 0.55:
            return "medium"
        else:
            return "low"

    def _generate_alert_message(self, match: Dict[str, Any], camera: Optional[Camera]) -> str:
        """Generate human-readable alert message."""
        location = f" at {camera.location}" if camera else ""
        return f"{match.get('signature_name')} detected{location}. {match.get('evidence_summary')}"

    async def create_custom_signature(
        self,
        db: AsyncSession,
        description: str,
        severity: str,
        category: str,
        alert_priority: str = "medium",
        created_by: Optional[str] = None
    ) -> ThreatSignature:
        """
        Create custom threat signature from natural language description.

        Args:
            db: Database session
            description: Natural language threat description
            severity: Severity level (critical, high, medium, low)
            category: Threat category
            alert_priority: Alert priority level
            created_by: User who created the signature

        Returns:
            New ThreatSignature instance
        """
        try:
            logger.info(f"Creating custom signature: {description[:50]}...")

            # Use Gemini to generate signature specification
            signature_def = self.gemini_client.create_custom_signature(
                description=description,
                severity=severity,
                category=category
            )

            signature_id = f"custom_{uuid.uuid4().hex[:12]}"

            # Create signature record
            signature = ThreatSignature(
                signature_id=signature_id,
                name=signature_def.get("name"),
                description=signature_def.get("description"),
                category=category,
                severity=severity,
                threat_type=signature_def.get("name"),
                trigger_conditions=signature_def.get("trigger_conditions", {}),
                differentiation_rules=signature_def.get("differentiation_rules"),
                contextual_rules=signature_def.get("contextual_rules"),
                confidence_threshold=signature_def.get("confidence_threshold", 0.60),
                temporal_window_seconds=signature_def.get("temporal_window_seconds"),
                alert_enabled=True,
                alert_priority=alert_priority,
                recommended_actions=signature_def.get("recommended_actions"),
                is_custom=True,
                created_by=created_by,
                natural_language_definition=description,
                is_active=True,
            )

            db.add(signature)
            await db.commit()

            logger.info(f"Created custom signature {signature_id}: {signature.name}")
            return signature

        except Exception as e:
            logger.error(f"Error creating custom signature: {e}")
            raise

    async def get_active_alerts(
        self,
        db: AsyncSession,
        limit: int = 100,
        severity: Optional[str] = None
    ) -> List[ThreatDetection]:
        """
        Get active (unresolved) threat alerts.

        Args:
            db: Database session
            limit: Maximum number of alerts to return
            severity: Optional severity filter

        Returns:
            List of ThreatDetection instances
        """
        try:
            query = select(ThreatDetection).where(
                ThreatDetection.alert_status.in_(["pending", "acknowledged", "investigating"])
            )

            if severity:
                query = query.where(ThreatDetection.severity == severity)

            query = query.order_by(ThreatDetection.detected_at.desc()).limit(limit)

            result = await db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error retrieving active alerts: {e}")
            raise

    async def acknowledge_alert(
        self,
        db: AsyncSession,
        detection_id: str,
        acknowledged_by: str
    ) -> Optional[ThreatDetection]:
        """
        Acknowledge a threat alert.

        Args:
            db: Database session
            detection_id: Detection identifier
            acknowledged_by: User acknowledging the alert

        Returns:
            Updated ThreatDetection instance
        """
        try:
            result = await db.execute(
                select(ThreatDetection).where(ThreatDetection.detection_id == detection_id)
            )
            detection = result.scalar_one_or_none()

            if detection:
                detection.alert_status = "acknowledged"
                detection.acknowledged_by = acknowledged_by
                detection.acknowledged_at = datetime.utcnow()
                await db.commit()

                logger.info(f"Alert {detection_id} acknowledged by {acknowledged_by}")

            return detection

        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            raise


# Global service instance
_threat_detection_service: Optional[ThreatDetectionService] = None


def get_threat_detection_service() -> ThreatDetectionService:
    """Get or create global threat detection service instance."""
    global _threat_detection_service
    if _threat_detection_service is None:
        _threat_detection_service = ThreatDetectionService()
    return _threat_detection_service
