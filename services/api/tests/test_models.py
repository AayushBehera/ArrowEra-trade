from decimal import Decimal

from services.api.app.models import Portfolio, Position, Signal


def test_models_use_decimal_and_safe_metadata_name():
    portfolio = Portfolio(name="Primary", cash_balance=Decimal("100.25"))
    position = Position(
        portfolio=portfolio,
        symbol="AAPL",
        quantity=Decimal("2"),
        average_cost=Decimal("100"),
        current_price=Decimal("110"),
    )
    signal = Signal(
        symbol="AAPL",
        signal_type="hold",
        confidence=Decimal("0.5"),
        signal_metadata={"source": "test"},
    )
    assert position.quantity == Decimal("2")
    assert signal.signal_metadata["source"] == "test"
