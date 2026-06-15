"""Signal generation engine combining quant indicators and research outputs."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4


@dataclass
class SignalResult:
    id: str = field(default_factory=lambda: str(uuid4()))
    symbol: str = ""
    signal_type: str = "HOLD"  # BUY, SELL, HOLD
    confidence: float = 0.0
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SignalEngine:
    """Generates trading signals by combining quant indicators and research outputs."""

    # Thresholds for signal generation
    RSI_OVERSOLD = 30.0
    RSI_OVERBOUGHT = 70.0
    MACD_BULLISH_THRESHOLD = 0.0
    BB_LOWER_TOUCH = 0.02  # within 2% of lower band
    BB_UPPER_TOUCH = 0.02  # within 2% of upper band
    MIN_CONFIDENCE = 0.3

    def generate_from_indicators(self, symbol: str, indicators: dict) -> SignalResult:
        """Generate a signal from technical indicators alone."""
        score = 0.0
        reasons: list[str] = []

        rsi = indicators.get("rsi_14", 50.0)
        if rsi < self.RSI_OVERSOLD:
            score += 0.3
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > self.RSI_OVERBOUGHT:
            score -= 0.3
            reasons.append(f"RSI overbought ({rsi:.1f})")

        macd_hist = indicators.get("macd_histogram", 0.0)
        if macd_hist > self.MACD_BULLISH_THRESHOLD:
            score += 0.15
            reasons.append(f"MACD bullish (hist={macd_hist:.4f})")
        elif macd_hist < -self.MACD_BULLISH_THRESHOLD:
            score -= 0.15
            reasons.append(f"MACD bearish (hist={macd_hist:.4f})")

        # Bollinger Band position
        bb_lower = indicators.get("bb_lower", 0)
        bb_upper = indicators.get("bb_upper", 0)
        if bb_lower and bb_upper:
            mid = (bb_upper + bb_lower) / 2
            if mid > 0:
                # Price proximity to bands (approximate)
                sma = indicators.get("sma_20") or indicators.get("bb_middle", mid)
                if sma:
                    range_pct = (bb_upper - bb_lower) / mid
                    if range_pct < self.BB_LOWER_TOUCH:
                        score += 0.1
                        reasons.append("Near lower Bollinger Band")

        # SMA alignment
        sma_20 = indicators.get("sma_20")
        sma_50 = indicators.get("sma_50")
        sma_200 = indicators.get("sma_200")
        if sma_20 and sma_50 and sma_200:
            if sma_20 > sma_50 > sma_200:
                score += 0.2
                reasons.append("Golden alignment (SMA20>50>200)")
            elif sma_20 < sma_50 < sma_200:
                score -= 0.2
                reasons.append("Death alignment (SMA20<50<200)")

        # Determine signal
        confidence = min(abs(score), 1.0)
        if confidence < self.MIN_CONFIDENCE:
            signal_type = "HOLD"
        elif score > 0:
            signal_type = "BUY"
        else:
            signal_type = "SELL"

        return SignalResult(
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            metadata={
                "reasons": reasons,
                "score": score,
                "indicators_used": ["rsi_14", "macd_histogram", "bb_position", "sma_alignment"],
            },
        )

    def generate_from_research(
        self, symbol: str, indicators: dict, research_results: list[dict]
    ) -> SignalResult:
        """Generate a signal combining indicators and research agent outputs."""
        base_signal = self.generate_from_indicators(symbol, indicators)

        # Boost or reduce confidence based on research consensus
        research_score = 0.0
        research_count = 0
        for result in research_results:
            content = result.get("content", "").lower()
            confidence = result.get("confidence", 0.5)
            research_count += 1

            # Simple sentiment extraction from research content
            bullish_keywords = ["bullish", "buy", "growth", "undervalued", "strong", "upgrade"]
            bearish_keywords = ["bearish", "sell", "overvalued", "weak", "downgrade", "risk"]

            bullish_count = sum(1 for kw in bullish_keywords if kw in content)
            bearish_count = sum(1 for kw in bearish_keywords if kw in content)

            if bullish_count > bearish_count:
                research_score += confidence * 0.1
            elif bearish_count > bullish_count:
                research_score -= confidence * 0.1

        if research_count > 0:
            avg_research = research_score / research_count
            base_signal.confidence = min(abs(base_signal.confidence + avg_research), 1.0)
            base_signal.metadata["research_consensus"] = research_score
            base_signal.metadata["research_count"] = research_count

            # Re-evaluate signal type
            total_score = base_signal.metadata.get("score", 0) + avg_research
            if base_signal.confidence < self.MIN_CONFIDENCE:
                base_signal.signal_type = "HOLD"
            elif total_score > 0:
                base_signal.signal_type = "BUY"
            else:
                base_signal.signal_type = "SELL"

        return base_signal
