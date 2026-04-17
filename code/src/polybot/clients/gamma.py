import httpx

from polybot.data.models import Market

GAMMA_MARKETS_URL = "https://gamma-api.polymarket.com/markets"


class GammaClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=10)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def list_markets(self, limit: int = 100, active: bool = True) -> list[Market]:
        response = self._client.get(
            GAMMA_MARKETS_URL,
            params={"limit": limit, "active": str(active).lower()},
        )
        response.raise_for_status()
        return [Market.model_validate(item) for item in response.json()]

    def search_markets(self, query: str, limit: int = 20) -> list[Market]:
        response = self._client.get(
            GAMMA_MARKETS_URL,
            params={"limit": limit, "active": "true", "q": query},
        )
        response.raise_for_status()
        return [Market.model_validate(item) for item in response.json()]
