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
    try:
        await bus.initialize()
    except Exception as e:
        log.warning("event_bus_init_failed", error=str(e))
    try:
        ai_scheduler.start()
    except Exception as e:
        log.warning("ai_scheduler_start_failed", error=str(e))
    log.info("sentinelops_started", env=settings.app_env)
    yield
    try:
        ai_scheduler.stop()
    except Exception:
        pass
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

    # Hardened CORS configuration: Never combine wildcard origins with credentials
    cors_origins = [o.strip() for o in settings.app_cors_origins.split(",") if o.strip()]
    if "*" in cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or ["http://localhost:5173", "http://127.0.0.1:5173"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=["*"],
        )
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def root_health():
        from sentinelops.api.routes.health import health
        return await health()

    @app.get("/metrics", tags=["metrics"])
    async def prometheus_metrics():
        from fastapi.responses import PlainTextResponse
        lines = [
            "# HELP sentinelops_up Whether SentinelOps backend is healthy",
            "# TYPE sentinelops_up gauge",
            "sentinelops_up 1",
            "# HELP sentinelops_build_info Build and version metadata",
            "# TYPE sentinelops_build_info gauge",
            'sentinelops_build_info{version="1.0.0",env="development"} 1',
        ]
        return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")

    @app.get("/api/v1/performance/metrics", tags=["performance"])
    async def performance_metrics():
        return {"metrics": get_all_metrics()}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await ws_hub.handle(websocket)

    return app


app = create_app()
