from decimal import Decimal

from polybot.reports.daily_stock import DailyStockReport


def render_daily_stock_email(
    report: DailyStockReport,
    subject_prefix: str = "美股收盘日报",
) -> tuple[str, str]:
    date_text = report.generated_at.strftime("%Y-%m-%d")
    time_text = report.generated_at.strftime("%Y-%m-%d %H:%M")
    subject = f"{subject_prefix} {date_text}"
    lines = [
        report.title,
        f"生成时间：{time_text} {report.timezone}",
        "",
        "一、概览",
        "Symbol | Close | 日涨跌幅 | MA20偏离 | MA50偏离 | 距52周高点 | 距52周低点",
    ]
    for row in report.rows:
        lines.append(
            " | ".join(
                [
                    row.symbol,
                    _decimal_text(row.close),
                    _pct_text(row.daily_change_pct),
                    _pct_text(row.vs_ma20_pct),
                    _pct_text(row.vs_ma50_pct),
                    _pct_text(row.from_52w_high_pct),
                    _pct_text(row.from_52w_low_pct),
                ]
            )
        )
    lines.extend(
        [
            "",
            "二、数据异常",
            *(report.errors if report.errors else ["无"]),
            "",
            "三、数据说明",
            "数据源：Yahoo Finance / yfinance",
            "用途：个人观察，不是交易级实时行情",
            "本邮件由 GitHub Actions 自动发送",
        ]
    )
    return subject, "\n".join(lines)


def _decimal_text(value: Decimal | None) -> str:
    return "N/A" if value is None else f"{value:.2f}"


def _pct_text(value: Decimal | None) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"
