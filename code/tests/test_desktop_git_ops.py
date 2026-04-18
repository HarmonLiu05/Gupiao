from polybot.desktop.git_ops import DesktopGitOps


class FakeCompletedProcess:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_preview_app_config_returns_empty_message_when_no_diff(tmp_path):
    calls = []

    def fake_run(command, cwd, text, capture_output, check):
        calls.append(command)
        return FakeCompletedProcess(stdout="")

    git_ops = DesktopGitOps(repo_root=tmp_path, run_command=fake_run)

    result = git_ops.preview_app_config()

    assert result == "没有可推送的配置变更"
    assert calls[0] == ["git", "diff", "--", "code/config/gui/daily_report.yml"]


def test_commit_and_push_only_stages_gui_config(tmp_path):
    calls = []

    def fake_run(command, cwd, text, capture_output, check):
        calls.append(command)
        if command[:4] == ["git", "diff", "--cached", "--name-only"]:
            return FakeCompletedProcess(stdout="code/config/gui/daily_report.yml\n")
        return FakeCompletedProcess(stdout="ok")

    git_ops = DesktopGitOps(repo_root=tmp_path, run_command=fake_run)
    message = git_ops.commit_and_push_app_config("Update tracked symbols")

    assert message == "配置已提交并推送"
    assert ["git", "add", "--", "code/config/gui/daily_report.yml"] in calls
    assert ["git", "push"] in calls
    assert ["git", "add", "--", ".env"] not in calls
