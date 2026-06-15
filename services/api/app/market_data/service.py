"""Market data service - orchestrates providers and cache."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import structlog

from .base import AssetType, MarketDataProvider, TimeFrame
from .cache import MarketDataCache
from .yfinance_provider import YFinanceProvider

logger = structlog.get_logger(__name__)


class MarketDataService:
    """Central market data orchestration service."""

    def __init__(self) -> None:
        self._providers: dict[str, MarketDataProvider] = {}
        self._cache = MarketDataCache()
        self._initialized = False

    async def initialize(self, redis_url: str | None = None) -> None:
        if self._initialized:
            return
        await self._cache.connect(redis_url)
        yf = YFinanceProvider()
        await yf.connect()
        self._providers["yfinance"] = yf
        self._initialized = True
        logger.info("market_data_service_initialized", providers=list(self._providers.keys()))

    async def shutdown(self) -> None:
        await self._cache.disconnect()
        for provider in self._providers.values():
            await provider.disconnect()
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError("MarketDataService not initialized - call initialize() first")

    def _default_provider(self) -> MarketDataProvider:
        if not self._providers:
            raise RuntimeError("No market data providers available")
        return next(iter(self._providers.values()))

    async def get_quote(self, symbol: str, provider_name: str | None = None) -> dict[str, Any]:
        self._ensure_initialized()
        cached = await self._cache.get_quote(symbol)
        if cached:
            return cached
        provider = self._providers.get(provider_name, self._default_provider()) if provider_name else self._default_provider()
        quote = await provider.get_quote(symbol)
        data = quote.to_dict()
        await self._cache.set_quote(symbol, data)
        return data

    async def get_market_overview(self, symbols: list[str]) -> dict[str, Any]:
        self._ensure_initialized()
        results: dict[str, Any] = {}
        for symbol in symbols:
            try:
                results[symbol] = await self.get_quote(symbol)
            except Exception as exc:
                logger.warning("quote_failed", symbol=symbol, error=str(exc))
                results[symbol] = {"symbol": symbol, "error": str(exc)}
        return results

    async def get_historical(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timeframe: TimeFrame = TimeFrame.DAILY,
        provider_name: str | None = None,
    ) -> list[dict[str, Any]]:
        self._ensure_initialized()
        end = end or datetime.now()
        start = start or (end - timedelta(days=365))

        cached = await self._cache.get_historical(symbol, timeframe.value)
        if cached:
            return cached

        provider = self._providers.get(provider_name, self._default_provider()) if provider_name else self._default_provider()
        bars = await provider.get_historical(symbol, start, end, timeframe)
        data = [bar.to_dict() for bar in bars]
        if data:
            await self._cache.set_historical(symbol, timeframe.value, data)
        return data

    async def get_symbols(self, asset_type: AssetType | None = None) -> list[str]:
        self._ensure_initialized()
        return await self._default_provider().get_symbols(asset_type)


# Singleton instance
market_data_service = MarketDataService()
