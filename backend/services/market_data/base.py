"""
ArrowEra Trade - Market Data Base Interface

Abstract base class for market data providers.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

class AssetType(str, Enum):
    """Supported asset types."""
    STOCK = "stock"
    CRYPTO = "crypto"
    FOREX = "forex"
    ETF = "etf"
    INDEX = "index"
    COMMODITY = "commodity"

class TimeFrame(str, Enum):
    """Supported timeframes."""
    TICK = "tick"
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1M"

class OHLCV:
    """OHLCV Data Container."""
    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        adjusted_close: Optional[float] = None,
    ):
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.adjusted_close = adjusted_close

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "adjusted_close": self.adjusted_close,
        }

class MarketDataProvider(ABC):
    """Abstract base class for market data providers."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the data provider."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the data provider."""
        pass

    @abstractmethod
    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: TimeFrame = TimeFrame.DAILY,
    ) -> List[OHLCV]:
        """Fetch historical OHLCV data."""
        pass

    @abstractmethod
    async def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time quote for a symbol."""
        pass

    @abstractmethod
    async def get_symbols(self, asset_type: Optional[AssetType] = None) -> List[Dict[str, Any]]:
        """Get list of available symbols."""
        pass

    @property
    def is_connected(self) -> bool:
        """Check if provider is connected."""
        return self._is_connected