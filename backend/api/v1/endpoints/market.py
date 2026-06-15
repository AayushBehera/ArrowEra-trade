"""
ArrowEra Trade - Market Data API Endpoints

FastAPI endpoints for market data, quotes, and overview.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timedelta
from typing import List, Optional
import structlog

from backend.services.market_data.service import market_data_service
from backend.services.market_data.base import TimeFrame
from backend.db.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

router = APIRouter()

@router.get("/quote/{symbol}")
async def get_quote(
    symbol: str,
    provider: Optional[str] = Query(None, description="Specific data provider")
):
    """
    Get real-time quote for a symbol.
    
    Args:
        symbol: Asset symbol (e.g., AAPL)
        provider: Optional provider override (e.g., 'yfinance')
    """
    try:
        quote = await market_data_service.get_realtime_quote(symbol, provider)
        return {
            "status": "success",
            "data": quote
        }
    except Exception as e:
        logger.error("Failed to fetch quote", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{symbol}")
async def get_historical_data(
    symbol: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    timeframe: TimeFrame = Query(TimeFrame.DAILY, description="Timeframe"),
    provider: Optional[str] = Query(None, description="Specific data provider")
):
    """
    Get historical OHLCV data for a symbol.
    
    Args:
        symbol: Asset symbol
        start_date: Start date string
        end_date: End date string
        timeframe: Data timeframe
        provider: Optional provider override
    """
    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        data = await market_data_service.get_historical_data(
            symbol, start, end, timeframe, provider
        )
        
        return {
            "status": "success",
            "symbol": symbol,
            "timeframe": timeframe.value,
            "count": len(data),
            "data": data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error("Failed to fetch historical data", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overview")
async def get_market_overview(
    symbols: str = Query(..., description="Comma-separated list of symbols")
):
    """
    Get market overview for multiple symbols.
    
    Args:
        symbols: Comma-separated list (e.g., "AAPL,MSFT,GOOGL")
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        overview = await market_data_service.get_market_overview(symbol_list)
        return {
            "status": "success",
            "data": overview
        }
    except Exception as e:
        logger.error("Failed to fetch market overview", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/symbols")
async def get_symbols(
    asset_type: Optional[str] = Query(None, description="Filter by asset type")
):
    """Get list of available symbols."""
    try:
        from backend.services.market_data.base import AssetType
        
        type_filter = None
        if asset_type:
            try:
                type_filter = AssetType(asset_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid asset type: {asset_type}")
        
        symbols = await market_data_service.get_symbols(type_filter)
        return {
            "status": "success",
            "count": len(symbols),
            "data": symbols
        }
    except Exception as e:
        logger.error("Failed to fetch symbols", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))