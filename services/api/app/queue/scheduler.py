"""Task scheduler - periodic and cron-like task execution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Callable, Coroutine

import structlog

from .publisher import publisher

logger = structlog.get_logger()


@dataclass
class ScheduledTask:
    """A scheduled periodic task."""
    name: str
    interval_seconds: int
    handler: Callable[..., Coroutine] | None = None
    payload: dict = field(default_factory=dict)
    enabled: bool = True
    last_run: str | None = None


class Scheduler:
    """Simple periodic task scheduler."""

    def __init__(self):
        self._tasks: dict[str, ScheduledTask] = {}
        self._running = False
        self._loop_task: asyncio.Task | None = None

    def register(self, name: str, interval_seconds: int, payload: dict | None = None) -> None:
        """Register a periodic task."""
        self._tasks[name] = ScheduledTask(
            name=name,
            interval_seconds=interval_seconds,
            payload=payload or {},
        )
        logger.info("scheduled_task_registered", name=name, interval=interval_seconds)

    def unregister(self, name: str) -> None:
        self._tasks.pop(name, None)

    async def start(self) -> None:
        """Start the scheduler."""
        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop(), name="scheduler")
        logger.info("scheduler_started", tasks=list(self._tasks.keys()))

    async def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
        logger.info("scheduler_stopped")

    async def _run_loop(self) -> None:
        """Main scheduler loop."""
        counters: dict[str, int] = {name: 0 for name in self._tasks}
        while self._running:
            await asyncio.sleep(1)
            for name, task in self._tasks.items():
                if not task.enabled:
                    continue
                counters[name] += 1
                if counters[name] >= task.interval_seconds:
                    counters[name] = 0
                    try:
                        task_id = await publisher.publish(name, task.payload)
                        from datetime import UTC, datetime
                        task.last_run = datetime.now(UTC).isoformat()
                        logger.info("scheduled_task_triggered", name=name, task_id=task_id)
                    except Exception as exc:
                        logger.error("scheduled_task_error", name=name, error=str(exc))

    def get_tasks(self) -> list[dict]:
        return [
            {"name": t.name, "interval": t.interval_seconds, "enabled": t.enabled, "last_run": t.last_run}
            for t in self._tasks.values()
        ]


# Global scheduler
scheduler = Scheduler()


def setup_default_schedules() -> None:
    """Set up default periodic tasks."""
    scheduler.register("market_data_refresh", interval_seconds=60, payload={"symbols": ["SPY", "QQQ"]})
    scheduler.register("signal_generation", interval_seconds=3600, payload={"symbol": "SPY", "days": 365})
