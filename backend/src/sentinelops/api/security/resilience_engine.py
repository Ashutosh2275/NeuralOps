"""
Resilience Engine — System 12
Auto-reconnect logic for Postgres, Redis, Ollama with graceful degraded mode.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Awaitable

from sentinelops.core.logging import get_logger

log = get_logger(__name__)


class CircuitBreaker:
    """Simple open/half-open/closed circuit breaker."""

    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at > self.recovery_timeout:
            # Half-open: allow one probe
            return False
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._opened_at = time.monotonic()
            log.warning("circuit_breaker_open", name=self.name)

    async def call(
        self,
        fn: Callable[..., Awaitable[Any]],
        *args: Any,
        fallback: Any = None,
        **kwargs: Any,
    ) -> Any:
        if self.is_open:
            log.warning("circuit_breaker_rejected", name=self.name)
            return fallback
        try:
            result = await fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:
            self.record_failure()
            log.error("circuit_breaker_failure", name=self.name, error=str(exc))
            return fallback


async def retry_with_backoff(
    fn: Callable[..., Awaitable[Any]],
    *args: Any,
    max_attempts: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    **kwargs: Any,
) -> Any:
    """Exponential back-off retry wrapper for service reconnects."""
    delay = base_delay
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as exc:
            if attempt == max_attempts:
                raise
            wait = min(delay * (2 ** (attempt - 1)), max_delay)
            log.warning("retry_backoff", attempt=attempt, wait=wait, error=str(exc))
            await asyncio.sleep(wait)


# Singleton breakers shared across the application
redis_breaker = CircuitBreaker("redis", failure_threshold=3, recovery_timeout=15.0)
postgres_breaker = CircuitBreaker("postgres", failure_threshold=3, recovery_timeout=15.0)
ollama_breaker = CircuitBreaker("ollama", failure_threshold=5, recovery_timeout=60.0)
