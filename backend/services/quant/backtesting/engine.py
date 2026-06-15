"""
ArrowEra Trade - Backtesting Engine

Engine for running backtests on trading strategies.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import structlog

from ..indicators.technical import TechnicalIndicators

logger = structlog.get_logger(__name__)

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class Order:
    """Represents a trading order."""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None  # For limit/stop orders
    timestamp: datetime = field(default_factory=datetime.utcnow)
    filled: bool = False
    fill_price: Optional[float] = None
    commission: float = 0.0

@dataclass
class Trade:
    """Represents a filled trade."""
    symbol: str
    side: OrderSide
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    entry_time: datetime = field(default_factory=datetime.utcnow)
    exit_time: Optional[datetime] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    commission: float = 0.0

class Portfolio:
    """Simple portfolio for backtesting."""

    def __init__(self, initial_capital: float, commission_rate: float = 0.001):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.positions: Dict[str, float] = {}  # symbol -> quantity
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict[str, Any]] = []

    def get_total_value(self, prices: Dict[str, float]) -> float:
        """Calculate total portfolio value based on current prices."""
        total = self.cash
        for symbol, qty in self.positions.items():
            if symbol in prices:
                total += qty * prices[symbol]
        return total

    def execute_order(self, order: Order, current_price: float) -> Trade:
        """Execute an order and update portfolio."""
        cost = order.quantity * current_price
        commission = cost * self.commission_rate
        
        if order.side == OrderSide.BUY:
            if self.cash >= (cost + commission):
                self.cash -= (cost + commission)
                self.positions[order.symbol] = self.positions.get(order.symbol, 0) + order.quantity
                trade = Trade(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.quantity,
                    entry_price=current_price,
                    commission=commission
                )
            else:
                logger.warning("Insufficient cash for buy order", order=order)
                raise ValueError("Insufficient cash")
        else: # SELL
            if self.positions.get(order.symbol, 0) >= order.quantity:
                self.cash += (cost - commission)
                self.positions[order.symbol] -= order.quantity
                if self.positions[order.symbol] == 0:
                    del self.positions[order.symbol]
                trade = Trade(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.quantity,
                    entry_price=current_price, # In this simple model, we treat sell as closing a trade immediately
                    commission=commission
                )
            else:
                logger.warning("Insufficient position for sell order", order=order)
                raise ValueError("Insufficient position")
        
        self.trades.append(trade)
        return trade

class BacktestEngine:
    """Core backtesting engine."""

    def __init__(
        self, 
        initial_capital: float = 100000.0, 
        commission_rate: float = 0.001
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.data: Dict[str, pd.DataFrame] = {}
        self.portfolio: Optional[Portfolio] = None
        self.orders: List[Order] = []
        self.results: Dict[str, Any] = {}

    def add_data(self, symbol: str, data: pd.DataFrame) -> None:
        """Add OHLCV data for a symbol."""
        # Ensure data is sorted by time
        data = data.sort_index()
        # Basic validation
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"Missing column {col} in data for {symbol}")
        self.data[symbol] = data

    def run(
        self, 
        strategy: Callable[[pd.DataFrame, datetime], List[Order]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run the backtest.
        
        Args:
            strategy: A function that takes current data snapshot and returns list of orders.
                      Signature: strategy(data_snapshot, current_time) -> List[Order]
        """
        if not self.data:
            raise ValueError("No data added to backtest engine")

        self.portfolio = Portfolio(self.initial_capital, self.commission_rate)
        self.orders = []
        
        # Determine date range
        all_indices = [df.index for df in self.data.values()]
        master_index = all_indices[0].union_many(all_indices[1:])
        
        if start_date:
            master_index = master_index[master_index >= start_date]
        if end_date:
            master_index = master_index[master_index <= end_date]

        logger.info(f"Starting backtest for {len(master_index)} bars")

        # Iterate through time
        for current_time in master_index:
            # 1. Get current prices
            current_prices = {}
            for symbol, df in self.data.items():
                if current_time in df.index:
                    current_prices[symbol] = df.loc[current_time, 'close']

            # 2. Get data snapshot (all data up to current time)
            snapshot = {}
            for symbol, df in self.data.items():
                snapshot[symbol] = df.loc[:current_time]

            # 3. Generate signals/orders
            try:
                new_orders = strategy(snapshot, current_time)
            except Exception as e:
                logger.error(f"Strategy error at {current_time}", error=str(e))
                new_orders = []

            # 4. Execute orders
            for order in new_orders:
                if order.symbol in current_prices:
                    try:
                        trade = self.portfolio.execute_order(order, current_prices[order.symbol])
                        self.orders.append(order)
                    except ValueError as e:
                        logger.warning(f"Order execution failed: {e}")

            # 5. Record equity
            total_value = self.portfolio.get_total_value(current_prices)
            self.portfolio.equity_curve.append({
                'timestamp': current_time,
                'total_value': total_value,
                'cash': self.portfolio.cash,
                'positions': self.portfolio.positions.copy()
            })

        # Calculate results
        self.results = self._calculate_results()
        return self.results

    def _calculate_results(self) -> Dict[str, Any]:
        """Calculate performance metrics."""
        if not self.portfolio or not self.portfolio.equity_curve:
            return {}

        equity_df = pd.DataFrame(self.portfolio.equity_curve)
        equity_df.set_index('timestamp', inplace=True)
        
        final_value = equity_df['total_value'].iloc[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Calculate daily returns
        equity_df['returns'] = equity_df['total_value'].pct_change()
        
        # Sharpe Ratio (assuming 252 trading days)
        returns = equity_df['returns'].dropna()
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std() if returns.std() != 0 else 0
        
        # Max Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        return {
            "initial_capital": self.initial_capital,
            "final_value": final_value,
            "total_return": total_return,
            "total_return_pct": total_return * 100,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown * 100,
            "total_trades": len(self.portfolio.trades),
            "equity_curve": equity_df.to_dict(orient='records')
        }