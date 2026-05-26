# gotdx 相对 pytdx 的功能对比与迁移规划

核对范围：

- Python 仓库：`E:\develop\quant\pytdx`，当前提交 `daa6d37 create readme`
- Go 仓库：`E:\develop\quant\gotdx`，当前提交 `14bbb21 Merge pull request #21 from abulo/main`
- 核对日期：2026-05-22

## 总体结论

`gotdx` 不是对 `pytdx` 的逐行翻译，而是把主行情、扩展行情、F10/文件、板块、MAC 协议、调试工具和示例重新组织成一个 Go 风格的 `Client + proto` 体系。相对 `pytdx`，Go 版本的独有重点是 MAC 协议、TDX 商品语义入口、Web Viewer、更多主行情/扩展行情实验接口，以及更完整的 host 列表和测速入口。

`pytdx` 仍然保留一些 Go 版本没有覆盖的能力，主要是交易 HTTP 封装、本地 TDX 数据文件 reader、历史财务 crawler、命令行抓取/benchmark 和交易服务端安装脚本。如果后续目标是把 `gotdx` 的能力反哺到 Python，建议先迁移协议和高阶行情能力，再评估是否补 MAC/Goods/Web Viewer。

## 对比表

| 功能域 | pytdx 当前能力 | gotdx 当前能力 | 差异类型 | 迁移/处理建议 | 主要依据 |
| --- | --- | --- | --- | --- | --- |
| 客户端与连接模型 | 主行情 `TdxHq_API`、扩展行情 `TdxExHq_API` 分开；底层由 `BaseSocketClient` 处理连接、重试、心跳。 | 一个 `Client` 通过 `New`、`NewEx`、`NewMAC`、`NewMACEx` 和 `Connect`、`ConnectEx`、`ConnectMAC` 覆盖多类连接。 | 重新做了 | 若反哺 Python，先设计统一连接/配置层，旧的 `TdxHq_API`、`TdxExHq_API` 可保留为兼容包装。 | `pytdx/hq.py`、`pytdx/exhq.py`、`pytdx/base_socket_client.py`；`gotdx/client.go`、`gotdx/options.go` |
| 协议执行与解析层 | `parser/` 下按命令拆分 parser class，通常是 `setParams` + `parseResponse`。 | `proto/` 下按协议定义 request/reply struct，客户端通过泛型 `executeProtocol[T]` 执行。 | 重新做了 | 迁移时不要只照搬公开方法，应先按 Go 的 `proto` 结构补 Python 协议层，否则新增接口会反复返工。 | `pytdx/parser/*.py`；`gotdx/proto/*.go`、`gotdx/client_helpers.go` |
| 主行情基础接口 | 支持证券数量/列表、批量报价、K 线、指数 K 线、分时、历史分时、逐笔、历史逐笔、公司资料、财务、除权除息、板块和报表文件。 | 底层 `Get*` 与高阶 `Stock*` 双入口，覆盖数量、列表、报价、K 线、分时、历史、逐笔、F10、板块等。 | 重新做了 | 建议先做 API 映射表：旧 pytdx 方法继续可用，同时新增 `Stock*` 风格高阶入口。 | `pytdx/hq.py`；`gotdx/client_quote.go`、`gotdx/client_unified.go` |
| 主行情新增能力 | 未看到对应封装。 | 增加 `StockIndexInfo`、`StockIndexMomentum`、`StockChartSampling`、`StockAuction`、`StockTopBoard`、`StockUnusual`、`StockVolumeProfile`、`StockHistoryOrders`、`StockHistoryTransactionWithTrans`、`StockQuotesEncrypt`、`StockKLineOffset`、`StockFeature452` 等。 | 更新 / Go 独有接口 | 按业务价值拆分优先级：报价/K 线修正、集合竞价、异动/榜单、历史委托优先；实验接口后置。 | `gotdx/client_unified.go`、`gotdx/README.md` |
| 报价数据修正 | Python 解析出了 `decimal_point`、财务字段等基础数据，但公开行情 API 没有统一做价格小数位和换手率补齐。 | `StockQuotesDetail`、`StockQuotesList`、`StockQuotes` 会按证券列表 `DecimalPoint` 修正价格，并在能取得流通股本时补齐 `Turnover`；K 线和量价分布也有换手率补齐。 | 更新 | 这是对上层使用体验影响很大的增强，适合优先迁移到 Python 的高阶 API。 | `pytdx/parser/get_security_list.py`、`pytdx/parser/get_finance_info.py`；`gotdx/client_unified.go` |
| 扩展行情基础接口 | `TdxExHq_API` 支持市场列表、扩展标的数量/信息/报价、K 线、分时、历史分时、逐笔、历史逐笔、历史 K 线范围、报价列表。 | `Ex*` / `ExGet*` 覆盖扩展市场数量、分类、列表、报价、批量报价、K 线、分时、历史成交等。 | 重新做了 | 先把 pytdx 的 `exhq.py` 方法与 `Ex*` 方法逐个对齐，再补新增协议。 | `pytdx/exhq.py`；`gotdx/client_exquote.go`、`gotdx/client_unified.go` |
| 扩展行情新增能力 | 未看到 `ExListExtra`、`ExQuotes2`、`ExKLine2`、扩展板块、映射 2562、扩展表格等封装。 | 增加 `ExListExtra`、`ExQuotes2`、`ExKLine2`、`ExExperiment2487`、`ExExperiment2488`、`ExBoardList`、`ExMapping2562`、`ExTable`、`ExTableDetail`、`ExDownloadFullFile`。 | 更新 / Go 独有接口 | 建议优先迁移 `ExQuotes2`、`ExKLine2`、`ExMapping2562` 和表格下载；实验接口保留低阶 raw 能力即可。 | `gotdx/client_exquote.go`、`gotdx/client_unified.go`、`gotdx/proto/ex_*.go` |
| MAC 协议 | 未看到 MAC 连接、MAC host、MAC 板块或 MAC 报价协议。 | 完整新增 `MAC*` / `GetMAC*`：板块数量/列表、成分股、成分报价、动态位图报价、批量股票报价、单只快照、历史日期快照、逐笔、竞价、多日分时、股票摘要、资金流向、服务端信息、K 线偏移、文件查询/下载、市场监控、所属板块、统一 K 线。 | Go 独有 | 这是最大独有功能，建议作为独立里程碑，不要混入主行情修补任务。 | `gotdx/client_mac.go`、`gotdx/proto/mac_*.go`、`gotdx/examples/mac_*` |
| MAC 动态字段位图 | 无对应实现。 | 提供 `MACFieldBit`、`MACPresetField`、`MACFieldBitmap`、默认/完整位图和按 bit 构造位图的辅助函数。 | Go 独有 | 若迁移 MAC，字段位图工具应同步迁移，否则动态报价接口难用且容易填错。 | `gotdx/mac_bitmap.go`、`gotdx/proto/mac_board_members_dynamic.go` |
| TDX 商品语义入口 | 无 `goods_*` 语义分组。 | 新增 `GoodsCount`、`GoodsCategoryList`、`GoodsList`、`GoodsVarieties`、`GoodsQuote`、`GoodsQuotes`、`GoodsQuotesList`、`GoodsKLine`、`GoodsTickChart`、`GoodsChartSampling`、`GoodsHistoryTransaction`。 | Go 独有 | 可作为扩展行情之上的语义包装迁移，依赖 `Ex*` 和部分 MAC 能力。 | `gotdx/client_goods.go`、`gotdx/README.md` |
| F10、公司资料与文件 | 有公司信息分类/正文、财务、除权除息、报表文件下载，以及板块信息协议。 | 保留底层 `GetCompanyCategories`、`GetCompanyContent`、`GetFinanceInfo`、`GetXDXRInfo`、文件下载，并新增 `GetCompanyInfo` 聚合、`DownloadFullFile`、`GetBlockFile`、`GetTableFile`、`GetCSVFile`。 | 重新做了 / 更新 | 适合先迁移 `DownloadFullFile` 与 `GetCompanyInfo` 聚合，让旧低阶接口之上有更好用的高阶 API。 | `pytdx/hq.py`、`pytdx/parser/get_company_info_*.py`、`pytdx/parser/get_report_file.py`；`gotdx/client_company.go`、`gotdx/client_extras.go` |
| 板块文件解析 | 有 `get_block_info` 协议和本地 `BlockReader`/`CustomerBlockReader`。 | 新增 `ParseBlockFlat`、`ParseBlockGroups`、`GetParsedBlockFile`、`GetGroupedBlockFile`，把下载与结构化解析放到客户端侧。 | 重新做了 / 更新 | Python 可复用现有 reader 思路，但建议补一个网络下载后直接解析的高阶方法。 | `pytdx/parser/get_block_info.py`、`pytdx/reader/block_reader.py`；`gotdx/block.go` |
| Host 列表、测速和自动选择 | 有 `util/best_ip.py`、`pool/ippool.py`、`pool/hqpool.py`，但与行情客户端是相对独立的池化/测速工具。 | 内置 `MainHosts`、`BrokerHosts`、`ExHosts`、`MACHosts`、`MACExHosts`，支持 `ProbeHosts`、`ProbeAddresses`、`FastestHost`、`FastestAddress`，并可通过 `WithAutoSelectFastest` 连接前自动排序。 | 重新做了 / 更新 | 建议迁移成客户端配置能力，而不是继续只作为外部工具。 | `pytdx/util/best_ip.py`、`pytdx/pool/*.py`；`gotdx/hosts.go`、`gotdx/options.go` |
| Web 调试界面 | 无对应 Web UI。 | 内置 `cmd/webviewer`，可直接填参数、调用接口、查看返回字段，并包含 MAC 动态位图和 goods 分组。 | Go 独有 | 若 Python 侧要复刻，建议等协议和高阶 API 稳定后再做；短期可把 gotdx Web Viewer 当对照工具。 | `gotdx/cmd/webviewer/`、`gotdx/README.md` |
| 原始/实验协议调试 | 有 `RawParser` 和部分 setup command，但未看到 Go 版本这些主站/扩展实验接口。 | 增加 `MainTodoB`、`MainTodoFDE`、`MainClient264B`、`MainClient26AC`、`MainClient26AD`、`MainClient26AE`、`MainClient26B1`，以及扩展实验 `ExExperiment2487`、`ExExperiment2488`。 | Go 独有 / 更新 | 保留为低阶实验模块，不建议直接承诺为稳定业务 API。 | `pytdx/parser/raw_parser.py`；`gotdx/client_unified.go`、`gotdx/proto/main_*.go`、`gotdx/proto/ex_*.go` |
| 市场/代码工具 | Python 主要通过参数和少量内部选择逻辑处理市场与代码。 | `types` 包提供 `DetectMarket`、`DecodeStockCode`、`IsStock`、`IsSZStock`、`IsSHStock`、`IsBJStock`、`IsETF`、`IsIndex`、`CleanCode`，并维护市场、周期、排序等常量。 | 更新 | 适合迁移为独立 util，降低调用者手工判断市场的成本。 | `pytdx/hq.py`、`pytdx/params.py`；`gotdx/types/constants.go`、`gotdx/types/util.go` |
| 示例与验证资产 | 有 `bin/hqget.py`、`bin/hqbenchmark.py` 等命令行工具，仓库内未看到同等规模的单元测试。 | 有大量 `examples/*`、`*_test.go`、协议测试和可选集成测试。 | 更新 / 工程化增强 | 迁移 Python 功能时同步补最小协议解析测试，避免只靠真实行情站点验证。 | `pytdx/bin/*.py`；`gotdx/examples/*`、`gotdx/*_test.go`、`gotdx/proto/*_test.go` |
| 交易 HTTP 封装 | 有 `TdxTradeApi`，覆盖登录、登出、查询、下单、撤单、行情、还款、批量查询/下单/撤单，并有交易服务端安装脚本。 | 未看到 Go 对应交易模块。 | Python 独有 / Go 未覆盖 | 若目标是 Python 反哺 gotdx，无需处理；若目标是功能全量迁移到 Go，这是单独的大模块。 | `pytdx/trade/trade.py`、`pytdx/bin/get_tdx_trader_server.py` |
| 本地 TDX 文件 reader 与历史财务 crawler | 有日线、分钟线、扩展行情日线、板块、股本变迁、历史财务 reader，以及历史财务 crawler。 | Go 侧主要面向网络协议和部分文件/table/csv/block 解析，未看到本地 vipdoc reader 或财务 crawler。 | Python 独有 / Go 未覆盖 | 若只是补行情协议，可暂不迁移；若要替代 pytdx 的离线数据能力，需要单独规划 reader/crawler。 | `pytdx/reader/*.py`、`pytdx/crawler/*.py` |

## 建议推进顺序

| 阶段 | 目标 | 主要工作 | 交付物 |
| --- | --- | --- | --- |
| 1 | 建立可扩展协议层 | 参考 gotdx 的 `proto` 结构，把 Python 现有 parser 梳理成可复用 request/reply 定义；保留旧 API 兼容。 | 主行情和扩展行情基础接口不破坏，新增协议实现有单元测试。 |
| 2 | 补齐主行情/扩展行情更新项 | 先迁移报价小数位/换手率修正、`Stock*` 高阶入口、`ExQuotes2`、`ExKLine2`、`ExMapping2562`、扩展表格/文件下载。 | Python 新增高阶行情 API 与 gotdx 核心功能基本对齐。 |
| 3 | 整合 host、测速和高阶文件能力 | 把 `best_ip`/pool 与客户端配置打通，补 `DownloadFullFile`、`GetCompanyInfo`、网络板块文件解析。 | 可配置地址池、自动选最快节点、F10/板块高阶 API。 |
| 4 | 独立迁移 MAC 协议 | 新增 MAC host、握手、MAC request/reply、动态字段位图、MAC 高阶入口。 | `MAC*` 能力在 Python 侧可用，并有协议解析测试。 |
| 5 | 视需要迁移 Goods 和 Web Viewer | 基于扩展行情/MAC 增加 goods 语义包装；待 API 稳定后再做 Web Viewer。 | goods 高阶 API；可选 Web 调试界面。 |
| 6 | 保留或另行规划 Python-only 模块 | 交易、reader、crawler 和 benchmark 不属于 gotdx 已覆盖范围。 | 明确哪些模块继续由 pytdx 维护，哪些后续迁移。 |

