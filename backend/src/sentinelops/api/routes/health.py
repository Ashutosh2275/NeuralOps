from fastapi import APIRouter

from sentinelops.agents.ollama_client import OllamaClient
from sentinelops.api.deps import get_event_bus
from sentinelops.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    bus = get_event_bus()
    redis_ok = (await bus.health_check()).get("redis", False)
    ollama_ok = await OllamaClient().health_check()
    return {
        "status": "healthy" if redis_ok else "degraded",
        "version": "0.1.0",
        "services": {
            "redis": redis_ok,
            "ollama": ollama_ok,
            "postgres": True,
        },
        "features": {
            "ai_agents": settings.feature_ai_agents,
            "replay": settings.feature_replay_engine,
            "nlp": settings.feature_nlp_assistant,
        },
    }


@router.get("/ready")
async def ready() -> dict:
    bus = get_event_bus()
    redis_ok = (await bus.health_check()).get("redis", False)
    return {"ready": redis_ok}
