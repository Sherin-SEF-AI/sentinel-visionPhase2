"""
WebSocket manager for real-time alerts and updates.
Handles client connections and broadcasts events to subscribed clients.
"""

import logging
import json
from typing import Dict, Set, Optional, List, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {
            "threats": set(),
            "tracking": set(),
            "cameras": set(),
            "all": set(),
        }

    async def connect(self, websocket: WebSocket, client_id: str, subscriptions: Optional[List[str]] = None):
        """Accept WebSocket connection and register subscriptions."""
        await websocket.accept()
        self.active_connections[client_id] = websocket

        # Default to all events if no specific subscriptions
        if not subscriptions:
            subscriptions = ["all"]

        # Register subscriptions
        for subscription in subscriptions:
            if subscription in self.subscriptions:
                self.subscriptions[subscription].add(client_id)

        logger.info(f"Client {client_id} connected with subscriptions: {subscriptions}")

    def disconnect(self, client_id: str):
        """Remove client connection and subscriptions."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        # Remove from all subscriptions
        for subscribers in self.subscriptions.values():
            subscribers.discard(client_id)

        logger.info(f"Client {client_id} disconnected")

    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send message to specific client."""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: Dict[str, Any], event_type: str = "all"):
        """Broadcast message to all subscribed clients."""
        # Get clients subscribed to this event type or "all"
        subscribers = self.subscriptions.get(event_type, set()) | self.subscriptions.get("all", set())

        disconnected_clients = []

        for client_id in subscribers:
            try:
                if client_id in self.active_connections:
                    websocket = self.active_connections[client_id]
                    await websocket.send_json(message)
            except WebSocketDisconnect:
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

        if subscribers:
            logger.debug(f"Broadcasted {event_type} event to {len(subscribers)} clients")

    async def broadcast_threat_alert(self, alert_data: Dict[str, Any]):
        """Broadcast threat alert to subscribed clients."""
        message = {
            "event": "threat_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "data": alert_data
        }
        await self.broadcast(message, event_type="threats")

    async def broadcast_tracking_update(self, tracking_data: Dict[str, Any]):
        """Broadcast person tracking update to subscribed clients."""
        message = {
            "event": "tracking_update",
            "timestamp": datetime.utcnow().isoformat(),
            "data": tracking_data
        }
        await self.broadcast(message, event_type="tracking")

    async def broadcast_camera_status(self, camera_data: Dict[str, Any]):
        """Broadcast camera status update to subscribed clients."""
        message = {
            "event": "camera_status",
            "timestamp": datetime.utcnow().isoformat(),
            "data": camera_data
        }
        await self.broadcast(message, event_type="cameras")

    async def broadcast_system_status(self, status_data: Dict[str, Any]):
        """Broadcast system status update to all clients."""
        message = {
            "event": "system_status",
            "timestamp": datetime.utcnow().isoformat(),
            "data": status_data
        }
        await self.broadcast(message, event_type="all")

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections."""
        return {
            "total_connections": len(self.active_connections),
            "subscriptions": {
                event_type: len(subscribers)
                for event_type, subscribers in self.subscriptions.items()
            }
        }


# Global connection manager
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create global connection manager instance."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
