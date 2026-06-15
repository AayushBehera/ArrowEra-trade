"""Task publisher - enqueue jobs for background processing."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, Coroutine
from uuid import uuid4

import structlog

logger = structlog.get_logger()


@dataclass
class Task:
    """A task to be processed by a worker."""
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending | running | completed | failed
    result: Any = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    retries: int = 0
    max_retries: int = 3


class TaskPublisher:
    """In-process task queue (use NATS/Redis in production)."""

    def __init__(self):
        self._queue: asyncio.Queue[Task] = asyncio.Queue()
        self._tasks: dict[str, Task] = {}
        self._handlers: dict[str, Callable[..., Coroutine]] = {}

    def register_handler(self, task_name: str, handler: Callable[..., Coroutine]) -> None:
        """Register a handler for a task type."""
        self._handlers[task_name] = handler
        logger.info("handler_registered", task_name=task_name)

    async def publish(self, task_name: str, payload: dict[str, Any] | None = None) -> str:
        """Publish a task to the queue."""
        task = Task(name=task_name, payload=payload or {})
        self._tasks[task.id] = task
        await self._queue.put(task)
        logger.info("task_published", task_id=task.id, task_name=task_name)
        return task.id

    async def get_status(self, task_id: str) -> dict | None:
        """Get the status of a task."""
        task = self._tasks.get(task_id)
        if not task:
            return None
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status,
            "result": task.result,
            "error": task.error,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "retries": task.retries,
        }

    async def process_next(self) -> Task | None:
        """Process the next task in the queue."""
        try:
            task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

        handler = self._handlers.get(task.name)
        if not handler:
            task.status = "failed"
            task.error = f"No handler for task: {task.name}"
            task.completed_at = datetime.now(UTC)
            return task

        task.status = "running"
        try:
            result = await handler(task.payload)
            task.status = "completed"
            task.result = result
            task.completed_at = datetime.now(UTC)
            logger.info("task_completed", task_id=task.id, task_name=task.name)
        except Exception as exc:
            task.retries += 1
            if task.retries < task.max_retries:
                task.status = "pending"
                await self._queue.put(task)
                logger.warning("task_retry", task_id=task.id, retries=task.retries)
            else:
                task.status = "failed"
                task.error = str(exc)
                task.completed_at = datetime.now(UTC)
                logger.error("task_failed", task_id=task.id, error=str(exc))
        return task

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()


# Global publisher
publisher = TaskPublisher()


# --- Pre-defined task publishers ---

async def publish_research_job(symbol: str, question: str, provider: str | None = None) -> str:
    return await publisher.publish("research", {"symbol": symbol, "question": question, "provider": provider})


async def publish_backtest_job(symbol: str, strategy: str, params: dict) -> str:
    return await publisher.publish("backtest", {"symbol": symbol, "strategy": strategy, "params": params})


async def publish_signal_generation(symbol: str, days: int = 365) -> str:
    return await publisher.publish("signal_generation", {"symbol": symbol, "days": days})
