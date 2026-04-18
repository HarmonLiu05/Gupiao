from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    repo_root: Path
    code_root: Path
    example_config_path: Path
    gui_config_path: Path


def resolve_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() and (candidate / "code" / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("未找到仓库根目录，请从仓库内运行桌面程序")


def build_app_paths(start: Path) -> AppPaths:
    repo_root = resolve_repo_root(start)
    code_root = repo_root / "code"
    return AppPaths(
        repo_root=repo_root,
        code_root=code_root,
        example_config_path=code_root / "config" / "daily_report.example.yml",
        gui_config_path=code_root / "config" / "gui" / "daily_report.yml",
    )
