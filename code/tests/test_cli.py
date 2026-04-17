from typer.testing import CliRunner

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
