from decimal import Decimal
from uuid import uuid4

from pydantic import BaseModel

from polybot.data.models import MarketSnapshot
from polybot.state.store import StateStore
from polybot.strategy.base import Signal


class Fill(BaseModel):
    order_id: str
    market_id: str
    token_id: str
    side: str
    price: Decimal
    size: Decimal


class PaperBroker:
    def __init__(self, store: StateStore, cash: Decimal = Decimal("0")) -> None:
        self.store = store
        self.cash = cash

    def submit(self, signal: Signal, snapshot: MarketSnapshot) -> Fill:
        execution_price = snapshot.best_ask if signal.side == "BUY" else snapshot.best_bid
        if execution_price is None:
            raise ValueError("missing executable quote")
        if snapshot.liquidity is not None and snapshot.liquidity < signal.size:
            raise ValueError("insufficient simulated liquidity")
        order_id = str(uuid4())
        self.store.record_order(
            order_id,
            signal.market_id,
            signal.token_id,
            signal.side,
            execution_price,
            signal.size,
            "filled",
        )
        self.store.record_fill(
            order_id,
            signal.market_id,
            signal.token_id,
            signal.side,
            execution_price,
            signal.size,
        )
        cash_delta = execution_price * signal.size
        self.cash = self.cash - cash_delta if signal.side == "BUY" else self.cash + cash_delta
        return Fill(
            order_id=order_id,
            market_id=signal.market_id,
            token_id=signal.token_id,
            side=signal.side,
            price=execution_price,
            size=signal.size,
        )
