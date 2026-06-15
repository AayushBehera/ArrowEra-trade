"""YFinance market data provider."""

from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
from functools import partial
from typing import Any

import structlog

from .base import AssetType, MarketDataProvider, OHLCVBar, Quote, TimeFrame

logger = structlog.get_logger(__name__)

_TIMEFRAME_MAP = {
    TimeFrame.MINUTE_1: "1m",
    TimeFrame.MINUTE_5: "5m",
    TimeFrame.MINUTE_15: "15m",
    TimeFrame.HOUR_1: "60m",
    TimeFrame.DAILY: "1d",
    TimeFrame.WEEKLY: "1wk",
    TimeFrame.MONTHLY: "1mo",
}


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value)).quantize(Decimal("0.00000001"))


class YFinanceProvider(MarketDataProvider):
    """Fetches data via yfinance (runs sync calls in thread pool)."""

    name = "yfinance"

    def __init__(self) -> None:
        self._connected = False

    async def connect(self) -> None:
        import yfinance  # noqa: F401 – verify import works
        self._connected = True
        logger.info("yfinance_provider_connected")

    async def disconnect(self) -> None:
        self._connected = False

    async def get_historical(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: TimeFrame = TimeFrame.DAILY,
    ) -> list[OHLCVBar]:
        import yfinance as yf

        interval = _TIMEFRAME_MAP.get(timeframe, "1d")
        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, partial(yf.Ticker, symbol))
        df = await loop.run_in_executor(
            None,
            partial(ticker.history, start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"), interval=interval),
        )
        if df.empty:
            return []

        bars: list[OHLCVBar] = []
        for idx, row in df.iterrows():
            ts = idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else datetime.fromisoformat(str(idx))
            bars.append(
                OHLCVBar(
                    symbol=symbol,
                    timestamp=ts,
                    open=_to_decimal(row.get("Open", 0)),
                    high=_to_decimal(row.get("High", 0)),
                    low=_to_decimal(row.get("Low", 0)),
                    close=_to_decimal(row.get("Close", 0)),
                    volume=_to_decimal(row.get("Volume", 0)),
                )
            )
        return bars

    async def get_quote(self, symbol: str) -> Quote:
        import yfinance as yf

        loop = asyncio.get_event_loop()
        ticker = await loop.run_in_executor(None, partial(yf.Ticker, symbol))
        info = await loop.run_in_executor(None, lambda: ticker.fast_info)

        price = _to_decimal(getattr(info, "last_price", 0))
        prev = _to_decimal(getattr(info, "previous_close", 0))
        change = price - prev
        change_pct = (change / prev * Decimal("100")) if prev else Decimal("0")

        return Quote(
            symbol=symbol,
            price=price,
            change=change,
            change_percent=change_pct.quantize(Decimal("0.01")),
            volume=_to_decimal(getattr(info, "last_volume", 0)),
            high=_to_decimal(getattr(info, "day_high", 0)),
            low=_to_decimal(getattr(info, "day_low", 0)),
            open=_to_decimal(getattr(info, "open", 0)),
            previous_close=prev,
        )

    async def get_symbols(self, asset_type: AssetType | None = None) -> list[str]:
        defaults = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "SPY", "QQQ", "IWM"]
        return defaults
