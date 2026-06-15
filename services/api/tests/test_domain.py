from datetime import UTC, datetime
from decimal import Decimal

import pytest

from services.api.app.config import Settings
from services.api.app.security import create_access_token, decode_access_token
from services.market_data import PriceBar
from services.quant_engine import market_value, portfolio_weight, unrealized_pnl


def test_settings_parse_csv():
    settings = Settings(
        SECRET_KEY="a" * 32,
        CORS_ORIGINS="https://one.example,https://two.example",
    )
    assert settings.cors_origins == ["https://one.example", "https://two.example"]


def test_jwt_round_trip():
    token = create_access_token("user-1", {"role": "analyst"})
    assert decode_access_token(token)["sub"] == "user-1"


def test_quant_calculations():
    assert market_value(Decimal("2"), Decimal("10.50")) == Decimal("21.00")
    assert unrealized_pnl(Decimal("2"), Decimal("10"), Decimal("11")) == Decimal("2")
    assert portfolio_weight(Decimal("25"), Decimal("100")) == Decimal("0.25")
    with pytest.raises(ValueError):
        portfolio_weight(Decimal("1"), Decimal("0"))


def test_price_bar_validation():
    bar = PriceBar(
        " msft ",
        datetime.now(UTC),
        Decimal("100"),
        Decimal("110"),
        Decimal("95"),
        Decimal("105"),
        Decimal("1000"),
    )
    assert bar.symbol == "MSFT"
    with pytest.raises(ValueError):
        PriceBar(
            "BAD",
            datetime.now(UTC),
            Decimal("100"),
            Decimal("99"),
            Decimal("95"),
            Decimal("105"),
            Decimal("1"),
        )
