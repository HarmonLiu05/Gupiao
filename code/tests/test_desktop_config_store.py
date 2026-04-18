from polybot.desktop.config_store import DesktopConfigStore


def test_load_or_create_copies_example_config(tmp_path):
    example = tmp_path / "daily_report.example.yml"
    example.write_text(
        "timezone: Asia/Shanghai\n"
        "report_title: 美股收盘日报\n"
        "symbols:\n"
        "  - QQQ\n"
        "mail:\n"
        "  subject_prefix: 美股收盘日报\n",
        encoding="utf-8",
    )
    target = tmp_path / "gui" / "daily_report.yml"
    store = DesktopConfigStore(gui_config_path=target, example_config_path=example)

    config = store.load_or_create()

    assert target.exists()
    assert config.symbols == ["QQQ"]
    assert config.timezone == "Asia/Shanghai"


def test_save_symbols_preserves_non_symbol_fields(tmp_path):
    example = tmp_path / "daily_report.example.yml"
    example.write_text(
        "timezone: Asia/Shanghai\n"
        "report_title: 美股收盘日报\n"
        "symbols:\n"
        "  - QQQ\n"
        "mail:\n"
        "  subject_prefix: 美股收盘日报\n"
        "indicators:\n"
        "  lookback_period: 1y\n",
        encoding="utf-8",
    )
    target = tmp_path / "gui" / "daily_report.yml"
    store = DesktopConfigStore(gui_config_path=target, example_config_path=example)
    store.load_or_create()

    store.save_symbols(["AAPL", "MSFT"])
    updated = store.load_or_create()

    assert updated.symbols == ["AAPL", "MSFT"]
    assert updated.mail["subject_prefix"] == "美股收盘日报"
    assert updated.indicators["lookback_period"] == "1y"
