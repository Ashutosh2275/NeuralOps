import asyncio
import json
import zlib
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

class CommandCenterWS:
    """Dedicated WebSocket manager for real-time command center rendering."""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.lock = asyncio.Lock()
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.add(websocket)
            
    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            self.active_connections.discard(websocket)
            
    async def broadcast_compressed(self, payload: dict):
        """Broadcast state sync events, compressed for 500+ nodes scaling."""
        raw_json = json.dumps(payload).encode('utf-8')
        compressed = zlib.compress(raw_json)
        
        dead_connections = set()
        async with self.lock:
            for ws in self.active_connections:
                try:
                    await ws.send_bytes(compressed)
                except Exception:
                    dead_connections.add(ws)
                    
            for dead in dead_connections:
                self.active_connections.discard(dead)

command_center_ws = CommandCenterWS()
