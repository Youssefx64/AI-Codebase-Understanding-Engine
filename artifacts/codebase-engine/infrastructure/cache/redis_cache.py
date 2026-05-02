"""Cache implementations: Redis (preferred) with in-memory fallback.

The factory function picks Redis when REDIS_URL is reachable, otherwise
falls back to an in-process TTL cache so the system works without Redis.
"""

import json
import time
from typing import Any, Dict, Optional, Tuple

from core.config import get_settings
from core.logging import get_logger
from domain.interfaces import ICacheStore

logger = get_logger(__name__)


class InMemoryCacheStore(ICacheStore):
    """Lightweight TTL-aware in-process cache (development / CI fallback)."""

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[Any, float]] = {}

    async def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        expires_at = time.monotonic() + ttl if ttl else 0.0
        self._store[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)


class RedisCacheStore(ICacheStore):
    """Redis-backed cache store using the async redis-py client."""

    def __init__(self, redis_url: str) -> None:
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(redis_url, decode_responses=True)
            logger.info("Redis cache store initialised", url=redis_url)
        except ImportError as exc:
            raise RuntimeError(f"redis package not available: {exc}") from exc

    async def get(self, key: str) -> Optional[Any]:
        try:
            raw = await self._redis.get(key)
            return json.loads(raw) if raw is not None else None
        except Exception as exc:
            logger.warning("Redis GET failed", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        try:
            await self._redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception as exc:
            logger.warning("Redis SET failed", key=key, error=str(exc))

    async def delete(self, key: str) -> None:
        try:
            await self._redis.delete(key)
        except Exception as exc:
            logger.warning("Redis DELETE failed", key=key, error=str(exc))


_cache: Optional[ICacheStore] = None


async def get_cache() -> ICacheStore:
    """Return a cache store, preferring Redis if available."""
    global _cache
    if _cache is not None:
        return _cache

    settings = get_settings()
    try:
        store = RedisCacheStore(settings.redis_url)
        # Verify connectivity
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        _cache = store
        logger.info("Using Redis cache")
    except Exception as exc:
        logger.warning("Redis unavailable, using in-memory cache", error=str(exc))
        _cache = InMemoryCacheStore()

    return _cache
