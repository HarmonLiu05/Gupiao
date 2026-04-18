from __future__ import annotations

from pathlib import Path

import yaml

from polybot.desktop.models import DesktopReportConfig


class DesktopConfigStore:
    def __init__(self, gui_config_path: Path, example_config_path: Path) -> None:
        self._gui_config_path = gui_config_path
        self._example_config_path = example_config_path

    def load_or_create(self) -> DesktopReportConfig:
        if not self._gui_config_path.exists():
            self._gui_config_path.parent.mkdir(parents=True, exist_ok=True)
            self._gui_config_path.write_text(
                self._example_config_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        return DesktopReportConfig.model_validate(self._load_raw())

    def save_symbols(self, symbols: list[str]) -> DesktopReportConfig:
        payload = self._load_raw()
        payload["symbols"] = symbols
        self._gui_config_path.parent.mkdir(parents=True, exist_ok=True)
        self._gui_config_path.write_text(
            yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return DesktopReportConfig.model_validate(payload)

    def _load_raw(self) -> dict:
        with self._gui_config_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
