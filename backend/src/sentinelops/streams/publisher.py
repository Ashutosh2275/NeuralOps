from typing import Any

import redis.asyncio as aioredis

from sentinelops.config import Settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import BaseEvent
from sentinelops.pipeline.normalized_event import NormalizedEvent, StreamKind
from sentinelops.streams.resilience import RedisConnectionManager

log = get_logger(__name__)

STREAM_KIND_MAP: dict[StreamKind, str] = {}


def _build_stream_map(settings: Settings) -> dict[StreamKind, str]:
    return {
        StreamKind.METRICS: settings.stream_metrics_events,
        StreamKind.TOPOLOGY: settings.stream_topology_events,
        StreamKind.ANOMALY: settings.stream_anomaly_events,
        StreamKind.INCIDENT: settings.stream_incident_events,
        StreamKind.RCA: settings.stream_rca_events,
        StreamKind.RAW: settings.stream_events_raw,
    }


class StreamPublisher:
    def __init__(
        self,
        redis: aioredis.Redis | None,
        settings: Settings,
        connection_manager: RedisConnectionManager | None = None,
    ) -> None:
        self._redis = redis
        self._settings = settings
        self._conn = connection_manager or RedisConnectionManager()
        self._stream_map = _build_stream_map(settings)

    async def _redis_client(self) -> aioredis.Redis:
        if self._redis is not None:
            return self._redis
        return await self._conn.get_redis()

    def _resolve_stream(self, kind: StreamKind) -> str:
        return self._stream_map.get(kind, self._settings.stream_events_raw)

    async def publish_normalized(self, event: NormalizedEvent) -> str:
        stream = self._resolve_stream(event.stream_kind)

        async def _xadd(r: aioredis.Redis) -> str:
            return await r.xadd(
                stream,
                event.to_stream_fields(),
                maxlen=self._settings.stream_max_len,
                approximate=True,
            )

        message_id = await self._conn.execute(_xadd)
        log.debug(
            "normalized_event_published",
            stream=stream,
            event_id=str(event.event_id),
            msg_id=message_id,
        )
        return message_id

    async def publish(self, stream: str, event: BaseEvent) -> str:
        async def _xadd(r: aioredis.Redis) -> str:
            return await r.xadd(
                stream,
                event.to_stream_fields(),
                maxlen=self._settings.stream_max_len,
                approximate=True,
            )

        return await self._conn.execute(_xadd)

    async def publish_raw(self, stream: str, fields: dict[str, str]) -> str:
        async def _xadd(r: aioredis.Redis) -> str:
            return await r.xadd(
                stream,
                fields,
                maxlen=self._settings.stream_max_len,
                approximate=True,
            )

        return await self._conn.execute(_xadd)

    async def publish_to_raw(self, event: BaseEvent) -> str:
        return await self.publish(self._settings.stream_events_raw, event)

    async def publish_to_enriched(self, event: BaseEvent) -> str:
        return await self.publish(self._settings.stream_events_enriched, event)

    async def publish_incident(self, event: BaseEvent) -> str:
        return await self.publish(self._settings.stream_incident_events, event)

    async def publish_rca(self, event: BaseEvent) -> str:
        return await self.publish(self._settings.stream_rca_events, event)

    async def publish_ai_task(self, task: dict[str, Any]) -> str:
        import json

        fields = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in task.items()}
        return await self.publish_raw(self._settings.stream_ai_tasks, fields)
