import json
from datetime import datetime

import redis.asyncio as aioredis

from sentinelops.config import Settings
from sentinelops.core.logging import get_logger
from sentinelops.pipeline.normalized_event import NormalizedEvent

log = get_logger(__name__)


class DeadLetterQueue:
    """Routes failed events to DLQ stream for inspection and replay."""

    def __init__(self, redis: aioredis.Redis, settings: Settings) -> None:
        self._redis = redis
        self._settings = settings

    async def send(
        self,
        original_stream: str,
        message_id: str,
        event: NormalizedEvent | None,
        error: str,
        raw_fields: dict[str, str] | None = None,
    ) -> str:
        fields = {
            "dlq_at": datetime.utcnow().isoformat(),
            "original_stream": original_stream,
            "original_message_id": message_id,
            "error": error[:2000],
            "retry_count": str(event.replay_metadata.get("retry_count", 0) if event else 0),
        }
        if event:
            fields["event"] = json.dumps(event.to_stream_fields())
        elif raw_fields:
            fields["event"] = json.dumps(raw_fields)

        msg_id = await self._redis.xadd(
            self._settings.stream_dead_letter,
            fields,
            maxlen=self._settings.stream_max_len,
            approximate=True,
        )
        log.error("event_sent_to_dlq", stream=original_stream, message_id=message_id, dlq_id=msg_id)
        return msg_id
