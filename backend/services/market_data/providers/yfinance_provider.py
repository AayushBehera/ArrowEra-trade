"""
ArrowEra Trade - YFinance Market Data Provider

Implementation of market data provider using yfinance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import structlog

from ..base import MarketDataProvider, OHLCV, TimeFrame, AssetType

logger = structlog.get_logger(__name__)

# Mapping TimeFrame enum to yfinance intervals
TIMEFRAME_MAP = {
    TimeFrame.MINUTE_1: "1m",
    TimeFrame.MINUTE_5: "5m",
    TimeFrame.MINUTE_15: "15m",
    TimeFrame.HOUR_1: "1h",
    TimeFrame.HOUR_4: "4h",  # Note: yfinance might not support all, fallback to 1h
    TimeFrame.DAILY: "1d",
    TimeFrame.WEEKLY: "1wk",
    TimeFrame.MONTHLY: "1mo",
}

class YFinanceProvider(MarketDataProvider):
    """Market data provider using Yahoo Finance API."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._client = None

    async def connect(self) -> bool:
        """Initialize yfinance client."""
        try:
            # yfinance doesn't have a persistent connection object in the same way
            # We just validate it's working by fetching a simple ticker
            test_ticker = yf.Ticker("AAPL")
            info = test_ticker.info
            if info:
                self._is_connected = True
                logger.info("YFinance provider connected successfully")
                return True
        except Exception as e:
            logger.error("Failed to connect to YFinance", error=str(e))
            return False
        return False

    async def disconnect(self) -> None:
        """Cleanup resources."""
        self._is_connected = False
        logger.info("YFinance provider disconnected")

    async def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: TimeFrame = TimeFrame.DAILY,
    ) -> List[OHLCV]:
        """Fetch historical OHLCV data."""
        if not self._is_connected:
            await self.connect()

        try:
            interval = TIMEFRAME_MAP.get(timeframe, "1d")
            
            # yfinance download
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True, # Adjust for splits/dividends
                prepost=False,
                threads=True
            )

            if df.empty:
                logger.warning(f"No data found for symbol {symbol}")
                return []

            # Convert DataFrame to OHLCV objects
            ohlcv_list = []
            for timestamp, row in df.iterrows():
                # Ensure timestamp is timezone-aware (UTC)
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=None) # Treat as naive if not provided
                
                ohlcv = OHLCV(
                    symbol=symbol,
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume']),
                    adjusted_close=float(row['Close']) # yfinance auto_adjust handles this
                )
                ohlcv_list.append(ohlcv)

            logger.info(
                "Fetched historical data",
                symbol=symbol,
                count=len(ohlcv_list),
                start=start_date,
                end=end_date
            )
            return ohlcv_list

        except Exception as e:
            logger.error(
                "Failed to fetch historical data",
                symbol=symbol,
                error=str(e)
            )
            raise

    async def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time quote for a symbol."""
        if not self._is_connected:
            await self.connect()

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            fast_info = ticker.fast_info

            # Combine fast_info (more reliable for price) with detailed info
            quote = {
                "symbol": symbol,
                "price": fast_info.last_price,
                "change": fast_info.last_price - fast_info.previous_close,
                "change_percent": ((fast_info.last_price - fast_info.previous_close) / fast_info.previous_close) * 100 if fast_info.previous_close else 0,
                "volume": fast_info.last_volume,
                "open": fast_info.open,
                "high": fast_info.day_high,
                "low": fast_info.day_low,
                "previous_close": fast_info.previous_close,
                "bid": fast_info.bid,
                "ask": fast_info.ask,
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency"),
                "timestamp": datetime.utcnow().isoformat()
            }
            return quote

        except Exception as e:
            logger.error("Failed to fetch realtime quote", symbol=symbol, error=str(e))
            raise

    async def get_symbols(self, asset_type: Optional[AssetType] = None) -> List[Dict[str, Any]]:
        """
        Get list of available symbols.
        Note: YFinance doesn't have a comprehensive 'list all' API.
        This is a placeholder for a screener implementation.
        """
        # In a real implementation, this would query a database or use a screener API
        # For now, we return a placeholder list
        logger.warning("YFinance get_symbols is not fully implemented, returning placeholder")
        return [
            {"symbol": "AAPL", "name": "Apple Inc.", "type": "stock"},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "type": "stock"},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "type": "stock"},
            {"symbol": "AMZN", "name": "Amazon.com, Inc.", "type": "stock"},
            {"symbol": "TSLA", "name": "Tesla, Inc.", "type": "stock"},
            {"symbol": "BTC-USD", "name": "Bitcoin USD", "type": "crypto"},
            {"symbol": "ETH-USD", "name": "Ethereum USD", "type": "crypto"},
        ]