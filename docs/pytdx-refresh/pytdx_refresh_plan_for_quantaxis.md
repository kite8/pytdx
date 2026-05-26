# 兼容 QUANTAXIS 的 pytdx 翻新计划

核对范围：

- pytdx：`E:\develop\quant\pytdx`
- gotdx：`E:\develop\quant\gotdx`
- QUANTAXIS：`E:\develop\github\QUANTAXIS`
- 核对日期：2026-05-22

## 目标

在不破坏 QUANTAXIS（以下简称 QA）现有调用方式的前提下，参考 gotdx 的协议实现和工程组织，对 pytdx 做一次分阶段翻新。优先修复 QA 已经依赖且当前容易出错的部分：股票列表、板块文件、编码解码、空返回、连接稳定性和扩展行情列表。后续再逐步引入 gotdx 的新增能力，如新版扩展接口、MAC、Goods、Web Viewer 等。

本计划的核心原则是：`pytdx.hq.TdxHq_API`、`pytdx.exhq.TdxExHq_API`、reader、crawler、trade 的旧入口继续可用；新增能力放在兼容层或新方法里，不要求 QA 立刻改代码。

## QA 依赖面清单

| QA 文件 | pytdx 依赖 | 硬兼容要求 |
| --- | --- | --- |
| `QUANTAXIS/QAFetch/QATdx.py` | `TdxHq_API`、`TdxExHq_API`，主行情、扩展行情、板块、财务、除权除息、实时行情、K 线、逐笔。 | 旧方法名、参数顺序、返回 list/dict 结构、`api.to_df()` 结果列名必须保持。 |
| `QUANTAXIS/QAFetch/QATdx_adv.py` | `TdxHq_API` 连接池、`get_security_list`、`get_security_quotes`、`get_security_bars`。 | `connect()` 返回可用 API 对象；多线程场景下旧方法不能变成全局共享状态。 |
| `QUANTAXIS/QAFetch/QAfinancial.py` | `HistoryFinancialReader`、`HistoryFinancialCrawler`。 | reader/crawler 的 import 路径、`get_df()`、`fetch_and_parse()` 继续可用。 |
| `QUANTAXIS/QASU/save_tdx_file.py` | `pytdx.reader.TdxMinBarReader`。 | 本地分钟线 reader 的 import 路径和 DataFrame index/列不变。 |
| `requirements.txt` / `scripts/verify_compatibility.py` | `pytdx>=1.72`。 | 发布版本号应高于 QA 当前要求，或在 QA 侧改成本地 fork 的明确来源。 |

## QA 当前依赖的关键字段契约

| 场景 | QA 代码中的字段/结构假设 | pytdx 翻新时必须保证 |
| --- | --- | --- |
| 股票/指数/债券列表 | `code`、`volunit`、`decimal_point`、`name`、`pre_close`、`sse`；QA 会 `set_index(['code', 'sse'])`，并把 `name` 截到 6 个字符。 | `get_security_list()` 返回字段名不改，`name` 必须是 Python `str`，不能因 GBK 截断或非法字节抛错。 |
| 板块信息 | `blockname`、`block_type`、`code_index`、`code`；QA 会 drop `block_type`、`code_index`，按 `code` 建索引。 | `get_and_parse_block_info()` 返回 list，字段名不改；坏文件不能静默返回空，应可区分空数据和解析失败。 |
| 实时行情 | `datetime`、`last_close`、`code`、`open`、`high`、`low`、`price`、`cur_vol`、`s_vol`、`b_vol`、`vol`、五档买卖价量。 | `get_security_quotes()` 的旧字段名、价格单位和 `to_df()` 行为不改。 |
| K 线 | `open`、`close`、`high`、`low`、`vol`、`amount`、`year`、`month`、`day`、`hour`、`minute`、`datetime`。 | `get_security_bars()`、`get_index_bars()` 保持旧字段；新增字段只能追加，不能重命名。 |
| 除权除息 | QA 会 rename `panhouliutong` 等旧字段。 | `get_xdxr_info()` 旧字段名保持，新增标准字段可并存。 |
| 财务信息 | QA 直接 `api.to_df(api.get_finance_info(...))`。 | `get_finance_info()` 返回 dict，字段名和数值单位保持。 |
| 扩展市场列表 | `market`、`category`、`code`、`name`、`desc` 等字段；QA 用 market 过滤期货、港股、期权等。 | `TdxExHq_API.get_instrument_info()` 和 `get_markets()` 旧字段保持，编码修复不能改变 market/category 类型。 |

## 设计总览

| 层 | 计划 | 兼容策略 |
| --- | --- | --- |
| 旧 API 兼容层 | 保留 `TdxHq_API`、`TdxExHq_API`、`BaseSocketClient.to_df()`、reader/crawler/trade 的 import 路径。 | QA 默认继续走旧入口，无需改 `QUANTAXIS/QAFetch/QATdx.py`。 |
| 新协议层 | 参考 gotdx 的 `proto/`，在 pytdx 内新增结构化 request/reply 协议模块，先覆盖股票列表、板块、主行情、扩展行情。 | 旧 parser 可逐步替换内部实现，但返回仍转成旧 list/dict。 |
| 编码层 | 增加统一的固定长度字符串解码工具：GBK/GB18030 优先，去除 `\0` 和控制字符，支持 `errors='replace'` 或记录错误。 | 替换 scattered `decode('gbk')`、`decode('gbk', 'ignore')`，避免静默丢字或半个中文导致异常。 |
| 高阶修正层 | 引入 gotdx 的 `DecimalPoint`、流通股本、`Turnover` best-effort 修正逻辑，但放到新方法或 opt-in 参数。 | 旧 QA 输出不默认改变价格字段单位，避免历史数据不一致。 |
| Host/连接层 | 参考 gotdx 内置 host 列表、测速、自动选最快；整合 pytdx 现有 `util/best_ip.py`、`pool/`。 | `connect(ip, port, time_out=...)` 行为不变；新增 `auto_select_fastest` 只在显式开启时生效。 |
| 测试层 | 建立 QA 兼容测试、协议解析 fixture 测试、真实站点可选集成测试。 | 没有真实网络时也能验证编码、字段和 DataFrame 契约。 |

## 分阶段实施计划

### 第 0 阶段：兼容基线与测试夹具

| 工作项 | 细节 | 验收标准 |
| --- | --- | --- |
| 建立 QA 调用契约测试 | 在 pytdx 仓库增加测试，模拟 QA 对 `get_security_list()`、`get_and_parse_block_info()`、`get_security_quotes()`、`get_security_bars()`、`get_instrument_info()` 的 `to_df()` 使用方式。 | 测试明确断言字段名、类型、空数据行为和 DataFrame 列。 |
| 加入编码 fixture | 构造 GBK/GB18030 固定长度字节样本：`红利ETF`、`中证红利ETF`、`红利ETF联接`、英文名、带 `\0` 填充、截断中文。 | 解码结果是合法 `str`；截断样本不会让整个列表解析失败。 |
| 增加 gotdx 对照样本 | 从 gotdx 复用或仿造 `proto` 测试样本，特别是新版 16 字节证券名称、板块文件结构。 | pytdx 解析结果与 gotdx 对同一 fixture 的语义一致。 |
| 记录当前行为 | 对当前 pytdx 的旧 parser 做快照测试，标明哪些字段不能改，哪些 bug 计划修。 | 后续改动能明确区分兼容破坏和预期修复。 |

### 第 1 阶段：先修 QA 痛点，保持 API 不变

| 工作项 | 参考 gotdx | pytdx 改造点 | 验收标准 |
| --- | --- | --- | --- |
| 股票列表新版解析 | gotdx `proto/get_security_list.go` 使用 16 字节名称字段，旧协议在 `get_security_list_old.go` 保留。 | 改造 `parser/get_security_list.py`：优先支持新版记录布局；保留旧 29 字节布局 fallback；公开方法仍叫 `get_security_list(market, start)`。 | QA 的 `QA_fetch_get_stock_list(type_='etf')` 能得到非空 DataFrame，`中证红利ETF` 类名称不因 8 字节截断报错。 |
| 统一字符串解码 | gotdx `proto.Utf8ToGbk` 统一去 `\0` 和控制字符。 | 新增 `pytdx.util.encoding`，提供 `decode_tdx_text(data, encoding='gb18030', errors='replace')`、`decode_tdx_code()`；替换股票列表、板块、扩展市场 info 中的裸 decode。 | 所有 parser 返回字符串均可 JSON 序列化、CSV 保存和 pandas 存储。 |
| 板块文件解析硬化 | gotdx `block.go` 有长度、header、code 边界检查。 | 改造 `reader/block_reader.py` 和 `parser/get_block_info.py`：保留字段名 `blockname/block_type/code_index/code`；解析失败返回明确异常，网络下载失败返回 `None` 的旧行为可通过兼容包装保留。 | QA `QA_fetch_get_stock_block()` 对空文件、坏块、正常块有可预测行为，不再因为局部坏字节整体空返回。 |
| `incon.dat` 下载入口补齐 | QA 调用 `api.get_block_dat_ver_up("incon.dat")`，当前本地 pytdx 未看到该方法。 | 明确补 `get_block_dat_ver_up()` 或兼容 alias，内部可复用文件下载协议。 | QA 板块逻辑不再依赖不存在的方法；拿不到 `incon.dat` 时仍走 QA 的 zip fallback。 |
| 返回空值策略 | gotdx 多数协议返回 error，不吞掉问题。 | pytdx 内部区分连接失败、协议解析失败、服务器空数据；旧 API 在 `raise_exception=False` 时仍可返回 `None`/空 list，但日志记录原因。 | QA 旧代码不崩；调试时能看到失败原因。 |

### 第 2 阶段：主行情与扩展行情协议翻新

| 工作项 | 参考 gotdx | pytdx 改造点 | 兼容注意 |
| --- | --- | --- | --- |
| 主行情 parser 结构化 | `client_quote.go` + `proto/get_*`。 | 逐步把 `parser/get_security_quotes.py`、`get_security_bars.py`、`get_index_bars.py`、`get_transaction_data.py` 改成结构化 parser，保留旧 OrderedDict 输出顺序。 | QA 实时行情字段和价格单位不能默认变化。 |
| 分页列表能力 | gotdx `GetSecurityListRange(market,start,count)`。 | 给 pytdx 新增 `get_security_list_range(market, start, count=1000/1600)`，旧 `get_security_list()` 调用 range 版本。 | QA 仍按 1000 分页，不能强制改变默认页大小导致重复/漏数据。 |
| 扩展市场列表修复 | gotdx `ExGetList`、`ExGetCategoryList`、`ExGetQuotesList`。 | 先修 `ex_get_instrument_info.py`、`ex_get_instrument_quote_list.py` 的编码与边界；再补更完整的扩展分类/列表接口。 | QA 用 market/category 过滤期货、港股、期权，字段类型和名字保持。 |
| 文件/F10 高阶能力 | gotdx `GetCompanyInfo`、`DownloadFullFile`、`GetTableFile`、`GetCSVFile`。 | 在旧 `get_company_info_category/content`、`get_report_file_by_size` 外新增高阶方法，不替换旧方法。 | QA 当前财务/除权逻辑不直接改，减少风险。 |

### 第 3 阶段：连接、host、并发和稳定性

| 工作项 | 参考 gotdx | pytdx 改造点 | 验收标准 |
| --- | --- | --- | --- |
| 内置 host 列表升级 | gotdx `MainHosts`、`ExHosts`、`MACHosts` 等。 | 更新 `config/hosts.py`，区分主行情、扩展行情、券商、MAC；保留旧列表变量。 | QA `stock_ip_list` 仍可用，新 host 可被测速工具使用。 |
| 自动测速与选择 | gotdx `ProbeHosts`、`FastestHost`、`WithAutoSelectFastest`。 | 在 pytdx 新增 `probe_hosts()`、`fastest_host()`；`connect(auto_select_fastest=True)` 可选启用。 | `QATdx_adv.QA_Tdx_Executor` 继续可自行测速，不被默认行为影响。 |
| 重试与错误分类 | gotdx 连接失败返回 error；pytdx 当前有 `auto_retry` 和 `raise_exception`。 | 梳理 `TdxConnectionError`、解析错误、空响应错误；保留 `raise_exception=False` 的兼容行为。 | 真实服务器波动时 QA 不频繁崩溃，调试日志能定位原因。 |
| 多线程连接安全 | QA_adv 使用多个 `TdxHq_API` 实例入队。 | 不引入全局 socket；缓存和 host 选择按实例或只读全局实现。 | 并发 `get_security_quotes`、`get_security_bars` 不交叉污染。 |

### 第 4 阶段：gotdx 增强能力的 Python 化

| 能力 | 是否影响 QA | 建议 |
| --- | --- | --- |
| `DecimalPoint` 价格修正、`Turnover` 补齐 | 间接影响 QA，默认改动可能破坏历史一致性。 | 新增 `get_security_quotes_enhanced()`、`get_security_bars_enhanced()` 或 `adjust_decimal=True` 参数，默认关闭。 |
| 扩展行情 `ExQuotes2`、`ExKLine2`、`ExMapping2562`、`ExTable` | QA 有扩展行情列表和期货/期权需求。 | 优先迁移，作为 `TdxExHq_API` 新方法；旧方法保持。 |
| Goods 语义入口 | QA 有 `QA_fetch_get_goods_list`，但现在只是扩展市场过滤。 | 在扩展行情稳定后新增 `get_goods_*`，可让 QA 后续选择性接入。 |
| MAC 协议 | QA 当前未直接依赖。 | 独立包/模块规划，不进入第一轮兼容修复；等主行情和扩展行情稳定后再做。 |
| Web Viewer | QA 当前不依赖。 | 作为调试工具后置，不影响库核心。 |

### 第 5 阶段：QA 联调与发布策略

| 工作项 | 细节 | 验收标准 |
| --- | --- | --- |
| 本地 editable 安装联调 | 在 QA 环境中把 pytdx fork 以 editable/path 方式安装，覆盖 `pytdx>=1.72`。 | QA import `pytdx` 指向本地 fork，`QAFetch/QATdx.py` 无需修改即可运行关键函数。 |
| QA 核心函数 smoke test | 覆盖 `QA_fetch_get_stock_list`、`QA_fetch_get_stock_block`、`QA_fetch_get_stock_realtime`、`QA_fetch_get_stock_day`、`QA_fetch_get_future_list`、`QA_fetch_get_extensionmarket_list`。 | 每个函数返回非空或在网络不可用时给出明确可解释错误。 |
| 数据保存验证 | 针对股票列表、板块、实时行情、扩展列表生成 DataFrame 后保存到 CSV/JSON/Mongo 测试集合。 | 中英混合名称可保存和读回，无乱码、无空字符串替代真实名称。 |
| 版本发布 | pytdx fork 发布内部版本，例如 `1.72.qa1` 或 `1.73.0a0`；QA requirements 可暂时使用 git/path。 | QA 的兼容检查能识别新版本，不误装旧 pytdx。 |

## 优先级建议

| 优先级 | 任务 | 原因 |
| --- | --- | --- |
| P0 | 股票列表 16 字节名称解析、统一 GBK/GB18030 解码、板块解析硬化、`get_block_dat_ver_up` 兼容。 | 直接解决你提到的中英混合名称、解析错误、空返回、无法保存问题，也是 QA 当前高频路径。 |
| P1 | QA 契约测试、主行情 K 线/实时行情 parser 边界检查、扩展市场列表编码修复。 | 防止修 P0 时破坏 QA 其他调用，并提升常用行情稳定性。 |
| P2 | host 列表/测速整合、错误分类、分页 range 接口、文件/F10 高阶接口。 | 改善可用性和排障能力，降低线上波动影响。 |
| P3 | `ExQuotes2`、`ExKLine2`、Goods 语义入口、价格小数位/换手率增强。 | gotdx 的实用增强能力，但需要避免默认改变 QA 历史数据口径。 |
| P4 | MAC 协议、Web Viewer。 | 功能价值高，但 QA 当前不是硬依赖，应作为独立里程碑。 |

## 风险与决策点

| 风险 | 说明 | 处理 |
| --- | --- | --- |
| 旧 pytdx API 与 gotdx 字段语义不完全一致 | gotdx 的高阶接口会修正 decimal/turnover，直接默认迁移可能让 QA 的历史数据口径变化。 | 增强字段默认 opt-in；旧方法保持旧单位和字段。 |
| 真实 TDX 服务器协议差异 | 不同 host、不同时间返回字段可能不一致。 | parser 使用 fixture 单测保证基础正确，集成测试只作为可选 gate。 |
| QA 中 pandas 版本兼容问题 | QA 代码有 `.append()` 等旧 pandas 写法，pytdx 不应放大问题。 | pytdx 返回标准 DataFrame/list，不主动依赖 pandas 新特性；QA 侧另行升级。 |
| 编码错误被 `ignore` 静默吞掉 | 旧代码会丢字，导致空名或错名。 | 默认 `replace` 或可配置严格模式；日志记录原始 bytes 与字段位置。 |
| 直接调用 Go 代码的维护成本 | Python 调 gotdx 需要 cgo/ffi/subprocess 或服务化，复杂度高。 | 第一阶段以“移植 gotdx 协议实现和测试思想”为主，不把 Go 作为 pytdx 运行时依赖。 |

## 建议的第一轮开发任务拆分

1. 新增 `pytdx.util.encoding`，集中处理固定长度 GBK/GB18030 字符串。
2. 为 `parser/get_security_list.py` 添加新版 16 字节名称解析和旧版 fallback。
3. 为 `reader/block_reader.py` 添加边界校验、明确异常、统一解码；保持旧字段名。
4. 补齐或确认 `TdxHq_API.get_block_dat_ver_up()`，让 QA 板块路径可运行。
5. 增加 QA 契约测试：股票列表字段、板块字段、`to_df()` 输出、混合中英文名称 fixture。
6. 用 QA 本地 smoke test 验证 `QA_fetch_get_stock_list(type_='etf')` 和 `QA_fetch_get_stock_block()`。
7. 再进入主行情/扩展行情 parser 的系统性翻新。

