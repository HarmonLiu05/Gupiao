from decimal import Decimal
from typing import Any

from polybot.data.models import OrderBook, OrderBookLevel


def _decimal_from_payload(payload: Any, *keys: str) -> Decimal:
    if isinstance(payload, dict):
        for key in keys:
            if key in payload:
                return Decimal(str(payload[key]))
    return Decimal(str(payload))


class ClobDataClient:
    def __init__(self, client: Any) -> None:
        self._client = client

    def get_order_book(self, token_id: str) -> OrderBook:
        raw = self._client.get_order_book(token_id)
        bids = [OrderBookLevel(price=level["price"], size=level["size"]) for level in raw.get("bids", [])]
        asks = [OrderBookLevel(price=level["price"], size=level["size"]) for level in raw.get("asks", [])]
        return OrderBook(token_id=token_id, bids=bids, asks=asks)

    def get_price(self, token_id: str, side: str) -> Decimal:
        return _decimal_from_payload(self._client.get_price(token_id, side), "price")

    def get_midpoint(self, token_id: str) -> Decimal:
        return _decimal_from_payload(self._client.get_midpoint(token_id), "mid", "midpoint", "price")

    def get_spread(self, token_id: str) -> Decimal:
        return _decimal_from_payload(self._client.get_spread(token_id), "spread")

    def estimate_fill_price(self, token_id: str, side: str, amount: Decimal) -> Decimal:
        book = self.get_order_book(token_id)
        levels = book.asks if side.upper() == "BUY" else book.bids
        remaining = amount
        total = Decimal("0")
        filled = Decimal("0")
        for level in levels:
            take = min(remaining, level.size)
            total += take * level.price
            filled += take
            remaining -= take
            if remaining <= 0:
                break
        if filled < amount:
            raise ValueError("insufficient order book depth")
        return total / filled
