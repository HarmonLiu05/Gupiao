# GitHub Actions 美股收盘日报邮件实现计划

> **给 agent 执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步执行。本计划使用 checkbox（`- [ ]`）记录进度。

**目标：** 实现一个只读美股收盘日报系统，每个美股交易日后的北京时间上午 10:00 通过 GitHub Actions 运行，并用 QQ 邮箱 SMTP 给用户发送 QQQ、NVDA、TSM、BABA 的收盘日报。

**架构：** 继续使用现有 `polybot` Python 包。新增日报配置、技术指标计算、邮件渲染、SMTP 发送和 GitHub Actions workflow；行情数据仍使用已有 `YahooMarketDataClient` / `yfinance`，所有功能只读，不接券商、不下单、不读取钱包或私钥。

**技术栈：** Python 3.12、Typer、Pydantic、Pandas、`yfinance`、PyYAML、SMTP SSL、GitHub Actions、Pytest、Ruff。

---

## 需求确认

本计划按以下需求实现：

- 每天都发送日报，不要求触发阈值才发送。
- 发送时间：北京时间上午 10:00。
- 覆盖美股交易日收盘数据。由于美股周五收盘对应北京时间周六凌晨，GitHub Actions 使用北京时间周二到周六上午 10:00，即 UTC 周二到周六 02:00。
- 监控标的：
  - `QQQ`
  - `NVDA`
  - `TSM`，台积电美股 ADR
  - `BABA`，阿里巴巴美股 ADR
- 报告字段：
  - 收盘价
  - 日涨跌幅百分比
  - 价格相对 20 日均线偏离百分比
  - 价格相对 50 日均线偏离百分比
  - 距离 52 周高点百分比
  - 距离 52 周低点百分比
- 不需要成交量字段。
- 邮件发送：QQ 邮箱 SMTP。GitHub Secrets 中保存 QQ SMTP 授权码，不使用 QQ 登录密码。
- 暂时不做期权，不做价格阈值提醒，不做实时盯盘。

## GitHub Actions 限制

- GitHub Actions `schedule` 最短间隔为 5 分钟，但本需求只需每天一次。
- 定时任务可能延迟或在 GitHub 高负载时被跳过，不能作为实时交易提醒系统。
- Scheduled workflow 只在默认分支运行。
- 邮箱账号和授权码必须放在 GitHub Secrets，不能写入仓库。

参考：

- https://docs.github.com/actions/using-workflows/events-that-trigger-workflows
- https://docs.github.com/actions/security-guides/encrypted-secrets

## 文件结构

- 修改：`code/pyproject.toml` - 增加 `PyYAML` 依赖。
- 创建：`code/config/daily_report.example.yml` - 日报配置示例。
- 创建：`code/src/polybot/reports/__init__.py` - reports 包标记。
- 创建：`code/src/polybot/reports/daily_stock.py` - 技术指标计算和日报数据模型。
- 创建：`code/src/polybot/reports/email_renderer.py` - 纯文本邮件渲染。
- 创建：`code/src/polybot/notifications/__init__.py` - notifications 包标记。
- 创建：`code/src/polybot/notifications/emailer.py` - QQ SMTP 邮件发送。
- 修改：`code/src/polybot/cli.py` - 新增 `daily-report` 命令。
- 创建：`code/.github/workflows/us-stock-daily-report.yml` - GitHub Actions 定时任务。
- 修改：`code/README.md` - 增加部署和 Secrets 说明。
- 创建：`code/tests/test_daily_stock_report.py` - 指标和报告模型测试。
- 创建：`code/tests/test_email_renderer.py` - 邮件文本测试。
- 创建：`code/tests/test_emailer.py` - SMTP 调用测试。
- 修改：`code/tests/test_cli.py` - CLI 新命令测试。

---

### 任务 1：确认基线

**文件：**
- 查看：`code/pyproject.toml`
- 查看：`code/src/polybot/cli.py`
- 查看：`code/src/polybot/clients/yahoo_market_data.py`

- [ ] **步骤 1：进入代码目录**

运行：

```bash
cd E:\4.17_coding\code
```

期望：当前目录为 `E:\4.17_coding\code`。

- [ ] **步骤 2：确认 Python 版本**

运行：

```bash
py -3.12 --version
```

期望：输出 `Python 3.12.x`。

- [ ] **步骤 3：运行基线验证**

运行：

```bash
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m ruff check .
py -3.12 -m pytest -v --basetemp .pytest_tmp
```

期望：Ruff 通过，pytest 全部通过。若失败，先修复基线，不要开始新增功能。

---

### 任务 2：新增日报配置文件

**文件：**
- 修改：`code/pyproject.toml`
- 创建：`code/config/daily_report.example.yml`

- [ ] **步骤 1：增加 YAML 依赖**

在 `code/pyproject.toml` 的 dependencies 中加入：

```toml
"PyYAML>=6.0.2",
```

- [ ] **步骤 2：创建配置示例**

创建 `code/config/daily_report.example.yml`：

```yaml
timezone: Asia/Shanghai
report_title: 美股收盘日报
symbols:
  - QQQ
  - NVDA
  - TSM
  - BABA

mail:
  subject_prefix: 美股收盘日报

indicators:
  moving_average_windows:
    - 20
    - 50
  lookback_period: 1y
```

- [ ] **步骤 3：安装并验证依赖**

运行：

```bash
py -3.12 -m pip install -e ".[dev]"
```

期望：安装成功。

---

### 任务 3：实现日报数据模型和技术指标

**文件：**
- 创建：`code/src/polybot/reports/__init__.py`
- 创建：`code/src/polybot/reports/daily_stock.py`
- 创建：`code/tests/test_daily_stock_report.py`

- [ ] **步骤 1：先写指标测试**

创建 `code/tests/test_daily_stock_report.py`，写入以下测试结构：

```python
from decimal import Decimal

import pandas as pd

from polybot.reports.daily_stock import build_stock_report_row, percent_change


def test_percent_change_returns_decimal_percent():
    result = percent_change(Decimal("110"), Decimal("100"))

    assert result == Decimal("10.00")


def test_build_stock_report_row_calculates_required_percentages():
    history = pd.DataFrame(
        {
            "Close": [float(100 + i) for i in range(260)],
        }
    )

    row = build_stock_report_row("QQQ", history)

    assert row.symbol == "QQQ"
    assert row.close == Decimal("359.00")
    assert row.daily_change_pct is not None
    assert row.vs_ma20_pct is not None
    assert row.vs_ma50_pct is not None
    assert row.from_52w_high_pct == Decimal("0.00")
    assert row.from_52w_low_pct is not None
```

- [ ] **步骤 2：运行测试确认失败**

运行：

```bash
py -3.12 -m pytest tests/test_daily_stock_report.py -v --basetemp .pytest_tmp
```

期望：因 `polybot.reports.daily_stock` 不存在而失败。

- [ ] **步骤 3：实现数据模型**

在 `daily_stock.py` 中定义：

```python
class StockReportRow(BaseModel):
    symbol: str
    close: Decimal
    previous_close: Decimal | None = None
    daily_change_pct: Decimal | None = None
    ma20: Decimal | None = None
    ma50: Decimal | None = None
    vs_ma20_pct: Decimal | None = None
    vs_ma50_pct: Decimal | None = None
    high_52w: Decimal | None = None
    low_52w: Decimal | None = None
    from_52w_high_pct: Decimal | None = None
    from_52w_low_pct: Decimal | None = None
```

百分比定义：

- `daily_change_pct = (close - previous_close) / previous_close * 100`
- `vs_ma20_pct = (close - ma20) / ma20 * 100`
- `vs_ma50_pct = (close - ma50) / ma50 * 100`
- `from_52w_high_pct = (close - high_52w) / high_52w * 100`
- `from_52w_low_pct = (close - low_52w) / low_52w * 100`

所有百分比保留两位小数，类型为 `Decimal`。

- [ ] **步骤 4：实现历史数据转报告行**

实现：

```python
def build_stock_report_row(symbol: str, history: pd.DataFrame) -> StockReportRow:
    ...
```

要求：

- 使用 `Close` 列。
- 去掉空值。
- 少于 2 个收盘价时抛出 `ValueError("not enough close prices for SYMBOL")`。
- MA20 需要至少 20 个收盘价；不足时为 `None`。
- MA50 需要至少 50 个收盘价；不足时为 `None`。
- 52 周高低点使用输入历史的最大/最小收盘价。

- [ ] **步骤 5：验证**

运行：

```bash
py -3.12 -m pytest tests/test_daily_stock_report.py -v --basetemp .pytest_tmp
```

期望：测试通过。

---

### 任务 4：获取历史行情并生成完整日报

**文件：**
- 修改：`code/src/polybot/reports/daily_stock.py`
- 修改：`code/tests/test_daily_stock_report.py`

- [ ] **步骤 1：写服务层测试**

在 `test_daily_stock_report.py` 增加 fake market data client：

```python
class FakeHistoryClient:
    def get_history(self, symbol: str, period: str = "1y"):
        return pd.DataFrame({"Close": [float(100 + i) for i in range(260)]})


def test_build_daily_stock_report_returns_rows_for_symbols():
    report = build_daily_stock_report(
        symbols=["QQQ", "NVDA"],
        history_client=FakeHistoryClient(),
        lookback_period="1y",
    )

    assert [row.symbol for row in report.rows] == ["QQQ", "NVDA"]
```

- [ ] **步骤 2：实现历史行情方法**

若 `YahooMarketDataClient` 尚无历史行情方法，在 `code/src/polybot/clients/yahoo_market_data.py` 增加：

```python
def get_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
    ticker = self._ticker_factory(symbol.upper())
    return ticker.history(period=period)
```

如果已有类似方法，复用现有方法，不重复实现。

- [ ] **步骤 3：实现完整报告模型**

在 `daily_stock.py` 中定义：

```python
class DailyStockReport(BaseModel):
    title: str = "美股收盘日报"
    generated_at: datetime
    timezone: str
    rows: list[StockReportRow]
    errors: list[str] = Field(default_factory=list)
```

实现：

```python
def build_daily_stock_report(
    symbols: list[str],
    history_client: Any,
    lookback_period: str = "1y",
    timezone: str = "Asia/Shanghai",
) -> DailyStockReport:
    ...
```

要求：

- 每个 symbol 单独拉取历史。
- 单个 symbol 失败时记录到 `errors`，不要让整个报告失败。
- 成功的 symbol 按配置顺序输出。
- `generated_at` 使用 timezone-aware datetime。

- [ ] **步骤 4：验证**

运行：

```bash
py -3.12 -m pytest tests/test_daily_stock_report.py -v --basetemp .pytest_tmp
```

期望：测试通过。

---

### 任务 5：渲染纯文本邮件

**文件：**
- 创建：`code/src/polybot/reports/email_renderer.py`
- 创建：`code/tests/test_email_renderer.py`

- [ ] **步骤 1：写邮件渲染测试**

创建 `code/tests/test_email_renderer.py`：

```python
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from polybot.reports.daily_stock import DailyStockReport, StockReportRow
from polybot.reports.email_renderer import render_daily_stock_email


def test_render_daily_stock_email_contains_required_fields():
    report = DailyStockReport(
        generated_at=datetime(2026, 4, 18, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai")),
        timezone="Asia/Shanghai",
        rows=[
            StockReportRow(
                symbol="QQQ",
                close=Decimal("500.00"),
                daily_change_pct=Decimal("1.25"),
                vs_ma20_pct=Decimal("2.30"),
                vs_ma50_pct=Decimal("4.10"),
                from_52w_high_pct=Decimal("-3.50"),
                from_52w_low_pct=Decimal("28.00"),
            )
        ],
    )

    subject, body = render_daily_stock_email(report)

    assert "美股收盘日报" in subject
    assert "QQQ" in body
    assert "日涨跌幅" in body
    assert "MA20偏离" in body
    assert "MA50偏离" in body
    assert "距52周高点" in body
    assert "距52周低点" in body
    assert "成交量" not in body
```

- [ ] **步骤 2：运行测试确认失败**

运行：

```bash
py -3.12 -m pytest tests/test_email_renderer.py -v --basetemp .pytest_tmp
```

期望：因模块不存在而失败。

- [ ] **步骤 3：实现邮件渲染**

邮件正文结构：

```text
美股收盘日报
生成时间：2026-04-18 10:00 Asia/Shanghai

一、概览
Symbol | Close | 日涨跌幅 | MA20偏离 | MA50偏离 | 距52周高点 | 距52周低点
QQQ    | 500.00 | +1.25% | +2.30% | +4.10% | -3.50% | +28.00%

二、数据异常
无

三、数据说明
数据源：Yahoo Finance / yfinance
用途：个人观察，不是交易级实时行情
本邮件由 GitHub Actions 自动发送
```

格式要求：

- 正数百分比加 `+`，负数保留 `-`。
- `None` 显示为 `N/A`。
- 不包含成交量。
- subject 形如：`美股收盘日报 2026-04-18`。

- [ ] **步骤 4：验证**

运行：

```bash
py -3.12 -m pytest tests/test_email_renderer.py -v --basetemp .pytest_tmp
```

期望：测试通过。

---

### 任务 6：实现 QQ 邮箱 SMTP 发送

**文件：**
- 创建：`code/src/polybot/notifications/__init__.py`
- 创建：`code/src/polybot/notifications/emailer.py`
- 创建：`code/tests/test_emailer.py`

- [ ] **步骤 1：写 SMTP 测试**

创建 `code/tests/test_emailer.py`：

```python
from polybot.notifications.emailer import SmtpEmailConfig, send_email


class FakeSMTP:
    sent_messages = []

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def login(self, user, password):
        self.user = user
        self.password = password

    def send_message(self, message):
        self.sent_messages.append(message)


def test_send_email_uses_smtp_ssl(monkeypatch):
    monkeypatch.setattr("polybot.notifications.emailer.smtplib.SMTP_SSL", FakeSMTP)
    FakeSMTP.sent_messages.clear()

    config = SmtpEmailConfig(
        host="smtp.qq.com",
        port=465,
        username="sender@qq.com",
        auth_code="auth-code",
        to_address="receiver@example.com",
    )

    send_email(config, subject="hello", body="body")

    assert len(FakeSMTP.sent_messages) == 1
    assert FakeSMTP.sent_messages[0]["Subject"] == "hello"
```

- [ ] **步骤 2：实现 emailer**

定义：

```python
class SmtpEmailConfig(BaseModel):
    host: str = "smtp.qq.com"
    port: int = 465
    username: str
    auth_code: str
    to_address: str
    from_name: str = "US Stock Daily Report"
```

实现：

```python
def send_email(config: SmtpEmailConfig, subject: str, body: str) -> None:
    ...
```

要求：

- 使用 `smtplib.SMTP_SSL(config.host, config.port)`。
- 使用 QQ 邮箱授权码登录，不使用 QQ 登录密码。
- 邮件编码为 UTF-8。
- 不打印 `auth_code`。

- [ ] **步骤 3：验证**

运行：

```bash
py -3.12 -m pytest tests/test_emailer.py -v --basetemp .pytest_tmp
```

期望：测试通过。

---

### 任务 7：新增 daily-report CLI 命令

**文件：**
- 修改：`code/src/polybot/cli.py`
- 修改：`code/tests/test_cli.py`

- [ ] **步骤 1：写 CLI 测试**

在 `code/tests/test_cli.py` 增加测试：

```python
def test_daily_report_dry_run_prints_email(monkeypatch, tmp_path):
    config = tmp_path / "daily_report.yml"
    config.write_text(
        "timezone: Asia/Shanghai\n"
        "symbols:\n"
        "  - QQQ\n"
        "mail:\n"
        "  subject_prefix: 美股收盘日报\n"
        "indicators:\n"
        "  lookback_period: 1y\n",
        encoding="utf-8",
    )

    class FakeClient:
        def get_history(self, symbol, period="1y"):
            import pandas as pd
            return pd.DataFrame({"Close": [float(100 + i) for i in range(260)]})

    monkeypatch.setattr("polybot.cli.YahooMarketDataClient", FakeClient)

    result = CliRunner().invoke(app, ["daily-report", "--config", str(config), "--dry-run"])

    assert result.exit_code == 0
    assert "美股收盘日报" in result.output
    assert "QQQ" in result.output
```

再增加缺少邮件环境变量时的测试：

```python
def test_daily_report_send_requires_email_env(tmp_path):
    config = tmp_path / "daily_report.yml"
    config.write_text("symbols:\n  - QQQ\n", encoding="utf-8")

    result = CliRunner().invoke(app, ["daily-report", "--config", str(config)])

    assert result.exit_code == 2
    assert "QQ_SMTP_USER" in result.output
```

- [ ] **步骤 2：实现配置读取**

在 `cli.py` 或新的 helper 中读取 YAML：

```python
with path.open("r", encoding="utf-8") as file:
    config = yaml.safe_load(file) or {}
```

默认值：

- `timezone`: `Asia/Shanghai`
- `symbols`: `["QQQ", "NVDA", "TSM", "BABA"]`
- `lookback_period`: `1y`

- [ ] **步骤 3：实现命令**

新增命令：

```bash
py -3.12 -m polybot daily-report --config config/daily_report.example.yml --dry-run
py -3.12 -m polybot daily-report --config config/daily_report.example.yml
```

行为：

- `--dry-run`：只打印 subject 和 body，不发邮件。
- 非 dry-run：读取环境变量并发送邮件。

邮件环境变量：

```text
QQ_SMTP_USER
QQ_SMTP_AUTH_CODE
ALERT_EMAIL_TO
```

可选环境变量：

```text
QQ_SMTP_HOST=smtp.qq.com
QQ_SMTP_PORT=465
```

缺少必需环境变量时，退出码为 `2`，输出明确缺少哪个变量。

- [ ] **步骤 4：验证**

运行：

```bash
py -3.12 -m pytest tests/test_cli.py -v --basetemp .pytest_tmp
```

期望：测试通过。

---

### 任务 8：新增 GitHub Actions workflow

**文件：**
- 创建：`code/.github/workflows/us-stock-daily-report.yml`

- [ ] **步骤 1：创建 workflow**

创建文件：

```yaml
name: US Stock Daily Report

on:
  schedule:
    - cron: "0 2 * * 2-6"
  workflow_dispatch:

jobs:
  send-report:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install package
        working-directory: code
        run: python -m pip install -e ".[dev]"

      - name: Run tests for report modules
        working-directory: code
        run: |
          python -m ruff check .
          python -m pytest tests/test_daily_stock_report.py tests/test_email_renderer.py tests/test_emailer.py tests/test_cli.py -v

      - name: Send daily report
        working-directory: code
        env:
          QQ_SMTP_USER: ${{ secrets.QQ_SMTP_USER }}
          QQ_SMTP_AUTH_CODE: ${{ secrets.QQ_SMTP_AUTH_CODE }}
          ALERT_EMAIL_TO: ${{ secrets.ALERT_EMAIL_TO }}
        run: python -m polybot daily-report --config config/daily_report.example.yml
```

说明：

- `cron: "0 2 * * 2-6"` 表示 UTC 周二到周六 02:00，即北京时间周二到周六 10:00。
- 覆盖美股周一到周五收盘后的北京时间上午日报。
- `workflow_dispatch` 允许在 GitHub 页面手动触发。

- [ ] **步骤 2：验证 YAML 文件存在**

运行：

```bash
Test-Path .github\workflows\us-stock-daily-report.yml
```

期望：输出 `True`。

---

### 任务 9：更新 README 部署说明

**文件：**
- 修改：`code/README.md`

- [ ] **步骤 1：新增“每日邮件日报”说明**

加入：

```markdown
## 每日美股收盘邮件日报

日报默认监控 `QQQ`、`NVDA`、`TSM`、`BABA`，字段包括收盘价、日涨跌幅、相对 MA20/MA50 偏离、距离 52 周高低点百分比，不包含成交量。

本地预览：

```bash
py -3.12 -m polybot daily-report --config config/daily_report.example.yml --dry-run
```

本地发送测试：

```bash
$env:QQ_SMTP_USER="你的QQ邮箱@qq.com"
$env:QQ_SMTP_AUTH_CODE="QQ邮箱SMTP授权码"
$env:ALERT_EMAIL_TO="收件邮箱"
py -3.12 -m polybot daily-report --config config/daily_report.example.yml
```
```

- [ ] **步骤 2：新增 GitHub Secrets 说明**

写明在 GitHub 仓库中配置：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

需要添加：

```text
QQ_SMTP_USER
QQ_SMTP_AUTH_CODE
ALERT_EMAIL_TO
```

说明 `QQ_SMTP_AUTH_CODE` 是 QQ 邮箱设置中生成的 SMTP 授权码，不是 QQ 登录密码。

- [ ] **步骤 3：新增定时说明**

说明：

- workflow 文件：`.github/workflows/us-stock-daily-report.yml`
- 运行时间：北京时间周二到周六上午 10:00
- 原因：覆盖美股周一到周五收盘后的日报
- GitHub Actions 可能延迟，不保证精确到秒

---

### 任务 10：最终验证

**文件：**
- 不修改文件，只运行命令并记录结果。

- [ ] **步骤 1：本地 dry-run**

运行：

```bash
py -3.12 -m polybot daily-report --config config/daily_report.example.yml --dry-run
```

期望：

- 输出 subject 和 body。
- body 包含 `QQQ`、`NVDA`、`TSM`、`BABA`。
- body 包含 `日涨跌幅`、`MA20偏离`、`MA50偏离`、`距52周高点`、`距52周低点`。
- body 不包含 `成交量`。

- [ ] **步骤 2：运行静态检查**

```bash
py -3.12 -m ruff check .
```

期望：`All checks passed!`

- [ ] **步骤 3：运行全量测试**

```bash
py -3.12 -m pytest -v --basetemp .pytest_tmp
```

期望：全部测试通过。

- [ ] **步骤 4：检查敏感信息**

运行：

```bash
Select-String -Path . -Pattern "QQ_SMTP_AUTH_CODE=|smtp授权码|真实授权码|PRIVATE_KEY|PASSWORD" -Recurse
```

期望：没有真实密钥。README 中可以出现变量名和说明文字，但不能出现真实授权码。

- [ ] **步骤 5：检查 diff 范围**

运行：

```bash
git diff -- code/pyproject.toml code/config/daily_report.example.yml code/src/polybot/reports code/src/polybot/notifications code/src/polybot/cli.py code/.github/workflows/us-stock-daily-report.yml code/README.md code/tests
```

期望：只包含日报、邮件、GitHub Actions 和测试相关改动，不包含交易下单、钱包、私钥或 Polymarket live trading 改动。

---

## GitHub 部署步骤

执行窗口完成代码后，需要把项目推送到 GitHub，并配置 GitHub Actions 所需的 Secrets。真实密钥不要写进聊天、代码、README、测试或日志。

### 方案 A：用户在 GitHub 网页手动配置 Secrets（推荐）

用户需要准备：

- GitHub 仓库地址，例如 `https://github.com/<owner>/<repo>`
- QQ 邮箱地址，例如 `123456@qq.com`
- QQ 邮箱 SMTP 授权码
- 接收日报的邮箱地址，可以和 QQ 发件邮箱相同

QQ 邮箱授权码获取方式：

1. 登录 QQ 邮箱网页版。
2. 进入 `设置`。
3. 找到 `账户` / `POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务`。
4. 开启 `SMTP` 或 `POP3/SMTP` 服务。
5. 按 QQ 邮箱提示完成验证，生成 SMTP 授权码。
6. 复制授权码，后续只填入 GitHub Secrets，不要发给任何 AI。

在 GitHub 仓库中配置：

```text
Settings -> Secrets and variables -> Actions -> New repository secret
```

需要添加：

```text
QQ_SMTP_USER=你的QQ邮箱@qq.com
QQ_SMTP_AUTH_CODE=QQ邮箱SMTP授权码
ALERT_EMAIL_TO=接收日报的邮箱
```

### 方案 B：执行窗口用 GitHub CLI 配置 Secrets

只有在用户明确允许执行窗口操作 GitHub，并且本机已登录 `gh` 时使用。执行窗口不能让用户把授权码发到聊天里。

执行窗口应先检查：

```bash
gh auth status
git remote -v
```

如果仓库 remote 已指向正确 GitHub 仓库，可以让用户在本机终端交互输入 secret：

```bash
gh secret set QQ_SMTP_USER
gh secret set QQ_SMTP_AUTH_CODE
gh secret set ALERT_EMAIL_TO
```

注意：

- `gh secret set` 会从终端读取输入，不应把 secret 写入命令行参数。
- 不要把 secret echo 到日志。
- 不要把 secret 写入 `.env` 后提交。
- 如果 `gh auth status` 未登录，执行窗口只提示用户登录，不要代替用户处理授权码。

### 推送和启用 workflow

执行窗口需要完成：

1. 确认 `.github/workflows/us-stock-daily-report.yml` 已提交。
2. 推送到 GitHub 默认分支，或开 PR 合并到默认分支。
3. 确认 workflow 在默认分支存在，因为 scheduled workflow 只在默认分支运行。
4. 在 GitHub Actions 页面手动运行一次 `US Stock Daily Report`。
5. 检查运行日志，不允许日志中出现 `QQ_SMTP_AUTH_CODE` 的真实值。
6. 确认用户邮箱收到日报。

部署后验证：

1. 推送到默认分支。
2. 打开 GitHub 仓库的 Actions 页面。
3. 选择 `US Stock Daily Report` workflow。
4. 点击 `Run workflow` 手动触发一次。
5. 确认邮箱收到日报。
6. 再等待北京时间周二到周六上午 10:00 的自动运行。

## 交接说明

- 只做股票日报，不做期权。
- 只读行情，不做交易。
- 阿里巴巴使用美股 ADR：`BABA`。
- 台积电使用美股 ADR：`TSM`。
- 不要在报告里加入成交量字段。
- 不要把 QQ 邮箱授权码写入代码、README、测试或日志。
- 如果需要 GitHub 插件或 `gh` 操作，只能处理仓库、PR、workflow 和 Actions 日志；Secrets 的真实值必须由用户在 GitHub 网页或本机终端交互输入。
- 完成后把执行反馈写入 `E:\4.17_coding\feddback\plan4-feedback.md`。

## 用户需要提供什么

用户需要提供给执行窗口的信息只有这些非敏感内容：

```text
GitHub 仓库地址：<owner>/<repo> 或完整 URL
发件 QQ 邮箱：例如 123456@qq.com
收件邮箱：例如 123456@qq.com 或其他邮箱
是否允许执行窗口 push/开 PR：是/否
```

用户不要提供到聊天里的敏感内容：

```text
QQ_SMTP_AUTH_CODE
QQ 登录密码
任何邮箱密码
任何 GitHub token
```

`QQ_SMTP_AUTH_CODE` 应由用户自己填入 GitHub Secrets，或在本机通过 `gh secret set QQ_SMTP_AUTH_CODE` 交互输入。
