from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from sentinelops.api.deps import get_event_bus
from sentinelops.api.routes import api_router
from sentinelops.api.security import SecurityMiddleware
from sentinelops.config import get_settings
from sentinelops.core.logging import configure_logging, get_logger
from sentinelops.engines.ai_scheduler import ai_scheduler
from sentinelops.engines.performance_profiler import get_all_metrics
from sentinelops.websocket.hub import ws_hub

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    settings = get_settings()
    bus = get_event_bus()
    await bus.initialize()
    ai_scheduler.start()
    log.info("sentinelops_started", env=settings.app_env)
    yield
    ai_scheduler.stop()
    log.info("sentinelops_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Event-driven AI operational intelligence for Kubernetes",
        lifespan=lifespan,
    )
    # Security middleware (before CORS)
    app.add_middleware(SecurityMiddleware, max_body_bytes=512_000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/api/v1/performance/metrics", tags=["performance"])
    async def performance_metrics():
        return {"metrics": get_all_metrics()}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await ws_hub.handle(websocket)

    return app


app = create_app()
