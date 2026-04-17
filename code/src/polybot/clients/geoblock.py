import httpx
from pydantic import BaseModel

from polybot.config import Settings

GEOBLOCK_URL = "https://polymarket.com/api/geoblock"


class GeoblockStatus(BaseModel):
    blocked: bool
    ip: str | None = None
    country: str | None = None
    region: str | None = None


def check_geoblock(client: httpx.Client | None = None) -> GeoblockStatus:
    close_client = client is None
    http_client = client or httpx.Client(timeout=10)
    try:
        response = http_client.get(GEOBLOCK_URL)
        response.raise_for_status()
        return GeoblockStatus.model_validate(response.json())
    finally:
        if close_client:
            http_client.close()


def assert_live_allowed(settings: Settings, geo: GeoblockStatus) -> None:
    if not settings.live_trading:
        raise PermissionError("POLYBOT_LIVE_TRADING must be true before live trading")
    if not settings.ack_risk:
        raise PermissionError("POLYBOT_ACK_RISK must be true before live trading")
    if geo.blocked:
        raise PermissionError("geoblock prevents live trading in this environment")
