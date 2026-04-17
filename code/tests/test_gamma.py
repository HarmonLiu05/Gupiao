import httpx

from polybot.clients.gamma import GammaClient
from polybot.data.models import Market


def test_market_is_tradable_requires_active_open_tokens_and_tick_size():
    tradable = Market(
        condition_id="c1",
        question="Will it rain?",
        active=True,
        closed=False,
        archived=False,
        outcomes=["Yes", "No"],
        clob_token_ids=["yes", "no"],
        minimum_tick_size="0.01",
        min_order_size="5",
    )
    missing_token = tradable.model_copy(update={"clob_token_ids": []})
    closed = tradable.model_copy(update={"closed": True})

    assert tradable.is_tradable() is True
    assert missing_token.is_tradable() is False
    assert closed.is_tradable() is False


def test_gamma_client_filters_market_payloads():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["active"] == "true"
        return httpx.Response(
            200,
            json=[
                {
                    "conditionId": "c1",
                    "question": "Q1",
                    "active": True,
                    "closed": False,
                    "archived": False,
                    "outcomes": '["Yes","No"]',
                    "clobTokenIds": '["t1","t2"]',
                    "minimumTickSize": "0.01",
                    "minOrderSize": "5",
                    "negRisk": False,
                },
                {"conditionId": "c2", "question": "Q2", "active": False},
            ],
        )

    client = GammaClient(httpx.Client(transport=httpx.MockTransport(handler)))

    markets = client.list_markets(limit=10, active=True)

    assert [market.condition_id for market in markets if market.is_tradable()] == ["c1"]
