from __future__ import annotations

import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk
from typing import Callable

from polybot.desktop.config_store import DesktopConfigStore
from polybot.desktop.git_ops import DesktopGitOps
from polybot.desktop.models import ActionResult, SaveSymbolsResult
from polybot.desktop.runtime import build_app_paths
from polybot.desktop.services import DesktopReportService


class DesktopAppController:
    def __init__(
        self,
        load_symbols_text: Callable[[], str],
        save_symbols: Callable[[str], SaveSymbolsResult],
        send_report_now: Callable[[], ActionResult],
        preview_git: Callable[[], str],
        push_git: Callable[[str], str],
    ) -> None:
        self._load_symbols_text = load_symbols_text
        self._save_symbols = save_symbols
        self._send_report_now = send_report_now
        self._preview_git = preview_git
        self._push_git = push_git

    def initial_symbols_text(self) -> str:
        return self._load_symbols_text()

    def handle_save(self, raw_text: str) -> list[str]:
        result = self._save_symbols(raw_text)
        lines = [result.message]
        for row in result.validations:
            if row.error:
                lines.append(f"{row.symbol} | {row.error}")
            else:
                lines.append(f"{row.symbol} | 收盘价 {row.last_close} | 日期 {row.last_close_date}")
        return lines

    def handle_send(self) -> list[str]:
        result = self._send_report_now()
        return [result.message, *result.details]

    def handle_preview(self) -> list[str]:
        return self._preview_git().splitlines() or ["没有可推送的配置变更"]

    def handle_push(self, message: str) -> list[str]:
        return [self._push_git(message.strip() or "Update tracked symbols")]


class DesktopApp:
    def __init__(self, controller: DesktopAppController) -> None:
        self._controller = controller
        self._root = tk.Tk()
        self._root.title("美股邮件助手")
        self._root.geometry("980x720")
        self._root.minsize(900, 640)
        self._commit_message = tk.StringVar(value="Update tracked symbols")

        main = ttk.Frame(self._root, padding=16)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(1, weight=1)
        main.rowconfigure(2, weight=1)

        ttk.Label(main, text="观察列表编辑区").grid(row=0, column=0, sticky="w")
        ttk.Label(main, text="操作区").grid(row=0, column=1, sticky="w", padx=(16, 0))

        self._symbol_text = scrolledtext.ScrolledText(main, wrap="word", font=("Consolas", 12))
        self._symbol_text.grid(row=1, column=0, rowspan=2, sticky="nsew")
        self._symbol_text.insert("1.0", self._controller.initial_symbols_text())

        actions = ttk.Frame(main, padding=(16, 0, 0, 0))
        actions.grid(row=1, column=1, sticky="new")
        actions.columnconfigure(0, weight=1)

        ttk.Button(actions, text="保存股票列表", command=self._save_symbols).grid(
            row=0, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(actions, text="立即发送邮件", command=self._send_report).grid(
            row=1, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(actions, text="预览变更", command=self._preview_git).grid(
            row=2, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Entry(actions, textvariable=self._commit_message).grid(
            row=3, column=0, sticky="ew", pady=(0, 8)
        )
        ttk.Button(actions, text="提交并推送", command=self._push_git).grid(
            row=4, column=0, sticky="ew"
        )

        ttk.Label(main, text="日志输出").grid(row=3, column=0, columnspan=2, sticky="w", pady=(16, 8))
        self._log = scrolledtext.ScrolledText(main, wrap="word", font=("Consolas", 11), state="disabled")
        self._log.grid(row=4, column=0, columnspan=2, sticky="nsew")
        main.rowconfigure(4, weight=2)

    def run(self) -> None:
        self._root.mainloop()

    def _run_async(self, action: Callable[[], list[str]]) -> None:
        def worker() -> None:
            try:
                lines = action()
            except Exception as exc:  # pragma: no cover - UI safety net
                lines = [f"操作失败：{exc}"]
            self._root.after(0, lambda: self._append_lines(lines))

        threading.Thread(target=worker, daemon=True).start()

    def _append_lines(self, lines: list[str]) -> None:
        self._log.configure(state="normal")
        for line in lines:
            self._log.insert("end", f"{line}\n")
        self._log.see("end")
        self._log.configure(state="disabled")
        if any("未保存配置" in line for line in lines):
            messagebox.showerror("保存失败", lines[0])

    def _save_symbols(self) -> None:
        self._run_async(lambda: self._controller.handle_save(self._symbol_text.get("1.0", "end")))

    def _send_report(self) -> None:
        self._run_async(self._controller.handle_send)

    def _preview_git(self) -> None:
        self._run_async(self._controller.handle_preview)

    def _push_git(self) -> None:
        self._run_async(lambda: self._controller.handle_push(self._commit_message.get()))


def _build_controller() -> DesktopAppController:
    start_path = Path.cwd()
    if getattr(sys, "frozen", False):
        start_path = Path(sys.executable).resolve().parent
    paths = build_app_paths(start_path)
    store = DesktopConfigStore(paths.gui_config_path, paths.example_config_path)
    service = DesktopReportService(store)
    git_ops = DesktopGitOps(paths.repo_root)
    return DesktopAppController(
        load_symbols_text=service.load_symbols_text,
        save_symbols=service.validate_and_save_symbols,
        send_report_now=service.send_report_now,
        preview_git=git_ops.preview_app_config,
        push_git=git_ops.commit_and_push_app_config,
    )


def main() -> None:
    DesktopApp(_build_controller()).run()


if __name__ == "__main__":
    main()
