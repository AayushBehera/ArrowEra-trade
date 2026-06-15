"""Market data base interfaces and types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


class AssetType(str, Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    FOREX = "forex"
    ETF = "etf"
    INDEX = "index"
    COMMODITY = "commodity"


class TimeFrame(str, Enum):
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1mo"


class OHLCVBar:
    """Single OHLCV bar with decimal-safe prices."""

    __slots__ = ("symbol", "timestamp", "open", "high", "low", "close", "volume", "adjusted_close")

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        open: Decimal,
        high: Decimal,
        low: Decimal,
        close: Decimal,
        volume: Decimal,
        adjusted_close: Decimal | None = None,
    ) -> None:
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.adjusted_close = adjusted_close or close

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": str(self.open),
            "high": str(self.high),
            "low": str(self.low),
            "close": str(self.close),
            "volume": str(self.volume),
            "adjusted_close": str(self.adjusted_close),
        }


class Quote:
    """Real-time quote snapshot."""

    __slots__ = ("symbol", "price", "change", "change_percent", "volume", "high", "low", "open", "previous_close", "asset_type")

    def __init__(
        self,
        symbol: str,
        price: Decimal,
        change: Decimal = Decimal("0"),
        change_percent: Decimal = Decimal("0"),
        volume: Decimal = Decimal("0"),
        high: Decimal = Decimal("0"),
        low: Decimal = Decimal("0"),
        open: Decimal = Decimal("0"),
        previous_close: Decimal = Decimal("0"),
        asset_type: AssetType = AssetType.STOCK,
    ) -> None:
        self.symbol = symbol
        self.price = price
        self.change = change
        self.change_percent = change_percent
        self.volume = volume
        self.high = high
        self.low = low
        self.open = open
        self.previous_close = previous_close
        self.asset_type = asset_type

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "price": str(self.price),
            "change": str(self.change),
            "changePercent": str(self.change_percent),
            "volume": str(self.volume),
            "high": str(self.high),
            "low": str(self.low),
            "open": str(self.open),
            "previousClose": str(self.previous_close),
            "assetType": self.asset_type.value,
        }


class MarketDataProvider(ABC):
    """Abstract base for market data providers."""

    name: str = "base"

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def get_historical(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: TimeFrame = TimeFrame.DAILY,
    ) -> list[OHLCVBar]: ...

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote: ...

    @abstractmethod
    async def get_symbols(self, asset_type: AssetType | None = None) -> list[str]: ...
