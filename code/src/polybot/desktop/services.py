from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import os
from typing import Any, Callable

import pandas as pd

from polybot.clients.yahoo_market_data import YahooMarketDataClient
from polybot.desktop.config_store import DesktopConfigStore
from polybot.desktop.models import ActionResult, SaveSymbolsResult, SymbolValidationResult
from polybot.notifications.emailer import SmtpEmailConfig, send_email
from polybot.reports.daily_stock import build_daily_stock_report
from polybot.reports.email_renderer import render_daily_stock_email, render_daily_stock_table_png


def normalize_symbol_lines(raw_text: str) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for line in raw_text.splitlines():
        symbol = line.strip().upper()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        normalized.append(symbol)
    return normalized


class DesktopReportService:
    def __init__(
        self,
        config_store: DesktopConfigStore,
        history_client_factory: Callable[[], Any] = YahooMarketDataClient,
        email_sender: Callable[..., None] = send_email,
    ) -> None:
        self._config_store = config_store
        self._history_client_factory = history_client_factory
        self._email_sender = email_sender

    def load_symbols_text(self) -> str:
        return "\n".join(self._config_store.load_or_create().symbols)

    def validate_and_save_symbols(self, raw_text: str) -> SaveSymbolsResult:
        symbols = normalize_symbol_lines(raw_text)
        if not symbols:
            return SaveSymbolsResult(saved=False, symbols=[], validations=[], message="请至少输入一个股票代码")

        client = self._history_client_factory()
        validations: list[SymbolValidationResult] = []
        has_error = False

        for symbol in symbols:
            try:
                history = client.get_history(symbol, period="5d")
                close_series = history["Close"].dropna()
                if close_series.empty:
                    raise ValueError("未查到有效收盘价")
                last_close = Decimal(str(close_series.iloc[-1])).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
                last_date = pd.Timestamp(close_series.index[-1]).date().isoformat()
                validations.append(
                    SymbolValidationResult(
                        symbol=symbol,
                        last_close=last_close,
                        last_close_date=last_date,
                    )
                )
            except Exception as exc:
                has_error = True
                validations.append(
                    SymbolValidationResult(
                        symbol=symbol,
                        error=f"未查到有效行情: {exc}",
                    )
                )

        if has_error:
            return SaveSymbolsResult(
                saved=False,
                symbols=symbols,
                validations=validations,
                message="存在无效股票代码，未保存配置",
            )

        self._config_store.save_symbols(symbols)
        return SaveSymbolsResult(
            saved=True,
            symbols=symbols,
            validations=validations,
            message="股票列表保存成功",
        )

    def send_report_now(self) -> ActionResult:
        try:
            config = self._config_store.load_or_create()
            username = os.environ["QQ_SMTP_USER"]
            auth_code = os.environ["QQ_SMTP_AUTH_CODE"]
            to_address = os.environ["ALERT_EMAIL_TO"]
        except KeyError as exc:
            return ActionResult(ok=False, message=f"缺少环境变量：{exc.args[0]}")

        try:
            report = build_daily_stock_report(
                symbols=config.symbols,
                history_client=self._history_client_factory(),
                lookback_period=str(config.indicators.get("lookback_period", "1y")),
                timezone=config.timezone,
                title=config.report_title,
            )
            subject, body = render_daily_stock_email(
                report,
                subject_prefix=str(config.mail.get("subject_prefix", config.report_title)),
            )
            attachment = render_daily_stock_table_png(report)
            self._email_sender(
                SmtpEmailConfig(
                    host=os.environ.get("QQ_SMTP_HOST", "smtp.qq.com"),
                    port=int(os.environ.get("QQ_SMTP_PORT", "465")),
                    username=username,
                    auth_code=auth_code,
                    to_address=to_address,
                ),
                subject=subject,
                body=body,
                attachments=[("daily-stock-report.png", attachment, "image/png")],
            )
        except Exception as exc:
            return ActionResult(ok=False, message=f"邮件发送失败：{exc}")

        return ActionResult(ok=True, message=f"邮件发送成功：{subject}")
