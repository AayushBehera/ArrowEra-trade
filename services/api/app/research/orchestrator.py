"""Research orchestrator - runs multiple agents in parallel and merges results."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from services.agents.arrowera_agents.runtime import AgentRuntime

from .agents import AGENT_REGISTRY, ResearchAgent

logger = structlog.get_logger(__name__)


class ResearchOrchestrator:
    """Runs multiple research agents and synthesizes results."""

    def __init__(self, runtime: AgentRuntime) -> None:
        self.runtime = runtime
        self._agents: dict[str, ResearchAgent] = {
            name: cls(runtime) for name, cls in AGENT_REGISTRY.items()
        }

    async def run_single(
        self, agent_type: str, context: dict[str, Any], provider: str | None = None
    ) -> dict[str, Any]:
        agent = self._agents.get(agent_type)
        if not agent:
            return {"error": f"Unknown agent type: {agent_type}. Available: {list(self._agents.keys())}"}
        return await agent.analyze(context, provider)

    async def run_all(
        self, context: dict[str, Any], provider: str | None = None
    ) -> dict[str, Any]:
        tasks = [agent.analyze(context, provider) for agent in self._agents.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        analyses: dict[str, Any] = {}
        for name, result in zip(self._agents.keys(), results):
            if isinstance(result, Exception):
                analyses[name] = {"agent": name, "error": str(result), "content": "", "confidence": 0}
            else:
                analyses[name] = result
        return analyses

    async def generate_report(
        self, context: dict[str, Any], provider: str | None = None
    ) -> dict[str, Any]:
        analyses = await self.run_all(context, provider)
        # Synthesize with a final LLM call
        summary_prompt = "Based on the following analyst reports, provide a unified investment thesis:\n\n"
        for name, analysis in analyses.items():
            content = analysis.get("content", "No analysis available.")
            summary_prompt += f"## {name.title()} Analyst\n{content}\n\n"
        summary_prompt += (
            "Provide: 1) Consensus view, 2) Key disagreements, "
            "3) Overall recommendation (BUY/HOLD/SELL), 4) Risk factors, 5) Confidence level."
        )
        try:
            synthesis = await self.runtime.complete(
                system_prompt="You are a senior portfolio manager synthesizing multiple analyst reports into actionable recommendations.",
                prompt=summary_prompt,
                requested_provider=provider,
            )
            return {
                "analyses": analyses,
                "synthesis": synthesis.content,
                "synthesis_provider": synthesis.provider,
                "synthesis_model": synthesis.model,
                "total_duration_ms": sum(a.get("duration_ms", 0) for a in analyses.values()),
            }
        except Exception as exc:
            logger.error("synthesis_failed", error=str(exc))
            return {
                "analyses": analyses,
                "synthesis": "Synthesis unavailable due to provider error.",
                "total_duration_ms": sum(a.get("duration_ms", 0) for a in analyses.values()),
            }
