from typer.testing import CliRunner

from polybot.clients.yahoo_market_data import OptionChainSnapshot, OptionContract, StockQuote
from polybot.cli import app


def test_paper_run_does_not_require_secrets(tmp_path):
    markets = tmp_path / "markets.json"
    fair_values = tmp_path / "fair.csv"
    markets.write_text('{"allowlist": ["m1"]}', encoding="utf-8")
    fair_values.write_text("market_id,token_id,fair_probability\nm1,t1,0.6\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["paper-run", "--markets", str(markets), "--fair-values", str(fair_values)])

    assert result.exit_code == 0
    assert "paper run complete" in result.output


def test_live_run_without_gates_exits_nonzero(tmp_path):
    markets = tmp_path / "markets.json"
    fair_values = tmp_path / "fair.csv"
    markets.write_text('{"allowlist": ["m1"]}', encoding="utf-8")
    fair_values.write_text("market_id,token_id,fair_probability\nm1,t1,0.6\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["live-run", "--markets", str(markets), "--fair-values", str(fair_values)])

    assert result.exit_code != 0
    assert "live trading refused" in result.output


def test_quote_command_prints_stock_price(monkeypatch):
    class FakeYahooClient:
        def get_quote(self, symbol):
            return StockQuote(
                symbol=symbol.upper(),
                last_price="212.34",
                currency="USD",
                previous_close="210.00",
                market_cap=3100000000,
            )

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["quote", "aapl"])

    assert result.exit_code == 0
    assert "AAPL" in result.output
    assert "212.34" in result.output
    assert "USD" in result.output


def test_options_command_prints_filtered_contracts(monkeypatch):
    class FakeYahooClient:
        def get_option_chain(self, symbol, expiration, side, min_strike, max_strike):
            assert symbol == "aapl"
            assert expiration == "2026-05-15"
            assert side == "calls"
            assert min_strike == 200.0
            assert max_strike == 220.0
            return OptionChainSnapshot(
                symbol="AAPL",
                expiration="2026-05-15",
                contracts=[
                    OptionContract(
                        contract_symbol="AAPL260515C00210000",
                        side="call",
                        strike="210",
                        last_price="5.5",
                        bid="5.4",
                        ask="5.6",
                        volume=100,
                        open_interest=200,
                        implied_volatility="0.25",
                    )
                ],
            )

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(
        app,
        [
            "options",
            "aapl",
            "--expiration",
            "2026-05-15",
            "--side",
            "calls",
            "--min-strike",
            "200",
            "--max-strike",
            "220",
        ],
    )

    assert result.exit_code == 0
    assert "AAPL260515C00210000" in result.output
    assert "call" in result.output
    assert "5.6" in result.output


def test_quote_command_prints_zero_values(monkeypatch):
    class FakeYahooClient:
        def get_quote(self, symbol):
            return StockQuote(
                symbol=symbol.upper(),
                last_price="0",
                currency="USD",
                previous_close="0",
                market_cap=0,
            )

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["quote", "zero"])

    assert result.exit_code == 0
    assert "ZERO\t0\tUSD\t0\t0" in result.output


def test_options_command_rejects_invalid_side():
    result = CliRunner().invoke(app, ["options", "AAPL", "--side", "bad"])

    assert result.exit_code == 2
    assert "side must be one of" in result.output
