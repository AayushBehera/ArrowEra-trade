"""Redis-backed market data cache."""

from __future__ import annotations

import json
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MarketDataCache:
    """In-memory fallback cache with optional Redis support."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._redis: Any = None

    async def connect(self, redis_url: str | None = None) -> None:
        if redis_url:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(redis_url, decode_responses=True)
                await self._redis.ping()
                logger.info("cache_redis_connected", url=redis_url)
            except Exception as exc:
                logger.warning("cache_redis_fallback", error=str(exc))
                self._redis = None
        logger.info("cache_initialized", backend="redis" if self._redis else "memory")

    async def disconnect(self) -> None:
        if self._redis:
            await self._redis.close()
        self._store.clear()

    async def get_quote(self, symbol: str) -> dict[str, Any] | None:
        key = f"quote:{symbol.upper()}"
        if self._redis:
            raw = await self._redis.get(key)
            if raw:
                return json.loads(raw)
            return None
        entry = self._store.get(key)
        if entry is None:
            return None
        import time
        expire_at, data = entry
        if time.time() > expire_at:
            del self._store[key]
            return None
        return data

    async def set_quote(self, symbol: str, data: dict[str, Any], ttl: int = 60) -> None:
        key = f"quote:{symbol.upper()}"
        if self._redis:
            await self._redis.set(key, json.dumps(data), ex=ttl)
            return
        import time
        self._store[key] = (time.time() + ttl, data)

    async def get_historical(self, symbol: str, timeframe: str) -> list[dict[str, Any]] | None:
        key = f"hist:{symbol.upper()}:{timeframe}"
        if self._redis:
            raw = await self._redis.get(key)
            if raw:
                return json.loads(raw)
            return None
        entry = self._store.get(key)
        if entry is None:
            return None
        import time
        expire_at, data = entry
        if time.time() > expire_at:
            del self._store[key]
            return None
        return data

    async def set_historical(self, symbol: str, timeframe: str, data: list[dict[str, Any]], ttl: int = 300) -> None:
        key = f"hist:{symbol.upper()}:{timeframe}"
        if self._redis:
            await self._redis.set(key, json.dumps(data), ex=ttl)
            return
        import time
        self._store[key] = (time.time() + ttl, data)

    async def invalidate(self, symbol: str) -> None:
        prefix = f"quote:{symbol.upper()}"
        if self._redis:
            await self._redis.delete(prefix)
            return
        self._store.pop(prefix, None)
