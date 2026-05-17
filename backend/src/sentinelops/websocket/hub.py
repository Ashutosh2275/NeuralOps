import asyncio
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from sentinelops.core.logging import get_logger

log = get_logger(__name__)


class WebSocketHub:
    """Broadcasts real-time events to connected dashboard clients with topology support."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._batch_queue = asyncio.Queue()
        self._batch_task = None

    async def _batch_worker(self):
        while True:
            events = []
            try:
                # Wait for at least one event
                event = await self._batch_queue.get()
                events.append(event)
                # Drain the queue of any other pending events
                while not self._batch_queue.empty():
                    events.append(self._batch_queue.get_nowait())
                
                if events:
                    if len(events) == 1:
                        message = json.dumps({"type": events[0][0], "payload": events[0][1]})
                    else:
                        message = json.dumps({"type": "batch", "payload": {"events": [{"type": e[0], "payload": e[1]} for e in events]}})
                    
                    dead = []
                    async with self._lock:
                        conns = list(self._connections)
                    for ws in conns:
                        try:
                            await ws.send_text(message)
                        except Exception:
                            dead.append(ws)
                    for ws in dead:
                        await self.disconnect(ws)
            except Exception as e:
                log.error(f"batch_worker_error: {e}")
            await asyncio.sleep(0.05) # 50ms batch window

    async def connect(self, websocket: WebSocket) -> None:
        if self._batch_task is None:
            self._batch_task = asyncio.create_task(self._batch_worker())
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        log.info("ws_client_connected", total=len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        log.info("ws_client_disconnected", total=len(self._connections))

    async def broadcast(self, event_type: str, payload: dict[str, Any]) -> None:
        """Broadcast an event to all connected clients via batch queue."""
        await self._batch_queue.put((event_type, payload))

    async def broadcast_topology_update(self, topology_data: dict) -> None:
        """Broadcast topology graph update."""
        await self.broadcast("topology", topology_data)

    async def broadcast_node_health_change(self, node_id: str, health: str, cascade_info: dict | None = None) -> None:
        """Broadcast node health status change."""
        payload = {
            "node_id": node_id,
            "health": health,
            "cascade": cascade_info or {},
        }
        await self.broadcast("node_health", payload)

    async def broadcast_edge_health_change(self, source: str, target: str, health: str) -> None:
        """Broadcast edge health status change."""
        payload = {
            "source": source,
            "target": target,
            "health": health,
        }
        await self.broadcast("edge_health", payload)

    async def broadcast_cascading_failure(self, cascade_data: dict) -> None:
        """Broadcast cascading failure detection."""
        await self.broadcast("cascading_failure", cascade_data)

    async def broadcast_health_propagation(self, propagation_data: dict) -> None:
        """Broadcast health status propagation."""
        await self.broadcast("health_propagation", propagation_data)

    async def handle(self, websocket: WebSocket) -> None:
        """Handle WebSocket client connection."""
        await self.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
        except WebSocketDisconnect:
            await self.disconnect(websocket)


ws_hub = WebSocketHub()

