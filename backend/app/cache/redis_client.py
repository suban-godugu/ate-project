import hashlib
import json
from typing import Any

import redis.asyncio as redis

from app.core.config import get_settings

settings = get_settings()
_redis: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


def prefix_key(key: str) -> str:
    return f"{settings.redis_prefix}{key}"


def filter_cache_key(module: str, tab: str, filters: dict, page: int = 1) -> str:
    normalized = json.dumps(filters, sort_keys=True)
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return f"dash:{module}:{tab}:{digest}:p{page}"


def executive_cache_key(filters: dict) -> str:
    normalized = json.dumps(filters, sort_keys=True)
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return f"dash:exec:{digest}"


async def blacklist_jwt(jti: str, ttl_seconds: int) -> None:
    await cache_set(f"jwt:blacklist:{jti}", {"revoked": True}, max(ttl_seconds, 1))


async def get_unread_notification_count(user_id: str) -> int | None:
    cached = await cache_get(f"notif:unread:{user_id}")
    if cached is None:
        return None
    return int(cached.get("count", 0))


async def set_unread_notification_count(user_id: str, count: int, ttl: int = 30) -> None:
    await cache_set(f"notif:unread:{user_id}", {"count": count}, ttl)


async def invalidate_unread_notification_count(user_id: str) -> None:
    client = await get_redis()
    await client.delete(prefix_key(f"notif:unread:{user_id}"))


async def cache_get(key: str) -> Any | None:
    client = await get_redis()
    raw = await client.get(prefix_key(key))
    prefix = key.split(":")[0] if ":" in key else key
    if raw is None:
        from app.core.metrics import CACHE_MISSES

        CACHE_MISSES.labels(key_prefix=prefix).inc()
        return None
    from app.core.metrics import CACHE_HITS

    CACHE_HITS.labels(key_prefix=prefix).inc()
    return json.loads(raw)


async def cache_set(key: str, value: Any, ttl: int) -> None:
    client = await get_redis()
    await client.set(prefix_key(key), json.dumps(value), ex=ttl)


async def cache_delete(key: str) -> None:
    client = await get_redis()
    await client.delete(prefix_key(key))


async def cache_delete_pattern(pattern: str) -> None:
    client = await get_redis()
    full_pattern = prefix_key(pattern)
    async for key in client.scan_iter(match=full_pattern):
        await client.delete(key)


async def publish_job_event(job_id: str, data: dict) -> None:
    client = await get_redis()
    payload = json.dumps(data)
    channel = prefix_key(f"job:{job_id}:events")
    await client.publish(channel, payload)
    # Also append to Redis Stream for spec compliance; SSE uses pub/sub
    await client.xadd(prefix_key(f"job:{job_id}:events:stream"), {"data": payload}, maxlen=100)


async def set_job_status(job_id: str, status: dict, ttl: int = 3600) -> None:
    await cache_set(f"job:{job_id}:status", status, ttl)


async def get_job_status(job_id: str) -> dict | None:
    return await cache_get(f"job:{job_id}:status")


async def increment_rate_limit(ip: str, route: str, limit: int = 100) -> bool:
    client = await get_redis()
    key = prefix_key(f"ratelimit:{ip}:{route}")
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, 60)
    return count <= limit
