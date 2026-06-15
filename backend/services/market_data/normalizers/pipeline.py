"""
ArrowEra Trade - Data Normalization Pipeline

Handles normalization of market data from various providers into a standard format.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import pandas as pd
import structlog

from ..base import OHLCV, TimeFrame

logger = structlog.get_logger(__name__)

class DataNormalizer:
    """Normalizes market data from various providers."""

    def __init__(self, target_timezone: str = "UTC"):
        self.target_timezone = target_timezone

    def normalize_ohlcv(self, data: List[OHLCV]) -> List[Dict[str, Any]]:
        """
        Normalize a list of OHLCV objects into a standard dictionary format.
        Ensures timezone consistency and data types.
        """
        normalized = []
        for item in data:
            try:
                # Ensure timestamp is timezone-aware
                ts = item.timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                else:
                    ts = ts.astimezone(timezone.utc)

                normalized_item = {
                    "symbol": item.symbol.upper(),
                    "timestamp": ts.isoformat(),
                    "open": round(float(item.open), 6),
                    "high": round(float(item.high), 6),
                    "low": round(float(item.low), 6),
                    "close": round(float(item.close), 6),
                    "volume": int(item.volume) if item.volume is not None else 0,
                    "adjusted_close": round(float(item.adjusted_close), 6) if item.adjusted_close else None,
                }
                normalized.append(normalized_item)
            except Exception as e:
                logger.error("Error normalizing OHLCV item", item=item, error=str(e))
                continue
        
        return normalized

    def normalize_dataframe(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Normalize a pandas DataFrame containing market data.
        Expected columns: Open, High, Low, Close, Volume (and optionally Adj Close)
        """
        try:
            # Standardize column names
            df.columns = [col.lower().replace(' ', '_') for col in df.columns]
            
            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")

            # Handle index (timestamp)
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'date' in df.columns or 'timestamp' in df.columns:
                    date_col = 'date' if 'date' in df.columns else 'timestamp'
                    df[date_col] = pd.to_datetime(df[date_col])
                    df.set_index(date_col, inplace=True)
                else:
                    raise ValueError("DataFrame must have a DatetimeIndex or a 'date'/'timestamp' column")

            # Ensure timezone is UTC
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC')
            else:
                df.index = df.index.tz_convert('UTC')

            # Sort by timestamp
            df.sort_index(inplace=True)

            # Add symbol column
            df['symbol'] = symbol.upper()

            # Clean data (remove NaNs in critical columns)
            df.dropna(subset=required_cols, inplace=True)

            # Round numerical columns
            numeric_cols = ['open', 'high', 'low', 'close']
            if 'adjusted_close' in df.columns:
                numeric_cols.append('adjusted_close')
            
            for col in numeric_cols:
                df[col] = df[col].round(6)

            return df

        except Exception as e:
            logger.error("Error normalizing DataFrame", symbol=symbol, error=str(e))
            raise

    def resample(
        self, 
        data: List[OHLCV], 
        target_timeframe: TimeFrame
    ) -> List[OHLCV]:
        """
        Resample data to a different timeframe (e.g., 1m to 5m).
        """
        if not data:
            return []

        try:
            # Convert to DataFrame
            df = pd.DataFrame([d.to_dict() for d in data])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)

            # Define resampling rule
            rule_map = {
                TimeFrame.MINUTE_1: '1T',
                TimeFrame.MINUTE_5: '5T',
                TimeFrame.MINUTE_15: '15T',
                TimeFrame.HOUR_1: '1H',
                TimeFrame.HOUR_4: '4H',
                TimeFrame.DAILY: '1D',
                TimeFrame.WEEKLY: '1W',
                TimeFrame.MONTHLY: '1M',
            }
            rule = rule_map.get(target_timeframe, '1D')

            # Resample
            resampled = df.resample(rule).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'adjusted_close': 'last' if 'adjusted_close' in df.columns else 'last'
            }).dropna()

            # Convert back to OHLCV objects
            result = []
            for ts, row in resampled.iterrows():
                result.append(OHLCV(
                    symbol=data[0].symbol,
                    timestamp=ts.to_pydatetime(),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=float(row['volume']),
                    adjusted_close=float(row['adjusted_close']) if 'adjusted_close' in row else None
                ))
            
            return result

        except Exception as e:
            logger.error("Error resampling data", error=str(e))
            raise