import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

import redis.asyncio as aioredis
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from sentinelops.config import get_settings
from sentinelops.core.logging import get_logger

log = get_logger(__name__)
T = TypeVar("T")


class RedisConnectionManager:
    """Manages Redis connection with reconnect on failure."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._redis: aioredis.Redis | None = None
        self._lock = asyncio.Lock()

    async def get_redis(self) -> aioredis.Redis:
        async with self._lock:
            if self._redis is None:
                self._redis = aioredis.from_url(
                    self._settings.effective_redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
            try:
                await self._redis.ping()
            except Exception:
                log.warning("redis_reconnecting")
                await self._redis.aclose()
                self._redis = aioredis.from_url(
                    self._settings.effective_redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
            return self._redis

    async def execute(self, fn: Callable[[aioredis.Redis], Awaitable[T]]) -> T:
        settings = get_settings()
        last_error: Exception | None = None
        for attempt in range(settings.stream_retry_max_attempts):
            try:
                redis = await self.get_redis()
                return await fn(redis)
            except Exception as e:
                last_error = e
                self._redis = None
                wait = min(2**attempt, 30)
                log.warning("redis_execute_retry", attempt=attempt + 1, error=str(e), wait=wait)
                await asyncio.sleep(wait)
        raise last_error or RuntimeError("redis execute failed")


def with_retry() -> Callable:
    settings = get_settings()

    return retry(
        stop=stop_after_attempt(settings.stream_retry_max_attempts),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, OSError)),
        reraise=True,
    )
