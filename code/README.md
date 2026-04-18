# Polybot

Polybot 是一个以 paper trading 为默认模式的 Polymarket 交易系统骨架。它用于市场发现、策略信号生成、风控、回测和模拟执行。

本项目不是投资建议，也不承诺收益。真实交易默认关闭，只有合规、钱包、授权、余额、allowance 和风控门槛全部通过时才允许 live mode。

## 安装

```bash
python -m pip install -e ".[dev]"
```

## 常用命令

```bash
py -3.12 -m polybot geocheck
py -3.12 -m polybot markets --query "fed"
py -3.12 -m polybot quote AAPL
py -3.12 -m polybot quotes AAPL,MSFT,NVDA --output table
py -3.12 -m polybot expirations AAPL
py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230
py -3.12 -m polybot paper-run --markets config/markets.example.json --fair-values config/fair_values.example.csv
py -3.12 -m polybot live-run --markets config/markets.example.json --fair-values config/fair_values.example.csv
py -3.12 -m polybot cancel-all --market <condition_id>
```

## 美股行情查询

本项目提供只读美股行情命令，不会下单，也不会读取钱包私钥。

查看股票报价：

```bash
py -3.12 -m polybot quote AAPL
```

批量查看股票报价：

```bash
py -3.12 -m polybot quotes AAPL,MSFT,NVDA --output table
py -3.12 -m polybot quotes --file config/watchlist.example.txt --output csv
```

`config/watchlist.example.txt` 每行一个 symbol，允许空行和以 `#` 开头的注释行。

查看某个 symbol 的可用期权到期日：

```bash
py -3.12 -m polybot expirations AAPL
```

查看期权链：

```bash
py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230
```

指定到期日并同时查看 calls 和 puts：

```bash
py -3.12 -m polybot options TSLA --expiration 2026-05-15 --side both
```

行情命令的 `--output` 支持 `table`、`json`、`csv`。默认是 tab 分隔的 `table`，便于直接在终端查看；`json` 和 `csv` 更适合交给其他脚本继续处理。

`yfinance` 适合个人研究和低频观察。它不是官方交易级实时行情源，不建议用于真实交易决策。股票日线、延迟报价和低频观察通常有免费方案；美股期权链可以免费拉取部分字段，但完整、稳定、实时的 OPRA 期权报价通常需要付费。免费源返回的 `bid` / `ask` 可能为空或为 `0.0`。

若需要稳定、完整、实时的美股和 OPRA 期权行情，应评估 Polygon.io、Alpaca、Tradier 等付费或半付费数据源。商业使用、转发数据、自动交易前必须确认数据授权、交易所授权和供应商条款。

## 每日美股收盘邮件日报

`daily-report` 是只读日报命令，默认读取 `QQQ`、`NVDA`、`TSM`、`BABA` 的日线数据，生成纯文本邮件，并在发送时附带一张 PNG 表格图片。内容包含最新收盘价、日涨跌幅、20 日均线、50 日均线、52 周高低点和数据源说明，不包含成交量，不会交易、下单或读取任何钱包信息。

本地预览邮件正文：

```bash
py -3.12 -m polybot daily-report --config config/daily_report.example.yml --dry-run
```

本地发送邮件前，需要在当前 shell 设置这些环境变量：

```powershell
$env:QQ_SMTP_USER = "<QQ 邮箱地址>"
$env:QQ_SMTP_AUTH_CODE = "<QQ 邮箱 SMTP 授权码>"
$env:ALERT_EMAIL_TO = "<收件邮箱地址>"
py -3.12 -m polybot daily-report --config config/daily_report.example.yml
```

GitHub Actions 定时任务位于仓库根目录 `.github/workflows/us-stock-daily-report.yml`。cron 为 `0 2 * * 2-6`，对应北京时间周二到周六 10:00，用于覆盖美股交易日收盘后的日报发送。

启用 GitHub Actions 发送邮件前，在仓库 `Settings -> Secrets and variables -> Actions` 添加以下 Secrets：

- `QQ_SMTP_USER`
- `QQ_SMTP_AUTH_CODE`
- `ALERT_EMAIL_TO`

可选 Secrets 或环境变量：

- `QQ_SMTP_HOST`：默认 `smtp.qq.com`
- `QQ_SMTP_PORT`：默认 `465`

不要把 QQ 邮箱授权信息写入代码、README、测试、日志或提交记录。若要修改观察列表，复制并编辑 `config/daily_report.example.yml` 中的 `symbols`。

## 安全模型

真实交易必须同时满足：

- 法律与平台资格允许。
- `GET https://polymarket.com/api/geoblock` 返回未 blocked。
- `POLYBOT_LIVE_TRADING=true`。
- `POLYBOT_ACK_RISK=true`。
- 钱包、funder address、API 凭证、余额和 allowance 均有效。
- 策略配置包含明确市场 allowlist 和每个市场风险限制。

不要提交 `.env`、private key、API credentials、wallet seed phrase 或生成的 SQLite 数据库。

## Live-readiness checklist

进入真实交易前必须逐项确认：

- 当前司法辖区、用户身份和平台规则允许使用 Polymarket。
- geoblock 检查返回 `blocked=false`。
- `.env` 中的敏感配置、钱包地址、funder address 和 API credentials 有效。
- 钱包余额和 allowance 足够。
- `POLYBOT_LIVE_TRADING=true` 和 `POLYBOT_ACK_RISK=true` 均已显式开启。
- 市场 allowlist、单笔限额、单市场限额、日亏损限额和策略参数已经通过 paper trading 与回测验证。
- live adapter 测试只使用 mock，人工确认命令不会绕过风控或合规 gate。
## 本地桌面程序

桌面程序用于编辑日报追踪股票代码、保存时自动校验最近收盘价、立即发送日报邮件，以及只提交并推送 GUI 自管配置文件。

开发环境直接运行：

```powershell
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m polybot.desktop.app
```

打包 Windows `.exe`：

```powershell
Set-Location code
powershell -ExecutionPolicy Bypass -File .\scripts\build_desktop.ps1
```

GUI 正式配置文件：

- `config/gui/daily_report.yml`

GUI 仍然依赖以下环境变量发送邮件：

- `QQ_SMTP_USER`
- `QQ_SMTP_AUTH_CODE`
- `ALERT_EMAIL_TO`
