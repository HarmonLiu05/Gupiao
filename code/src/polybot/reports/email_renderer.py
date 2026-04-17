from io import BytesIO
from decimal import Decimal

from PIL import Image, ImageDraw, ImageFont

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


def render_daily_stock_table_png(report: DailyStockReport) -> bytes:
    headers = ["Symbol", "Close", "Daily", "vs MA20", "vs MA50", "52W High", "52W Low"]
    rows = [
        [
            row.symbol,
            _decimal_text(row.close),
            _pct_text(row.daily_change_pct),
            _pct_text(row.vs_ma20_pct),
            _pct_text(row.vs_ma50_pct),
            _pct_text(row.from_52w_high_pct),
            _pct_text(row.from_52w_low_pct),
        ]
        for row in report.rows
    ]
    if not rows:
        rows = [["N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"]]

    font = ImageFont.load_default(size=18)
    title_font = ImageFont.load_default(size=24)
    cell_padding_x = 16
    cell_padding_y = 12
    table = [headers, *rows]
    column_widths = [
        max(
            int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(str(row[index]), font=font))
            for row in table
        )
        + cell_padding_x * 2
        for index in range(len(headers))
    ]
    row_height = 44
    title_height = 68
    footer_height = 42
    width = sum(column_widths) + 2
    height = title_height + row_height * len(table) + footer_height

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title = f"US Stock Daily Report {report.generated_at:%Y-%m-%d}"
    draw.rectangle([(0, 0), (width, title_height)], fill="#102a43")
    draw.text((16, 20), title, fill="white", font=title_font)

    y = title_height
    for row_index, row in enumerate(table):
        x = 0
        fill = "#d9e8f5" if row_index == 0 else ("#f7fbff" if row_index % 2 else "white")
        text_fill = "#102a43" if row_index == 0 else "#1f2933"
        for column_index, value in enumerate(row):
            cell_width = column_widths[column_index]
            draw.rectangle(
                [(x, y), (x + cell_width, y + row_height)],
                fill=fill,
                outline="#bcccdc",
            )
            draw.text((x + cell_padding_x, y + cell_padding_y), str(value), fill=text_fill, font=font)
            x += cell_width
        y += row_height

    footer = f"Generated: {report.generated_at:%Y-%m-%d %H:%M} {report.timezone}"
    draw.text((16, y + 12), footer, fill="#52606d", font=font)

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
