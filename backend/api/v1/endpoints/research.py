"""
ArrowEra Trade - Research & Agents API Endpoints

FastAPI endpoints for AI research agents and analysis.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
import structlog

from backend.services.research.agents.market_analyst import MarketAnalyst
from backend.services.market_data.service import market_data_service
from backend.services.market_data.base import TimeFrame
from backend.db.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

router = APIRouter()

# --- Pydantic Models ---

class ResearchRequest(BaseModel):
    """Request model for running research analysis."""
    agent_type: str = Field(..., description="Type of agent to run (e.g., 'market_analyst')")
    symbols: List[str] = Field(..., description="List of symbols to analyze")
    start_date: Optional[str] = Field(None, description="Start date for historical context")
    end_date: Optional[str] = Field(None, description="End date for historical context")
    timeframe: TimeFrame = Field(TimeFrame.DAILY, description="Timeframe for data")
    params: Optional[Dict[str, Any]] = Field(None, description="Additional parameters for the agent")

class ResearchResponse(BaseModel):
    """Response model for research results."""
    status: str
    agent: str
    timestamp: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# --- Endpoints ---

@router.post("/analyze", response_model=ResearchResponse)
async def run_analysis(
    request: ResearchRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Run an AI agent analysis.
    
    This endpoint orchestrates the process of fetching market data,
    passing it to the specified agent, and returning the results.
    """
    try:
        # 1. Initialize Agent
        if request.agent_type == "market_analyst":
            agent = MarketAnalyst(config=request.params)
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown agent type: {request.agent_type}"
            )

        # 2. Fetch Market Data
        # Default to last 3 months if no dates provided
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)
        
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date)
        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date)

        market_data = {}
        for symbol in request.symbols:
            try:
                data = await market_data_service.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    timeframe=request.timeframe
                )
                if data:
                    import pandas as pd
                    df = pd.DataFrame(data)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    market_data[symbol] = df
            except Exception as e:
                logger.warning(f"Failed to fetch data for {symbol}", error=str(e))
                continue

        if not market_data:
            raise HTTPException(status_code=404, detail="No market data could be fetched for provided symbols")

        # 3. Prepare Context for Agent
        context = {
            "market_data": market_data,
            "indices": {}, # Could fetch SPY/QQQ here automatically
            "news": []   # Could fetch news here
        }

        # 4. Run Analysis
        results = await agent.analyze(context)

        return ResearchResponse(
            status="success",
            agent=request.agent_type,
            timestamp=datetime.utcnow().isoformat(),
            results=results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Research analysis failed", error=str(e))
        return ResearchResponse(
            status="error",
            agent=request.agent_type,
            timestamp=datetime.utcnow().isoformat(),
            error=str(e)
        )

@router.get("/agents")
async def list_agents():
    """List available research agents."""
    return {
        "status": "success",
        "agents": [
            {
                "id": "market_analyst",
                "name": "Market Analyst",
                "description": "Analyzes broad market trends, sector performance, and macroeconomic indicators.",
                "capabilities": ["trend_analysis", "volatility_analysis", "support_resistance"]
            },
            {
                "id": "technical_analyst",
                "name": "Technical Analyst",
                "description": "Analyzes price action, chart patterns, and technical indicators.",
                "capabilities": ["indicator_analysis", "pattern_recognition", "signal_generation"]
            },
            {
                "id": "fundamental_analyst",
                "name": "Fundamental Analyst",
                "description": "Analyzes financial statements, valuation metrics, and earnings.",
                "capabilities": ["valuation", "earnings_analysis", "financial_health"]
            }
        ]
    }