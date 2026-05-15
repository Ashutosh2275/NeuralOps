import asyncio
import json
import logging
from typing import Callable, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time event streaming."""

    def __init__(self):
        self.connections: Set[WebSocket] = set()
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.subscribers = {}

    async def connect(self, websocket: WebSocket):
        """Register a new WebSocket connection."""
        await websocket.accept()
        self.connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        self.connections.discard(websocket)

    async def broadcast(self, event_type: str, payload: dict):
        """Broadcast event to all connected clients."""
        message = {
            "event_type": event_type,
            "payload": payload,
        }

        disconnected = set()
        for connection in self.connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"WebSocket broadcast error: {e}")
                disconnected.add(connection)

        for connection in disconnected:
            await self.disconnect(connection)

    async def send_personal(self, websocket: WebSocket, event_type: str, payload: dict):
        """Send event to specific connection."""
        try:
            await websocket.send_json({
                "event_type": event_type,
                "payload": payload,
            })
        except Exception as e:
            logger.debug(f"WebSocket personal send error: {e}")
            await self.disconnect(websocket)

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to specific event types."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def emit_event(self, event_type: str, payload: dict):
        """Emit event and notify all subscribers."""
        await self.broadcast(event_type, payload)

        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(payload)
                    else:
                        handler(payload)
                except Exception as e:
                    logger.error(f"Subscriber error: {e}")


ws_manager = WebSocketManager()


# Event types for streaming
EVENT_TYPES = {
    # Simulation events
    "simulation_created": "New simulation started",
    "degradation_progress": "Infrastructure degradation in progress",
    "blast_radius_updated": "Blast radius expanding",
    "cascade_started": "Cascading failure detected",
    "cascade_completed": "Cascading failure completed",
    "simulation_completed": "Simulation completed",

    # Incident events
    "incident_created": "New incident detected",
    "incident_escalated": "Incident escalated",
    "incident_resolved": "Incident resolved",

    # Remediation events
    "remediation_planned": "Remediation action planned",
    "remediation_started": "Remediation starting",
    "remediation_completed": "Remediation completed",

    # AI reasoning events
    "ai_reasoning_update": "AI agent reasoning",
    "rca_progress": "Root cause analysis progressing",
    "recommendation_generated": "Recommendation generated",

    # Recovery events
    "recovery_started": "Recovery process started",
    "recovery_verified": "Recovery verified",
    "health_improved": "Infrastructure health improved",

    # Replay events
    "replay_generated": "Incident replay generated",
    "replay_frame_available": "Replay frame ready",
}
