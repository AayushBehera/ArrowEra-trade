from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import settings
from .db import close_database, create_schema
from .exceptions import ArrowEraError
from .middleware import RateLimitMiddleware, RequestContextMiddleware
from .routers import router

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_schema()
    # Initialize market data service
    from .market_data.service import market_data_service
    redis_url = None
    if "redis" in settings.database_url or hasattr(settings, "redis_url"):
        redis_url = getattr(settings, "redis_url", None)
    try:
        await market_data_service.initialize(redis_url)
    except Exception as exc:
        logger.warning("market_data_init_failed", error=str(exc))
    logger.info("api_started", version=settings.version, environment=settings.environment)
    # Start background worker and scheduler
    from .queue.worker import worker
    from .queue.scheduler import scheduler, setup_default_schedules
    try:
        await worker.start()
        setup_default_schedules()
        await scheduler.start()
    except Exception as exc:
        logger.warning("worker_start_failed", error=str(exc))
    yield
    # Stop worker and scheduler
    try:
        await scheduler.stop()
        await worker.stop()
    except Exception:
        pass
    try:
        await market_data_service.shutdown()
    except Exception:
        pass
    await close_database()
    logger.info("api_stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.include_router(router)


@app.exception_handler(ArrowEraError)
async def domain_exception_handler(request: Request, exc: ArrowEraError) -> JSONResponse:
    logger.warning("domain_error", error=exc.message, status=exc.status_code, path=request.url.path)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# WebSocket endpoints
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        await websocket.accept()
        if channel not in self._connections:
            self._connections[channel] = []
        self._connections[channel].append(websocket)
        logger.info("ws_connected", channel=channel)

    def disconnect(self, websocket: WebSocket, channel: str) -> None:
        conns = self._connections.get(channel, [])
        if websocket in conns:
            conns.remove(websocket)
        logger.info("ws_disconnected", channel=channel)

    async def broadcast(self, channel: str, data: dict) -> None:
        import json
        for ws in self._connections.get(channel, []):
            try:
                await ws.send_json(data)
            except Exception:
                pass


ws_manager = ConnectionManager()


@app.websocket("/ws/market")
async def ws_market(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket, "market")
    try:
        while True:
            data = await websocket.receive_json()
            # Client can subscribe to specific symbols
            symbols = data.get("symbols", [])
            if symbols:
                from .market_data.service import market_data_service
                try:
                    overview = await market_data_service.get_market_overview(symbols)
                    await websocket.send_json({"type": "market_update", "data": overview})
                except Exception as exc:
                    await websocket.send_json({"type": "error", "detail": str(exc)})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "market")


@app.websocket("/ws/agents")
async def ws_agents(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket, "agents")
    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("prompt", "")
            provider = data.get("provider")
            if prompt:
                from services.agents.arrowera_agents.runtime import AgentRuntime
                runtime = AgentRuntime.from_settings(settings)
                try:
                    result = await runtime.complete(
                        system_prompt="You are a trading intelligence assistant.",
                        prompt=prompt,
                        requested_provider=provider,
                    )
                    await websocket.send_json({
                        "type": "agent_response",
                        "content": result.content,
                        "provider": result.provider,
                        "model": result.model,
                        "duration_ms": result.duration_ms,
                    })
                except Exception as exc:
                    await websocket.send_json({"type": "error", "detail": str(exc)})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "agents")


@app.websocket("/ws/copilot")
async def ws_copilot(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket, "copilot")
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            if message:
                from services.agents.arrowera_agents.runtime import AgentRuntime
                runtime = AgentRuntime.from_settings(settings)
                try:
                    result = await runtime.complete(
                        system_prompt=(
                            "You are ArrowEra Trade Copilot, an AI trading assistant. "
                            "Help users with market analysis, portfolio questions, strategy ideas, "
                            "and trading education. Be concise and data-driven. "
                            "Never provide guaranteed financial advice."
                        ),
                        prompt=message,
                        requested_provider=data.get("provider"),
                    )
                    await websocket.send_json({
                        "type": "copilot_response",
                        "content": result.content,
                        "provider": result.provider,
                        "model": result.model,
                    })
                except Exception as exc:
                    await websocket.send_json({"type": "error", "detail": str(exc)})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "copilot")
