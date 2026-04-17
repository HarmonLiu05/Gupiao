from decimal import Decimal

from polybot.data.models import MarketSnapshot
from polybot.strategy.value_edge import ValueEdgeStrategy


def test_weak_edge_does_not_generate_signal():
    strategy = ValueEdgeStrategy(
        fair_probability=Decimal("0.55"),
        min_edge=Decimal("0.05"),
        max_spread=Decimal("0.03"),
        base_size=Decimal("10"),
    )
    snapshot = MarketSnapshot(
        market_id="m1",
        token_id="t1",
        best_bid=Decimal("0.51"),
        best_ask=Decimal("0.52"),
        spread=Decimal("0.01"),
    )

    assert strategy.generate(snapshot) == []


def test_strong_edge_generates_buy_signal():
    strategy = ValueEdgeStrategy(
        fair_probability=Decimal("0.60"),
        min_edge=Decimal("0.05"),
        max_spread=Decimal("0.03"),
        base_size=Decimal("10"),
    )
    snapshot = MarketSnapshot(
        market_id="m1",
        token_id="t1",
        best_bid=Decimal("0.50"),
        best_ask=Decimal("0.52"),
        spread=Decimal("0.02"),
    )

    signals = strategy.generate(snapshot)

    assert len(signals) == 1
    assert signals[0].side == "BUY"
    assert signals[0].price == Decimal("0.52")
