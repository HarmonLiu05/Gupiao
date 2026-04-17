from decimal import Decimal

from polybot.config import Settings
from polybot.data.models import Market, MarketSnapshot
from polybot.risk.manager import PortfolioState, RiskManager
from polybot.strategy.base import Signal


def make_market() -> Market:
    return Market(
        condition_id="m1",
        question="Q",
        active=True,
        closed=False,
        archived=False,
        outcomes=["Yes", "No"],
        clob_token_ids=["t1", "t2"],
        minimum_tick_size=Decimal("0.01"),
        min_order_size=Decimal("5"),
    )


def make_signal(**updates) -> Signal:
    data = {
        "market_id": "m1",
        "token_id": "t1",
        "side": "BUY",
        "price": Decimal("0.50"),
        "size": Decimal("10"),
        "reason": "edge",
        "confidence": Decimal("0.7"),
    }
    data.update(updates)
    return Signal(**data)


def test_rejects_market_not_in_allowlist():
    manager = RiskManager(Settings(), allowlist={"other"})

    decision = manager.evaluate(make_signal(), make_market(), MarketSnapshot.for_empty("m1", "t1"))

    assert decision.allowed is False
    assert "market_not_allowed" in decision.reasons


def test_rejects_order_above_notional_limit():
    manager = RiskManager(Settings(max_order_notional=Decimal("1")), allowlist={"m1"})

    decision = manager.evaluate(make_signal(), make_market(), MarketSnapshot.for_empty("m1", "t1"))

    assert "order_notional_exceeded" in decision.reasons


def test_rejects_invalid_tick_size():
    manager = RiskManager(Settings(), allowlist={"m1"})

    decision = manager.evaluate(
        make_signal(price=Decimal("0.505")),
        make_market(),
        MarketSnapshot.for_empty("m1", "t1"),
    )

    assert "invalid_tick_size" in decision.reasons


def test_allows_order_when_limits_pass():
    manager = RiskManager(Settings(), allowlist={"m1"})
    snapshot = MarketSnapshot(
        market_id="m1",
        token_id="t1",
        best_bid=Decimal("0.49"),
        best_ask=Decimal("0.50"),
        spread=Decimal("0.01"),
    )

    decision = manager.evaluate(make_signal(), make_market(), snapshot, PortfolioState())

    assert decision.allowed is True
    assert decision.reasons == []
