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
