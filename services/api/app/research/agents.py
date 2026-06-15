"""Research agent base and specialist implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

from services.agents.arrowera_agents.runtime import AgentRuntime, CompletionResult

logger = structlog.get_logger(__name__)


class ResearchAgent(ABC):
    """Base class for research agents."""

    name: str = "base"
    system_prompt: str = "You are a financial research analyst."

    def __init__(self, runtime: AgentRuntime) -> None:
        self.runtime = runtime

    @abstractmethod
    def build_prompt(self, context: dict[str, Any]) -> str:
        """Build the analysis prompt from context data."""
        ...

    async def analyze(self, context: dict[str, Any], provider: str | None = None) -> dict[str, Any]:
        prompt = self.build_prompt(context)
        try:
            result = await self.runtime.complete(
                system_prompt=self.system_prompt,
                prompt=prompt,
                requested_provider=provider,
            )
            return {
                "agent": self.name,
                "provider": result.provider,
                "model": result.model,
                "content": result.content,
                "duration_ms": result.duration_ms,
                "confidence": 0.7,
            }
        except Exception as exc:
            logger.error("agent_failed", agent=self.name, error=str(exc))
            return {
                "agent": self.name,
                "error": str(exc),
                "content": "Analysis unavailable.",
                "confidence": 0.0,
            }


class MarketAnalyst(ResearchAgent):
    name = "market_analyst"
    system_prompt = (
        "You are a senior market analyst specializing in broad market trends, "
        "sector performance, and macroeconomic indicators. Distinguish observations "
        "from assumptions, state data limitations, and never present analysis as "
        "guaranteed financial advice."
    )

    def build_prompt(self, context: dict[str, Any]) -> str:
        symbols = context.get("symbols", [])
        market_data = context.get("market_data", {})
        timeframe = context.get("timeframe", "daily")
        question = context.get("question", "Provide a market overview.")
        data_summary = "\n".join(
            f"- {sym}: price={d.get('price', 'N/A')}, change={d.get('changePercent', 'N/A')}%"
            for sym, d in market_data.items()
        ) if market_data else "No live data available."
        return (
            f"Analyze the current market conditions for: {', '.join(symbols) or 'major indices'}.\n\n"
            f"Timeframe: {timeframe}\n\n"
            f"Current data:\n{data_summary}\n\n"
            f"Specific question: {question}\n\n"
            "Provide: 1) Market trend assessment, 2) Key support/resistance levels, "
            "3) Sector rotation signals, 4) Risk factors."
        )


class TechnicalAnalyst(ResearchAgent):
    name = "technical_analyst"
    system_prompt = (
        "You are a technical analyst specializing in chart patterns, indicator "
        "analysis, and price action. Use quantitative data to support your conclusions."
    )

    def build_prompt(self, context: dict[str, Any]) -> str:
        symbol = context.get("symbol", "UNKNOWN")
        indicators = context.get("indicators", {})
        question = context.get("question", f"Technical analysis of {symbol}.")
        ind_text = "\n".join(f"- {k}: {v}" for k, v in indicators.items()) if indicators else "No indicator data."
        return (
            f"Perform technical analysis on {symbol}.\n\n"
            f"Current indicators:\n{ind_text}\n\n"
            f"Question: {question}\n\n"
            "Provide: 1) Trend direction, 2) Key indicator signals, "
            "3) Chart pattern identification, 4) Entry/exit levels."
        )


class FundamentalAnalyst(ResearchAgent):
    name = "fundamental_analyst"
    system_prompt = (
        "You are a fundamental analyst specializing in financial statements, "
        "valuation metrics, earnings analysis, and competitive positioning."
    )

    def build_prompt(self, context: dict[str, Any]) -> str:
        symbol = context.get("symbol", "UNKNOWN")
        financials = context.get("financials", {})
        question = context.get("question", f"Fundamental analysis of {symbol}.")
        fin_text = "\n".join(f"- {k}: {v}" for k, v in financials.items()) if financials else "No financial data available."
        return (
            f"Analyze the fundamentals of {symbol}.\n\n"
            f"Financial data:\n{fin_text}\n\n"
            f"Question: {question}\n\n"
            "Provide: 1) Valuation assessment, 2) Earnings quality, "
            "3) Balance sheet health, 4) Competitive moat."
        )


class MacroAnalyst(ResearchAgent):
    name = "macro_analyst"
    system_prompt = (
        "You are a macroeconomic analyst specializing in economic indicators, "
        "interest rate analysis, geopolitical events, and their market impact."
    )

    def build_prompt(self, context: dict[str, Any]) -> str:
        region = context.get("region", "US")
        question = context.get("question", "Provide macroeconomic outlook.")
        indicators = context.get("economic_indicators", {})
        ind_text = "\n".join(f"- {k}: {v}" for k, v in indicators.items()) if indicators else "No indicator data."
        return (
            f"Analyze the macroeconomic environment for {region}.\n\n"
            f"Economic indicators:\n{ind_text}\n\n"
            f"Question: {question}\n\n"
            "Provide: 1) Economic cycle position, 2) Interest rate outlook, "
            "3) Sector implications, 4) Geopolitical risks."
        )


class SentimentAnalyst(ResearchAgent):
    name = "sentiment_analyst"
    system_prompt = (
        "You are a sentiment analyst specializing in market psychology, news sentiment, "
        "social media signals, and fear/greed indicators."
    )

    def build_prompt(self, context: dict[str, Any]) -> str:
        symbol = context.get("symbol", "UNKNOWN")
        news = context.get("news", [])
        question = context.get("question", f"Sentiment analysis for {symbol}.")
        news_text = "\n".join(f"- {n}" for n in news[:10]) if news else "No news data available."
        return (
            f"Analyze market sentiment for {symbol}.\n\n"
            f"Recent headlines:\n{news_text}\n\n"
            f"Question: {question}\n\n"
            "Provide: 1) Overall sentiment score (bullish/bearish/neutral), "
            "2) Key sentiment drivers, 3) Contrarian signals, 4) Short-term outlook."
        )


# Agent registry
AGENT_REGISTRY: dict[str, type[ResearchAgent]] = {
    "market": MarketAnalyst,
    "technical": TechnicalAnalyst,
    "fundamental": FundamentalAnalyst,
    "macro": MacroAnalyst,
    "sentiment": SentimentAnalyst,
}
