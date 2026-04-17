from decimal import Decimal

from polybot.config import Settings


def test_live_trading_disabled_by_default():
    settings = Settings()

    assert settings.mode == "paper"
    assert settings.live_trading is False
    assert settings.ack_risk is False


def test_risk_limits_are_decimal_values():
    settings = Settings()

    assert settings.max_order_notional == Decimal("10")
    assert settings.max_market_notional == Decimal("50")
    assert settings.max_daily_loss == Decimal("25")
