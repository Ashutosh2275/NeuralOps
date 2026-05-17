"""
Rate Limit Engine — System 12
Redis-backed sliding window, falls back to in-memory gracefully.
"""
from __future__ import annotations

import time
from collections import defaultdict

_memory_store: dict[str, list[float]] = defaultdict(list)


async def check_rate_limit(
    key: str,
    limit: int = 100,
    window: int = 60,
    redis=None,
) -> bool:
    """
    Returns True if the action is allowed.
    Uses Redis ZSET if available, otherwise in-memory sliding window.
    """
    now = time.time()
    window_start = now - window

    if redis is not None:
        try:
            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, "-inf", window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window * 2)
            results = await pipe.execute()
            count = results[2]
            return count <= limit
        except Exception:
            pass  # fall through to memory

    # In-memory fallback
    hits = _memory_store[key]
    _memory_store[key] = [t for t in hits if t > window_start]
    _memory_store[key].append(now)
    return len(_memory_store[key]) <= limit
