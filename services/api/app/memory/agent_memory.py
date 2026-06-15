"""Agent memory - per-agent conversation and learning memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

import structlog

from .vector_store import vector_store

logger = structlog.get_logger()


@dataclass
class MemoryEntry:
    """A memory entry for an agent."""
    id: str = field(default_factory=lambda: str(uuid4()))
    agent_name: str = ""
    role: str = "user"  # user | assistant | system
    content: str = ""
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class AgentMemory:
    """Per-agent conversation and learning memory with vector retrieval."""

    def __init__(self, agent_name: str, max_history: int = 50):
        self.agent_name = agent_name
        self.max_history = max_history
        self._history: list[MemoryEntry] = []

    async def add_message(self, role: str, content: str, metadata: dict | None = None) -> str:
        """Add a message to the agent's memory."""
        entry = MemoryEntry(
            agent_name=self.agent_name,
            role=role,
            content=content,
            metadata=metadata or {},
        )
        self._history.append(entry)
        # Trim old history
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
        # Index in vector store for retrieval
        doc_id = await vector_store.add(
            content=content,
            metadata={"agent": self.agent_name, "role": role, "entry_id": entry.id, **(metadata or {})},
        )
        return doc_id

    async def get_history(self, limit: int = 20) -> list[dict]:
        """Get recent conversation history."""
        return [
            {"role": e.role, "content": e.content, "timestamp": e.timestamp.isoformat()}
            for e in self._history[-limit:]
        ]

    async def search_context(self, query: str, top_k: int = 5) -> list[dict]:
        """Search past conversations and indexed knowledge for relevant context."""
        results = await vector_store.search(
            query, top_k=top_k, filter_metadata={"agent": self.agent_name}
        )
        return results

    async def build_context_prompt(self, query: str, top_k: int = 3) -> str:
        """Build a context prompt from relevant past interactions."""
        results = await self.search_context(query, top_k)
        if not results:
            return ""
        parts = ["Relevant context from previous interactions:"]
        for r in results:
            if r["score"] > 0.3:
                parts.append(f"- {r['content'][:200]}")
        return "\n".join(parts)

    def clear(self):
        self._history.clear()
