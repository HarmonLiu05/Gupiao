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


def test_quote_command_supports_json_output(monkeypatch):
    class FakeYahooClient:
        def get_quote(self, symbol):
            return StockQuote(symbol=symbol.upper(), last_price="212.34", currency="USD")

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["quote", "aapl", "--output", "json"])

    assert result.exit_code == 0
    assert '"symbol": "AAPL"' in result.output
    assert '"last_price": "212.34"' in result.output


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


def test_options_command_supports_csv_output(monkeypatch):
    class FakeYahooClient:
        def get_option_chain(self, symbol, expiration, side, min_strike, max_strike):
            return OptionChainSnapshot(
                symbol="AAPL",
                expiration="2026-05-15",
                contracts=[
                    OptionContract(
                        contract_symbol="AAPL260515C00210000",
                        side="call",
                        strike="210",
                        last_price="5.5",
                    )
                ],
            )

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["options", "AAPL", "--output", "csv"])

    assert result.exit_code == 0
    assert "symbol,expiration,contract,side,strike,last_price" in result.output
    assert "AAPL,2026-05-15,AAPL260515C00210000,call,210,5.5" in result.output


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


def test_quotes_command_prints_csv(monkeypatch):
    class FakeYahooClient:
        def get_quotes(self, symbols):
            assert symbols == ["AAPL", "MSFT"]
            return [
                StockQuote(symbol="AAPL", last_price="212.34", currency="USD"),
                StockQuote(symbol="MSFT", last_price="499.50", currency="USD"),
            ]

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["quotes", "AAPL,MSFT", "--output", "csv"])

    assert result.exit_code == 0
    assert "AAPL" in result.output
    assert "MSFT" in result.output
    assert "symbol,last_price,currency" in result.output


def test_quotes_command_reads_watchlist_file(monkeypatch, tmp_path):
    watchlist = tmp_path / "watchlist.txt"
    watchlist.write_text("# comment\nAAPL\n\nMSFT\n", encoding="utf-8")

    class FakeYahooClient:
        def get_quotes(self, symbols):
            assert symbols == ["AAPL", "MSFT"]
            return [StockQuote(symbol=symbol, last_price="1", currency="USD") for symbol in symbols]

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["quotes", "--file", str(watchlist), "--output", "table"])

    assert result.exit_code == 0
    assert "AAPL" in result.output
    assert "MSFT" in result.output


def test_expirations_command_prints_available_dates(monkeypatch):
    class FakeYahooClient:
        def get_expirations(self, symbol):
            assert symbol == "aapl"
            return ["2026-05-15", "2026-06-19"]

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["expirations", "aapl"])

    assert result.exit_code == 0
    assert "AAPL" in result.output
    assert "2026-05-15" in result.output


def test_expirations_command_supports_json_output(monkeypatch):
    class FakeYahooClient:
        def get_expirations(self, symbol):
            return ["2026-05-15"]

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["expirations", "aapl", "--output", "json"])

    assert result.exit_code == 0
    assert '"symbol": "AAPL"' in result.output
    assert '"expiration": "2026-05-15"' in result.output


def test_quotes_command_requires_symbols_or_file():
    result = CliRunner().invoke(app, ["quotes"])

    assert result.exit_code == 2
    assert "provide symbols or --file" in result.output


def test_options_command_prints_no_match_message(monkeypatch):
    class FakeYahooClient:
        def get_option_chain(self, symbol, expiration, side, min_strike, max_strike):
            return OptionChainSnapshot(symbol="AAPL", expiration="2026-05-15", contracts=[])

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["options", "AAPL", "--min-strike", "999999"])

    assert result.exit_code == 0
    assert "no contracts matched" in result.output.lower()


def test_market_data_errors_are_user_facing(monkeypatch):
    class FakeYahooClient:
        def get_quote(self, symbol):
            raise RuntimeError("timeout")

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeYahooClient)

    result = CliRunner().invoke(app, ["quote", "AAPL"])

    assert result.exit_code == 1
    assert "market data unavailable: timeout" in result.output


def test_options_command_rejects_invalid_side():
    result = CliRunner().invoke(app, ["options", "AAPL", "--side", "bad"])

    assert result.exit_code == 2
    assert "side must be one of" in result.output


def test_daily_report_dry_run_prints_email(monkeypatch, tmp_path):
    config = tmp_path / "daily_report.yml"
    config.write_text(
        "timezone: Asia/Shanghai\n"
        "symbols:\n"
        "  - QQQ\n"
        "mail:\n"
        "  subject_prefix: 美股收盘日报\n"
        "indicators:\n"
        "  lookback_period: 1y\n",
        encoding="utf-8",
    )

    class FakeClient:
        def get_history(self, symbol, period="1y"):
            import pandas as pd

            return pd.DataFrame({"Close": [float(100 + i) for i in range(260)]})

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeClient)

    result = CliRunner().invoke(app, ["daily-report", "--config", str(config), "--dry-run"])

    assert result.exit_code == 0
    assert "美股收盘日报" in result.output
    assert "QQQ" in result.output


def test_daily_report_send_requires_email_env(monkeypatch, tmp_path):
    config = tmp_path / "daily_report.yml"
    config.write_text("symbols:\n  - QQQ\n", encoding="utf-8")
    for name in ("QQ_SMTP_USER", "QQ_SMTP_AUTH_CODE", "ALERT_EMAIL_TO"):
        monkeypatch.delenv(name, raising=False)

    result = CliRunner().invoke(app, ["daily-report", "--config", str(config)])

    assert result.exit_code == 2
    assert "QQ_SMTP_USER" in result.output


def test_daily_report_send_attaches_table_png(monkeypatch, tmp_path):
    config = tmp_path / "daily_report.yml"
    config.write_text("symbols:\n  - QQQ\n", encoding="utf-8")
    monkeypatch.setenv("QQ_SMTP_USER", "sender@qq.com")
    monkeypatch.setenv("QQ_SMTP_AUTH_CODE", "auth-code")
    monkeypatch.setenv("ALERT_EMAIL_TO", "receiver@example.com")
    sent = {}

    class FakeClient:
        def get_history(self, symbol, period="1y"):
            import pandas as pd

            return pd.DataFrame({"Close": [float(100 + i) for i in range(260)]})

    def fake_send_email(config, subject, body, attachments=None):
        sent["subject"] = subject
        sent["attachments"] = attachments or []

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeClient)
    monkeypatch.setattr("polybot.cli.send_email", fake_send_email)

    result = CliRunner().invoke(app, ["daily-report", "--config", str(config)])

    assert result.exit_code == 0
    assert sent["subject"].startswith("美股收盘日报")
    assert sent["attachments"][0][0] == "daily-stock-report.png"
    assert sent["attachments"][0][1].startswith(b"\x89PNG\r\n\x1a\n")
    assert sent["attachments"][0][2] == "image/png"
