import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

import redis.asyncio as aioredis

from sentinelops.config import Settings
from sentinelops.core.logging import get_logger
from sentinelops.events.schemas import BaseEvent
from sentinelops.pipeline.normalized_event import NormalizedEvent
from sentinelops.streams.dead_letter import DeadLetterQueue
from sentinelops.streams.resilience import RedisConnectionManager

log = get_logger(__name__)

EventHandler = Callable[[BaseEvent, str], Awaitable[None]]
NormalizedHandler = Callable[[NormalizedEvent, str], Awaitable[None]]


class StreamConsumer:
    def __init__(
        self,
        redis: aioredis.Redis | None,
        settings: Settings,
        connection_manager: RedisConnectionManager | None = None,
    ) -> None:
        self._redis = redis
        self._settings = settings
        self._conn = connection_manager or RedisConnectionManager()
        self._dlq: DeadLetterQueue | None = None

    async def _get_dlq(self) -> DeadLetterQueue:
        if self._dlq is None:
            redis = await self._conn.get_redis()
            self._dlq = DeadLetterQueue(redis, self._settings)
        return self._dlq

    async def consume(
        self,
        stream: str,
        group: str,
        consumer_name: str,
        handler: EventHandler,
        batch_size: int = 10,
        block_ms: int = 5000,
    ) -> None:
        while True:
            try:
                redis = await self._conn.get_redis()
                messages = await redis.xreadgroup(
                    groupname=group,
                    consumername=consumer_name,
                    streams={stream: ">"},
                    count=batch_size,
                    block=block_ms,
                )
                if not messages:
                    continue

                for _stream_name, entries in messages:
                    for message_id, fields in entries:
                        await self._process_message(
                            redis, stream, group, message_id, fields, handler, use_normalized=False
                        )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error("stream_consume_error", stream=stream, error=str(e))
                await asyncio.sleep(self._settings.stream_retry_backoff_seconds)

    async def consume_normalized(
        self,
        stream: str,
        group: str,
        consumer_name: str,
        handler: NormalizedHandler,
        batch_size: int = 10,
        block_ms: int = 5000,
    ) -> None:
        while True:
            try:
                redis = await self._conn.get_redis()
                messages = await redis.xreadgroup(
                    groupname=group,
                    consumername=consumer_name,
                    streams={stream: ">"},
                    count=batch_size,
                    block=block_ms,
                )
                if not messages:
                    continue

                for _stream_name, entries in messages:
                    for message_id, fields in entries:
                        await self._process_message(
                            redis, stream, group, message_id, fields, handler, use_normalized=True
                        )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.error("stream_consume_normalized_error", stream=stream, error=str(e))
                await asyncio.sleep(self._settings.stream_retry_backoff_seconds)

    async def _process_message(
        self,
        redis: aioredis.Redis,
        stream: str,
        group: str,
        message_id: str,
        fields: dict[str, str],
        handler: Any,
        use_normalized: bool,
    ) -> None:
        retry_count = 0
        max_retries = self._settings.stream_retry_max_attempts
        dlq = await self._get_dlq()

        while retry_count <= max_retries:
            try:
                if use_normalized:
                    event = NormalizedEvent.from_stream_fields(fields)
                    await handler(event, message_id)
                else:
                    event = BaseEvent.from_stream_fields(fields)
                    await handler(event, message_id)
                await redis.xack(stream, group, message_id)
                return
            except Exception as e:
                retry_count += 1
                log.warning(
                    "event_handler_retry",
                    stream=stream,
                    message_id=message_id,
                    retry=retry_count,
                    error=str(e),
                )
                if retry_count > max_retries:
                    try:
                        normalized = None
                        if "event_id" in fields and "stream_kind" in fields:
                            normalized = NormalizedEvent.from_stream_fields(fields)
                        await dlq.send(stream, message_id, normalized, str(e), fields)
                    except Exception as dlq_err:
                        log.error("dlq_send_failed", error=str(dlq_err))
                    await redis.xack(stream, group, message_id)
                    return
                await asyncio.sleep(min(2**retry_count, 30))

    async def read_pending(
        self,
        stream: str,
        group: str,
        consumer_name: str,
        handler: EventHandler,
    ) -> int:
        redis = await self._conn.get_redis()
        processed = 0
        pending = await redis.xpending_range(stream, group, "-", "+", 100)
        for entry in pending:
            message_id = entry["message_id"]
            claimed = await redis.xclaim(
                stream, group, consumer_name, min_idle_time=60_000, message_ids=[message_id]
            )
            for msg_id, fields in claimed:
                await self._process_message(
                    redis, stream, group, msg_id, fields, handler, use_normalized=False
                )
                processed += 1
        return processed
