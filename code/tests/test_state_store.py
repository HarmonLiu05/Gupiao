from decimal import Decimal

from polybot.state.store import StateStore


def test_store_records_fills_and_updates_position(tmp_path):
    store = StateStore(tmp_path / "polybot.sqlite3")
    store.initialize()

    store.record_fill(
        order_id="o1",
        market_id="m1",
        token_id="t1",
        side="BUY",
        price=Decimal("0.50"),
        size=Decimal("10"),
    )

    position = store.get_position("m1", "t1")

    assert position["size"] == Decimal("10")
    assert position["average_cost"] == Decimal("0.50")
