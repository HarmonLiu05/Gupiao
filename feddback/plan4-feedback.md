# plan4 执行反馈：GitHub Actions 美股收盘日报邮件

## 计划信息

- 计划文件：`E:\4.17_coding\plan\plan4.md`
- 执行日期：2026-04-17
- 代码目录：`E:\4.17_coding\code`
- 范围：新增只读美股收盘日报、技术指标、纯文本邮件渲染、QQ SMTP 发送、GitHub Actions 定时 workflow、CLI dry-run/发送命令和中文 README。

## 执行前评审

- 需求清晰度：清楚。计划明确要求每天发送 QQQ、NVDA、TSM、BABA 的美股收盘日报，字段限定为价格和技术指标，不包含成交量。
- 关键假设：
  - 日报仍使用已有 `YahooMarketDataClient` / `yfinance` 作为只读行情源。
  - GitHub Actions 定时任务使用 UTC 周二到周六 02:00，对应北京时间周二到周六 10:00。
  - QQ SMTP 授权码只能通过 GitHub Secrets 或本机交互输入，不能写入代码、README、测试、日志或聊天。
  - 当前没有 GitHub 远端仓库地址和是否允许 push/开 PR 的信息，因此本轮先完成本地实现和提交。
- 风险点：
  - 不能新增交易、券商下单、钱包、私钥或 Polymarket live trading 相关改动。
  - 邮件发送测试必须 mock SMTP，不能真实发送。
  - 真实 dry-run 依赖 Yahoo 数据源，可能受网络或数据源限制影响。
  - README 可以出现环境变量名和授权码说明，但不能出现真实密钥。
- 验证方式：
  - 先跑基线安装、Ruff 和 pytest。
  - 按 TDD 先写日报指标、邮件渲染、SMTP 和 CLI 测试，再实现。
  - 最终运行 dry-run、Ruff、全量 pytest、敏感信息扫描和限定 diff 检查。
- 执行决定：计划可执行。本轮执行本地代码、workflow、文档、测试和 commit；GitHub push、Secrets 配置和手动触发 workflow 需要用户后续提供仓库地址和授权。

## 执行记录

- 已修改内容：
  - 在 `code/pyproject.toml` 增加 `PyYAML>=6.0.2`，用于读取日报 YAML 配置。
  - 新增 `code/config/daily_report.example.yml`，默认观察 `QQQ`、`NVDA`、`TSM`、`BABA`。
  - 新增 `code/src/polybot/reports/daily_stock.py` 和 `email_renderer.py`，实现只读日线数据日报、涨跌幅、MA20/MA50、52 周高低点偏离和纯文本邮件渲染。
  - 新增 `code/src/polybot/notifications/emailer.py`，通过 `smtplib.SMTP_SSL` 发送 UTF-8 邮件，测试中使用 mock SMTP。
  - 在 `code/src/polybot/clients/yahoo_market_data.py` 增加 `get_history()`，复用已有 yfinance 客户端。
  - 在 `code/src/polybot/cli.py` 增加 `daily-report` 命令，支持 `--config` 和 `--dry-run`。非 dry-run 会先检查 `QQ_SMTP_USER`、`QQ_SMTP_AUTH_CODE`、`ALERT_EMAIL_TO`，缺失时退出，不先拉行情。
  - 新增 GitHub Actions workflow：`.github/workflows/us-stock-daily-report.yml`。计划里写的是 `code/.github/workflows`，但 GitHub Actions 只识别仓库根目录 `.github/workflows`，所以按可运行部署路径创建；workflow 内部仍然使用 `working-directory: code`。
  - 更新 `code/README.md`，补充中文的日报 dry-run、本地发送、GitHub Secrets、北京时间周二到周六 10:00 定时说明。
  - 新增测试：`code/tests/test_daily_stock_report.py`、`code/tests/test_email_renderer.py`、`code/tests/test_emailer.py`，并更新 `code/tests/test_cli.py`。
- 已运行命令：
  - `py -3.12 --version`：Python 3.12.3。
  - `py -3.12 -m pip install -e ".[dev]"`：成功安装本地包和开发依赖。
  - `py -3.12 -m ruff check .`：基线通过，最终再次通过。
  - `py -3.12 -m pytest -v --basetemp .pytest_tmp`：基线 44 个测试通过；最终 52 个测试通过。
  - `py -3.12 -m pytest tests/test_daily_stock_report.py -v --basetemp .pytest_tmp`：4 个测试通过。
  - `py -3.12 -m pytest tests/test_email_renderer.py tests/test_emailer.py -v --basetemp .pytest_tmp`：2 个测试通过。
  - `py -3.12 -m pytest tests/test_cli.py -v --basetemp .pytest_tmp`：17 个测试通过。
  - `py -3.12 -m polybot daily-report --config config/daily_report.example.yml --dry-run`：成功拉取真实行情并生成邮件预览，包含 QQQ、NVDA、TSM、BABA，不包含成交量。
  - `Select-String -Path . -Pattern "QQ_SMTP_AUTH_CODE=|smtp授权码|真实授权码|PRIVATE_KEY|PASSWORD" -Recurse`：当前 Windows PowerShell 不支持 `Select-String -Recurse`，命令参数报错。
  - `Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\\.git\\|\\.pytest_cache\\|\\.pytest_tmp\\|\\__pycache__\\' } | Select-String -Pattern 'QQ_SMTP_AUTH_CODE=|smtp授权码|真实授权码|PRIVATE_KEY|PASSWORD'`：发现既有 Polymarket 私钥变量名、测试中的 `password` 参数名，以及 `plan/plan4.md` 的占位示例；未发现真实密钥。
  - `Get-ChildItem -Recurse -File .github,code\config,code\src\polybot\reports,code\src\polybot\notifications | Select-String -Pattern 'QQ_SMTP_AUTH_CODE=|smtp授权码|真实授权码|PRIVATE_KEY|PASSWORD'`：无输出，新增日报核心文件未写入敏感值。
- 结果：
  - plan4 的本地实现、测试、README 和 workflow 已完成。
  - 代码保持只读行情和邮件通知，不新增交易、券商、钱包或私钥读取逻辑。
  - GitHub push、GitHub Secrets 配置和手动触发 workflow 仍需用户提供仓库远端和授权后再执行。
