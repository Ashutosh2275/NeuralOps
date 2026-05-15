from sentinelops.config import Settings, get_settings
from sentinelops.core.logging import get_logger
from sentinelops.core.redis_client import get_redis
from sentinelops.streams.consumer import StreamConsumer
from sentinelops.streams.publisher import StreamPublisher
from sentinelops.streams.resilience import RedisConnectionManager

log = get_logger(__name__)


class EventBus:
    """Redis Streams event bus with resilience and consumer group management."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._conn = RedisConnectionManager()
        self._redis = get_redis()
        self.publisher = StreamPublisher(self._redis, self._settings, self._conn)
        self.consumer = StreamConsumer(self._redis, self._settings, self._conn)

    async def initialize(self) -> None:
        stream_group_map = {
            self._settings.stream_events_raw: self._settings.consumer_group_collector,
            self._settings.stream_events_enriched: self._settings.consumer_group_correlation,
            self._settings.stream_metrics_events: self._settings.consumer_group_collector,
            self._settings.stream_topology_events: self._settings.consumer_group_collector,
            self._settings.stream_anomaly_events: self._settings.consumer_group_correlation,
            self._settings.stream_incident_events: self._settings.consumer_group_correlation,
            self._settings.stream_rca_events: self._settings.consumer_group_ai,
            self._settings.stream_correlation: self._settings.consumer_group_correlation,
            self._settings.stream_ai_tasks: self._settings.consumer_group_ai,
            self._settings.stream_replay: self._settings.consumer_group_replay,
            self._settings.stream_dead_letter: self._settings.consumer_group_dlq,
        }
        redis = await self._conn.get_redis()
        for stream, group in stream_group_map.items():
            try:
                await redis.xgroup_create(stream, group, id="0", mkstream=True)
                log.info("stream_group_created", stream=stream, group=group)
            except Exception as e:
                if "BUSYGROUP" not in str(e):
                    log.warning("stream_group_create_failed", stream=stream, error=str(e))

    async def health_check(self) -> dict[str, bool]:
        try:
            redis = await self._conn.get_redis()
            await redis.ping()
            return {"redis": True}
        except Exception:
            return {"redis": False}

    async def stream_info(self) -> dict[str, int]:
        redis = await self._conn.get_redis()
        info: dict[str, int] = {}
        for stream in self._settings.all_ingestion_streams:
            try:
                length = await redis.xlen(stream)
                info[stream] = length
            except Exception:
                info[stream] = -1
        return info
