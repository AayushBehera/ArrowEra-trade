"""LangGraph-based orchestration for multi-agent workflows."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

import structlog

logger = structlog.get_logger()


@dataclass
class WorkflowState:
    """Shared state for workflow execution."""
    workflow_id: str = field(default_factory=lambda: str(uuid4()))
    symbol: str = ""
    question: str = ""
    context: dict = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    status: str = "pending"
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "symbol": self.symbol,
            "question": self.question,
            "results": self.results,
            "errors": self.errors,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AgentNode:
    """A node in the workflow graph that runs a specific agent."""

    def __init__(self, name: str, agent_type: str, system_prompt: str = ""):
        self.name = name
        self.agent_type = agent_type
        self.system_prompt = system_prompt

    async def execute(self, state: WorkflowState, runtime) -> WorkflowState:
        """Execute this agent node."""
        logger.info("node_execute", node=self.name, agent_type=self.agent_type)
        try:
            from ..research.agents import AGENT_REGISTRY
            agent_cls = AGENT_REGISTRY.get(self.agent_type)
            if not agent_cls:
                state.errors.append(f"Agent type '{self.agent_type}' not found")
                return state

            agent = agent_cls(runtime)
            context = {
                "symbol": state.symbol,
                "question": state.question,
                **state.context,
                **state.results,  # Pass previous results as context
            }
            result = await agent.analyze(context)
            state.results[self.name] = result
        except Exception as exc:
            logger.error("node_error", node=self.name, error=str(exc))
            state.errors.append(f"{self.name}: {str(exc)}")
            state.results[self.name] = {"error": str(exc)}
        return state


class SynthesisNode:
    """A node that synthesizes results from multiple agents."""

    def __init__(self, name: str = "synthesis"):
        self.name = name

    async def execute(self, state: WorkflowState, runtime) -> WorkflowState:
        """Synthesize all agent results."""
        logger.info("synthesis_execute", results_count=len(state.results))
        try:
            # Build synthesis prompt from all results
            parts = []
            for name, result in state.results.items():
                if isinstance(result, dict) and "content" in result:
                    parts.append(f"## {name}\n{result['content']}")

            synthesis_prompt = (
                "You are a senior investment analyst. Synthesize the following research "
                "analyses into a concise, actionable investment thesis.\n\n"
                "Focus on: key findings, areas of agreement/disagreement, risk factors, "
                "and a clear BUY/SELL/HOLD recommendation with confidence level.\n\n"
                + "\n\n---\n\n".join(parts)
            )

            result = await runtime.complete(
                system_prompt="You are a senior investment research analyst synthesizing multiple research reports.",
                prompt=synthesis_prompt,
            )
            state.results[self.name] = {
                "content": result.content,
                "provider": result.provider,
                "model": result.model,
            }
        except Exception as exc:
            logger.error("synthesis_error", error=str(exc))
            state.errors.append(f"synthesis: {str(exc)}")
        return state


class RiskReviewNode:
    """A node that performs risk assessment on the analysis."""

    async def execute(self, state: WorkflowState, runtime) -> WorkflowState:
        """Review risk factors."""
        logger.info("risk_review_execute")
        try:
            context_summary = f"Symbol: {state.symbol}\n"
            if state.results:
                context_summary += f"Analyses completed: {list(state.results.keys())}\n"

            risk_prompt = (
                f"Given the following analysis context for {state.symbol}, "
                "identify the top 3-5 risk factors and provide a risk score (1-10).\n\n"
                f"Context: {context_summary}"
            )
            result = await runtime.complete(
                system_prompt="You are a risk management specialist. Be conservative and thorough.",
                prompt=risk_prompt,
            )
            state.results["risk_review"] = {
                "content": result.content,
                "provider": result.provider,
            }
        except Exception as exc:
            logger.error("risk_review_error", error=str(exc))
            state.errors.append(f"risk_review: {str(exc)}")
        return state


class WorkflowGraph:
    """Orchestrates a multi-agent workflow as a directed graph."""

    def __init__(self, runtime):
        self.runtime = runtime
        self.nodes: list[Any] = []

    def add_node(self, node: Any) -> "WorkflowGraph":
        self.nodes.append(node)
        return self

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute all nodes sequentially (can be parallelized)."""
        state.status = "running"
        for node in self.nodes:
            try:
                state = await node.execute(state, self.runtime)
            except Exception as exc:
                logger.error("workflow_node_failed", node=node.name, error=str(exc))
                state.errors.append(f"Node {node.name} failed: {str(exc)}")

        state.status = "completed" if not state.errors else "completed_with_errors"
        state.completed_at = datetime.now(UTC)
        return state


# Pre-built workflows

def build_research_workflow(runtime) -> WorkflowGraph:
    """Full research report workflow - runs all 5 analysts + synthesis."""
    graph = WorkflowGraph(runtime)
    for agent_type in ["market", "technical", "fundamental", "macro", "sentiment"]:
        graph.add_node(AgentNode(
            name=f"{agent_type}_analyst",
            agent_type=agent_type,
        ))
    graph.add_node(SynthesisNode())
    return graph


def build_trade_decision_workflow(runtime) -> WorkflowGraph:
    """Trade decision workflow - analysis + risk + signal."""
    graph = WorkflowGraph(runtime)
    graph.add_node(AgentNode(name="market_analysis", agent_type="market"))
    graph.add_node(AgentNode(name="technical_analysis", agent_type="technical"))
    graph.add_node(RiskReviewNode())
    return graph


def build_portfolio_review_workflow(runtime) -> WorkflowGraph:
    """Portfolio review workflow."""
    graph = WorkflowGraph(runtime)
    graph.add_node(AgentNode(name="fundamental_review", agent_type="fundamental"))
    graph.add_node(AgentNode(name="macro_context", agent_type="macro"))
    graph.add_node(RiskReviewNode())
    graph.add_node(SynthesisNode())
    return graph


WORKFLOW_REGISTRY = {
    "full_research": build_research_workflow,
    "trade_decision": build_trade_decision_workflow,
    "portfolio_review": build_portfolio_review_workflow,
}
