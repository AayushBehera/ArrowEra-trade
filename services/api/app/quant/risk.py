"""Portfolio risk analytics."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def value_at_risk(returns: list[float], confidence: float = 0.95, method: str = "historical") -> float:
    """Calculate Value at Risk."""
    arr = np.array(returns)
    if method == "parametric":
        z = 1.645 if confidence == 0.95 else 2.326
        return float(-(np.mean(arr) - z * np.std(arr)))
    return float(-np.percentile(arr, (1 - confidence) * 100))


def beta(portfolio_returns: list[float], benchmark_returns: list[float]) -> float:
    """Calculate portfolio beta relative to benchmark."""
    p = np.array(portfolio_returns)
    b = np.array(benchmark_returns)
    if len(p) < 2 or len(b) < 2:
        return 0.0
    covariance = np.cov(p, b)[0][1]
    variance = np.var(b)
    return float(covariance / variance) if variance > 0 else 0.0


def alpha(portfolio_return: float, risk_free_rate: float, benchmark_return: float, portfolio_beta: float) -> float:
    """Jensen's Alpha."""
    return portfolio_return - (risk_free_rate + portfolio_beta * (benchmark_return - risk_free_rate))


def sortino_ratio(returns: list[float], risk_free: float = 0.0) -> float:
    """Sortino ratio using downside deviation."""
    arr = np.array(returns) - risk_free
    downside = arr[arr < 0]
    if len(downside) == 0:
        return float("inf")
    downside_dev = np.std(downside)
    return float(np.mean(arr) / downside_dev * np.sqrt(252)) if downside_dev > 0 else 0.0


def information_ratio(portfolio_returns: list[float], benchmark_returns: list[float]) -> float:
    """Information ratio."""
    p = np.array(portfolio_returns)
    b = np.array(benchmark_returns)
    active = p - b
    tracking_error = np.std(active)
    if tracking_error == 0:
        return 0.0
    return float(np.mean(active) / tracking_error * np.sqrt(252))


def max_drawdown(equity_curve: list[float]) -> tuple[float, float]:
    """Returns (max_drawdown_value, max_drawdown_percent)."""
    arr = np.array(equity_curve)
    peak = np.maximum.accumulate(arr)
    dd = peak - arr
    max_dd = float(np.max(dd))
    max_dd_pct = float(np.max(dd / (peak + 1e-10)) * 100)
    return max_dd, max_dd_pct


def correlation_matrix(returns_dict: dict[str, list[float]]) -> dict[str, dict[str, float]]:
    """Compute correlation matrix from multiple return series."""
    df = pd.DataFrame(returns_dict)
    corr = df.corr()
    return {col: {row: round(float(corr.loc[row, col]), 4) for row in corr.index} for col in corr.columns}


def portfolio_risk_summary(
    returns: list[float],
    benchmark_returns: list[float] | None = None,
    risk_free_rate: float = 0.04,
) -> dict[str, Any]:
    """Comprehensive risk summary for a portfolio."""
    arr = np.array(returns)
    annualized_return = float(np.mean(arr) * 252)
    annualized_vol = float(np.std(arr) * np.sqrt(252))
    sharpe = (annualized_return - risk_free_rate) / annualized_vol if annualized_vol > 0 else 0

    result: dict[str, Any] = {
        "annualizedReturn": round(annualized_return * 100, 2),
        "annualizedVolatility": round(annualized_vol * 100, 2),
        "sharpeRatio": round(sharpe, 4),
        "sortinoRatio": round(sortino_ratio(returns, risk_free_rate / 252), 4),
        "var95": round(value_at_risk(returns, 0.95) * 100, 2),
        "var99": round(value_at_risk(returns, 0.99) * 100, 2),
    }

    if benchmark_returns:
        b = beta(returns, benchmark_returns)
        bench_return = float(np.mean(benchmark_returns) * 252)
        result["beta"] = round(b, 4)
        result["alpha"] = round(alpha(annualized_return, risk_free_rate, bench_return, b) * 100, 2)
        result["informationRatio"] = round(information_ratio(returns, benchmark_returns), 4)

    return result
