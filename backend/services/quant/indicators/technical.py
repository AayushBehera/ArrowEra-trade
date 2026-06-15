"""
ArrowEra Trade - Technical Indicators Library

Comprehensive library of technical analysis indicators.
"""

import pandas as pd
import numpy as np
from typing import Optional, Union
import structlog

logger = structlog.get_logger(__name__)

class TechnicalIndicators:
    """Collection of technical analysis indicators."""

    @staticmethod
    def sma(data: Union[pd.Series, np.ndarray], window: int) -> pd.Series:
        """Simple Moving Average."""
        return pd.Series(data).rolling(window=window).mean()

    @staticmethod
    def ema(data: Union[pd.Series, np.ndarray], window: int) -> pd.Series:
        """Exponential Moving Average."""
        return pd.Series(data).ewm(span=window, adjust=False).mean()

    @staticmethod
    def rsi(data: Union[pd.Series, np.ndarray], window: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = pd.Series(data).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def macd(
        data: Union[pd.Series, np.ndarray], 
        fast: int = 12, 
        slow: int = 26, 
        signal: int = 9
    ) -> pd.DataFrame:
        """Moving Average Convergence Divergence."""
        ema_fast = TechnicalIndicators.ema(data, fast)
        ema_slow = TechnicalIndicators.ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        return pd.DataFrame({
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        })

    @staticmethod
    def bollinger_bands(
        data: Union[pd.Series, np.ndarray], 
        window: int = 20, 
        num_std: float = 2.0
    ) -> pd.DataFrame:
        """Bollinger Bands."""
        sma = TechnicalIndicators.sma(data, window)
        std = pd.Series(data).rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return pd.DataFrame({
            'middle': sma,
            'upper': upper_band,
            'lower': lower_band
        })

    @staticmethod
    def atr(
        high: Union[pd.Series, np.ndarray], 
        low: Union[pd.Series, np.ndarray], 
        close: Union[pd.Series, np.ndarray], 
        window: int = 14
    ) -> pd.Series:
        """Average True Range."""
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=window).mean()

    @staticmethod
    def stochastic_oscillator(
        high: Union[pd.Series, np.ndarray], 
        low: Union[pd.Series, np.ndarray], 
        close: Union[pd.Series, np.ndarray], 
        k_window: int = 14, 
        d_window: int = 3
    ) -> pd.DataFrame:
        """Stochastic Oscillator."""
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        low_min = low.rolling(window=k_window).min()
        high_max = high.rolling(window=k_window).max()
        
        k_percent = 100 * ((close - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_window).mean()
        
        return pd.DataFrame({
            'k': k_percent,
            'd': d_percent
        })

    @staticmethod
    def williams_r(
        high: Union[pd.Series, np.ndarray], 
        low: Union[pd.Series, np.ndarray], 
        close: Union[pd.Series, np.ndarray], 
        window: int = 14
    ) -> pd.Series:
        """Williams %R."""
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        high_max = high.rolling(window=window).max()
        low_min = low.rolling(window=window).min()
        
        return -100 * ((high_max - close) / (high_max - low_min))

    @staticmethod
    def cci(
        high: Union[pd.Series, np.ndarray], 
        low: Union[pd.Series, np.ndarray], 
        close: Union[pd.Series, np.ndarray], 
        window: int = 20
    ) -> pd.Series:
        """Commodity Channel Index."""
        high = pd.Series(high)
        low = pd.Series(low)
        close = pd.Series(close)
        
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(window=window).mean()
        mad = tp.rolling(window=window).apply(lambda x: np.abs(x - x.mean()).mean())
        
        return (tp - sma_tp) / (0.015 * mad)

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume."""
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return obv