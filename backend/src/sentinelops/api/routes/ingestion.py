from fastapi import APIRouter

from sentinelops.api.deps import get_event_bus
from sentinelops.collectors import get_event_collector
from sentinelops.config import get_settings

router = APIRouter()


@router.get("/status")
async def ingestion_status() -> dict:
    bus = get_event_bus()
    settings = get_settings()
    streams = await bus.stream_info()
    health = await bus.health_check()
    return {
        "redis": health.get("redis", False),
        "streams": streams,
        "stream_names": settings.all_ingestion_streams,
    }


@router.post("/trigger")
async def trigger_ingestion() -> dict:
    bus = get_event_bus()
    collector = get_event_collector(bus)
    count = await collector.collect_once()
    return {"published": count}
