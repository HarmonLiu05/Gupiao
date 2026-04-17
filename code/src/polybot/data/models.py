import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _parse_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        parsed = json.loads(value)
        return [str(item) for item in parsed]
    return [str(item) for item in value]


class Market(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    condition_id: str = Field(alias="conditionId")
    question: str = ""
    active: bool = False
    closed: bool = False
    archived: bool = False
    outcomes: list[str] = Field(default_factory=list)
    clob_token_ids: list[str] = Field(default_factory=list, alias="clobTokenIds")
    minimum_tick_size: Decimal | None = Field(default=None, alias="minimumTickSize")
    min_order_size: Decimal | None = Field(default=None, alias="minOrderSize")
    neg_risk: bool = Field(default=False, alias="negRisk")
    end_date: datetime | None = Field(default=None, alias="endDate")

    @field_validator("outcomes", "clob_token_ids", mode="before")
    @classmethod
    def parse_json_list(cls, value: Any) -> list[str]:
        return _parse_list(value)

    def is_tradable(self) -> bool:
        return (
            self.active
            and not self.closed
            and not self.archived
            and bool(self.clob_token_ids)
            and self.minimum_tick_size is not None
        )


class OrderBookLevel(BaseModel):
    price: Decimal
    size: Decimal


class OrderBook(BaseModel):
    token_id: str
    bids: list[OrderBookLevel] = Field(default_factory=list)
    asks: list[OrderBookLevel] = Field(default_factory=list)


class MarketSnapshot(BaseModel):
    market_id: str
    token_id: str
    best_bid: Decimal | None = None
    best_ask: Decimal | None = None
    spread: Decimal | None = None
    midpoint: Decimal | None = None
    liquidity: Decimal | None = None

    @classmethod
    def for_empty(cls, market_id: str, token_id: str) -> "MarketSnapshot":
        return cls(market_id=market_id, token_id=token_id)
