import json
from pathlib import Path
from typing import Literal

import pandas as pd
from pydantic import BaseModel
import typer

from polybot.clients.gamma import GammaClient
from polybot.clients.geoblock import assert_live_allowed, check_geoblock
from polybot.clients.yahoo_market_data import YahooMarketDataClient
from polybot.config import Settings
from polybot.marketdata.formatters import format_records

app = typer.Typer()


class ExpirationRow(BaseModel):
    symbol: str
    expiration: str


class OptionContractRow(BaseModel):
    symbol: str
    expiration: str
    contract: str
    side: str
    strike: object
    last_price: object | None = None
    bid: object | None = None
    ask: object | None = None
    volume: int | None = None
    open_interest: int | None = None
    iv: object | None = None


def _parse_symbols(symbols: str | None, file: Path | None) -> list[str]:
    parsed: list[str] = []
    if symbols:
        parsed.extend(item.strip().upper() for item in symbols.split(",") if item.strip())
    if file is not None:
        for line in file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                parsed.append(stripped.upper())
    return parsed


def _run_market_data(action):
    try:
        return action()
    except typer.Exit:
        raise
    except Exception as exc:
        typer.echo(f"market data unavailable: {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def geocheck() -> None:
    status = check_geoblock()
    typer.echo(
        f"blocked={status.blocked} country={status.country or 'unknown'} "
        f"region={status.region or 'unknown'}"
    )


@app.command()
def markets(query: str = typer.Option("")) -> None:
    client = GammaClient()
    try:
        results = client.search_markets(query) if query else client.list_markets()
        for market in results:
            typer.echo(f"{market.condition_id}\t{market.question}")
    finally:
        client.close()


@app.command()
def quote(
    symbol: str,
    output: Literal["table", "json", "csv"] = typer.Option("table"),
) -> None:
    item = _run_market_data(lambda: YahooMarketDataClient().get_quote(symbol))
    typer.echo(format_records([item], output=output))


@app.command()
def quotes(
    symbols: str | None = typer.Argument(None),
    file: Path | None = typer.Option(None),
    output: Literal["table", "json", "csv"] = typer.Option("table"),
) -> None:
    parsed = _parse_symbols(symbols, file)
    if not parsed:
        typer.echo("provide symbols or --file")
        raise typer.Exit(code=2)
    rows = _run_market_data(lambda: YahooMarketDataClient().get_quotes(parsed))
    typer.echo(format_records(rows, output=output))


@app.command()
def expirations(
    symbol: str,
    output: Literal["table", "json", "csv"] = typer.Option("table"),
) -> None:
    dates = _run_market_data(lambda: YahooMarketDataClient().get_expirations(symbol))
    rows = [
        ExpirationRow(symbol=symbol.upper(), expiration=expiration)
        for expiration in dates
    ]
    if not rows:
        typer.echo(f"no expirations found for {symbol.upper()}")
        return
    typer.echo(format_records(rows, output=output))


@app.command("options")
def options_chain(
    symbol: str,
    expiration: str | None = typer.Option(None),
    side: str = typer.Option("both"),
    min_strike: float | None = typer.Option(None),
    max_strike: float | None = typer.Option(None),
    output: Literal["table", "json", "csv"] = typer.Option("table"),
) -> None:
    if side not in {"calls", "puts", "both"}:
        typer.echo("side must be one of: calls, puts, both")
        raise typer.Exit(code=2)

    chain = _run_market_data(
        lambda: YahooMarketDataClient().get_option_chain(
            symbol,
            expiration=expiration,
            side=side,
            min_strike=min_strike,
            max_strike=max_strike,
        )
    )
    if not chain.contracts:
        typer.echo("no contracts matched")
        return
    rows = [
        OptionContractRow(
            symbol=chain.symbol,
            expiration=chain.expiration,
            contract=contract.contract_symbol,
            side=contract.side,
            strike=contract.strike,
            last_price=contract.last_price,
            bid=contract.bid,
            ask=contract.ask,
            volume=contract.volume,
            open_interest=contract.open_interest,
            iv=contract.implied_volatility,
        )
        for contract in chain.contracts
    ]
    typer.echo(format_records(rows, output=output))


@app.command("paper-run")
def paper_run(
    markets: Path = typer.Option(...),
    fair_values: Path = typer.Option(...),
) -> None:
    market_config = json.loads(markets.read_text(encoding="utf-8"))
    fair_data = pd.read_csv(fair_values)
    typer.echo(
        f"paper run complete: markets={len(market_config.get('allowlist', []))} "
        f"fair_values={len(fair_data)}"
    )


@app.command("live-run")
def live_run(
    markets: Path = typer.Option(...),
    fair_values: Path = typer.Option(...),
) -> None:
    _ = json.loads(markets.read_text(encoding="utf-8"))
    _ = pd.read_csv(fair_values)
    settings = Settings(mode="live")
    try:
        if not settings.live_trading:
            raise PermissionError("POLYBOT_LIVE_TRADING must be true before live trading")
        if not settings.ack_risk:
            raise PermissionError("POLYBOT_ACK_RISK must be true before live trading")
        geo = check_geoblock()
        assert_live_allowed(settings, geo)
    except Exception as exc:
        typer.echo(f"live trading refused: {exc}")
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"live gate passed: country={geo.country or 'unknown'} region={geo.region or 'unknown'} "
        f"funder={settings.funder_address or 'missing'} "
        f"max_order_notional={settings.max_order_notional}"
    )


@app.command("cancel-all")
def cancel_all(market: str = typer.Option(...)) -> None:
    settings = Settings(mode="live")
    if not settings.live_trading:
        typer.echo("live trading refused: POLYBOT_LIVE_TRADING must be true before cancellation")
        raise typer.Exit(code=1)
    typer.echo(f"cancel requested for market={market}")
