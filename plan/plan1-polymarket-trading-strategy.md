# Polymarket 交易策略实现计划

> **给 agent 执行者：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步执行。本计划使用 checkbox（`- [ ]`）记录进度。

**目标：** 构建一个 Polymarket 交易系统，能够调研市场、运行回测和 paper trading，并且只有在合规、钱包、授权、余额和风控门槛全部通过后才允许真实下单。

**架构：** 使用 Python 包拆分为市场发现、行情数据、策略信号、风控、执行、状态存储和 CLI 编排模块。优先使用 Polymarket 官方 SDK；除非 SDK 无法满足已测试需求，否则不要手写签名逻辑。

**技术栈：** Python 3.11+、`py-clob-client`、`httpx`、`websockets`、`pydantic`、`pandas`、`sqlite`、`pytest`、`ruff`、`python-dotenv`。

---

## 调研结论

实现时必须遵守以下约束：

- Polymarket 主要有三类 API：Gamma API 用于市场和事件发现，Data API 用于持仓、成交和活动数据，CLOB API 用于订单簿、价格、历史行情、下单、撤单和认证交易：https://docs.polymarket.com/api-reference
- CLOB 交易使用两层认证：L1 用私钥做 EIP-712 签名来创建或派生 API 凭证，L2 用 HMAC 凭证认证交易请求。即使有 L2 凭证，订单本身仍需要本地签名：https://docs.polymarket.com/api-reference/authentication
- 官方提供 Python、TypeScript、Rust 客户端。本计划使用 Python 的 `py-clob-client`：https://docs.polymarket.com/api-reference/clients-sdks
- Polymarket 订单本质上都是限价单。市价单通过可立即成交的限价单表达。订单类型包括 GTC、GTD、FOK、FAK：https://docs.polymarket.com/trading/orders/create
- 每个市场都有 tick size、最小订单规模和可能的 negative risk 配置。下单前必须获取并校验：https://docs.polymarket.com/trading/orders/overview
- CLOB 公开端点提供订单簿、价格、中间价、价差、历史价格、批量查询和成交价格估算：https://docs.polymarket.com/trading/orderbook
- WebSocket market channel 提供订单簿、价格变化、最后成交、best bid/ask、新市场和市场结算事件。user channel 需要 API 凭证：https://docs.polymarket.com/market-data/websocket/overview
- 速率限制已有官方文档。即使 Cloudflare 可能采用排队而不是立即拒绝，也要在本地实现节流：https://docs.polymarket.com/api-reference/rate-limits
- 地域限制是硬约束。必须实际调用 geoblock 端点判断运行环境是否允许下单，不要绕过地域限制、VPN 限制、制裁限制或当地法律：https://docs.polymarket.com/api-reference/geoblock

这是工程实现计划，不是投资建议。系统不得承诺收益。

## 合规与真实交易门槛

真实交易默认关闭，只有全部条件满足时才允许进入 live 模式：

- `POLYBOT_LIVE_TRADING=true`
- `POLYBOT_ACK_RISK=true`
- `GET https://polymarket.com/api/geoblock` 返回 `blocked: false`
- 钱包、funder address、API 凭证、余额和 allowance 均有效
- 策略配置包含明确的市场 allowlist 和每个市场的风险限制

你在国内运行时，不能预设一定可以交易。执行窗口必须在本机或部署环境实际调用 geoblock。如果返回 blocked，或者请求失败无法确认资格，只允许运行回测和 paper trading。

## 建议仓库结构

- 创建：`pyproject.toml` - 依赖、脚本、lint/test 配置。
- 创建：`.env.example` - 环境变量说明，不包含密钥。
- 创建：`README.md` - 安装、运行、安全模型和命令示例。
- 创建：`src/polybot/config.py` - 类型化配置。
- 创建：`src/polybot/clients/geoblock.py` - 地域资格检查。
- 创建：`src/polybot/clients/gamma.py` - 市场和事件发现。
- 创建：`src/polybot/clients/clob.py` - CLOB SDK 封装。
- 创建：`src/polybot/data/models.py` - 共享 Pydantic 模型。
- 创建：`src/polybot/strategy/base.py` - 策略协议和信号模型。
- 创建：`src/polybot/strategy/value_edge.py` - 第一个确定性策略。
- 创建：`src/polybot/risk/manager.py` - 订单和组合风控。
- 创建：`src/polybot/execution/paper.py` - paper broker。
- 创建：`src/polybot/execution/live.py` - 使用 CLOB 的 live broker。
- 创建：`src/polybot/state/store.py` - SQLite 订单、成交和持仓存储。
- 创建：`src/polybot/cli.py` - 命令入口。
- 创建：`tests/` - 与源码结构匹配的测试。

## 策略设计

先实现一个保守、可插拔的价值边际策略：

```python
edge = fair_probability - best_ask
if edge >= min_edge and spread <= max_spread:
    signal = BUY
```

第一个策略必须从本地 CSV 或 JSON 读取 `fair_probability`，不要在系统里虚构 alpha 来源。其他策略应在执行系统测试稳定后，作为独立计划继续扩展。

策略必须包含以下保护：

- 不交易已结算、关闭、非活跃或语义不清的市场。
- 没有 best bid/ask 或最低流动性不足时不交易。
- 价格必须按市场 tick size 取整。
- 遵守 `min_order_size`。
- 限制单笔名义金额、单市场敞口、日亏损和开放订单总数。
- 超过配置时间的订单必须撤单。

---

### 任务 1：项目脚手架

**文件：**
- 创建：`pyproject.toml`
- 创建：`.env.example`
- 创建：`README.md`
- 创建：`src/polybot/__init__.py`
- 创建：`tests/__init__.py`

- [ ] **步骤 1：创建 Python 包元数据**

使用以下依赖基线：

```toml
[project]
name = "polybot"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "py-clob-client>=0.23.0",
  "httpx>=0.27.0",
  "websockets>=12.0",
  "pydantic>=2.7.0",
  "pydantic-settings>=2.2.0",
  "pandas>=2.2.0",
  "python-dotenv>=1.0.0",
  "typer>=0.12.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "ruff>=0.5.0"]

[project.scripts]
polybot = "polybot.cli:app"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **步骤 2：创建 `.env.example`**

```bash
POLYBOT_MODE=paper
POLYBOT_LIVE_TRADING=false
POLYBOT_ACK_RISK=false
POLYBOT_DB_PATH=.polybot/polybot.sqlite3
POLYBOT_PRIVATE_KEY=
POLYBOT_FUNDER_ADDRESS=
POLYBOT_SIGNATURE_TYPE=2
POLYBOT_MAX_ORDER_NOTIONAL=10
POLYBOT_MAX_MARKET_NOTIONAL=50
POLYBOT_MAX_DAILY_LOSS=25
```

- [ ] **步骤 3：验证**

运行：`python -m pip install -e ".[dev]"`

期望：包安装成功。

---

### 任务 2：配置与安全默认值

**文件：**
- 创建：`src/polybot/config.py`
- 测试：`tests/test_config.py`

- [ ] **步骤 1：写默认 paper mode 测试**

```python
from polybot.config import Settings

def test_live_trading_disabled_by_default():
    settings = Settings()
    assert settings.mode == "paper"
    assert settings.live_trading is False
    assert settings.ack_risk is False
```

- [ ] **步骤 2：实现配置**

使用 `pydantic_settings.BaseSettings`，环境变量前缀为 `POLYBOT_`。字段包含 mode、live gate、private key、funder address、signature type、DB path 和风控上限。

- [ ] **步骤 3：验证**

运行：`pytest tests/test_config.py -v`

期望：测试全部通过。

---

### 任务 3：Geoblock 合规客户端

**文件：**
- 创建：`src/polybot/clients/geoblock.py`
- 测试：`tests/test_geoblock.py`

- [ ] **步骤 1：定义 geoblock 响应模型**

字段：`blocked: bool`、`ip: str | None`、`country: str | None`、`region: str | None`。

- [ ] **步骤 2：实现 `check_geoblock(client: httpx.Client | None = None)`**

调用 `https://polymarket.com/api/geoblock`，设置 10 秒超时，返回类型化模型。

- [ ] **步骤 3：添加 live gate helper**

实现 `assert_live_allowed(settings, geo)`。除非 live trading 和 risk acknowledgment 都开启，并且 `geo.blocked` 为 false，否则抛出 `PermissionError`。

- [ ] **步骤 4：验证**

mock blocked 和 unblocked 响应。运行：`pytest tests/test_geoblock.py -v`

期望：blocked 响应阻止真实交易。

---

### 任务 4：市场发现

**文件：**
- 创建：`src/polybot/clients/gamma.py`
- 创建：`src/polybot/data/models.py`
- 测试：`tests/test_gamma.py`

- [ ] **步骤 1：定义市场模型**

包含 `condition_id`、`question`、`active`、`closed`、`archived`、`outcomes`、`clob_token_ids`、`minimum_tick_size`、`min_order_size`、`neg_risk`、`end_date`。

- [ ] **步骤 2：实现 Gamma client**

添加方法：

```python
list_markets(limit: int = 100, active: bool = True) -> list[Market]
search_markets(query: str, limit: int = 20) -> list[Market]
```

使用 `https://gamma-api.polymarket.com/markets`。

- [ ] **步骤 3：过滤可交易市场**

实现 `Market.is_tradable()`。只有 active、未 closed、未 archived、有 token IDs、有 tick size 时返回 true。

- [ ] **步骤 4：验证**

使用 mocked HTTP responses。运行：`pytest tests/test_gamma.py -v`

期望：非活跃和字段缺失的市场被过滤。

---

### 任务 5：CLOB 行情封装

**文件：**
- 创建：`src/polybot/clients/clob.py`
- 测试：`tests/test_clob_data.py`

- [ ] **步骤 1：封装只读 CLOB 方法**

实现：

```python
get_order_book(token_id: str) -> OrderBook
get_price(token_id: str, side: str) -> Decimal
get_midpoint(token_id: str) -> Decimal
get_spread(token_id: str) -> Decimal
estimate_fill_price(token_id: str, side: str, amount: Decimal) -> Decimal
```

- [ ] **步骤 2：统一 Decimal**

交易管线内的价格、数量和名义金额全部使用 `Decimal`，不要使用 float。

- [ ] **步骤 3：验证**

mock SDK 返回的字符串价格和数量。运行：`pytest tests/test_clob_data.py -v`

期望：输出为 `Decimal`，且精度不丢失。

---

### 任务 6：策略接口与第一个策略

**文件：**
- 创建：`src/polybot/strategy/base.py`
- 创建：`src/polybot/strategy/value_edge.py`
- 测试：`tests/test_value_edge_strategy.py`

- [ ] **步骤 1：定义信号模型**

字段：`market_id`、`token_id`、`side`、`price`、`size`、`reason`、`confidence`。

- [ ] **步骤 2：定义策略协议**

```python
class Strategy(Protocol):
    def generate(self, snapshot: MarketSnapshot) -> list[Signal]:
        ...
```

- [ ] **步骤 3：实现 `ValueEdgeStrategy`**

输入：`fair_probability`、`min_edge`、`max_spread`、`base_size`。

行为：只有当 `fair_probability - best_ask >= min_edge` 且 spread 不超过限制时，生成 BUY signal。

- [ ] **步骤 4：验证**

运行：`pytest tests/test_value_edge_strategy.py -v`

期望：弱 edge 不生成信号，强 edge 生成一个 BUY 信号。

---

### 任务 7：风控管理器

**文件：**
- 创建：`src/polybot/risk/manager.py`
- 测试：`tests/test_risk_manager.py`

- [ ] **步骤 1：实现风控检查**

任一条件成立时拒单：

- market 不在 allowlist
- 单笔名义金额超过 `max_order_notional`
- 预计单市场敞口超过 `max_market_notional`
- 当日已实现加未实现亏损超过 `max_daily_loss`
- 价格不在 `[0.01, 0.99]`
- size 低于市场 `min_order_size`
- 价格不符合 tick size
- spread 超过策略配置

- [ ] **步骤 2：返回结构化结果**

使用 `RiskDecision(allowed: bool, reasons: list[str])`。

- [ ] **步骤 3：验证**

运行：`pytest tests/test_risk_manager.py -v`

期望：每一种拒单原因都有独立测试。

---

### 任务 8：Paper Execution 与状态存储

**文件：**
- 创建：`src/polybot/execution/paper.py`
- 创建：`src/polybot/state/store.py`
- 测试：`tests/test_paper_execution.py`
- 测试：`tests/test_state_store.py`

- [ ] **步骤 1：创建 SQLite schema**

表：`orders`、`fills`、`positions`、`strategy_runs`、`risk_rejections`。

- [ ] **步骤 2：实现 paper broker**

BUY 订单按 best ask 成交，SELL 订单按 best bid 成交，但只有在模拟流动性足够时才成交。写入 fills 并更新 positions。

- [ ] **步骤 3：验证**

运行：`pytest tests/test_state_store.py tests/test_paper_execution.py -v`

期望：paper fills 正确更新 position size、average cost 和 cash balance。

---

### 任务 9：Live Execution Adapter

**文件：**
- 创建：`src/polybot/execution/live.py`
- 测试：`tests/test_live_execution.py`

- [ ] **步骤 1：实现认证客户端构建**

使用 `py_clob_client.client.ClobClient`，参数包括 host `https://clob.polymarket.com`、chain ID `137`、private key、API credentials、signature type 和 funder address。

- [ ] **步骤 2：实现下单**

调用 `create_and_post_order` 前必须满足：

- live gate 已通过
- risk decision 为 allowed
- 已从市场数据加载 tick size 和 `neg_risk`
- 订单价格已按 tick size 取整
- 订单 size 大于等于 `min_order_size`

- [ ] **步骤 3：实现撤单**

暴露 `cancel_order(order_id)` 和 `cancel_market_orders(condition_id)`。

- [ ] **步骤 4：只用 mock 验证**

运行：`pytest tests/test_live_execution.py -v`

期望：测试不会发送真实订单。live adapter 在 gate 不满足时拒绝运行。

---

### 任务 10：CLI 工作流

**文件：**
- 创建：`src/polybot/cli.py`
- 测试：`tests/test_cli.py`

- [ ] **步骤 1：添加命令**

命令：

```bash
polybot geocheck
polybot markets --query "fed"
polybot paper-run --markets config/markets.json --fair-values config/fair_values.csv
polybot live-run --markets config/markets.json --fair-values config/fair_values.csv
polybot cancel-all --market <condition_id>
```

- [ ] **步骤 2：让 live 命令显式输出风险信息**

`live-run` 必须输出 geoblock 检测到的 country/region、wallet/funder address、最大名义金额限制，并要求 env gates 已开启。不得提示用户输入 private key。

- [ ] **步骤 3：验证**

运行：`pytest tests/test_cli.py -v`

期望：`paper-run` 不需要 secrets；`live-run` 在 gate 缺失时以非零状态退出。

---

### 任务 11：回测与报告

**文件：**
- 创建：`src/polybot/backtest/runner.py`
- 创建：`src/polybot/reporting.py`
- 测试：`tests/test_backtest.py`

- [ ] **步骤 1：从 CSV 回测**

输入列：`timestamp`、`market_id`、`token_id`、`best_bid`、`best_ask`、`midpoint`、`fair_probability`、`resolved_value`。

- [ ] **步骤 2：计算指标**

报告：trade count、win rate、average edge、realized PnL、max drawdown、max exposure、rejected signal count。

- [ ] **步骤 3：验证**

运行：`pytest tests/test_backtest.py -v`

期望：确定性 fixture 产生固定 PnL 和 drawdown。

---

### 任务 12：最终验证

**文件：**
- 修改：`README.md`

- [ ] **步骤 1：运行完整检查**

```bash
ruff check .
pytest -v
```

期望：所有检查通过。

- [ ] **步骤 2：运行安全 smoke commands**

```bash
polybot geocheck
polybot markets --query "election"
polybot paper-run --markets config/markets.example.json --fair-values config/fair_values.example.csv
```

期望：没有命令发送真实订单。

- [ ] **步骤 3：记录 live-readiness checklist**

`README.md` 必须说明真实交易需要：法律与平台资格允许、geoblock 未 blocked、secrets 有效、余额和 allowance 有效、显式 env gates 开启、策略配置已测试。

---

## 给另一个 Codex 窗口的执行说明

- 先只实现 paper mode。
- 测试期间不要发送真实订单。
- 不要提交 `.env`、private keys、API credentials、wallet seed phrases 或生成的 SQLite 数据库。
- 优先使用官方 SDK，不要直接手写 REST 签名。
- 如果 SDK 方法名和本计划不同，先检查已安装的 `py-clob-client` examples，并先更新 wrapper tests。
- geoblock 失败、auth 失败、allowance 失败或风控拒单，都必须作为 live trading 的硬停止条件。
- 每个任务完成后提交一次，commit message 示例：`chore: scaffold polybot`、`feat: add geoblock gate`、`feat: add paper execution`。
