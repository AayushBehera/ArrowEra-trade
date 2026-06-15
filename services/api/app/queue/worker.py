"""Background task worker - processes tasks from the queue."""

from __future__ import annotations

import asyncio

import structlog

from .publisher import publisher

logger = structlog.get_logger()


class Worker:
    """Background worker that processes tasks from the queue."""

    def __init__(self, concurrency: int = 2):
        self.concurrency = concurrency
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def _process_loop(self) -> None:
        """Main processing loop."""
        while self._running:
            task = await publisher.process_next()
            if task is None:
                await asyncio.sleep(0.5)

    async def start(self) -> None:
        """Start the worker."""
        self._running = True
        # Register default handlers
        publisher.register_handler("research", self._handle_research)
        publisher.register_handler("backtest", self._handle_backtest)
        publisher.register_handler("signal_generation", self._handle_signal_generation)
        # Start processing tasks
        for i in range(self.concurrency):
            t = asyncio.create_task(self._process_loop(), name=f"worker-{i}")
            self._tasks.append(t)
        logger.info("worker_started", concurrency=self.concurrency)

    async def stop(self) -> None:
        """Stop the worker."""
        self._running = False
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()
        logger.info("worker_stopped")

    async def _handle_research(self, payload: dict) -> dict:
        """Handle research task."""
        from ..research.autonomous import AutonomousResearch
        from services.agents.arrowera_agents.runtime import AgentRuntime
        from ..config import settings
        runtime = AgentRuntime.from_settings(settings)
        researcher = AutonomousResearch(runtime)
        return await researcher.run_research(
            question=payload.get("question", ""),
            symbol=payload.get("symbol", ""),
        )

    async def _handle_backtest(self, payload: dict) -> dict:
        """Handle backtest task."""
        from ..market_data.service import market_data_service
        from ..quant.backtesting import BacktestEngine, sma_crossover_strategy
        from datetime import datetime, timedelta
        symbol = payload.get("symbol", "AAPL").upper()
        days = payload.get("days", 365)
        end = datetime.now()
        start = end - timedelta(days=days)
        data = await market_data_service.get_historical(symbol, start, end)
        engine = BacktestEngine(initial_capital=payload.get("initial_capital", 100000.0))
        params = payload.get("params", {})
        strategy = sma_crossover_strategy(fast=params.get("fast", 10), slow=params.get("slow", 30))
        result = engine.run(data, strategy)
        return result.to_dict()

    async def _handle_signal_generation(self, payload: dict) -> dict:
        """Handle signal generation task."""
        from ..market_data.service import market_data_service
        from ..quant.indicators import compute_all_indicators
        from ..signals.engine import SignalEngine
        from datetime import datetime, timedelta
        symbol = payload.get("symbol", "SPY").upper()
        days = payload.get("days", 365)
        end = datetime.now()
        start = end - timedelta(days=days)
        data = await market_data_service.get_historical(symbol, start, end)
        indicators = compute_all_indicators(data)
        engine = SignalEngine()
        result = engine.generate_from_indicators(symbol, indicators)
        return {
            "symbol": result.symbol,
            "signal_type": result.signal_type,
            "confidence": result.confidence,
            "metadata": result.metadata,
        }


# Global worker
worker = Worker()
