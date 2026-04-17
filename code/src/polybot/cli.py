import json
from pathlib import Path

import pandas as pd
import typer

from polybot.clients.gamma import GammaClient
from polybot.clients.geoblock import assert_live_allowed, check_geoblock
from polybot.config import Settings

app = typer.Typer()


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
