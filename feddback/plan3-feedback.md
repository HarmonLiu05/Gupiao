# plan3 执行反馈：美股行情工具增强

## 计划信息

- 计划文件：`E:\4.17_coding\plan\plan3.md`
- 执行日期：2026-04-17
- 代码目录：`E:\4.17_coding\code`
- 范围：增强只读美股行情 CLI，支持批量股票报价、watchlist 文件、期权到期日查询、table/json/csv 输出、错误处理、空结果处理和中文 README。

## 执行前评审

- 需求清晰度：清楚。计划明确要求继续增强现有 `polybot` CLI 的只读美股行情能力，不涉及交易、下单、钱包或私钥。
- 关键假设：
  - 当前基线来自 plan2 提交，已有 `quote`、`options` 和 `YahooMarketDataClient`。
  - 输出格式化应独立成 `polybot.marketdata` 包，避免 CLI 内部继续堆格式化逻辑。
  - `yfinance` 真实数据 smoke test 可能受网络、Yahoo 限流或免费数据源字段缺失影响。
- 风险点：
  - 新增 `quotes`、`expirations` 时不能引入任何交易接口或 Polymarket live trading 改动。
  - CSV/JSON/table 输出需要正确处理 `Decimal`，避免浮点误差或非 JSON 可序列化对象。
  - CLI 错误不能抛 Python traceback，应给出可读错误和合适退出码。
  - 空期权链需要正常提示，而不是当作异常崩溃。
- 验证方式：
  - 先运行基线 `py -3.12 -m pytest -v --basetemp .pytest_tmp` 和 `py -3.12 -m ruff check .`。
  - 先写新增行为测试，确认目标能力缺失时失败，再实现。
  - 最终运行 Ruff、全量 pytest、真实数据 smoke test 和限定 diff 检查。
- 执行决定：计划可执行。按 TDD 分批实现，并把最终验证结果补入本文档。

## 执行记录

- 已修改内容：
  - 新增 `code/src/polybot/marketdata/__init__.py` 和 `code/src/polybot/marketdata/formatters.py`，支持 `table`、`json`、`csv` 输出。
  - 新增 `code/tests/test_marketdata_formatters.py`，覆盖 JSON、CSV、table 格式化。
  - 在 `YahooMarketDataClient` 中新增 `get_quotes()`，支持批量股票报价并过滤空 symbol。
  - 在 `code/src/polybot/cli.py` 中增强只读行情命令：
    - `quote SYMBOL --output table|json|csv`
    - `quotes AAPL,MSFT,NVDA --output table|json|csv`
    - `quotes --file config/watchlist.example.txt --output csv`
    - `expirations AAPL --output table|json|csv`
    - `options AAPL ... --output table|json|csv`
  - 新增 `code/config/watchlist.example.txt`。
  - 增强 CLI 错误处理：缺少 symbol/watchlist 时返回 code 2；市场数据异常输出 `market data unavailable: <message>` 并返回 code 1；空期权链输出 `no contracts matched`。
  - 更新 `code/README.md` 的中文说明，补充批量报价、watchlist、期权到期日和输出格式说明。
  - 补充 `code/tests/test_cli.py` 和 `code/tests/test_yahoo_market_data.py`，覆盖批量报价、到期日、输出格式、空结果和错误处理。
- 已运行命令：
  - `py -3.12 --version`，结果：Python 3.12.3。
  - `py -3.12 -m pip install -e ".[dev]"`，结果：安装成功。
  - `py -3.12 -m pytest tests/test_marketdata_formatters.py -v --basetemp .pytest_tmp`，先因模块不存在失败，随后实现后通过。
  - `py -3.12 -m pytest tests/test_yahoo_market_data.py tests/test_cli.py -v --basetemp .pytest_tmp`，新增测试先暴露缺失能力，修复后通过。
  - `py -3.12 -m ruff check .`，结果：`All checks passed!`。
  - `py -3.12 -m pytest -v --basetemp .pytest_tmp`，结果：44 个测试全部通过。
  - `py -3.12 -m polybot quote AAPL`，结果：输出 AAPL 且 `last_price` 不为空。
  - `py -3.12 -m polybot quotes AAPL,MSFT,NVDA --output table`，结果：输出 AAPL、MSFT、NVDA 三个 symbol。
  - `py -3.12 -m polybot expirations AAPL`，结果：输出多个 AAPL 期权到期日。
  - `py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230`，结果：输出期权链表头和 8 条合约。
- 结果：plan3 已执行完成。所有新增功能均为只读行情查询，没有新增交易下单、钱包、私钥或 Polymarket live trading 改动。真实数据 smoke 中期权 `bid` / `ask` 出现 `0.0`，记录为 Yahoo 免费数据源限制。
