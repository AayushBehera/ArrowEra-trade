"""Autonomous research - planner, multi-agent debate, strategy evaluator."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

from ..memory.research_memory import research_memory

logger = structlog.get_logger()


@dataclass
class ResearchPlan:
    """A structured research plan with sub-tasks."""
    id: str = field(default_factory=lambda: str(uuid4()))
    question: str = ""
    sub_tasks: list[dict[str, str]] = field(default_factory=list)
    status: str = "planned"
    results: list[dict] = field(default_factory=list)
    final_report: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class ResearchPlanner:
    """Breaks complex research questions into sub-tasks."""

    async def create_plan(self, question: str, runtime) -> ResearchPlan:
        """Create a research plan by decomposing the question."""
        plan_prompt = (
            f"Break down this research question into 3-5 specific sub-tasks:\n\n"
            f"Question: {question}\n\n"
            f"Return as a numbered list. Each sub-task should be specific and actionable."
        )
        result = await runtime.complete(
            system_prompt="You are a research planning specialist. Break complex questions into actionable sub-tasks.",
            prompt=plan_prompt,
        )
        plan = ResearchPlan(question=question)
        # Parse sub-tasks from the response
        lines = result.content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                clean = line.lstrip("0123456789.-) ")
                if clean:
                    plan.sub_tasks.append({"task": clean, "status": "pending"})
        if not plan.sub_tasks:
            plan.sub_tasks = [{"task": question, "status": "pending"}]
        return plan


class MultiAgentDebate:
    """Runs a multi-agent debate where agents present conflicting views."""

    async def debate(self, topic: str, runtime, num_agents: int = 3) -> dict:
        """Run a structured debate with multiple agent perspectives."""
        perspectives = ["bullish", "bearish", "neutral"]
        tasks = []
        for i in range(min(num_agents, len(perspectives))):
            prompt = (
                f"Analyze the following from a {perspectives[i]} perspective:\n\n"
                f"Topic: {topic}\n\n"
                f"Present 3 key arguments supporting your {perspectives[i]} view. "
                f"Be specific with data points and reasoning."
            )
            tasks.append(
                runtime.complete(
                    system_prompt=f"You are a {perspectives[i]} market analyst. Present strong arguments for your view.",
                    prompt=prompt,
                )
            )
        results = await asyncio.gather(*tasks, return_exceptions=True)
        debate_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                debate_results.append({"perspective": perspectives[i], "error": str(result)})
            else:
                debate_results.append({
                    "perspective": perspectives[i],
                    "content": result.content,
                    "provider": result.provider,
                })
        return {"topic": topic, "debates": debate_results}


class StrategyEvaluator:
    """Evaluates strategies using backtest + risk analysis + agent review."""

    async def evaluate(self, strategy_name: str, symbol: str, runtime) -> dict:
        """Run comprehensive strategy evaluation."""
        eval_prompt = (
            f"Evaluate the following trading strategy concept:\n\n"
            f"Strategy: {strategy_name}\n"
            f"Symbol: {symbol}\n\n"
            f"Provide:\n"
            f"1. Strategy strengths (3 points)\n"
            f"2. Strategy weaknesses (3 points)\n"
            f"3. Risk factors to consider\n"
            f"4. Suggested improvements\n"
            f"5. Overall rating (1-10) with justification"
        )
        result = await runtime.complete(
            system_prompt="You are a quantitative strategy evaluator. Be thorough and critical.",
            prompt=eval_prompt,
        )
        return {
            "strategy": strategy_name,
            "symbol": symbol,
            "evaluation": result.content,
            "provider": result.provider,
        }


class AutonomousResearch:
    """Orchestrates autonomous research with planning, debate, and evaluation."""

    def __init__(self, runtime):
        self.runtime = runtime
        self.planner = ResearchPlanner()
        self.debate = MultiAgentDebate()
        self.evaluator = StrategyEvaluator()
        self._runs: dict[str, ResearchPlan] = {}

    async def run_research(self, question: str, symbol: str = "") -> dict:
        """Run full autonomous research pipeline."""
        run_id = str(uuid4())
        logger.info("autonomous_research_start", run_id=run_id, question=question[:100])

        # Step 1: Plan
        plan = await self.planner.create_plan(question, self.runtime)
        plan.status = "running"
        self._runs[run_id] = plan

        # Step 2: Execute sub-tasks
        for i, sub_task in enumerate(plan.sub_tasks):
            try:
                result = await self.runtime.complete(
                    system_prompt="You are a research analyst. Be thorough and data-driven.",
                    prompt=f"Research task: {sub_task['task']}\n\nContext: {question}" + (f"\nSymbol: {symbol}" if symbol else ""),
                )
                plan.results.append({
                    "task": sub_task["task"],
                    "content": result.content,
                    "provider": result.provider,
                })
                plan.sub_tasks[i]["status"] = "completed"
            except Exception as exc:
                plan.results.append({"task": sub_task["task"], "error": str(exc)})
                plan.sub_tasks[i]["status"] = "failed"

        # Step 3: Synthesis
        synthesis_parts = [f"Question: {question}\n"]
        for r in plan.results:
            if "content" in r:
                synthesis_parts.append(f"## {r['task']}\n{r['content']}")
        synthesis_prompt = (
            "Synthesize the following research findings into a comprehensive report.\n\n"
            + "\n\n---\n\n".join(synthesis_parts)
            + "\n\nProvide: Executive Summary, Key Findings, Recommendations, Risk Factors."
        )
        try:
            synthesis = await self.runtime.complete(
                system_prompt="You are a senior research analyst writing a comprehensive report.",
                prompt=synthesis_prompt,
            )
            plan.final_report = synthesis.content
        except Exception as exc:
            plan.final_report = f"Synthesis failed: {exc}"

        plan.status = "completed"

        # Index in research memory for future retrieval
        await research_memory.index_report({
            "synthesis": plan.final_report,
            "symbol": symbol,
            "report_type": "autonomous",
            "question": question,
        })

        return {
            "run_id": run_id,
            "question": question,
            "sub_tasks": plan.sub_tasks,
            "results_count": len(plan.results),
            "report": plan.final_report,
            "status": plan.status,
        }

    async def run_debate(self, topic: str) -> dict:
        """Run a multi-agent debate on a topic."""
        return await self.debate.debate(topic, self.runtime)

    async def evaluate_strategy(self, strategy_name: str, symbol: str) -> dict:
        """Evaluate a trading strategy."""
        return await self.evaluator.evaluate(strategy_name, symbol, self.runtime)

    def get_run(self, run_id: str) -> dict | None:
        """Get status of a research run."""
        plan = self._runs.get(run_id)
        if not plan:
            return None
        return {
            "run_id": plan.id,
            "question": plan.question,
            "status": plan.status,
            "sub_tasks": plan.sub_tasks,
            "results_count": len(plan.results),
            "report": plan.final_report,
            "created_at": plan.created_at.isoformat(),
        }
