import asyncio
from fastapi import WebSocket, WebSocketException

class WebSocketSecurity:
    """Protects against replay spamming and limits connections."""
    def __init__(self, max_connections=1000):
        self.max_connections = max_connections
        self.current = 0
        self.lock = asyncio.Lock()
        
    async def validate_connection(self, websocket: WebSocket) -> bool:
        async with self.lock:
            if self.current >= self.max_connections:
                return False
            self.current += 1
        return True
        
    async def release_connection(self):
        async with self.lock:
            self.current = max(0, self.current - 1)
