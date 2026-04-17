from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POLYBOT_", env_file=".env", extra="ignore")

    mode: Literal["paper", "live", "backtest"] = "paper"
    live_trading: bool = False
    ack_risk: bool = False
    db_path: Path = Path(".polybot/polybot.sqlite3")
    private_key: str | None = None
    funder_address: str | None = None
    signature_type: int = 2
    max_order_notional: Decimal = Field(default=Decimal("10"), gt=Decimal("0"))
    max_market_notional: Decimal = Field(default=Decimal("50"), gt=Decimal("0"))
    max_daily_loss: Decimal = Field(default=Decimal("25"), ge=Decimal("0"))
