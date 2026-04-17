from decimal import Decimal

import pandas as pd

from polybot.reports.daily_stock import (
    build_daily_stock_report,
    build_stock_report_row,
    percent_change,
)


def test_percent_change_returns_decimal_percent():
    result = percent_change(Decimal("110"), Decimal("100"))

    assert result == Decimal("10.00")


def test_build_stock_report_row_calculates_required_percentages():
    history = pd.DataFrame(
        {
            "Close": [float(100 + i) for i in range(260)],
        }
    )

    row = build_stock_report_row("QQQ", history)

    assert row.symbol == "QQQ"
    assert row.close == Decimal("359.00")
    assert row.daily_change_pct is not None
    assert row.vs_ma20_pct is not None
    assert row.vs_ma50_pct is not None
    assert row.from_52w_high_pct == Decimal("0.00")
    assert row.from_52w_low_pct is not None


class FakeHistoryClient:
    def get_history(self, symbol: str, period: str = "1y"):
        return pd.DataFrame({"Close": [float(100 + i) for i in range(260)]})


def test_build_daily_stock_report_returns_rows_for_symbols():
    report = build_daily_stock_report(
        symbols=["QQQ", "NVDA"],
        history_client=FakeHistoryClient(),
        lookback_period="1y",
    )

    assert [row.symbol for row in report.rows] == ["QQQ", "NVDA"]
    assert report.errors == []


def test_build_daily_stock_report_records_symbol_errors():
    class FailingHistoryClient:
        def get_history(self, symbol: str, period: str = "1y"):
            if symbol == "BAD":
                raise RuntimeError("unavailable")
            return pd.DataFrame({"Close": [float(100 + i) for i in range(260)]})

    report = build_daily_stock_report(
        symbols=["QQQ", "BAD"],
        history_client=FailingHistoryClient(),
    )

    assert [row.symbol for row in report.rows] == ["QQQ"]
    assert report.errors == ["BAD: unavailable"]
