from decimal import Decimal


def market_value(quantity: Decimal, price: Decimal) -> Decimal:
    if quantity < 0 or price < 0:
        raise ValueError("quantity and price must be non-negative")
    return quantity * price


def unrealized_pnl(quantity: Decimal, average_cost: Decimal, current_price: Decimal) -> Decimal:
    if quantity < 0 or average_cost < 0 or current_price < 0:
        raise ValueError("position values must be non-negative")
    return quantity * (current_price - average_cost)


def portfolio_weight(position_value: Decimal, portfolio_value: Decimal) -> Decimal:
    if portfolio_value <= 0:
        raise ValueError("portfolio value must be positive")
    return position_value / portfolio_value
