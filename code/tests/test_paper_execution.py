from decimal import Decimal

from polybot.data.models import MarketSnapshot
from polybot.execution.paper import PaperBroker
from polybot.state.store import StateStore
from polybot.strategy.base import Signal


def test_paper_buy_fills_at_best_ask_and_updates_cash(tmp_path):
    store = StateStore(tmp_path / "paper.sqlite3")
    store.initialize()
    broker = PaperBroker(store=store, cash=Decimal("100"))
    signal = Signal(
        market_id="m1",
        token_id="t1",
        side="BUY",
        price=Decimal("0.51"),
        size=Decimal("10"),
        reason="test",
        confidence=Decimal("0.8"),
    )
    snapshot = MarketSnapshot(
        market_id="m1",
        token_id="t1",
        best_bid=Decimal("0.49"),
        best_ask=Decimal("0.51"),
        liquidity=Decimal("20"),
    )

    fill = broker.submit(signal, snapshot)

    assert fill.price == Decimal("0.51")
    assert fill.size == Decimal("10")
    assert broker.cash == Decimal("94.90")
    assert store.get_position("m1", "t1")["size"] == Decimal("10")
