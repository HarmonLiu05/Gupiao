from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable


APP_CONFIG_RELATIVE_PATH = "code/config/gui/daily_report.yml"


class DesktopGitOps:
    def __init__(
        self,
        repo_root: Path,
        run_command: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self._repo_root = repo_root
        self._run_command = run_command

    def preview_app_config(self) -> str:
        diff = self._run_git("diff", "--", APP_CONFIG_RELATIVE_PATH).stdout.strip()
        return diff or "没有可推送的配置变更"

    def commit_and_push_app_config(self, message: str) -> str:
        self._run_git("rev-parse", "--is-inside-work-tree")
        self._run_git("remote", "get-url", "origin")
        self._run_git("add", "--", APP_CONFIG_RELATIVE_PATH)
        cached = self._run_git("diff", "--cached", "--name-only", "--", APP_CONFIG_RELATIVE_PATH).stdout.strip()
        if not cached:
            return "没有可推送的配置变更"
        self._run_git("commit", "-m", message)
        self._run_git("push")
        return "配置已提交并推送"

    def _run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        result = self._run_command(
            ["git", *args],
            cwd=self._repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "未知 Git 错误"
            raise RuntimeError(stderr)
        return result
