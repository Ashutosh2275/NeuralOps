import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from sentinelops.websocket.manager import ws_manager, EVENT_TYPES

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """WebSocket endpoint for real-time event streaming."""
    await ws_manager.connect(websocket)

    try:
        await ws_manager.send_personal(websocket, "connected", {
            "message": "Connected to SentinelOps event stream",
            "event_types": list(EVENT_TYPES.keys()),
        })

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await ws_manager.send_personal(websocket, "pong", {})
            except json.JSONDecodeError as e:
                logger.warning(f"WebSocket message parse error: {e}")
            except Exception as e:
                logger.error(f"WebSocket message processing error: {e}")

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(websocket)
