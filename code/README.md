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
py -3.12 -m polybot paper-run --markets config/markets.example.json --fair-values config/fair_values.example.csv
py -3.12 -m polybot live-run --markets config/markets.example.json --fair-values config/fair_values.example.csv
py -3.12 -m polybot cancel-all --market <condition_id>
```

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
- `.env` 中的 secrets、钱包地址、funder address 和 API credentials 有效。
- 钱包余额和 allowance 足够。
- `POLYBOT_LIVE_TRADING=true` 和 `POLYBOT_ACK_RISK=true` 均已显式开启。
- 市场 allowlist、单笔限额、单市场限额、日亏损限额和策略参数已经通过 paper trading 与回测验证。
- live adapter 测试只使用 mock，人工确认命令不会绕过风控或合规 gate。
