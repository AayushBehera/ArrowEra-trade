"""
ArrowEra Trade - Market Data Service

Main service for fetching, caching, and normalizing market data.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog

from .base import MarketDataProvider, OHLCV, TimeFrame, AssetType
from .providers.yfinance_provider import YFinanceProvider
from .normalizers.pipeline import DataNormalizer
from .cache import MarketDataCache
from backend.config import settings

logger = structlog.get_logger(__name__)

class MarketDataService:
    """Orchestrates market data fetching, caching, and normalization."""

    def __init__(self):
        self.providers: Dict[str, MarketDataProvider] = {}
        self.normalizer = DataNormalizer()
        self.cache = MarketDataCache()
        self._is_initialized = False

    async def initialize(self):
        """Initialize the service and connect to providers/cache."""
        if self._is_initialized:
            return

        try:
            # Initialize Cache
            await self.cache.connect()

            # Initialize Providers
            if settings.YFINANCE_ENABLED:
                yf_provider = YFinanceProvider()
                await yf_provider.connect()
                self.providers["yfinance"] = yf_provider
                logger.info("YFinance provider initialized")

            # Add other providers here (AlphaVantage, Polygon, etc.)
            # if settings.ALPHA_VANTAGE_API_KEY:
            #     av_provider = AlphaVantageProvider(...)
            #     await av_provider.connect()
            #     self.providers["alphavantage"] = av_provider

            self._is_initialized = True
            logger.info("Market Data Service initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Market Data Service", error=str(e))
            raise

    async def shutdown(self):
        """Shutdown the service and close connections."""
        await self.cache.disconnect()
        for name, provider in self.providers.items():
            await provider.disconnect()
        self._is_initialized = False
        logger.info("Market Data Service shut down")

    def _get_provider(self, provider_name: Optional[str] = None) -> MarketDataProvider:
        """Get a specific provider or the default one."""
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name]
        
        if not self.providers:
            raise RuntimeError("No market data providers available")
        
        # Return the first available provider as default
        return next(iter(self.providers.values()))

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: TimeFrame = TimeFrame.DAILY,
        provider: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get historical OHLCV data.
        
        Args:
            symbol: Asset symbol (e.g., 'AAPL')
            start_date: Start date for data
            end_date: End date for data
            timeframe: Data timeframe
            provider: Specific provider to use (optional)
            use_cache: Whether to check cache first
        """
        if not self._is_initialized:
            await self.initialize()

        # 1. Check Cache
        if use_cache:
            cached_data = await self.cache.get_ohlcv(symbol, timeframe, start_date, end_date)
            if cached_data:
                logger.info("Returning cached data", symbol=symbol)
                return cached_data

        # 2. Fetch from Provider
        data_provider = self._get_provider(provider)
        raw_data = await data_provider.get_historical_data(symbol, start_date, end_date, timeframe)

        if not raw_data:
            logger.warning("No data returned from provider", symbol=symbol)
            return []

        # 3. Normalize
        normalized_data = self.normalizer.normalize_ohlcv(raw_data)

        # 4. Update Cache
        if use_cache and normalized_data:
            await self.cache.set_ohlcv(symbol, timeframe, normalized_data)

        return normalized_data

    async def get_realtime_quote(
        self,
        symbol: str,
        provider: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Get real-time quote for a symbol."""
        if not self._is_initialized:
            await self.initialize()

        # 1. Check Cache (short TTL)
        if use_cache:
            cached_quote = await self.cache.get_quote(symbol)
            if cached_quote:
                return cached_quote

        # 2. Fetch from Provider
        data_provider = self._get_provider(provider)
        quote = await data_provider.get_realtime_quote(symbol)

        # 3. Update Cache
        if use_cache and quote:
            await self.cache.set_quote(symbol, quote)

        return quote

    async def get_symbols(
        self,
        asset_type: Optional[AssetType] = None,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of available symbols."""
        if not self._is_initialized:
            await self.initialize()

        data_provider = self._get_provider(provider)
        return await data_provider.get_symbols(asset_type)

    async def get_market_overview(self, symbols: List[str]) -> Dict[str, Any]:
        """Get a quick overview of multiple symbols (quotes)."""
        quotes = {}
        for symbol in symbols:
            try:
                quote = await self.get_realtime_quote(symbol)
                quotes[symbol] = quote
            except Exception as e:
                logger.error("Failed to fetch quote for overview", symbol=symbol, error=str(e))
                quotes[symbol] = {"error": str(e)}
        return quotes

# Singleton instance
market_data_service = MarketDataService()