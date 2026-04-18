from decimal import Decimal

from polybot.desktop.app import DesktopAppController
from polybot.desktop.models import ActionResult, SaveSymbolsResult, SymbolValidationResult


def test_controller_formats_save_feedback_lines():
    controller = DesktopAppController(
        load_symbols_text=lambda: "AAPL\nMSFT",
        save_symbols=lambda raw: SaveSymbolsResult(
            saved=True,
            symbols=["AAPL", "MSFT"],
            validations=[
                SymbolValidationResult(symbol="AAPL", last_close=Decimal("175.23"), last_close_date="2026-04-17"),
                SymbolValidationResult(symbol="MSFT", last_close=Decimal("499.50"), last_close_date="2026-04-17"),
            ],
            message="股票列表保存成功",
        ),
        send_report_now=lambda: ActionResult(ok=True, message="邮件发送成功：美股收盘日报 2026-04-18"),
        preview_git=lambda: "没有可推送的配置变更",
        push_git=lambda message: "配置已提交并推送",
    )

    lines = controller.handle_save("aapl\nmsft")

    assert lines[0] == "股票列表保存成功"
    assert "AAPL | 收盘价 175.23 | 日期 2026-04-17" in lines[1]


def test_controller_passes_commit_message_to_git_push():
    received = {}
    controller = DesktopAppController(
        load_symbols_text=lambda: "AAPL",
        save_symbols=lambda raw: SaveSymbolsResult(saved=True, symbols=["AAPL"], validations=[], message="ok"),
        send_report_now=lambda: ActionResult(ok=True, message="ok"),
        preview_git=lambda: "diff --git",
        push_git=lambda message: received.setdefault("message", message) or "配置已提交并推送",
    )

    controller.handle_push("Update tracked symbols")

    assert received["message"] == "Update tracked symbols"
