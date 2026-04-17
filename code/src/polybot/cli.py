import json
from pathlib import Path

import pandas as pd
import typer

from polybot.clients.gamma import GammaClient
from polybot.clients.geoblock import assert_live_allowed, check_geoblock
from polybot.clients.yahoo_market_data import YahooMarketDataClient
from polybot.config import Settings

app = typer.Typer()


def _display(value: object) -> str:
    return "" if value is None else str(value)


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
def quote(symbol: str) -> None:
    market_data = YahooMarketDataClient()
    item = market_data.get_quote(symbol)
    typer.echo(
        "symbol\tlast_price\tcurrency\tprevious_close\tmarket_cap\n"
        f"{item.symbol}\t{_display(item.last_price)}\t{_display(item.currency)}\t"
        f"{_display(item.previous_close)}\t{_display(item.market_cap)}"
    )


@app.command("options")
def options_chain(
    symbol: str,
    expiration: str | None = typer.Option(None),
    side: str = typer.Option("both"),
    min_strike: float | None = typer.Option(None),
    max_strike: float | None = typer.Option(None),
) -> None:
    if side not in {"calls", "puts", "both"}:
        typer.echo("side must be one of: calls, puts, both")
        raise typer.Exit(code=2)

    market_data = YahooMarketDataClient()
    chain = market_data.get_option_chain(
        symbol,
        expiration=expiration,
        side=side,
        min_strike=min_strike,
        max_strike=max_strike,
    )
    typer.echo(
        "symbol\texpiration\tcontract\tside\tstrike\tlast_price\tbid\task\t"
        "volume\topen_interest\tiv"
    )
    for contract in chain.contracts:
        typer.echo(
            f"{chain.symbol}\t{chain.expiration}\t{contract.contract_symbol}\t"
            f"{contract.side}\t{contract.strike}\t{_display(contract.last_price)}\t"
            f"{_display(contract.bid)}\t{_display(contract.ask)}\t{_display(contract.volume)}\t"
            f"{_display(contract.open_interest)}\t{_display(contract.implied_volatility)}"
        )


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
