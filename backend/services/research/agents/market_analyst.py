"""
ArrowEra Trade - Market Analyst Agent

Analyzes broad market trends, sector performance, and macroeconomic indicators.
"""

from typing import Dict, Any, List
import pandas as pd
import structlog

from .base_agent import BaseAgent

logger = structlog.get_logger(__name__)

class MarketAnalyst(BaseAgent):
    """Agent for analyzing market trends and macro conditions."""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("MarketAnalyst", config)

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze market conditions.
        
        Context expects:
        - market_data: Dict of symbol -> DataFrame with OHLCV
        - indices: Dict of index symbol -> DataFrame
        - news: List of recent news headlines (optional)
        """
        self._log_start(context)

        market_data = context.get("market_data", {})
        indices = context.get("indices", {})
        
        analysis = {
            "agent": self.name,
            "timestamp": pd.Timestamp.now().isoformat(),
            "market_trend": "neutral",
            "volatility_regime": "normal",
            "sector_performance": {},
            "key_levels": {},
            "reasoning": [],
            "confidence": 0.5
        }

        try:
            # 1. Analyze Indices (SPY, QQQ, etc.) for overall trend
            if indices:
                trend_analysis = self._analyze_indices(indices)
                analysis.update(trend_analysis)
                analysis["reasoning"].append(f"Index trend identified as {trend_analysis.get('market_trend')}")

            # 2. Analyze Volatility (VIX or realized vol)
            if market_data:
                vol_analysis = self._analyze_volatility(market_data)
                analysis["volatility_regime"] = vol_analysis.get("regime", "normal")
                analysis["reasoning"].append(f"Volatility regime: {vol_analysis.get('regime')}")

            # 3. Identify Key Support/Resistance levels
            if market_data:
                levels = self._identify_key_levels(market_data)
                analysis["key_levels"] = levels

            # 4. Generate overall sentiment
            analysis["market_trend"] = self._determine_overall_trend(analysis)
            analysis["confidence"] = self._calculate_confidence(analysis)

        except Exception as e:
            logger.error(f"Error in MarketAnalyst analysis", error=str(e))
            analysis["error"] = str(e)

        self._log_complete(analysis)
        return analysis

    def _analyze_indices(self, indices: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze major indices to determine market direction."""
        trends = {}
        bullish_count = 0
        bearish_count = 0

        for symbol, df in indices.items():
            if len(df) < 50:
                continue

            # Simple Moving Average Trend
            sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
            sma_200 = df['close'].rolling(window=200).mean().iloc[-1]
            current_price = df['close'].iloc[-1]

            if current_price > sma_50 > sma_200:
                trends[symbol] = "bullish"
                bullish_count += 1
            elif current_price < sma_50 < sma_200:
                trends[symbol] = "bearish"
                bearish_count += 1
            else:
                trends[symbol] = "neutral"

        overall = "neutral"
        if bullish_count > bearish_count:
            overall = "bullish"
        elif bearish_count > bullish_count:
            overall = "bearish"

        return {"market_trend": overall, "index_trends": trends}

    def _analyze_volatility(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze volatility to determine market regime."""
        # Use SPY or first available symbol as proxy
        symbol = list(market_data.keys())[0]
        df = market_data[symbol]
        
        if len(df) < 20:
            return {"regime": "unknown"}

        # Calculate realized volatility (std dev of returns)
        returns = df['close'].pct_change().dropna()
        realized_vol = returns.rolling(window=20).std().iloc[-1]
        
        # Annualize
        annualized_vol = realized_vol * (252 ** 0.5)

        regime = "normal"
        if annualized_vol < 0.10:
            regime = "low"
        elif annualized_vol > 0.25:
            regime = "high"

        return {"regime": regime, "realized_volatility": annualized_vol}

    def _identify_key_levels(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Identify support and resistance levels."""
        levels = {}
        for symbol, df in market_data.items():
            if len(df) < 20:
                continue
            
            # Simple pivot points (highs and lows of recent period)
            recent = df.tail(20)
            resistance = recent['high'].max()
            support = recent['low'].min()
            
            levels[symbol] = {
                "resistance": resistance,
                "support": support,
                "current": df['close'].iloc[-1]
            }
        return levels

    def _determine_overall_trend(self, analysis: Dict[str, Any]) -> str:
        """Synthesize individual signals into an overall trend."""
        # Simple logic: if index trend is bullish and vol is normal/low -> bullish
        trend = analysis.get("market_trend", "neutral")
        vol = analysis.get("volatility_regime", "normal")
        
        if vol == "high":
            # High volatility often overrides trend signals
            return "neutral" 
        
        return trend

    def _calculate_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score based on data quality and agreement."""
        # Placeholder: In real implementation, this would check data consistency
        return 0.7