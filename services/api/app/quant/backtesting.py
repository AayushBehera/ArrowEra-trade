"""Backtesting engine for strategy evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable

import numpy as np
import pandas as pd


@dataclass
class Trade:
    entry_date: str
    exit_date: str
    direction: str  # "long" or "short"
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    pnl_percent: float


@dataclass
class BacktestResult:
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_percent: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_percent: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "initialCapital": self.initial_capital,
            "finalCapital": round(self.final_capital, 2),
            "totalReturn": round(self.total_return, 2),
            "totalReturnPercent": round(self.total_return_percent, 2),
            "sharpeRatio": round(self.sharpe_ratio, 4),
            "maxDrawdown": round(self.max_drawdown, 2),
            "maxDrawdownPercent": round(self.max_drawdown_percent, 2),
            "winRate": round(self.win_rate, 4),
            "totalTrades": self.total_trades,
            "winningTrades": self.winning_trades,
            "losingTrades": self.losing_trades,
            "avgWin": round(self.avg_win, 2),
            "avgLoss": round(self.avg_loss, 2),
            "profitFactor": round(self.profit_factor, 4),
            "trades": [
                {
                    "entryDate": t.entry_date,
                    "exitDate": t.exit_date,
                    "direction": t.direction,
                    "entryPrice": round(t.entry_price, 4),
                    "exitPrice": round(t.exit_price, 4),
                    "quantity": t.quantity,
                    "pnl": round(t.pnl, 2),
                    "pnlPercent": round(t.pnl_percent, 2),
                }
                for t in self.trades
            ],
        }


# Type alias for strategy functions
# Strategy receives a DataFrame and returns "buy", "sell", or "hold"
StrategyFn = Callable[[pd.DataFrame], str]


class BacktestEngine:
    """Event-driven backtesting engine."""

    def __init__(
        self,
        initial_capital: float = 100_000.0,
        commission: float = 0.001,
        position_size: float = 1.0,
    ) -> None:
        self.initial_capital = initial_capital
        self.commission = commission
        self.position_size = position_size

    def run(self, data: list[dict[str, Any]], strategy: StrategyFn) -> BacktestResult:
        df = pd.DataFrame(data)
        for col in ("open", "high", "low", "close", "volume"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        capital = self.initial_capital
        position = 0.0
        entry_price = 0.0
        trades: list[Trade] = []
        equity: list[float] = [capital]

        for i in range(1, len(df)):
            window = df.iloc[: i + 1]
            signal = strategy(window)
            price = float(df.iloc[i]["close"])
            date = str(df.iloc[i].get("timestamp", i))

            if signal == "buy" and position == 0:
                qty = (capital * self.position_size) / price
                cost = qty * price * (1 + self.commission)
                capital -= cost
                position = qty
                entry_price = price

            elif signal == "sell" and position > 0:
                proceeds = position * price * (1 - self.commission)
                pnl = proceeds - (position * entry_price * (1 + self.commission))
                pnl_pct = (price / entry_price - 1) * 100 if entry_price else 0
                capital += proceeds
                trades.append(Trade(
                    entry_date=str(df.iloc[max(0, i - 5)].get("timestamp", "")),
                    exit_date=date,
                    direction="long",
                    entry_price=entry_price,
                    exit_price=price,
                    quantity=position,
                    pnl=pnl,
                    pnl_percent=pnl_pct,
                ))
                position = 0.0
                entry_price = 0.0

            equity.append(capital + position * price)

        final_capital = capital + position * float(df.iloc[-1]["close"]) if len(df) > 0 else capital
        total_return = final_capital - self.initial_capital
        total_return_pct = (total_return / self.initial_capital * 100) if self.initial_capital else 0

        # Compute metrics
        equity_arr = np.array(equity)
        returns = np.diff(equity_arr) / equity_arr[:-1]
        sharpe = float(np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252))

        peak = np.maximum.accumulate(equity_arr)
        drawdown = (peak - equity_arr) / (peak + 1e-10)
        max_dd = float(np.max(drawdown)) * 100
        max_dd_val = float(np.max(peak - equity_arr))

        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        win_rate = len(wins) / len(trades) if trades else 0
        avg_win = np.mean([t.pnl for t in wins]) if wins else 0
        avg_loss = np.mean([t.pnl for t in losses]) if losses else 0
        gross_profit = sum(t.pnl for t in wins) if wins else 0
        gross_loss = abs(sum(t.pnl for t in losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        return BacktestResult(
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_percent=total_return_pct,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd_val,
            max_drawdown_percent=max_dd,
            win_rate=win_rate,
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            avg_win=float(avg_win),
            avg_loss=float(avg_loss),
            profit_factor=profit_factor,
            trades=trades,
            equity_curve=equity,
        )


def sma_crossover_strategy(fast: int = 10, slow: int = 30) -> StrategyFn:
    """Factory for a simple SMA crossover strategy."""
    def strategy(df: pd.DataFrame) -> str:
        if len(df) < slow:
            return "hold"
        close = df["close"]
        fast_sma = close.rolling(fast).mean().iloc[-1]
        slow_sma = close.rolling(slow).mean().iloc[-1]
        prev_fast = close.rolling(fast).mean().iloc[-2]
        prev_slow = close.rolling(slow).mean().iloc[-2]
        if prev_fast <= prev_slow and fast_sma > slow_sma:
            return "buy"
        if prev_fast >= prev_slow and fast_sma < slow_sma:
            return "sell"
        return "hold"
    return strategy
