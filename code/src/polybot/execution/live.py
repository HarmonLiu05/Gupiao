from decimal import Decimal
from typing import Any

from polybot.clients.geoblock import GeoblockStatus, assert_live_allowed
from polybot.config import Settings
from polybot.data.models import Market
from polybot.risk.manager import RiskDecision
from polybot.strategy.base import Signal

CLOB_HOST = "https://clob.polymarket.com"
POLYGON_CHAIN_ID = 137


def round_to_tick(price: Decimal, tick_size: Decimal) -> Decimal:
    return (price // tick_size) * tick_size


class LiveBroker:
    def __init__(self, settings: Settings, client: Any) -> None:
        self.settings = settings
        self.client = client

    def submit(
        self,
        signal: Signal,
        market: Market,
        risk: RiskDecision,
        geo: GeoblockStatus,
    ) -> Any:
        assert_live_allowed(self.settings, geo)
        if not risk.allowed:
            raise PermissionError(f"risk rejected live order: {','.join(risk.reasons)}")
        if market.minimum_tick_size is None or market.min_order_size is None:
            raise PermissionError("missing market tick size or minimum order size")
        price = round_to_tick(signal.price, market.minimum_tick_size)
        if signal.size < market.min_order_size:
            raise PermissionError("order size is below market minimum")
        order_args = {
            "token_id": signal.token_id,
            "side": signal.side,
            "price": str(price),
            "size": str(signal.size),
            "neg_risk": market.neg_risk,
        }
        return self.client.create_and_post_order(order_args)

    def cancel_order(self, order_id: str) -> Any:
        return self.client.cancel(order_id)

    def cancel_market_orders(self, condition_id: str) -> Any:
        return self.client.cancel_market_orders(condition_id)


def build_clob_client(settings: Settings) -> Any:
    from py_clob_client.client import ClobClient

    if settings.private_key is None:
        raise PermissionError("POLYBOT_PRIVATE_KEY is required for live trading")
    return ClobClient(
        CLOB_HOST,
        key=settings.private_key,
        chain_id=POLYGON_CHAIN_ID,
        signature_type=settings.signature_type,
        funder=settings.funder_address,
    )
