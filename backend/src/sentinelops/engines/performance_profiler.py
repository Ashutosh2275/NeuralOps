"""
Performance Profiler — System 13
Lightweight async profiler that tracks latency percentiles per endpoint.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable, Awaitable, Any
import statistics

from sentinelops.core.logging import get_logger

log = get_logger(__name__)

_latency_store: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=200))


def record_latency(name: str, latency_ms: float) -> None:
    _latency_store[name].append(latency_ms)


def get_percentiles(name: str) -> dict:
    data = list(_latency_store.get(name, []))
    if not data:
        return {"p50": 0, "p95": 0, "p99": 0, "count": 0}
    s = sorted(data)
    n = len(s)
    return {
        "p50": round(s[int(n * 0.50)], 2),
        "p95": round(s[int(n * 0.95)], 2),
        "p99": round(s[min(int(n * 0.99), n - 1)], 2),
        "count": n,
        "mean": round(statistics.mean(s), 2),
    }


def get_all_metrics() -> dict:
    return {name: get_percentiles(name) for name in list(_latency_store.keys())}


class latency_track:
    """Async context manager to time a named operation."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._start: float = 0.0

    async def __aenter__(self):
        self._start = time.perf_counter()
        return self

    async def __aexit__(self, *_):
        elapsed_ms = (time.perf_counter() - self._start) * 1000
        record_latency(self.name, elapsed_ms)
