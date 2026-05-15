from functools import lru_cache

import redis.asyncio as aioredis

from sentinelops.config import get_settings


@lru_cache
def get_redis() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(
        settings.effective_redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
