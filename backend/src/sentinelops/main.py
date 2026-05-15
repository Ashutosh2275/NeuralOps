from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from sentinelops.api.deps import get_event_bus
from sentinelops.api.routes import api_router
from sentinelops.config import get_settings
from sentinelops.core.logging import configure_logging, get_logger
from sentinelops.websocket.hub import ws_hub

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    settings = get_settings()
    bus = get_event_bus()
    await bus.initialize()
    log.info("sentinelops_started", env=settings.app_env)
    yield
    log.info("sentinelops_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Event-driven AI operational intelligence for Kubernetes",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await ws_hub.handle(websocket)

    return app


app = create_app()
