"""
ArrowEra Trade - Market Data Cache

Redis-based caching layer for market data to reduce API calls and latency.
"""

import json
import orjson
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import redis.asyncio as redis
from redis.asyncio import Redis
import structlog

from ..base import OHLCV, TimeFrame
from backend.config import settings

logger = structlog.get_logger(__name__)

class MarketDataCache:
    """Redis cache for market data."""

    def __init__(self):
        self._client: Optional[Redis] = None
        self.default_ttl = settings.CACHE_TTL_MARKET_DATA

    async def connect(self) -> None:
        """Initialize Redis connection."""
        try:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_POOL_SIZE
            )
            # Test connection
            await self._client.ping()
            logger.info("Market Data Cache connected to Redis")
        except Exception as e:
            logger.error("Failed to connect to Redis cache", error=str(e))
            raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            logger.info("Market Data Cache disconnected")

    def _generate_key(self, symbol: str, timeframe: TimeFrame, timestamp: Optional[datetime] = None) -> str:
        """Generate a cache key."""
        base = f"market:{symbol.lower()}:{timeframe.value}"
        if timestamp:
            base += f":{timestamp.strftime('%Y%m%d')}"
        return base

    async def get_ohlcv(
        self, 
        symbol: str, 
        timeframe: TimeFrame, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve cached OHLCV data for a date range.
        Note: This is a simplified implementation. For large ranges, 
        we might store individual days or use a different strategy.
        """
        try:
            # For simplicity, we try to fetch the whole range as one key
            # In production, you might iterate over days or use Redis TimeSeries
            key = self._generate_key(symbol, timeframe)
            cached_data = await self._client.get(key)
            
            if cached_data:
                data = orjson.loads(cached_data)
                # Filter by date range
                filtered = [
                    d for d in data 
                    if start_date <= datetime.fromisoformat(d['timestamp']) <= end_date
                ]
                logger.debug("Cache hit", symbol=symbol, count=len(filtered))
                return filtered
            
            return None
        except Exception as e:
            logger.error("Error getting data from cache", symbol=symbol, error=str(e))
            return None

    async def set_ohlcv(
        self, 
        symbol: str, 
        timeframe: TimeFrame, 
        data: List[Dict[str, Any]], 
        ttl: Optional[int] = None
    ) -> None:
        """Cache OHLCV data."""
        try:
            if not data:
                return
            
            key = self._generate_key(symbol, timeframe)
            ttl = ttl or self.default_ttl
            
            # Serialize using orjson for speed
            serialized = orjson.dumps(data)
            
            await self._client.set(key, serialized, ex=ttl)
            logger.debug("Data cached", symbol=symbol, key=key, ttl=ttl)
        except Exception as e:
            logger.error("Error setting data in cache", symbol=symbol, error=str(e))

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached real-time quote."""
        try:
            key = f"quote:{symbol.lower()}"
            cached_data = await self._client.get(key)
            if cached_data:
                return orjson.loads(cached_data)
            return None
        except Exception as e:
            logger.error("Error getting quote from cache", symbol=symbol, error=str(e))
            return None

    async def set_quote(self, symbol: str, quote: Dict[str, Any], ttl: int = 60) -> None:
        """Cache real-time quote."""
        try:
            key = f"quote:{symbol.lower()}"
            await self._client.set(key, orjson.dumps(quote), ex=ttl)
        except Exception as e:
            logger.error("Error setting quote in cache", symbol=symbol, error=str(e))

    async def invalidate_symbol(self, symbol: str) -> None:
        """Invalidate all cached data for a symbol."""
        try:
            pattern = f"market:{symbol.lower()}:*"
            keys = []
            async for key in self._client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self._client.delete(*keys)
                logger.info("Invalidated cache for symbol", symbol=symbol, count=len(keys))
        except Exception as e:
            logger.error("Error invalidating cache", symbol=symbol, error=str(e))

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            info = await self._client.info("stats")
            keyspace = await self._client.info("keyspace")
            return {
                "total_keys": info.get("keyspace", 0),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "db_info": keyspace
            }
        except Exception as e:
            logger.error("Error getting cache stats", error=str(e))
            return {}