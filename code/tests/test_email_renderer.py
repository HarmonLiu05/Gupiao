from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from polybot.reports.daily_stock import DailyStockReport, StockReportRow
from polybot.reports.email_renderer import render_daily_stock_email, render_daily_stock_table_png


def test_render_daily_stock_email_contains_required_fields():
    report = DailyStockReport(
        generated_at=datetime(2026, 4, 18, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        timezone="Asia/Shanghai",
        rows=[
            StockReportRow(
                symbol="QQQ",
                close=Decimal("500.00"),
                daily_change_pct=Decimal("1.25"),
                vs_ma20_pct=Decimal("2.30"),
                vs_ma50_pct=Decimal("4.10"),
                from_52w_high_pct=Decimal("-3.50"),
                from_52w_low_pct=Decimal("28.00"),
            )
        ],
    )

    subject, body = render_daily_stock_email(report)

    assert "美股收盘日报" in subject
    assert "QQQ" in body
    assert "日涨跌幅" in body
    assert "MA20偏离" in body
    assert "MA50偏离" in body
    assert "距52周高点" in body
    assert "距52周低点" in body
    assert "成交量" not in body


def test_render_daily_stock_table_png_returns_png_bytes():
    report = DailyStockReport(
        generated_at=datetime(2026, 4, 18, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        timezone="Asia/Shanghai",
        rows=[
            StockReportRow(
                symbol="QQQ",
                close=Decimal("500.00"),
                daily_change_pct=Decimal("1.25"),
                vs_ma20_pct=Decimal("2.30"),
                vs_ma50_pct=Decimal("4.10"),
                from_52w_high_pct=Decimal("-3.50"),
                from_52w_low_pct=Decimal("28.00"),
            )
        ],
    )

    png = render_daily_stock_table_png(report)

    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(png) > 1000
