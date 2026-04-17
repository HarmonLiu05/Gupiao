from decimal import Decimal

import pytest

from polybot.clients.geoblock import GeoblockStatus
from polybot.config import Settings
from polybot.data.models import Market
from polybot.execution.live import LiveBroker
from polybot.risk.manager import RiskDecision
from polybot.strategy.base import Signal


def make_signal() -> Signal:
    return Signal(
        market_id="m1",
        token_id="t1",
        side="BUY",
        price=Decimal("0.50"),
        size=Decimal("10"),
        reason="edge",
        confidence=Decimal("0.7"),
    )


def make_market() -> Market:
    return Market(
        condition_id="m1",
        active=True,
        closed=False,
        archived=False,
        clobTokenIds=["t1", "t2"],
        minimumTickSize=Decimal("0.01"),
        minOrderSize=Decimal("5"),
    )


def test_live_broker_refuses_when_gate_missing():
    broker = LiveBroker(Settings(live_trading=False, ack_risk=True), object())

    with pytest.raises(PermissionError):
        broker.submit(make_signal(), make_market(), RiskDecision(allowed=True), GeoblockStatus(blocked=False))


def test_live_broker_refuses_risk_rejection():
    broker = LiveBroker(Settings(live_trading=True, ack_risk=True), object())

    with pytest.raises(PermissionError, match="risk"):
        broker.submit(
            make_signal(),
            make_market(),
            RiskDecision(allowed=False, reasons=["market_not_allowed"]),
            GeoblockStatus(blocked=False),
        )
