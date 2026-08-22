"""
CrisisFlow WebSocket Manager — broadcasts real-time events to all connected clients.
"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import WebSocket

logger = logging.getLogger("crisisflow.realtime")


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, data: dict, entity_id: Optional[str] = None, zone: Optional[str] = None):
        """Send an event to every connected client in standard envelope + data format."""
        message = json.dumps({
            "event_type": event_type,
            "data": data,
            "entity_id": entity_id,
            "zone": zone or "Central",
            "source": "crisisflow-realtime",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, websocket: WebSocket, event_type: str, data: dict):
        message = json.dumps({
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        try:
            await websocket.send_text(message)
        except Exception:
            self.disconnect(websocket)


# Singleton instance
ws_manager = ConnectionManager()
