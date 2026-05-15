from sentinelops.ingestion.pipeline import IngestionPipeline
from sentinelops.streams.bus import EventBus


class EventCollector:
    """Delegates to IngestionPipeline for full observability ingestion."""

    def __init__(self, bus: EventBus) -> None:
        self._pipeline = IngestionPipeline(bus)

    async def start(self) -> None:
        await self._pipeline.start()

    async def stop(self) -> None:
        await self._pipeline.stop()

    async def collect_once(self) -> int:
        return await self._pipeline.run_once()
