from decimal import Decimal

import pandas as pd

from polybot.clients.yahoo_market_data import YahooMarketDataClient


class FakeTicker:
    options = ("2026-05-15", "2026-06-19")

    def __init__(self, symbol: str):
        self.symbol = symbol

    @property
    def fast_info(self):
        return {
            "last_price": 212.34,
            "currency": "USD",
            "previous_close": 210.00,
            "market_cap": 3_100_000_000,
        }

    def option_chain(self, expiration: str):
        calls = pd.DataFrame(
            [
                {
                    "contractSymbol": "AAPL260515C00210000",
                    "strike": 210.0,
                    "lastPrice": 5.5,
                    "bid": 5.4,
                    "ask": 5.6,
                    "volume": 100,
                    "openInterest": 200,
                    "impliedVolatility": 0.25,
                },
                {
                    "contractSymbol": "AAPL260515C00230000",
                    "strike": 230.0,
                    "lastPrice": 1.2,
                    "bid": 1.1,
                    "ask": 1.3,
                    "volume": 10,
                    "openInterest": 20,
                    "impliedVolatility": 0.3,
                },
            ]
        )
        puts = pd.DataFrame(
            [
                {
                    "contractSymbol": "AAPL260515P00210000",
                    "strike": 210.0,
                    "lastPrice": 4.8,
                    "bid": 4.7,
                    "ask": 4.9,
                    "volume": 90,
                    "openInterest": 180,
                    "impliedVolatility": 0.27,
                }
            ]
        )
        return type("OptionChain", (), {"calls": calls, "puts": puts})()


def test_get_quote_accepts_snake_case_fast_info_keys():
    client = YahooMarketDataClient(ticker_factory=FakeTicker)

    quote = client.get_quote("aapl")

    assert quote.symbol == "AAPL"
    assert quote.last_price == Decimal("212.34")
    assert quote.currency == "USD"
    assert quote.previous_close == Decimal("210.0")
    assert quote.market_cap == 3100000000


def test_get_quote_accepts_camel_case_fast_info_keys():
    class CamelCaseTicker(FakeTicker):
        @property
        def fast_info(self):
            return {
                "lastPrice": 212.34,
                "currency": "USD",
                "previousClose": 210.00,
                "marketCap": 3_100_000_000,
            }

    client = YahooMarketDataClient(ticker_factory=CamelCaseTicker)

    quote = client.get_quote("aapl")

    assert quote.last_price == Decimal("212.34")
    assert quote.previous_close == Decimal("210.0")
    assert quote.market_cap == 3100000000


def test_get_option_chain_filters_side_and_strike_range():
    client = YahooMarketDataClient(ticker_factory=FakeTicker)

    chain = client.get_option_chain("aapl", expiration="2026-05-15", side="calls", min_strike=215)

    assert chain.symbol == "AAPL"
    assert chain.expiration == "2026-05-15"
    assert len(chain.contracts) == 1
    assert chain.contracts[0].contract_symbol == "AAPL260515C00230000"
    assert chain.contracts[0].strike == Decimal("230.0")


def test_get_option_chain_uses_first_expiration_when_missing():
    client = YahooMarketDataClient(ticker_factory=FakeTicker)

    chain = client.get_option_chain("aapl", expiration=None, side="puts")

    assert chain.expiration == "2026-05-15"
    assert len(chain.contracts) == 1
    assert chain.contracts[0].side == "put"
