from decimal import Decimal

from polybot.clients.clob import ClobDataClient


class FakeClob:
    def get_order_book(self, token_id):
        return {
            "market": token_id,
            "bids": [{"price": "0.49", "size": "12.5"}],
            "asks": [{"price": "0.51", "size": "7.25"}],
        }

    def get_price(self, token_id, side):
        return {"price": "0.51"}

    def get_midpoint(self, token_id):
        return {"mid": "0.50"}

    def get_spread(self, token_id):
        return {"spread": "0.02"}

    def get_order_book_summary(self, token_id):
        return self.get_order_book(token_id)


def test_clob_outputs_decimal_values():
    client = ClobDataClient(FakeClob())

    book = client.get_order_book("t1")

    assert book.bids[0].price == Decimal("0.49")
    assert book.asks[0].size == Decimal("7.25")
    assert client.get_price("t1", "BUY") == Decimal("0.51")
    assert client.get_midpoint("t1") == Decimal("0.50")
    assert client.get_spread("t1") == Decimal("0.02")


def test_estimate_fill_price_uses_orderbook_depth():
    client = ClobDataClient(FakeClob())

    assert client.estimate_fill_price("t1", "BUY", Decimal("3")) == Decimal("0.51")
