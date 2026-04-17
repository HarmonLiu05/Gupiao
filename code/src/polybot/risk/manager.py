from decimal import Decimal

from pydantic import BaseModel, Field

from polybot.config import Settings
from polybot.data.models import Market, MarketSnapshot
from polybot.strategy.base import Signal


class PortfolioState(BaseModel):
    market_exposure: dict[str, Decimal] = Field(default_factory=dict)
    daily_pnl: Decimal = Decimal("0")
    open_orders: int = 0


class RiskDecision(BaseModel):
    allowed: bool
    reasons: list[str] = Field(default_factory=list)


class RiskManager:
    def __init__(
        self,
        settings: Settings,
        allowlist: set[str],
        max_spread: Decimal | None = None,
    ) -> None:
        self.settings = settings
        self.allowlist = allowlist
        self.max_spread = max_spread

    def evaluate(
        self,
        signal: Signal,
        market: Market,
        snapshot: MarketSnapshot,
        portfolio: PortfolioState | None = None,
    ) -> RiskDecision:
        portfolio = portfolio or PortfolioState()
        reasons: list[str] = []
        notional = signal.price * signal.size
        current_exposure = portfolio.market_exposure.get(signal.market_id, Decimal("0"))
        next_exposure = current_exposure + notional

        if signal.market_id not in self.allowlist:
            reasons.append("market_not_allowed")
        if notional > self.settings.max_order_notional:
            reasons.append("order_notional_exceeded")
        if next_exposure > self.settings.max_market_notional:
            reasons.append("market_notional_exceeded")
        if portfolio.daily_pnl < -self.settings.max_daily_loss:
            reasons.append("daily_loss_exceeded")
        if signal.price < Decimal("0.01") or signal.price > Decimal("0.99"):
            reasons.append("price_out_of_bounds")
        if market.min_order_size is not None and signal.size < market.min_order_size:
            reasons.append("min_order_size")
        if market.minimum_tick_size is not None:
            if signal.price % market.minimum_tick_size != 0:
                reasons.append("invalid_tick_size")
        if self.max_spread is not None and snapshot.spread is not None:
            if snapshot.spread > self.max_spread:
                reasons.append("spread_exceeded")

        return RiskDecision(allowed=not reasons, reasons=reasons)
