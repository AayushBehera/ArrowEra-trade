"""Technical indicators computed from OHLCV data."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _ensure_df(data: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(data)
    for col in ("open", "high", "low", "close", "volume"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict[str, pd.Series]:
    fast_ema = ema(series, fast)
    slow_ema = ema(series, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def bollinger_bands(series: pd.Series, period: int = 20, num_std: float = 2.0) -> dict[str, pd.Series]:
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    return {
        "upper": middle + num_std * std,
        "middle": middle,
        "lower": middle - num_std * std,
    }


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def vwap(df: pd.DataFrame) -> pd.Series:
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    cumulative_volume = df["volume"].cumsum()
    cumulative_tp_vol = (typical_price * df["volume"]).cumsum()
    return cumulative_tp_vol / cumulative_volume


def compute_all_indicators(data: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute all indicators for a given OHLCV dataset and return latest values."""
    df = _ensure_df(data)
    if df.empty or len(df) < 26:
        return {"error": "Insufficient data (need at least 26 bars)"}

    close = df["close"]
    last = len(df) - 1

    macd_result = macd(close)
    bb = bollinger_bands(close)

    return {
        "symbol": data[0].get("symbol", "UNKNOWN"),
        "bars": len(df),
        "sma_20": float(sma(close, 20).iloc[last]) if len(df) >= 20 else None,
        "sma_50": float(sma(close, 50).iloc[last]) if len(df) >= 50 else None,
        "sma_200": float(sma(close, 200).iloc[last]) if len(df) >= 200 else None,
        "ema_12": float(ema(close, 12).iloc[last]),
        "ema_26": float(ema(close, 26).iloc[last]),
        "rsi_14": float(rsi(close).iloc[last]),
        "macd": float(macd_result["macd"].iloc[last]),
        "macd_signal": float(macd_result["signal"].iloc[last]),
        "macd_histogram": float(macd_result["histogram"].iloc[last]),
        "bb_upper": float(bb["upper"].iloc[last]),
        "bb_middle": float(bb["middle"].iloc[last]),
        "bb_lower": float(bb["lower"].iloc[last]),
        "atr_14": float(atr(df).iloc[last]),
        "vwap": float(vwap(df).iloc[last]),
    }
