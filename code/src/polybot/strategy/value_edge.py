from decimal import Decimal

from polybot.data.models import MarketSnapshot
from polybot.strategy.base import Signal


class ValueEdgeStrategy:
    def __init__(
        self,
        fair_probability: Decimal,
        min_edge: Decimal,
        max_spread: Decimal,
        base_size: Decimal,
    ) -> None:
        self.fair_probability = fair_probability
        self.min_edge = min_edge
        self.max_spread = max_spread
        self.base_size = base_size

    def generate(self, snapshot: MarketSnapshot) -> list[Signal]:
        if snapshot.best_ask is None or snapshot.spread is None:
            return []
        edge = self.fair_probability - snapshot.best_ask
        if edge < self.min_edge or snapshot.spread > self.max_spread:
            return []
        return [
            Signal(
                market_id=snapshot.market_id,
                token_id=snapshot.token_id,
                side="BUY",
                price=snapshot.best_ask,
                size=self.base_size,
                reason=f"value_edge:{edge}",
                confidence=max(Decimal("0"), min(Decimal("1"), edge)),
            )
        ]
