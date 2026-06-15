"""AI Trading Copilot - multi-turn conversational assistant with tool calling."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

logger = structlog.get_logger()


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)
    result: Any = None


@dataclass
class ChatTurn:
    role: str  # user, assistant, system, tool
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class CopilotTools:
    """Available tools for the copilot to call."""

    @staticmethod
    async def fetch_quote(symbol: str) -> dict:
        from ..market_data.service import market_data_service
        try:
            return await market_data_service.get_quote(symbol.upper())
        except Exception as exc:
            return {"error": str(exc), "symbol": symbol}

    @staticmethod
    async def run_analysis(symbol: str, question: str = "") -> dict:
        from ..research.agents import AGENT_REGISTRY
        from ..config import settings
        from services.agents.arrowera_agents.runtime import AgentRuntime
        runtime = AgentRuntime.from_settings(settings)
        agent_cls = AGENT_REGISTRY.get("market")
        if not agent_cls:
            return {"error": "Market analyst not available"}
        agent = agent_cls(runtime)
        result = await agent.analyze({"symbol": symbol, "question": question})
        return result

    @staticmethod
    async def compute_indicators(symbol: str, days: int = 365) -> dict:
        from ..market_data.service import market_data_service
        from ..quant.indicators import compute_all_indicators
        from datetime import timedelta
        end = datetime.now()
        start = end - timedelta(days=days)
        try:
            data = await market_data_service.get_historical(symbol.upper(), start, end)
            return compute_all_indicators(data)
        except Exception as exc:
            return {"error": str(exc)}

    @staticmethod
    def generate_chart_config(symbol: str, chart_type: str = "candlestick") -> dict:
        return {
            "type": chart_type,
            "symbol": symbol.upper(),
            "timeframe": "1d",
            "indicators": ["sma_20", "sma_50", "volume"],
        }


TOOL_REGISTRY: dict[str, Any] = {
    "fetch_quote": CopilotTools.fetch_quote,
    "run_analysis": CopilotTools.run_analysis,
    "compute_indicators": CopilotTools.compute_indicators,
    "generate_chart": CopilotTools.generate_chart_config,
}

SYSTEM_PROMPT = (
    "You are ArrowEra Trade Copilot, an AI trading assistant.\n"
    "Help users with market analysis, portfolio questions, strategy ideas, "
    "and trading education.\n\n"
    "Available tools: fetch_quote(symbol), run_analysis(symbol, question), "
    "compute_indicators(symbol), generate_chart(symbol, chart_type).\n\n"
    "Be concise and data-driven. Never provide guaranteed financial advice. "
    "Always state when analysis is speculative. "
    "Use tools when the user asks for real-time data or analysis."
)


class CopilotSession:
    """Manages a single copilot conversation session."""

    def __init__(self, user_id: str | None = None):
        self.id = str(uuid4())
        self.user_id = user_id
        self.history: list[ChatTurn] = []
        self.created_at = datetime.now(UTC)

    def add_user_message(self, content: str) -> ChatTurn:
        turn = ChatTurn(role="user", content=content)
        self.history.append(turn)
        return turn

    def add_assistant_message(self, content: str, tool_calls: list[ToolCall] | None = None) -> ChatTurn:
        turn = ChatTurn(role="assistant", content=content, tool_calls=tool_calls or [])
        self.history.append(turn)
        return turn

    def get_context_messages(self, max_turns: int = 20) -> list[dict]:
        """Get recent conversation context for the LLM."""
        recent = self.history[-max_turns:]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in recent:
            messages.append({"role": turn.role, "content": turn.content})
        return messages

    async def chat(self, message: str, provider: str | None = None) -> ChatTurn:
        """Process a user message and return the assistant response."""
        self.add_user_message(message)

        # Detect tool calls from user message
        tool_calls = self._detect_tool_calls(message)
        tool_results: list[dict] = []

        for tc in tool_calls:
            func = TOOL_REGISTRY.get(tc.name)
            if func:
                try:
                    if hasattr(func, "__call__"):
                        import inspect
                        if inspect.iscoroutinefunction(func):
                            tc.result = await func(**tc.args)
                        else:
                            tc.result = func(**tc.args)
                    tool_results.append({"tool": tc.name, "result": tc.result})
                except Exception as exc:
                    tc.result = {"error": str(exc)}
                    tool_results.append({"tool": tc.name, "error": str(exc)})

        # Build prompt with tool context
        context_parts = []
        if tool_results:
            context_parts.append("Tool results:\n")
            for tr in tool_results:
                context_parts.append(f"- {tr['tool']}: {tr.get('result', tr.get('error', 'N/A'))}")
            context_parts.append("\nUse these results to answer the user's question.")

        context_msg = "\n".join(context_parts) if context_parts else ""
        full_prompt = f"{message}\n\n{context_msg}".strip() if context_msg else message

        # Get LLM response
        try:
            from services.agents.arrowera_agents.runtime import AgentRuntime
            from ..config import settings
            runtime = AgentRuntime.from_settings(settings)

            # Build conversation context
            history_text = ""
            for turn in self.history[-10:]:
                history_text += f"{turn.role}: {turn.content}\n"

            result = await runtime.complete(
                system_prompt=SYSTEM_PROMPT,
                prompt=f"Conversation history:\n{history_text}\n\nCurrent message: {full_prompt}",
                requested_provider=provider,
            )
            response = self.add_assistant_message(result.content, tool_calls if tool_calls else None)
            return response
        except Exception as exc:
            logger.error("copilot_chat_error", error=str(exc))
            return self.add_assistant_message(f"I encountered an error: {exc}")

    def _detect_tool_calls(self, message: str) -> list[ToolCall]:
        """Simple heuristic tool call detection from user messages."""
        calls: list[ToolCall] = []
        msg_lower = message.lower()

        # Extract symbol patterns (e.g., AAPL, MSFT, $TSLA)
        import re
        symbols = re.findall(r"\$?([A-Z]{2,5})\b", message.upper())
        primary_symbol = symbols[0] if symbols else "SPY"

        if any(kw in msg_lower for kw in ["quote", "price", "how much"]):
            calls.append(ToolCall(name="fetch_quote", args={"symbol": primary_symbol}))

        if any(kw in msg_lower for kw in ["analyze", "analysis", "research", "think about"]):
            calls.append(ToolCall(name="run_analysis", args={"symbol": primary_symbol, "question": message}))

        if any(kw in msg_lower for kw in ["indicator", "rsi", "macd", "moving average", "technical"]):
            calls.append(ToolCall(name="compute_indicators", args={"symbol": primary_symbol}))

        if any(kw in msg_lower for kw in ["chart", "graph", "plot", "candlestick"]):
            calls.append(ToolCall(name="generate_chart", args={"symbol": primary_symbol}))

        return calls
