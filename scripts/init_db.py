"""
Database initialization script.
Creates all tables and loads initial data including threat signatures.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import text
from app.database import async_engine, init_database, init_qdrant_collection
from app.models.threat_signature import ThreatSignature
from app.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def load_threat_signatures():
    """Load threat signatures from JSON file."""
    logger.info("Loading threat signatures...")

    # Load signatures from file
    signatures_file = Path(__file__).parent.parent / "backend" / "data" / "threat_signatures.json"

    if not signatures_file.exists():
        logger.warning(f"Threat signatures file not found: {signatures_file}")
        return

    with open(signatures_file, "r") as f:
        data = json.load(f)

    signatures = data.get("signatures", [])

    async with AsyncSessionLocal() as session:
        # Check if signatures already loaded
        result = await session.execute(text("SELECT COUNT(*) FROM threat_signatures"))
        count = result.scalar()

        if count > 0:
            logger.info(f"Threat signatures already loaded ({count} signatures)")
            return

        # Load signatures
        for sig_data in signatures:
            signature = ThreatSignature(
                signature_id=sig_data["signature_id"],
                name=sig_data["name"],
                description=sig_data.get("description"),
                category=sig_data["category"],
                severity=sig_data["severity"],
                threat_type=sig_data.get("threat_type"),
                trigger_conditions=sig_data.get("trigger_conditions", {}),
                differentiation_rules=sig_data.get("differentiation_rules"),
                contextual_rules=sig_data.get("contextual_rules"),
                confidence_threshold=sig_data.get("confidence_threshold", 0.60),
                temporal_window_seconds=sig_data.get("temporal_window_seconds"),
                spatial_requirements=sig_data.get("spatial_requirements"),
                environmental_factors=sig_data.get("environmental_factors"),
                alert_enabled=sig_data.get("alert_enabled", True),
                alert_priority=sig_data.get("alert_priority", "medium"),
                recommended_actions=sig_data.get("recommended_actions"),
                notification_targets=sig_data.get("notification_targets"),
                is_custom=False,
                is_active=True,
            )
            session.add(signature)

        await session.commit()
        logger.info(f"Loaded {len(signatures)} threat signatures")


async def create_sample_cameras():
    """Create sample camera records for testing."""
    logger.info("Creating sample cameras...")

    async with AsyncSessionLocal() as session:
        # Check if cameras already exist
        result = await session.execute(text("SELECT COUNT(*) FROM cameras"))
        count = result.scalar()

        if count > 0:
            logger.info(f"Cameras already exist ({count} cameras)")
            return

        from app.models.camera import Camera

        cameras = [
            {
                "camera_id": "CAM001",
                "name": "Main Entrance",
                "location": "Building A - Main Entrance",
                "facility_zone": "Public Entry",
                "access_level": "public",
                "location_type": "entrance",
                "stream_url": "rtsp://example.com/cam001",
                "is_active": True,
            },
            {
                "camera_id": "CAM002",
                "name": "Parking Lot North",
                "location": "North Parking Lot",
                "facility_zone": "Parking",
                "access_level": "public",
                "location_type": "parking_lot",
                "stream_url": "rtsp://example.com/cam002",
                "is_active": True,
            },
            {
                "camera_id": "CAM003",
                "name": "Server Room Entrance",
                "location": "Building B - Server Room Entrance",
                "facility_zone": "Server Room",
                "access_level": "high_security",
                "location_type": "entrance",
                "stream_url": "rtsp://example.com/cam003",
                "is_active": True,
            },
        ]

        for cam_data in cameras:
            camera = Camera(**cam_data)
            session.add(camera)

        await session.commit()
        logger.info(f"Created {len(cameras)} sample cameras")


async def main():
    """Main initialization function."""
    try:
        logger.info("Starting database initialization...")

        # Initialize database tables
        logger.info("Creating database tables...")
        await init_database()

        # Initialize Qdrant collection
        logger.info("Initializing Qdrant collection...")
        await init_qdrant_collection()

        # Load threat signatures
        await load_threat_signatures()

        # Create sample cameras
        await create_sample_cameras()

        logger.info("Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
