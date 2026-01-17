"""
WebSocket endpoints for real-time updates.
"""

import uuid
import logging
from typing import Optional, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.services.websocket_manager import get_connection_manager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    subscriptions: Optional[str] = Query(None, description="Comma-separated event types: threats,tracking,cameras,all")
):
    """
    WebSocket endpoint for real-time updates.

    Clients can subscribe to specific event types:
    - threats: Threat detection alerts
    - tracking: Person tracking updates
    - cameras: Camera status changes
    - all: All events (default)

    Usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws?subscriptions=threats,tracking');

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('Event:', message.event);
        console.log('Data:', message.data);
    };
    ```

    Message format:
    ```json
    {
        "event": "threat_alert",
        "timestamp": "2024-01-17T12:00:00",
        "data": { ... }
    }
    ```
    """
    manager = get_connection_manager()
    client_id = str(uuid.uuid4())

    # Parse subscriptions
    subscription_list = None
    if subscriptions:
        subscription_list = [s.strip() for s in subscriptions.split(",")]

    try:
        # Connect client
        await manager.connect(websocket, client_id, subscription_list)

        # Send welcome message
        await manager.send_personal_message(
            {
                "event": "connected",
                "client_id": client_id,
                "subscriptions": subscription_list or ["all"],
                "message": "Connected to Sentinel Vision real-time updates"
            },
            client_id
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (heartbeat, etc.)
                data = await websocket.receive_text()

                # Echo back or handle client messages if needed
                logger.debug(f"Received message from {client_id}: {data}")

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")

    finally:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} connection closed")


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    manager = get_connection_manager()
    return manager.get_connection_stats()
