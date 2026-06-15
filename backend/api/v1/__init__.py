"""
ArrowEra Trade - API v1 Router
"""

from fastapi import APIRouter
from .endpoints import market, backtest, research

api_router = APIRouter()

# Include sub-routers
api_router.include_router(market.router, prefix="/market", tags=["Market Data"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["Backtesting"])
api_router.include_router(research.router, prefix="/research", tags=["Research & Agents"])