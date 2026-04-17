from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from pydantic import BaseModel, Field


class StockReportRow(BaseModel):
    symbol: str
    close: Decimal
    previous_close: Decimal | None = None
    daily_change_pct: Decimal | None = None
    ma20: Decimal | None = None
    ma50: Decimal | None = None
    vs_ma20_pct: Decimal | None = None
    vs_ma50_pct: Decimal | None = None
    high_52w: Decimal | None = None
    low_52w: Decimal | None = None
    from_52w_high_pct: Decimal | None = None
    from_52w_low_pct: Decimal | None = None


class DailyStockReport(BaseModel):
    title: str = "美股收盘日报"
    generated_at: datetime
    timezone: str
    rows: list[StockReportRow]
    errors: list[str] = Field(default_factory=list)


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def percent_change(current: Decimal, base: Decimal | None) -> Decimal | None:
    if base is None or base == 0:
        return None
    return (((current - base) / base) * Decimal("100")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def build_stock_report_row(symbol: str, history: pd.DataFrame) -> StockReportRow:
    close_series = history["Close"].dropna()
    if len(close_series) < 2:
        raise ValueError(f"not enough close prices for {symbol.upper()}")

    closes = [_decimal(value) for value in close_series.tolist()]
    close = _money(closes[-1])
    previous_close = _money(closes[-2])
    ma20 = _money(sum(closes[-20:]) / Decimal("20")) if len(closes) >= 20 else None
    ma50 = _money(sum(closes[-50:]) / Decimal("50")) if len(closes) >= 50 else None
    high_52w = _money(max(closes))
    low_52w = _money(min(closes))

    return StockReportRow(
        symbol=symbol.upper(),
        close=close,
        previous_close=previous_close,
        daily_change_pct=percent_change(close, previous_close),
        ma20=ma20,
        ma50=ma50,
        vs_ma20_pct=percent_change(close, ma20),
        vs_ma50_pct=percent_change(close, ma50),
        high_52w=high_52w,
        low_52w=low_52w,
        from_52w_high_pct=percent_change(close, high_52w),
        from_52w_low_pct=percent_change(close, low_52w),
    )


def build_daily_stock_report(
    symbols: list[str],
    history_client: Any,
    lookback_period: str = "1y",
    timezone: str = "Asia/Shanghai",
    title: str = "美股收盘日报",
) -> DailyStockReport:
    rows: list[StockReportRow] = []
    errors: list[str] = []
    for symbol in symbols:
        normalized = symbol.strip().upper()
        if not normalized:
            continue
        try:
            history = history_client.get_history(normalized, period=lookback_period)
            rows.append(build_stock_report_row(normalized, history))
        except Exception as exc:
            errors.append(f"{normalized}: {exc}")

    return DailyStockReport(
        title=title,
        generated_at=datetime.now(ZoneInfo(timezone)),
        timezone=timezone,
        rows=rows,
        errors=errors,
    )
