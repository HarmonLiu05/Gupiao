# plan2 执行反馈：美股与美股期权行情脚本

## 计划信息

- 计划文件：`E:\4.17_coding\plan\plan2-us-market-data-script.md`
- 执行日期：2026-04-17
- 代码目录：`E:\4.17_coding\code`
- 提交记录：`b92ad5c feat: add us market data commands`

## 执行前评审

- 需求清晰度：清楚。计划只要求实现只读美股股票报价和美股期权链查询，不涉及交易、不下单。
- 关键假设：
  - 使用 `yfinance` 作为免费观察数据源。
  - 免费 Yahoo 数据可能不稳定，且不适合作为真实交易级实时行情。
  - 完整、稳定、实时 OPRA 期权行情通常需要付费数据源。
- 风险点：
  - 必须和 Polymarket live trading、钱包、私钥、下单逻辑隔离。
  - CLI 不能在参数错误时抛 Python traceback。
  - Yahoo `fast_info` 字段命名可能是 snake_case 或 camelCase，需要兼容。
- 执行决定：计划可执行。当前已有部分未提交实现，按要求先审查，再在原有改动基础上修正。

## 已修改内容

- 在 `code/pyproject.toml` 中加入 `yfinance>=0.2.66`。
- 新增 `code/src/polybot/clients/yahoo_market_data.py`。
- 在 `code/src/polybot/cli.py` 中新增：
  - `quote`
  - `options`
- 支持：
  - `py -3.12 -m polybot quote AAPL`
  - `py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230`
  - `py -3.12 -m polybot options TSLA --expiration 2026-05-15 --side both`
- 新增和扩展测试：
  - `code/tests/test_yahoo_market_data.py`
  - `code/tests/test_cli.py`
- README 新增中文“美股行情查询”说明，并写明免费数据源和 OPRA 付费数据限制。
- 修正 CLI 输出逻辑：合法的 `0` 值不会被错误显示为空。

## 验证结果

已运行：

```powershell
py -3.12 --version
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m ruff check .
py -3.12 -m pytest -v --basetemp .pytest_tmp
Select-String -Path README.md -Pattern "PRIVATE_KEY|SECRET|TOKEN|PASSWORD"
py -3.12 -m polybot quote AAPL
py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230
py -3.12 -m polybot options SPY --side both --min-strike 400 --max-strike 700
```

结果：

- Python 版本：Python 3.12.3。
- 安装成功，`yfinance` 已安装。
- Ruff：`All checks passed!`
- Pytest：`30 passed`。
- README 密钥检查：无输出。
- AAPL 股票报价：成功返回，`last_price` 不为空。
- AAPL calls 期权链：成功返回表头和 8 条合约。
- SPY both 期权链：成功返回表头和 293 条合约。

## 注意事项

- 本次实现是只读行情查询，没有新增交易下单逻辑。
- Yahoo 返回的部分期权 `bid` / `ask` 为 `0.0` 或空值，属于免费数据源限制，不代表程序失败。
- 若后续要做真实交易级美股或期权行情，应单独评估 Polygon.io、Alpaca、Tradier 等数据源和授权。
