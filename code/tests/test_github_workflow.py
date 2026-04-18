from pathlib import Path

import yaml


def test_daily_report_workflow_uses_gui_config_file():
    repo_root = Path(__file__).resolve().parents[2]
    workflow_path = repo_root / ".github" / "workflows" / "us-stock-daily-report.yml"

    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["send-report"]["steps"]
    send_step = next(step for step in steps if step["name"] == "Send daily report")

    assert "config/gui/daily_report.yml" in send_step["run"]
