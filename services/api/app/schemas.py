from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, serialize_by_alias=True)


class ContactCreate(ApiModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    company: str = Field(min_length=2, max_length=180)
    phone: str | None = Field(default=None, max_length=40)
    message: str = Field(min_length=10, max_length=5000)


class ContactCreated(ApiModel):
    id: UUID
    status: str


class AgentRequest(ApiModel):
    prompt: str = Field(min_length=10, max_length=12000)
    provider: str | None = None


class AgentResponse(ApiModel):
    run_id: UUID
    provider: str
    model: str
    content: str
    duration_ms: int


class PositionSummary(ApiModel):
    symbol: str
    quantity: str
    market_value: str
    pnl: str


class DashboardSummary(ApiModel):
    portfolio_value: str
    cash_balance: str
    active_signals: int
    agent_runs: int
    positions: list[PositionSummary]


class ResearchRequest(ApiModel):
    symbol: str | None = None
    question: str | None = None
    provider: str | None = None
    context: dict | None = None


class BacktestRequest(ApiModel):
    symbol: str = Field(min_length=1, max_length=20)
    strategy_name: str = Field(default="sma_crossover", max_length=120)
    initial_capital: float = Field(default=100000.0, ge=1000)
    days: int = Field(default=365, ge=30, le=3650)
    params: dict = Field(default_factory=dict)


class AuthRegister(ApiModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=120)


class AuthLogin(ApiModel):
    email: EmailStr
    password: str


class AuthToken(ApiModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
