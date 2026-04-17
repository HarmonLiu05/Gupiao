from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable, Literal

import pandas as pd
from pydantic import BaseModel


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None or pd.isna(value):
        return None
    return Decimal(str(value))


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None


class StockQuote(BaseModel):
    symbol: str
    last_price: Decimal | None
    currency: str | None = None
    previous_close: Decimal | None = None
    market_cap: int | None = None


class OptionContract(BaseModel):
    contract_symbol: str
    side: Literal["call", "put"]
    strike: Decimal
    last_price: Decimal | None = None
    bid: Decimal | None = None
    ask: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None
    implied_volatility: Decimal | None = None


class OptionChainSnapshot(BaseModel):
    symbol: str
    expiration: str
    contracts: list[OptionContract]


class YahooMarketDataClient:
    def __init__(self, ticker_factory: Callable[[str], Any] | None = None) -> None:
        self._ticker_factory = ticker_factory or self._default_ticker_factory

    def get_quote(self, symbol: str) -> StockQuote:
        normalized = symbol.upper()
        ticker = self._ticker_factory(normalized)
        fast_info = dict(ticker.fast_info)
        market_cap = _first_present(fast_info, "market_cap", "marketCap")
        return StockQuote(
            symbol=normalized,
            last_price=_decimal_or_none(_first_present(fast_info, "last_price", "lastPrice")),
            currency=fast_info.get("currency"),
            previous_close=_decimal_or_none(
                _first_present(fast_info, "previous_close", "previousClose")
            ),
            market_cap=int(market_cap) if market_cap is not None else None,
        )

    def get_quotes(self, symbols: list[str]) -> list[StockQuote]:
        normalized = [symbol.strip().upper() for symbol in symbols if symbol.strip()]
        return [self.get_quote(symbol) for symbol in normalized]

    def get_expirations(self, symbol: str) -> list[str]:
        ticker = self._ticker_factory(symbol.upper())
        return [str(item) for item in ticker.options]

    def get_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        ticker = self._ticker_factory(symbol.upper())
        return ticker.history(period=period)

    def get_option_chain(
        self,
        symbol: str,
        expiration: str | None = None,
        side: Literal["calls", "puts", "both"] = "both",
        min_strike: float | int | Decimal | None = None,
        max_strike: float | int | Decimal | None = None,
    ) -> OptionChainSnapshot:
        normalized = symbol.upper()
        ticker = self._ticker_factory(normalized)
        selected_expiration = expiration or str(ticker.options[0])
        raw_chain = ticker.option_chain(selected_expiration)

        frames: list[tuple[Literal["call", "put"], pd.DataFrame]] = []
        if side in {"calls", "both"}:
            frames.append(("call", raw_chain.calls))
        if side in {"puts", "both"}:
            frames.append(("put", raw_chain.puts))

        contracts: list[OptionContract] = []
        min_value = Decimal(str(min_strike)) if min_strike is not None else None
        max_value = Decimal(str(max_strike)) if max_strike is not None else None
        for option_side, frame in frames:
            contracts.extend(
                self._contracts_from_frame(frame, option_side, min_value=min_value, max_value=max_value)
            )

        return OptionChainSnapshot(
            symbol=normalized,
            expiration=selected_expiration,
            contracts=contracts,
        )

    def _contracts_from_frame(
        self,
        frame: pd.DataFrame,
        side: Literal["call", "put"],
        min_value: Decimal | None,
        max_value: Decimal | None,
    ) -> list[OptionContract]:
        contracts: list[OptionContract] = []
        for row in frame.to_dict(orient="records"):
            strike = Decimal(str(row["strike"]))
            if min_value is not None and strike < min_value:
                continue
            if max_value is not None and strike > max_value:
                continue
            contracts.append(
                OptionContract(
                    contract_symbol=str(row["contractSymbol"]),
                    side=side,
                    strike=strike,
                    last_price=_decimal_or_none(row.get("lastPrice")),
                    bid=_decimal_or_none(row.get("bid")),
                    ask=_decimal_or_none(row.get("ask")),
                    volume=self._int_or_none(row.get("volume")),
                    open_interest=self._int_or_none(row.get("openInterest")),
                    implied_volatility=_decimal_or_none(row.get("impliedVolatility")),
                )
            )
        return contracts

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        if value is None or pd.isna(value):
            return None
        return int(value)

    @staticmethod
    def _default_ticker_factory(symbol: str) -> Any:
        try:
            import yfinance as yf
        except ImportError as exc:
            raise RuntimeError(
                "yfinance is required for Yahoo market data. Install it with: "
                "py -3.12 -m pip install yfinance"
            ) from exc
        return yf.Ticker(symbol)
