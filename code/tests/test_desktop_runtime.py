from pathlib import Path

from polybot.desktop.runtime import build_app_paths, resolve_repo_root


def test_resolve_repo_root_walks_up_to_git_directory(tmp_path):
    repo_root = tmp_path / "repo"
    (repo_root / ".git").mkdir(parents=True)
    (repo_root / "code").mkdir()
    (repo_root / "code" / "pyproject.toml").write_text("[project]\nname = 'polybot'\n", encoding="utf-8")
    nested = repo_root / "code" / "dist" / "win"
    nested.mkdir(parents=True)

    assert resolve_repo_root(nested) == repo_root


def test_build_app_paths_points_to_gui_config_files(tmp_path):
    repo_root = tmp_path / "repo"
    (repo_root / ".git").mkdir(parents=True)
    (repo_root / "code" / "config").mkdir(parents=True)
    (repo_root / "code" / "pyproject.toml").write_text("[project]\nname = 'polybot'\n", encoding="utf-8")

    paths = build_app_paths(repo_root)

    assert paths.repo_root == repo_root
    assert paths.code_root == repo_root / "code"
    assert paths.example_config_path == repo_root / "code" / "config" / "daily_report.example.yml"
    assert paths.gui_config_path == repo_root / "code" / "config" / "gui" / "daily_report.yml"
