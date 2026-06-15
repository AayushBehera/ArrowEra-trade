from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class PriceBar:
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        normalized = self.symbol.strip().upper()
        if not normalized or len(normalized) > 20:
            raise ValueError("symbol must contain 1 to 20 characters")
        if min(self.open, self.high, self.low, self.close) < 0:
            raise ValueError("prices cannot be negative")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("OHLC values are inconsistent")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")
        object.__setattr__(self, "symbol", normalized)
