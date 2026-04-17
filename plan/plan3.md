# 美股行情工具增强实现计划

> **给 agent 执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步执行。本计划使用 checkbox（`- [ ]`）记录进度。

**目标：** 将现有只读美股行情脚本从“单个 symbol 查询”增强为可日常使用的观察工具，支持批量股票报价、期权到期日查看、JSON/CSV 输出和稳定的错误提示。

**架构：** 继续使用 `polybot` Typer CLI。行情数据仍由 `YahooMarketDataClient` 提供，新增格式化层负责 table/json/csv 输出，CLI 只负责参数解析和调用。所有功能保持只读，不接交易接口。

**技术栈：** Python 3.12、Typer、`yfinance`、Pandas、Pydantic、Pytest、Ruff。

---

## 当前基线

根据 `feddback/plan2-us-market-data-script-feedback.md`，当前状态：

- 已提交：`b92ad5c feat: add us market data commands`
- 已支持：
  - `py -3.12 -m polybot quote AAPL`
  - `py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230`
  - `py -3.12 -m polybot options TSLA --expiration 2026-05-15 --side both`
- 已验证：`ruff check .` 通过，`pytest` 为 `30 passed`
- 已知限制：Yahoo 免费数据中部分期权 `bid` / `ask` 可能为 `0.0` 或空值，这不是程序失败。

本计划只增强只读行情能力，不新增交易、不读取钱包、不使用私钥。

## 文件结构

- 修改：`code/src/polybot/clients/yahoo_market_data.py` - 增加批量报价和更明确的数据错误。
- 修改：`code/src/polybot/cli.py` - 增加 CLI 命令和输出格式参数。
- 创建：`code/src/polybot/marketdata/__init__.py` - marketdata 包标记。
- 创建：`code/src/polybot/marketdata/formatters.py` - table/json/csv 输出格式化。
- 修改：`code/tests/test_yahoo_market_data.py` - 覆盖批量报价、到期日和错误场景。
- 修改：`code/tests/test_cli.py` - 覆盖新增 CLI 命令。
- 创建：`code/tests/test_marketdata_formatters.py` - 覆盖输出格式。
- 创建：`code/config/watchlist.example.txt` - 批量观察示例。
- 修改：`code/README.md` - 增加中文使用说明。

---

### 任务 1：确认执行基线

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

- [ ] **步骤 3：安装依赖并跑基线测试**

运行：

```bash
py -3.12 -m pip install -e ".[dev]"
py -3.12 -m pytest -v --basetemp .pytest_tmp
py -3.12 -m ruff check .
```

期望：测试和 Ruff 均通过。若失败，先记录失败信息并修复基线，再执行后续任务。

---

### 任务 2：新增输出格式化层

**文件：**
- 创建：`code/src/polybot/marketdata/__init__.py`
- 创建：`code/src/polybot/marketdata/formatters.py`
- 创建：`code/tests/test_marketdata_formatters.py`

- [ ] **步骤 1：先写格式化测试**

在 `code/tests/test_marketdata_formatters.py` 中写入行为测试，覆盖：

```python
from polybot.clients.yahoo_market_data import StockQuote
from polybot.marketdata.formatters import format_records


def test_format_records_as_json():
    rows = [StockQuote(symbol="AAPL", last_price="212.34", currency="USD")]

    output = format_records(rows, output="json")

    assert '"symbol": "AAPL"' in output
    assert '"last_price": "212.34"' in output


def test_format_records_as_csv():
    rows = [StockQuote(symbol="AAPL", last_price="212.34", currency="USD")]

    output = format_records(rows, output="csv")

    assert "symbol,last_price,currency" in output
    assert "AAPL,212.34,USD" in output
```

- [ ] **步骤 2：运行测试确认失败**

运行：

```bash
py -3.12 -m pytest tests/test_marketdata_formatters.py -v --basetemp .pytest_tmp
```

期望：因 `polybot.marketdata.formatters` 不存在而失败。

- [ ] **步骤 3：实现 `format_records`**

实现要求：

- 入参：`records: Sequence[pydantic.BaseModel]`，`output: Literal["table", "json", "csv"]`
- `json` 输出使用 `model_dump(mode="json")`
- `csv` 使用 `csv.DictWriter`
- `table` 返回 tab 分隔文本，首行为字段名
- `Decimal` 必须输出为字符串，避免浮点误差

- [ ] **步骤 4：验证**

运行：

```bash
py -3.12 -m pytest tests/test_marketdata_formatters.py -v --basetemp .pytest_tmp
```

期望：测试通过。

---

### 任务 3：批量股票报价

**文件：**
- 修改：`code/src/polybot/clients/yahoo_market_data.py`
- 修改：`code/src/polybot/cli.py`
- 修改：`code/tests/test_yahoo_market_data.py`
- 修改：`code/tests/test_cli.py`
- 创建：`code/config/watchlist.example.txt`

- [ ] **步骤 1：写客户端测试**

在 `test_yahoo_market_data.py` 中增加：

```python
def test_get_quotes_returns_multiple_symbols():
    client = YahooMarketDataClient(ticker_factory=FakeTicker)

    quotes = client.get_quotes(["aapl", "msft"])

    assert [item.symbol for item in quotes] == ["AAPL", "MSFT"]
    assert all(item.last_price is not None for item in quotes)
```

- [ ] **步骤 2：实现 `get_quotes`**

在 `YahooMarketDataClient` 中添加：

```python
def get_quotes(self, symbols: list[str]) -> list[StockQuote]:
    return [self.get_quote(symbol) for symbol in symbols]
```

同时去除空白 symbol，并把 symbol 转为大写。

- [ ] **步骤 3：写 CLI 测试**

在 `test_cli.py` 中增加 `quotes` 命令测试：

```python
result = CliRunner().invoke(app, ["quotes", "AAPL,MSFT", "--output", "csv"])
assert result.exit_code == 0
assert "AAPL" in result.output
assert "MSFT" in result.output
```

- [ ] **步骤 4：实现 CLI 命令**

新增命令：

```bash
py -3.12 -m polybot quotes AAPL,MSFT,NVDA --output table
py -3.12 -m polybot quotes --file config/watchlist.example.txt --output csv
```

规则：

- 支持位置参数 `symbols`，逗号分隔。
- 支持 `--file`，每行一个 symbol，允许空行和以 `#` 开头的注释行。
- `symbols` 和 `--file` 至少提供一个。
- `--output` 支持 `table`、`json`、`csv`。

- [ ] **步骤 5：创建 watchlist 示例**

创建 `code/config/watchlist.example.txt`：

```text
# US stock watchlist
AAPL
MSFT
NVDA
SPY
QQQ
```

- [ ] **步骤 6：验证**

运行：

```bash
py -3.12 -m pytest tests/test_yahoo_market_data.py tests/test_cli.py -v --basetemp .pytest_tmp
```

期望：新增和已有测试全部通过。

---

### 任务 4：期权到期日查询命令

**文件：**
- 修改：`code/src/polybot/clients/yahoo_market_data.py`
- 修改：`code/src/polybot/cli.py`
- 修改：`code/tests/test_yahoo_market_data.py`
- 修改：`code/tests/test_cli.py`

- [ ] **步骤 1：写客户端测试**

确认 `YahooMarketDataClient.get_expirations("AAPL")` 返回字符串列表：

```python
def test_get_expirations_returns_available_dates():
    client = YahooMarketDataClient(ticker_factory=FakeTicker)

    expirations = client.get_expirations("aapl")

    assert expirations == ["2026-05-15", "2026-06-19"]
```

- [ ] **步骤 2：写 CLI 测试**

在 `test_cli.py` 中增加：

```python
result = CliRunner().invoke(app, ["expirations", "aapl"])
assert result.exit_code == 0
assert "AAPL" in result.output
assert "2026-05-15" in result.output
```

- [ ] **步骤 3：实现 CLI 命令**

新增命令：

```bash
py -3.12 -m polybot expirations AAPL
```

输出格式：

```text
symbol	expiration
AAPL	2026-05-15
AAPL	2026-06-19
```

- [ ] **步骤 4：验证**

运行：

```bash
py -3.12 -m pytest tests/test_yahoo_market_data.py tests/test_cli.py -v --basetemp .pytest_tmp
```

期望：测试全部通过。

---

### 任务 5：CLI 错误处理与空结果处理

**文件：**
- 修改：`code/src/polybot/cli.py`
- 修改：`code/tests/test_cli.py`

- [ ] **步骤 1：写错误处理测试**

覆盖：

```python
result = CliRunner().invoke(app, ["quotes"])
assert result.exit_code == 2
assert "provide symbols or --file" in result.output
```

覆盖空期权链：

```python
result = CliRunner().invoke(app, ["options", "AAPL", "--min-strike", "999999"])
assert result.exit_code == 0
assert "no contracts matched" in result.output.lower()
```

- [ ] **步骤 2：实现错误提示**

要求：

- 参数错误使用 `typer.BadParameter` 或 `typer.Exit(code=2)`。
- 数据为空时不抛 traceback，输出明确文本。
- 网络或数据源异常时输出 `market data unavailable: <message>`，退出码为 `1`。

- [ ] **步骤 3：验证**

运行：

```bash
py -3.12 -m pytest tests/test_cli.py -v --basetemp .pytest_tmp
```

期望：测试全部通过。

---

### 任务 6：README 中文说明更新

**文件：**
- 修改：`code/README.md`

- [ ] **步骤 1：补充批量报价说明**

加入：

```markdown
批量查看股票报价：

```bash
py -3.12 -m polybot quotes AAPL,MSFT,NVDA --output table
py -3.12 -m polybot quotes --file config/watchlist.example.txt --output csv
```
```

- [ ] **步骤 2：补充期权到期日说明**

加入：

```markdown
查看某个 symbol 的可用期权到期日：

```bash
py -3.12 -m polybot expirations AAPL
```
```

- [ ] **步骤 3：补充数据源限制**

说明：

- `yfinance` 适合个人研究和低频观察。
- 免费源返回的 `bid` / `ask` 可能为空或为 `0.0`。
- 如果用于真实交易级策略，需要另建计划评估 Polygon.io、Alpaca、Tradier 等授权数据源。

---

### 任务 7：最终验证

**文件：**
- 不修改文件，只运行命令并记录结果。

- [ ] **步骤 1：运行静态检查**

```bash
py -3.12 -m ruff check .
```

期望：`All checks passed!`

- [ ] **步骤 2：运行全量测试**

```bash
py -3.12 -m pytest -v --basetemp .pytest_tmp
```

期望：全部测试通过。

- [ ] **步骤 3：运行真实数据 smoke test**

```bash
py -3.12 -m polybot quote AAPL
py -3.12 -m polybot quotes AAPL,MSFT,NVDA --output table
py -3.12 -m polybot expirations AAPL
py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230
```

期望：

- `quote` 输出 `AAPL` 且 `last_price` 不为空。
- `quotes` 输出多个 symbol。
- `expirations` 至少输出一个日期。
- `options` 输出合约表；若 `bid` / `ask` 为空或为 `0.0`，记录为免费数据源限制。

- [ ] **步骤 4：检查 diff 范围**

```bash
git diff -- code/src/polybot/clients/yahoo_market_data.py code/src/polybot/cli.py code/src/polybot/marketdata code/tests/test_yahoo_market_data.py code/tests/test_cli.py code/tests/test_marketdata_formatters.py code/config/watchlist.example.txt code/README.md
```

期望：只包含只读美股行情工具增强，不包含交易下单、钱包、私钥或 Polymarket live trading 改动。

---

## 交接说明

- 严格保持只读行情工具定位。
- 不要添加交易 API、不接券商下单、不读取私钥。
- 所有命令使用 `py -3.12`。
- 测试命令统一加 `--basetemp .pytest_tmp`，避开本机 pytest 临时目录权限问题。
- 若 Yahoo 数据源网络失败，记录失败命令和错误，不要改成无来源的网页爬虫。
- 完成后把执行反馈写入 `E:\4.17_coding\feddback\plan3-feedback.md`。
