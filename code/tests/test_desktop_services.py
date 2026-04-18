from decimal import Decimal

import pandas as pd

from polybot.desktop.models import ActionResult, SaveSymbolsResult
from polybot.desktop.services import DesktopReportService, normalize_symbol_lines


def test_normalize_symbol_lines_uppercases_and_deduplicates():
    assert normalize_symbol_lines(" aapl \nmsft\nAAPL\n\n nvda ") == ["AAPL", "MSFT", "NVDA"]


def test_validate_and_save_symbols_rejects_invalid_symbols():
    saved_symbols = []

    class FakeStore:
        def save_symbols(self, symbols):
            saved_symbols.append(symbols)

    class FakeClient:
        def get_history(self, symbol, period="5d"):
            if symbol == "BAD":
                raise RuntimeError("symbol not found")
            return pd.DataFrame(
                {"Close": [100.0, 101.5]},
                index=pd.to_datetime(["2026-04-16", "2026-04-17"]),
            )

    service = DesktopReportService(
        config_store=FakeStore(),
        history_client_factory=lambda: FakeClient(),
    )

    result = service.validate_and_save_symbols("aapl\nbad\n")

    assert isinstance(result, SaveSymbolsResult)
    assert result.saved is False
    assert saved_symbols == []
    assert result.validations[0].last_close == Decimal("101.50")
    assert result.validations[1].error is not None


def test_validate_and_save_symbols_persists_when_all_symbols_are_valid():
    saved_symbols = []

    class FakeStore:
        def save_symbols(self, symbols):
            saved_symbols.append(symbols)

    class FakeClient:
        def get_history(self, symbol, period="5d"):
            return pd.DataFrame(
                {"Close": [100.0, 101.5]},
                index=pd.to_datetime(["2026-04-16", "2026-04-17"]),
            )

    service = DesktopReportService(
        config_store=FakeStore(),
        history_client_factory=lambda: FakeClient(),
    )

    result = service.validate_and_save_symbols("aapl\nmsft\n")

    assert result.saved is True
    assert result.symbols == ["AAPL", "MSFT"]
    assert saved_symbols == [["AAPL", "MSFT"]]


def test_send_report_now_requires_email_env(monkeypatch):
    class FakeStore:
        def load_or_create(self):
            from polybot.desktop.models import DesktopReportConfig

            return DesktopReportConfig(symbols=["QQQ"], indicators={"lookback_period": "1y"})

    service = DesktopReportService(config_store=FakeStore(), history_client_factory=lambda: object())
    for name in ("QQ_SMTP_USER", "QQ_SMTP_AUTH_CODE", "ALERT_EMAIL_TO"):
        monkeypatch.delenv(name, raising=False)

    result = service.send_report_now()

    assert isinstance(result, ActionResult)
    assert result.ok is False
    assert "QQ_SMTP_USER" in result.message


def test_send_report_now_uses_existing_report_pipeline(monkeypatch):
    sent = {}

    class FakeStore:
        def load_or_create(self):
            from polybot.desktop.models import DesktopReportConfig

            return DesktopReportConfig(
                symbols=["QQQ"],
                indicators={"lookback_period": "1y"},
                mail={"subject_prefix": "美股收盘日报"},
            )

    class FakeHistoryClient:
        def get_history(self, symbol, period="1y"):
            return pd.DataFrame(
                {"Close": [100.0, 101.5]},
                index=pd.to_datetime(["2026-04-16", "2026-04-17"]),
            )

    def fake_send_email(config, subject, body, attachments=None):
        sent["subject"] = subject
        sent["attachments"] = attachments or []

    monkeypatch.setenv("QQ_SMTP_USER", "sender@qq.com")
    monkeypatch.setenv("QQ_SMTP_AUTH_CODE", "auth-code")
    monkeypatch.setenv("ALERT_EMAIL_TO", "receiver@example.com")

    service = DesktopReportService(
        config_store=FakeStore(),
        history_client_factory=lambda: FakeHistoryClient(),
        email_sender=fake_send_email,
    )

    result = service.send_report_now()

    assert result.ok is True
    assert sent["subject"].startswith("美股收盘日报")
    assert sent["attachments"][0][0] == "daily-stock-report.png"
