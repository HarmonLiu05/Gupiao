# 美股与美股期权行情脚本完善计划

> **给 agent 执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步执行。本计划使用 checkbox（`- [ ]`）记录进度。

**目标：** 完善一个只读行情脚本，用于查看美股股票价格和美股期权链，不接真实交易、不下单。

**架构：** 在现有 `code/` Python 包中保留 `polybot` CLI，新增或修正 Yahoo Finance 数据客户端作为免费观察源，同时把付费数据源选择写入文档。行情模块必须和 Polymarket 交易模块隔离。

**技术栈：** Python 3.12、Typer CLI、`yfinance`、Pandas、Pydantic、Pytest、Ruff。

---

## 背景与约束

- 用户要看的是美股和美股期权，不是 Polymarket 市场。
- 当前仓库已有 `code/` Python 项目和 `polybot` CLI。
- 只读行情脚本不得读取钱包私钥、不得访问交易下单接口、不得发送订单。
- 免费数据源优先用于学习、观察和低频查询；不要把免费 Yahoo 数据当作稳定实时交易数据。
- 美股期权实时、完整、稳定的 OPRA 行情通常需要付费。可研究的数据源包括：
  - `yfinance` / Yahoo Finance：免费、方便、个人研究用途，稳定性和授权范围有限。
  - Polygon.io：有免费层，完整或实时期权数据通常需要付费。
  - Alpaca Market Data：Basic 有免费数据，但美股全市场和完整 OPRA 期权数据通常需要付费档。
  - Tradier：适合期权交易和链式行情，但需要账号/API token，权限和费用以官网为准。

## 当前执行窗口已做的疑似变更

执行者先确认这些文件是否已经存在，若存在就审查并在其基础上修正：

- `code/src/polybot/clients/yahoo_market_data.py`
- `code/tests/test_yahoo_market_data.py`
- `code/tests/test_cli.py`
- `code/src/polybot/cli.py`
- `code/pyproject.toml`

不要盲目重写。先运行测试确认现状。

---

### 任务 1：确认基线与测试环境

**文件：**
- 查看：`code/pyproject.toml`
- 查看：`code/src/polybot/cli.py`
- 查看：`code/src/polybot/clients/yahoo_market_data.py`
- 查看：`code/tests/test_yahoo_market_data.py`

- [ ] **步骤 1：确认 Python 版本**

运行：

```bash
py -3.12 --version
```

期望：输出 Python 3.12.x。不要使用系统默认 `python`，因为本机默认可能是 Python 3.7。

- [ ] **步骤 2：安装依赖**

运行：

```bash
cd E:\4.17_coding\code
py -3.12 -m pip install -e ".[dev]"
```

期望：安装成功，`yfinance` 已安装。

- [ ] **步骤 3：运行当前测试**

运行：

```bash
py -3.12 -m pytest -v --basetemp .pytest_tmp
```

期望：测试通过。如果失败，记录失败测试名和错误，不要先改实现。

---

### 任务 2：修正美股股票报价命令

**文件：**
- 修改：`code/src/polybot/clients/yahoo_market_data.py`
- 修改：`code/tests/test_yahoo_market_data.py`
- 修改：`code/src/polybot/cli.py`
- 修改：`code/tests/test_cli.py`

- [ ] **步骤 1：写字段兼容测试**

在 `code/tests/test_yahoo_market_data.py` 中确保存在测试覆盖两类 `fast_info` 字段：

```python
def test_get_quote_accepts_snake_case_fast_info_keys():
    ...

def test_get_quote_accepts_camel_case_fast_info_keys():
    ...
```

要求同时支持：

- `last_price` 和 `lastPrice`
- `previous_close` 和 `previousClose`
- `market_cap` 和 `marketCap`

- [ ] **步骤 2：验证测试先失败**

运行：

```bash
py -3.12 -m pytest tests/test_yahoo_market_data.py -v --basetemp .pytest_tmp
```

期望：如果当前实现未兼容字段，测试失败在 quote 字段断言处。

- [ ] **步骤 3：修正字段读取**

在 `YahooMarketDataClient.get_quote()` 中实现一个小 helper，例如：

```python
def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return None
```

然后读取：

```python
last_price = _first_present(fast_info, "last_price", "lastPrice")
previous_close = _first_present(fast_info, "previous_close", "previousClose")
market_cap = _first_present(fast_info, "market_cap", "marketCap")
```

- [ ] **步骤 4：验证**

运行：

```bash
py -3.12 -m pytest tests/test_yahoo_market_data.py tests/test_cli.py -v --basetemp .pytest_tmp
```

期望：相关测试全部通过。

---

### 任务 3：完善期权链命令输出

**文件：**
- 修改：`code/src/polybot/clients/yahoo_market_data.py`
- 修改：`code/src/polybot/cli.py`
- 修改：`code/tests/test_yahoo_market_data.py`
- 修改：`code/tests/test_cli.py`

- [ ] **步骤 1：确认 CLI 参数**

`options` 命令必须支持：

```bash
py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230
py -3.12 -m polybot options TSLA --expiration 2026-05-15 --side both
```

参数含义：

- `symbol`：美股 ticker，例如 `AAPL`、`TSLA`、`SPY`
- `--expiration`：期权到期日，格式 `YYYY-MM-DD`，不传则使用最近到期日
- `--side`：`calls`、`puts` 或 `both`
- `--min-strike` / `--max-strike`：按 strike 过滤

- [ ] **步骤 2：补充无到期日时的测试**

在 `test_yahoo_market_data.py` 中增加测试：`expiration=None` 时使用 `ticker.options[0]`。

- [ ] **步骤 3：补充非法 side 测试**

在 `test_cli.py` 中增加测试：

```python
result = CliRunner().invoke(app, ["options", "AAPL", "--side", "bad"])
assert result.exit_code == 2
assert "side must be one of" in result.output
```

- [ ] **步骤 4：验证**

运行：

```bash
py -3.12 -m pytest tests/test_yahoo_market_data.py tests/test_cli.py -v --basetemp .pytest_tmp
```

期望：全部通过。

---

### 任务 4：添加中文使用说明

**文件：**
- 修改：`code/README.md`

- [ ] **步骤 1：新增“美股行情查询”小节**

加入以下内容，允许按实际命令微调：

```markdown
## 美股行情查询

本项目提供只读美股行情命令，不会下单。

查看股票报价：

```bash
py -3.12 -m polybot quote AAPL
```

查看期权链：

```bash
py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230
```

`yfinance` 适合个人研究和低频观察。它不是官方交易级实时行情源，不建议用于真实交易决策。若需要稳定、完整、实时的美股和 OPRA 期权行情，应评估 Polygon.io、Alpaca、Tradier 等付费或半付费数据源。
```

- [ ] **步骤 2：说明数据源费用判断**

在 README 中明确：

- 股票日线、延迟报价、低频观察有免费方案。
- 美股期权链可以免费拉取部分字段，但完整实时 OPRA 报价通常付费。
- 商业使用、转发数据、自动交易前必须确认数据授权。

- [ ] **步骤 3：验证文档不含密钥**

运行：

```bash
Select-String -Path README.md -Pattern "PRIVATE_KEY|SECRET|TOKEN|PASSWORD"
```

期望：没有真实密钥。

---

### 任务 5：真实数据 Smoke Test

**文件：**
- 不修改文件，只运行命令。

- [ ] **步骤 1：测试 AAPL 股票报价**

运行：

```bash
py -3.12 -m polybot quote AAPL
```

期望：输出包含表头 `symbol last_price currency previous_close market_cap`，且 `AAPL` 的 `last_price` 不为空。

- [ ] **步骤 2：测试 AAPL 期权链**

运行：

```bash
py -3.12 -m polybot options AAPL --side calls --min-strike 200 --max-strike 230
```

期望：输出至少包含 `contract`、`side`、`strike`、`last_price`、`bid`、`ask` 列。若 `bid` / `ask` 为空，记录为数据源限制，不作为程序失败。

- [ ] **步骤 3：测试 ETF 期权链**

运行：

```bash
py -3.12 -m polybot options SPY --side both --min-strike 400 --max-strike 700
```

期望：命令能返回或明确显示无结果，不抛 Python traceback。

---

### 任务 6：最终质量检查

**文件：**
- 可能修改：`code/README.md`

- [ ] **步骤 1：运行 lint**

```bash
py -3.12 -m ruff check .
```

期望：`All checks passed!`

- [ ] **步骤 2：运行全量测试**

```bash
py -3.12 -m pytest -v --basetemp .pytest_tmp
```

期望：全部测试通过。

- [ ] **步骤 3：检查 git diff**

```bash
git diff -- code/src/polybot/clients/yahoo_market_data.py code/src/polybot/cli.py code/tests/test_yahoo_market_data.py code/tests/test_cli.py code/pyproject.toml code/README.md
```

期望：只包含美股/美股期权行情查询相关改动，不包含交易下单逻辑。

---

## 交接说明

- 本计划只要求实现只读行情查询，不做自动交易。
- 免费数据源用 `yfinance` 即可；真实交易级期权数据后续再单独评估 Polygon.io、Alpaca、Tradier。
- 如果 `yfinance` 在国内网络下不稳定，先记录错误和复现命令，不要绕到无来源的爬虫。
- 所有验证命令使用 `py -3.12`。
- 因本机 pytest 默认临时目录可能有权限问题，测试命令统一加 `--basetemp .pytest_tmp`。
