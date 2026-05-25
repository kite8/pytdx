# pytdx 翻新第一阶段实施报告

日期：2026-05-23

## Phase 0 review 结论

| 问题 | 影响 | 本次处理 |
| --- | --- | --- |
| Phase 0 commit 已经改动生产 parser，不只是基线测试。 | 后续实现不能再把它视为纯测试快照。 | 保留可用部分，重做错误协议和测试。 |
| `get_security_list` 把新版记录误判为 41 字节。 | 新版证券列表字段错位，名称和昨收解析都有风险。 | 改为 gotdx 的 37 字节布局。 |
| `get_security_list` 仍发送旧方法 `0x0450`。 | 即使 parser 支持 16 字节名称，也不会请求新版数据。 | 默认发送新版 `0x044d`，保留 `get_security_list_old()`。 |
| `tests/test_encoding.py` 和 `tests/test_quantaxis_compatibility.py` 在 import 时改 `sys.stdout/stderr`。 | Windows 下 pytest capture 会崩溃。 | 删除测试目录里的联调脚本，重建 pytest-safe 单测。 |
| QA 兼容脚本里 `get_instrument_info(0, 100, market)` 参数错误。 | 在 QA 环境中直接报错。 | 新脚本使用 pytdx 当前签名 `get_instrument_info(start, count)`。 |
| `get_report_file_by_size()` 预填充 `bytearray(filesize)`。 | 下载失败时返回一串零字节，QA 难以判断真实空数据。 | 改为空 `bytearray()` 后按 chunk 追加。 |

## 已完成改造

| 模块 | 改造内容 |
| --- | --- |
| `util/encoding.py` | 固定长度字段统一解码；GB18030/GBK fallback；末尾半个中文字符会被丢弃，不再生成 `�`；清理 `\0` 和控制字符。 |
| `parser/get_security_list.py` | 默认请求 gotdx 新版 `0x044d`；按 37 字节解析 16 字节名称字段；旧 `0x0450` 作为 `GetSecurityListOld` 保留；旧版昨收价改为 float32。 |
| `hq.py` | 保持 `get_security_list(market, start)` 旧签名；新增 `get_security_list_range(market, start, count)` 和 `get_security_list_old()`；补 `get_block_dat_ver_up()`；修复文件下载零填充。 |
| `reader/block_reader.py` | 支持 bytes/bytearray/memoryview；按 gotdx 记录边界解析；结构损坏抛 `BlockReaderError`；字段名保持 QA 兼容。 |
| `parser/get_block_info.py` | 分片下载使用本段 chunk size；下载失败仍返回 `None`，保留旧调用方兼容。 |
| 扩展行情/公司信息 parser | `ex_get_markets`、`ex_get_instrument_info`、`ex_get_instrument_quote_list`、公司信息目录/正文改用统一解码。 |
| `tests/` | 新增 pytest-safe fixture 测试：编码、证券列表新旧协议、板块文件、多块错位、文件下载 alias。 |
| `scripts/qa_compat_smoke.py` | 独立 QA/pytdx smoke 脚本，不再被 pytest 收集；支持 `--mode direct/qa/both/auto`。 |

## 验证结果

| 验证 | 结果 |
| --- | --- |
| `python -m pytest pytdx\tests -q` | 16 passed |
| 在线股票 smoke：`119.97.185.59:7709` | 证券数量、新版/旧版列表、`block_gn.dat`、行情、K 线均通过。 |
| 名称专项扫描 | 前 8000 条深沪列表中 `\ufffd` 数量为 0；ETF/红利样本能正常解码。 |
| `incon.dat` | 接口返回 bytearray，当前服务器返回 0 字节；QA 侧仍可走 zip fallback。 |
| 在线扩展行情：`121.37.232.167:7727` | `get_instrument_info(0, 100)` 返回 100 条；`get_markets()` 当前超时。 |

## 后续建议

1. 在安装 QUANTAXIS 的环境中运行：

   ```powershell
   python scripts\qa_compat_smoke.py --mode qa --stock-ip 119.97.185.59 --stock-port 7709 --future-ip 121.37.232.167 --future-port 7727
   ```

2. 如果 QA 的 `QA_fetch_get_extensionmarket_info()` 仍依赖 `get_markets()`，需要额外确认可用扩展行情服务器，或补一个基于 `get_instrument_info()` 的兼容 fallback。
3. 第二阶段再进入主行情、K 线、扩展行情 quote list 的协议级系统翻新。

## 2026-05-25 补齐安装和兼容入口

| 文件 | 作用 |
| --- | --- |
| `setup.py` / `pyproject.toml` / `requirements.txt` / `MANIFEST.in` | 补齐本地 fork 的 pip 安装能力，支持 `pip install -e .`。 |
| `INSTALL.md` | 记录同环境卸载旧 pytdx、安装本仓库、验证导入路径、处理旧全局包遮蔽 editable 安装的方法。 |
| `scripts/verify_local_install.py` | 不修改 `sys.path`，直接检查当前解释器的 `import pytdx` 是否指向本仓库。 |
| `tests/test_quantaxis_compatibility.py` | 恢复旧文档中的入口；pytest 下只做轻量导入检查，手动执行时转发到 `scripts/qa_compat_smoke.py`。 |

### 本轮验证

| 验证 | 结果 |
| --- | --- |
| `python -B -m pytest tests -q -s -p no:cacheprovider` | 19 passed |
| `python tests\test_quantaxis_compatibility.py --help` | 旧入口可用，并透出 smoke 脚本参数。 |
| `python scripts\qa_compat_smoke.py --mode direct ...` | 10/11 passed；股票列表、板块、行情、K 线、期货合约列表通过；`get_markets()` 在 `121.37.232.167:7727` 超时。 |
| `python scripts\verify_local_install.py` | 当前 Anaconda 仍被旧的 `E:\ProgramData\anaconda3\Lib\site-packages\pytdx` 遮蔽；清理步骤已写入 `INSTALL.md`。 |
