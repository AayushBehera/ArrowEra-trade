"""
ArrowEra Trade - Backtesting API Endpoints

FastAPI endpoints for running and managing backtests.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog

from backend.services.quant.backtesting.engine import BacktestEngine, Order, OrderSide, OrderType
from backend.services.market_data.service import market_data_service
from backend.services.market_data.base import TimeFrame
from backend.db.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

router = APIRouter()

# --- Pydantic Models for Request/Response ---

class BacktestRequest(BaseModel):
    """Request model for running a backtest."""
    symbol: str = Field(..., description="Symbol to backtest")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    timeframe: TimeFrame = Field(TimeFrame.DAILY, description="Data timeframe")
    initial_capital: float = Field(100000.0, description="Starting capital")
    commission_rate: float = Field(0.001, description="Commission per trade (e.g., 0.001 = 0.1%)")
    strategy_type: str = Field("simple_ma_crossover", description="Strategy identifier")
    strategy_params: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters")

class BacktestResponse(BaseModel):
    """Response model for backtest results."""
    status: str
    backtest_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

# --- Strategy Implementations ---

def simple_ma_crossover_strategy(
    data_snapshot: Dict[str, pd.DataFrame], 
    current_time: datetime,
    params: Dict[str, Any]
) -> List[Order]:
    """
    Simple Moving Average Crossover Strategy.
    
    Params:
    - fast_period: Fast MA period (default 10)
    - slow_period: Slow MA period (default 30)
    """
    fast_period = params.get("fast_period", 10)
    slow_period = params.get("slow_period", 30)
    
    orders = []
    
    for symbol, df in data_snapshot.items():
        if len(df) < slow_period:
            continue
            
        # Calculate MAs
        df['ma_fast'] = df['close'].rolling(window=fast_period).mean()
        df['ma_slow'] = df['close'].rolling(window=slow_period).mean()
        
        # Get current state
        current_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        
        current_price = current_row['close']
        
        # Check for crossover
        if (prev_row['ma_fast'] <= prev_row['ma_slow']) and (current_row['ma_fast'] > current_row['ma_slow']):
            # Golden Cross -> Buy
            orders.append(Order(
                symbol=symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=10, # Fixed quantity for simplicity
                timestamp=current_time
            ))
        elif (prev_row['ma_fast'] >= prev_row['ma_slow']) and (current_row['ma_fast'] < current_row['ma_slow']):
            # Death Cross -> Sell
            orders.append(Order(
                symbol=symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=10,
                timestamp=current_time
            ))
    
    return orders

# --- Endpoints ---

@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Run a backtest synchronously (for MVP).
    
    In a production system, this would likely be an async task (Celery).
    """
    try:
        # 1. Initialize Engine
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            commission_rate=request.commission_rate
        )

        # 2. Fetch Data
        start = datetime.fromisoformat(request.start_date)
        end = datetime.fromisoformat(request.end_date)
        
        raw_data = await market_data_service.get_historical_data(
            symbol=request.symbol,
            start_date=start,
            end_date=end,
            timeframe=request.timeframe,
            use_cache=True
        )
        
        if not raw_data:
            raise HTTPException(status_code=404, detail="No data found for symbol and date range")

        # 3. Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(raw_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # 4. Add data to engine
        engine.add_data(request.symbol, df)

        # 5. Select Strategy
        strategy_func = simple_ma_crossover_strategy
        params = request.strategy_params or {}

        # 6. Run Backtest
        # We wrap the strategy to inject params
        def strategy_wrapper(snapshot, time):
            return strategy_func(snapshot, time, params)

        results = engine.run(strategy_wrapper, start, end)

        return BacktestResponse(
            status="success",
            results=results,
            message="Backtest completed successfully"
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Backtest execution failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/strategies")
async def list_strategies():
    """List available backtesting strategies."""
    return {
        "status": "success",
        "strategies": [
            {
                "id": "simple_ma_crossover",
                "name": "Simple Moving Average Crossover",
                "description": "Buys when fast MA crosses above slow MA, sells when it crosses below.",
                "params": {
                    "fast_period": {"type": "int", "default": 10, "description": "Fast MA period"},
                    "slow_period": {"type": "int", "default": 30, "description": "Slow MA period"}
                }
            }
        ]
    }