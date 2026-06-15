from decimal import Decimal
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from services.agents.arrowera_agents.runtime import AgentRuntime, ProviderUnavailable

from .config import settings
from .db import check_database, session_dependency
from .models import AgentRun, AuditLog, BacktestRun, ContactSubmission, Organization, Portfolio, Position, Signal, User, Watchlist, WorkflowDefinition
from .schemas import (
    AgentRequest,
    AgentResponse,
    AuthLogin,
    AuthRegister,
    AuthToken,
    BacktestRequest,
    ContactCreate,
    ContactCreated,
    DashboardSummary,
    PositionSummary,
    ResearchRequest,
)
from .auth import (
    authenticate_user,
    create_user_token,
    get_current_user,
    hash_password,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@router.get("/health")
async def health() -> dict[str, str]:
    await check_database()
    return {"status": "healthy", "database": "up", "version": settings.version}


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

@router.post("/api/v1/contact", response_model=ContactCreated, status_code=201)
async def create_contact(
    payload: ContactCreate, session: AsyncSession = Depends(session_dependency)
) -> ContactCreated:
    submission = ContactSubmission(**payload.model_dump())
    session.add(submission)
    await session.flush()
    return ContactCreated(id=submission.id, status=submission.status)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get("/api/v1/dashboard", response_model=DashboardSummary)
async def dashboard(session: AsyncSession = Depends(session_dependency)) -> DashboardSummary:
    portfolio = await session.scalar(select(Portfolio).limit(1))
    positions = []
    portfolio_value = Decimal("0")
    cash_balance = Decimal("0")
    if portfolio:
        cash_balance = portfolio.cash_balance
        rows = (await session.scalars(select(Position).where(Position.portfolio_id == portfolio.id))).all()
        for row in rows:
            market_value = row.quantity * row.current_price
            pnl = (row.current_price - row.average_cost) * row.quantity
            portfolio_value += market_value
            positions.append(PositionSummary(
                symbol=row.symbol,
                quantity=format(row.quantity, "f"),
                market_value=f"${market_value:,.2f}",
                pnl=f"${pnl:,.2f}",
            ))
    portfolio_value += cash_balance
    signals = await session.scalar(select(func.count()).select_from(Signal).where(Signal.status == "active"))
    runs = await session.scalar(select(func.count()).select_from(AgentRun))
    return DashboardSummary(
        portfolio_value=f"${portfolio_value:,.2f}",
        cash_balance=f"${cash_balance:,.2f}",
        active_signals=signals or 0,
        agent_runs=runs or 0,
        positions=positions,
    )


# ---------------------------------------------------------------------------
# Market Data
# ---------------------------------------------------------------------------

@router.get("/api/v1/market/quote/{symbol}")
async def get_quote(symbol: str) -> dict:
    from .market_data.service import market_data_service
    try:
        return await market_data_service.get_quote(symbol.upper())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Market data unavailable: {exc}") from exc


@router.get("/api/v1/market/overview")
async def get_market_overview(
    symbols: str = Query(default="AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,SPY,QQQ,IWM"),
) -> dict:
    from .market_data.service import market_data_service
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    try:
        return await market_data_service.get_market_overview(symbol_list)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/api/v1/market/historical/{symbol}")
async def get_historical(
    symbol: str,
    days: int = Query(default=365, ge=1, le=3650),
    timeframe: str = Query(default="1d"),
) -> dict:
    from .market_data.service import market_data_service
    from .market_data.base import TimeFrame
    tf = TimeFrame(timeframe) if timeframe in [t.value for t in TimeFrame] else TimeFrame.DAILY
    end = datetime.now()
    start = end - timedelta(days=days)
    try:
        data = await market_data_service.get_historical(symbol.upper(), start, end, tf)
        return {"symbol": symbol.upper(), "timeframe": tf.value, "bars": len(data), "data": data}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Quant - Indicators & Backtesting
# ---------------------------------------------------------------------------

@router.get("/api/v1/quant/indicators/{symbol}")
async def get_indicators(symbol: str, days: int = Query(default=365, ge=30)) -> dict:
    from .market_data.service import market_data_service
    from .quant.indicators import compute_all_indicators
    end = datetime.now()
    start = end - timedelta(days=days)
    try:
        data = await market_data_service.get_historical(symbol.upper(), start, end)
        return compute_all_indicators(data)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/v1/quant/backtest")
async def run_backtest(
    payload: BacktestRequest,
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    from .market_data.service import market_data_service
    from .quant.backtesting import BacktestEngine, sma_crossover_strategy
    end = datetime.now()
    start = end - timedelta(days=payload.days)
    try:
        data = await market_data_service.get_historical(payload.symbol.upper(), start, end)
        if len(data) < 50:
            raise HTTPException(status_code=400, detail="Insufficient historical data for backtest")
        engine = BacktestEngine(initial_capital=payload.initial_capital)
        strategy = sma_crossover_strategy(
            fast=payload.params.get("fast", 10),
            slow=payload.params.get("slow", 30),
        )
        result = engine.run(data, strategy)
        run = BacktestRun(
            strategy_name=payload.strategy_name,
            symbol=payload.symbol.upper(),
            params=payload.params,
            results=result.to_dict(),
            status="completed",
        )
        session.add(run)
        await session.flush()
        return {"run_id": str(run.id), **result.to_dict()}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Research Agents
# ---------------------------------------------------------------------------

@router.post("/api/v1/research/analyst/{agent_type}")
async def run_analyst(
    agent_type: str,
    payload: ResearchRequest,
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    runtime = AgentRuntime.from_settings(settings)
    from .research.agents import AGENT_REGISTRY
    agent_cls = AGENT_REGISTRY.get(agent_type)
    if not agent_cls:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_type}. Available: {list(AGENT_REGISTRY.keys())}")
    agent = agent_cls(runtime)
    context = {"symbol": payload.symbol, "question": payload.question, **(payload.context or {})}
    result = await agent.analyze(context, payload.provider)
    run = AgentRun(
        agent_name=f"research_{agent_type}",
        provider=result.get("provider", "unknown"),
        model=result.get("model", "unknown"),
        status="completed",
        prompt=payload.question or "research analysis",
        output=result.get("content", ""),
        duration_ms=result.get("duration_ms", 0),
    )
    session.add(run)
    await session.flush()
    return result


@router.post("/api/v1/research/report")
async def generate_research_report(
    payload: ResearchRequest,
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    runtime = AgentRuntime.from_settings(settings)
    from .research.orchestrator import ResearchOrchestrator
    orchestrator = ResearchOrchestrator(runtime)
    context = {
        "symbol": payload.symbol,
        "question": payload.question,
        **(payload.context or {}),
    }
    report = await orchestrator.generate_report(context, payload.provider)
    run = AgentRun(
        agent_name="research_report",
        provider=report.get("synthesis_provider", "unknown"),
        model=report.get("synthesis_model", "unknown"),
        status="completed",
        prompt=payload.question or "full research report",
        output=report.get("synthesis", ""),
        duration_ms=report.get("total_duration_ms", 0),
    )
    session.add(run)
    await session.flush()
    return report


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

@router.get("/api/v1/signals")
async def list_signals(
    status: str = Query(default="active"),
    session: AsyncSession = Depends(session_dependency),
) -> list[dict]:
    rows = await session.scalars(
        select(Signal).where(Signal.status == status).order_by(Signal.created_at.desc()).limit(50)
    )
    return [
        {
            "id": str(s.id),
            "symbol": s.symbol,
            "signalType": s.signal_type,
            "confidence": str(s.confidence),
            "status": s.status,
            "metadata": s.signal_metadata,
            "createdAt": s.created_at.isoformat(),
        }
        for s in rows
    ]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@router.post("/api/v1/auth/register", response_model=AuthToken, status_code=201)
async def register(
    payload: AuthRegister,
    session: AsyncSession = Depends(session_dependency),
) -> AuthToken:
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
        role="member",
    )
    session.add(user)
    await session.flush()
    return AuthToken(**create_user_token(user))


@router.post("/api/v1/auth/login", response_model=AuthToken)
async def login(
    payload: AuthLogin,
    session: AsyncSession = Depends(session_dependency),
) -> AuthToken:
    user = await authenticate_user(payload.email, payload.password, session)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return AuthToken(**create_user_token(user))


@router.get("/api/v1/auth/me")
async def get_me(user: User = Depends(get_current_user)) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "org_id": str(user.org_id) if user.org_id else None,
        "is_active": user.is_active,
    }


# ---------------------------------------------------------------------------
# Watchlist
# ---------------------------------------------------------------------------

@router.get("/api/v1/watchlists")
async def list_watchlists(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(session_dependency),
) -> list[dict]:
    rows = await session.scalars(select(Watchlist).where(Watchlist.user_id == user.id))
    return [{"id": str(w.id), "name": w.name, "symbols": w.symbols} for w in rows]


@router.post("/api/v1/watchlists")
async def create_watchlist(
    payload: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    wl = Watchlist(user_id=user.id, name=payload.get("name", "Default"), symbols=payload.get("symbols", []))
    session.add(wl)
    await session.flush()
    return {"id": str(wl.id), "name": wl.name, "symbols": wl.symbols}


# ---------------------------------------------------------------------------
# Signal Generation
# ---------------------------------------------------------------------------

@router.post("/api/v1/signals/generate")
async def generate_signal(
    payload: dict,
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    from .market_data.service import market_data_service
    from .quant.indicators import compute_all_indicators
    from .signals.engine import SignalEngine
    symbol = payload.get("symbol", "SPY").upper()
    end = datetime.now()
    start = end - timedelta(days=payload.get("days", 365))
    try:
        data = await market_data_service.get_historical(symbol, start, end)
        indicators = compute_all_indicators(data)
        engine = SignalEngine()
        result = engine.generate_from_indicators(symbol, indicators)
        sig = Signal(
            symbol=result.symbol,
            signal_type=result.signal_type,
            confidence=Decimal(str(result.confidence)),
            signal_metadata=result.metadata,
            status="active",
        )
        session.add(sig)
        await session.flush()
        return {
            "id": str(sig.id),
            "symbol": sig.symbol,
            "signalType": sig.signal_type,
            "confidence": str(sig.confidence),
            "status": sig.status,
            "metadata": sig.signal_metadata,
            "createdAt": sig.created_at.isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Copilot
# ---------------------------------------------------------------------------

@router.post("/api/v1/copilot/chat")
async def copilot_chat(payload: dict) -> dict:
    from .copilot.session import CopilotSession
    message = payload.get("message", "")
    provider = payload.get("provider")
    session_id = payload.get("session_id")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")
    # Simple session management (in production, use Redis or DB)
    copilot = CopilotSession()
    response = await copilot.chat(message, provider=provider)
    return {
        "session_id": copilot.id,
        "content": response.content,
        "tool_calls": [
            {"name": tc.name, "args": tc.args, "result": tc.result}
            for tc in response.tool_calls
        ],
    }


# ---------------------------------------------------------------------------
# Workflows (Orchestration)
# ---------------------------------------------------------------------------

@router.post("/api/v1/workflows/execute")
async def execute_workflow(
    payload: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    from .orchestration.graph import WORKFLOW_REGISTRY, WorkflowState
    workflow_name = payload.get("workflow", "full_research")
    builder = WORKFLOW_REGISTRY.get(workflow_name)
    if not builder:
        raise HTTPException(status_code=400, detail=f"Unknown workflow: {workflow_name}. Available: {list(WORKFLOW_REGISTRY.keys())}")
    runtime = AgentRuntime.from_settings(settings)
    graph = builder(runtime)
    state = WorkflowState(
        symbol=payload.get("symbol", "SPY"),
        question=payload.get("question", ""),
        context=payload.get("context", {}),
    )
    result = await graph.execute(state)
    # Persist workflow run as agent run
    run = AgentRun(
        agent_name=f"workflow_{workflow_name}",
        provider="orchestrator",
        model="multi-agent",
        status=result.status,
        prompt=f"Workflow: {workflow_name}, Symbol: {state.symbol}",
        output=str(result.results.get("synthesis", {}).get("content", ""))[:10000],
        duration_ms=int((result.completed_at - result.started_at).total_seconds() * 1000) if result.completed_at else 0,
    )
    session.add(run)
    await session.flush()
    return {"run_id": str(run.id), **result.to_dict()}


@router.get("/api/v1/workflows/status/{run_id}")
async def workflow_status(
    run_id: str,
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    from uuid import UUID as _UUID
    try:
        uid = _UUID(run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    run = await session.get(AgentRun, uid)
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return {
        "id": str(run.id),
        "agent_name": run.agent_name,
        "status": run.status,
        "output": run.output,
        "duration_ms": run.duration_ms,
        "created_at": run.created_at.isoformat(),
    }


@router.get("/api/v1/workflows")
async def list_workflows() -> dict:
    from .orchestration.graph import WORKFLOW_REGISTRY
    return {
        "workflows": [
            {"id": name, "name": name.replace("_", " ").title()}
            for name in WORKFLOW_REGISTRY
        ]
    }


# ---------------------------------------------------------------------------
# IDE (Strategy Execution)
# ---------------------------------------------------------------------------

@router.post("/api/v1/ide/execute")
async def execute_strategy(
    payload: dict,
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    """Execute strategy code in a sandboxed environment."""
    code = payload.get("code", "")
    symbol = payload.get("symbol", "AAPL").upper()
    days = payload.get("days", 365)
    if not code:
        raise HTTPException(status_code=400, detail="Code is required")
    from .market_data.service import market_data_service
    from .quant.backtesting import BacktestEngine
    end = datetime.now()
    start = end - timedelta(days=days)
    try:
        data = await market_data_service.get_historical(symbol, start, end)
        # Execute strategy code in restricted namespace
        safe_ns: dict = {"__builtins__": {"sum": sum, "len": len, "range": range, "min": min, "max": max, "abs": abs, "round": round, "int": int, "float": float, "print": print}}
        exec(code, safe_ns)  # noqa: S102
        # Find the first callable function
        strategy_fn = None
        for v in safe_ns.values():
            if callable(v) and not isinstance(v, type):
                strategy_fn = v
                break
        if not strategy_fn:
            raise HTTPException(status_code=400, detail="No strategy function found in code")
        signal = strategy_fn(data)
        run = BacktestRun(
            strategy_name="ide_custom",
            symbol=symbol,
            params={"code_length": len(code)},
            results={"signal": str(signal), "data_points": len(data)},
            status="completed",
        )
        session.add(run)
        await session.flush()
        return {"run_id": str(run.id), "signal": str(signal), "data_points": len(data)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Strategy execution error: {exc}") from exc


# ---------------------------------------------------------------------------
# Agents (legacy compatibility)
# ---------------------------------------------------------------------------

@router.post("/api/v1/agents/market-analyst", response_model=AgentResponse)
async def market_analyst(
    payload: AgentRequest, session: AsyncSession = Depends(session_dependency)
) -> AgentResponse:
    runtime = AgentRuntime.from_settings(settings)
    try:
        result = await runtime.complete(
            system_prompt=(
                "You are a cautious market analyst. Distinguish observations from assumptions, "
                "state data limitations, and never present analysis as guaranteed financial advice."
            ),
            prompt=payload.prompt,
            requested_provider=payload.provider,
        )
    except ProviderUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    run = AgentRun(
        agent_name="market_analyst",
        provider=result.provider,
        model=result.model,
        status="completed",
        prompt=payload.prompt,
        output=result.content,
        duration_ms=result.duration_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cost_usd=Decimal("0"),
    )
    session.add(run)
    await session.flush()
    return AgentResponse(
        run_id=run.id,
        provider=result.provider,
        model=result.model,
        content=result.content,
        duration_ms=result.duration_ms,
    )


# ---------------------------------------------------------------------------
# Autonomous Research
# ---------------------------------------------------------------------------

@router.post("/api/v1/research/autonomous")
async def autonomous_research(
    payload: dict,
    user: User = Depends(get_current_user),
) -> dict:
    from .research.autonomous import AutonomousResearch
    runtime = AgentRuntime.from_settings(settings)
    researcher = AutonomousResearch(runtime)
    question = payload.get("question", "")
    symbol = payload.get("symbol", "")
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    result = await researcher.run_research(question, symbol)
    return result


@router.get("/api/v1/research/autonomous/{run_id}")
async def get_autonomous_research(run_id: str) -> dict:
    from .research.autonomous import AutonomousResearch
    runtime = AgentRuntime.from_settings(settings)
    researcher = AutonomousResearch(runtime)
    result = researcher.get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Research run not found")
    return result


@router.post("/api/v1/research/debate")
async def research_debate(payload: dict) -> dict:
    from .research.autonomous import AutonomousResearch
    runtime = AgentRuntime.from_settings(settings)
    researcher = AutonomousResearch(runtime)
    topic = payload.get("topic", "")
    if not topic:
        raise HTTPException(status_code=400, detail="Topic is required")
    return await researcher.run_debate(topic)


# ---------------------------------------------------------------------------
# Memory / RAG
# ---------------------------------------------------------------------------

@router.post("/api/v1/memory/search")
async def memory_search(payload: dict) -> dict:
    from .memory.vector_store import vector_store
    query = payload.get("query", "")
    top_k = payload.get("top_k", 5)
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    results = await vector_store.search(query, top_k=top_k)
    return {"results": results, "count": len(results)}


@router.get("/api/v1/memory/stats")
async def memory_stats() -> dict:
    from .memory.vector_store import vector_store
    return {"total_documents": vector_store.count}


# ---------------------------------------------------------------------------
# Organizations (Multi-tenancy)
# ---------------------------------------------------------------------------

@router.post("/api/v1/orgs", status_code=201)
async def create_org(
    payload: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    if user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Only admins can create organizations")
    org = Organization(
        name=payload.get("name", "New Organization"),
        plan=payload.get("plan", "free"),
        settings=payload.get("settings", {}),
    )
    session.add(org)
    await session.flush()
    user.org_id = org.id
    user.role = "owner"
    await session.flush()
    return {"id": str(org.id), "name": org.name, "plan": org.plan}


@router.get("/api/v1/orgs/{org_id}/members")
async def list_org_members(
    org_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(session_dependency),
) -> list[dict]:
    from uuid import UUID as _UUID
    try:
        uid = _UUID(org_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid org ID")
    if user.org_id != uid and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    members = await session.scalars(select(User).where(User.org_id == uid))
    return [
        {"id": str(m.id), "email": m.email, "display_name": m.display_name, "role": m.role}
        for m in members
    ]


@router.post("/api/v1/orgs/{org_id}/invite")
async def invite_to_org(
    org_id: str,
    payload: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    from uuid import UUID as _UUID
    try:
        uid = _UUID(org_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid org ID")
    if user.org_id != uid or user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Only org admins can invite members")
    email = payload.get("email", "")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    target = await session.scalar(select(User).where(User.email == email))
    if target:
        target.org_id = uid
        target.role = payload.get("role", "member")
        await session.flush()
        return {"status": "added", "user_id": str(target.id)}
    return {"status": "invited", "email": email}


@router.put("/api/v1/orgs/{org_id}/settings")
async def update_org_settings(
    org_id: str,
    payload: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    from uuid import UUID as _UUID
    try:
        uid = _UUID(org_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid org ID")
    if user.org_id != uid or user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Access denied")
    org = await session.get(Organization, uid)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org.settings = payload.get("settings", {})
    org.name = payload.get("name", org.name)
    await session.flush()
    return {"id": str(org.id), "name": org.name, "settings": org.settings}


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

@router.get("/api/v1/audit-logs")
async def list_audit_logs(
    action: str | None = None,
    user_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(session_dependency),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    if current_user.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Admin access required")
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    rows = await session.scalars(stmt)
    return [
        {
            "id": str(r.id),
            "user_id": str(r.user_id) if r.user_id else None,
            "action": r.action,
            "resource": r.resource,
            "details": r.details,
            "ip_address": r.ip_address,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Marketplace
# ---------------------------------------------------------------------------

@router.get("/api/v1/marketplace/strategies")
async def list_strategies(
    category: str | None = None,
    search: str | None = None,
) -> dict:
    # Curated marketplace strategies (in production, load from DB)
    strategies = [
        {"id": "sma_crossover", "name": "SMA Crossover", "category": "trend", "rating": 4.2, "downloads": 1250, "author": "ArrowEra", "description": "Classic moving average crossover strategy"},
        {"id": "rsi_mean_reversion", "name": "RSI Mean Reversion", "category": "oscillator", "rating": 4.0, "downloads": 980, "author": "ArrowEra", "description": "Buy oversold, sell overbought using RSI"},
        {"id": "bollinger_squeeze", "name": "Bollinger Band Squeeze", "category": "volatility", "rating": 3.8, "downloads": 750, "author": "ArrowEra", "description": "Trade volatility breakouts from tight Bollinger Bands"},
        {"id": "macd_divergence", "name": "MACD Divergence", "category": "momentum", "rating": 4.1, "downloads": 1100, "author": "ArrowEra", "description": "Trade MACD divergence patterns"},
        {"id": "vwap_reversion", "name": "VWAP Reversion", "category": "intraday", "rating": 3.9, "downloads": 620, "author": "ArrowEra", "description": "Mean reversion to VWAP for intraday trading"},
        {"id": "pairs_trading", "name": "Statistical Pairs Trading", "category": "statistical", "rating": 4.3, "downloads": 450, "author": "QuantLab", "description": "Cointegration-based pairs trading"},
    ]
    if category:
        strategies = [s for s in strategies if s["category"] == category]
    if search:
        q = search.lower()
        strategies = [s for s in strategies if q in s["name"].lower() or q in s["description"].lower()]
    return {"strategies": strategies, "count": len(strategies)}


@router.get("/api/v1/marketplace/strategies/{strategy_id}")
async def get_strategy(strategy_id: str) -> dict:
    return {
        "id": strategy_id,
        "name": strategy_id.replace("_", " ").title(),
        "category": "general",
        "version": "1.0.0",
        "description": f"Trading strategy: {strategy_id}",
        "parameters": {"fast_period": 10, "slow_period": 30},
    }


# ---------------------------------------------------------------------------
# Workflow Definitions (CRUD)
# ---------------------------------------------------------------------------

@router.get("/api/v1/workflow-definitions")
async def list_workflow_definitions(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(session_dependency),
) -> list[dict]:
    rows = await session.scalars(
        select(WorkflowDefinition).where(WorkflowDefinition.user_id == user.id)
    )
    return [
        {"id": str(w.id), "name": w.name, "description": w.description, "dag": w.dag, "is_active": w.is_active}
        for w in rows
    ]


@router.post("/api/v1/workflow-definitions", status_code=201)
async def create_workflow_definition(
    payload: dict,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(session_dependency),
) -> dict:
    wf = WorkflowDefinition(
        user_id=user.id,
        name=payload.get("name", "Untitled"),
        description=payload.get("description", ""),
        dag=payload.get("dag", {}),
    )
    session.add(wf)
    await session.flush()
    return {"id": str(wf.id), "name": wf.name}


# ---------------------------------------------------------------------------
# Task Queue
# ---------------------------------------------------------------------------

@router.post("/api/v1/tasks/publish")
async def publish_task(payload: dict) -> dict:
    from .queue.publisher import publisher
    task_name = payload.get("name", "")
    task_payload = payload.get("payload", {})
    if not task_name:
        raise HTTPException(status_code=400, detail="Task name is required")
    task_id = await publisher.publish(task_name, task_payload)
    return {"task_id": task_id, "status": "published"}


@router.get("/api/v1/tasks/{task_id}")
async def get_task_status(task_id: str) -> dict:
    from .queue.publisher import publisher
    status = await publisher.get_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@router.get("/api/v1/tasks/queue/stats")
async def queue_stats() -> dict:
    from .queue.publisher import publisher
    from .queue.scheduler import scheduler
    return {
        "pending_tasks": publisher.pending_count,
        "scheduled_tasks": scheduler.get_tasks(),
    }
