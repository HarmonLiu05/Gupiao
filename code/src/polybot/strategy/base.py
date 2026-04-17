from decimal import Decimal
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from polybot.data.models import MarketSnapshot


class Signal(BaseModel):
    market_id: str
    token_id: str
    side: Literal["BUY", "SELL"]
    price: Decimal
    size: Decimal
    reason: str
    confidence: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))


class Strategy(Protocol):
    def generate(self, snapshot: MarketSnapshot) -> list[Signal]:
        ...
