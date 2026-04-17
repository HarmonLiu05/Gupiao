import httpx
import pytest

from polybot.clients.geoblock import GeoblockStatus, assert_live_allowed, check_geoblock
from polybot.config import Settings


def test_check_geoblock_returns_typed_status():
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://polymarket.com/api/geoblock"
        return httpx.Response(
            200,
            json={"blocked": False, "ip": "127.0.0.1", "country": "US", "region": "NY"},
        )

    status = check_geoblock(httpx.Client(transport=httpx.MockTransport(handler)))

    assert status == GeoblockStatus(blocked=False, ip="127.0.0.1", country="US", region="NY")


def test_blocked_geo_prevents_live_trading():
    settings = Settings(mode="live", live_trading=True, ack_risk=True)

    with pytest.raises(PermissionError, match="geoblock"):
        assert_live_allowed(settings, GeoblockStatus(blocked=True))


def test_live_requires_explicit_env_gates():
    geo = GeoblockStatus(blocked=False)

    with pytest.raises(PermissionError, match="POLYBOT_LIVE_TRADING"):
        assert_live_allowed(Settings(mode="live", live_trading=False, ack_risk=True), geo)

    with pytest.raises(PermissionError, match="POLYBOT_ACK_RISK"):
        assert_live_allowed(Settings(mode="live", live_trading=True, ack_risk=False), geo)
