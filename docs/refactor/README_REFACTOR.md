# pytdx 翻新说明

## 概述

本次翻新针对 pytdx 进行了兼容性改进，重点解决了 QUANTAXIS 使用中遇到的编码问题、名称解析问题和板块解析问题。

**核心原则**: 保持 QUANTAXIS 现有调用方式不变，所有改进都是向后兼容的。

## 主要改进

### 1. 统一编码处理 ✓

新增 `pytdx.util.encoding` 模块，提供统一的字符串编码/解码函数：

- `decode_tdx_text()` - 解码固定长度文本字段（支持 GBK/GB18030）
- `decode_tdx_code()` - 解码证券代码字段
- 自动处理 `\0` 填充、控制字符、截断的多字节字符

**解决的问题**:
- ✓ 中英混合名称解析错误（如"中证红利ETF联接"）
- ✓ 长名称被截断
- ✓ 解码异常导致程序崩溃

### 2. 股票列表解析增强 ✓

改进 `pytdx/parser/get_security_list.py`：

- 支持新版协议（41 字节/记录，16 字节名称字段）
- 保留旧版协议兼容（29 字节/记录，8 字节名称字段）
- 自动检测协议版本
- 使用统一编码函数

**解决的问题**:
- ✓ ETF 等长名称无法完整显示
- ✓ 名称包含非法字符
- ✓ 解析失败返回空列表

### 3. 板块解析硬化 ✓

改进 `pytdx/reader/block_reader.py` 和 `pytdx/parser/get_block_info.py`：

- 添加文件大小和边界校验
- 使用统一编码函数
- 明确的异常类型和错误处理
- 详细的日志记录

**解决的问题**:
- ✓ 板块文件解析失败静默返回空
- ✓ 板块名称编码错误
- ✓ 无法区分空数据和解析失败

### 4. 补齐缺失方法 ✓

在 `pytdx/hq.py` 中添加：

- `get_block_dat_ver_up()` - QUANTAXIS 需要的板块文件下载方法

## 兼容性保证

### 保持不变
- ✓ API 类名和方法名
- ✓ 方法参数和返回值结构
- ✓ DataFrame 列名
- ✓ Import 路径

### 新增内容
- 编码处理模块 `pytdx.util.encoding`
- 异常类型 `BlockReaderError`
- 日志记录（使用 Python logging）

## 测试

### 编码测试
```bash
python util/encoding.py
```

### QUANTAXIS 兼容性测试
```bash
python tests/test_quantaxis_compatibility.py --ip 119.97.185.59 --port 7709
```

### 使用示例
```bash
python examples/usage_examples.py
```

## 测试结果

**测试服务器**: 119.97.185.59:7709

**通过项目**:
- ✓ 股票列表获取（深圳、上海）
- ✓ 实时行情获取
- ✓ K 线数据获取
- ✓ DataFrame 转换和索引设置

**已知问题**:
- ⚠ 部分服务器数据本身包含非法字符（如 "ChatGPT�"）
- ⚠ 板块数据中部分记录需要进一步过滤

## 在 QUANTAXIS 中使用

### 安装
```bash
cd E:\develop\quant\pytdx
pip install -e .
```

### 验证
```python
from pytdx.hq import TdxHq_API

api = TdxHq_API()
with api.connect('119.97.185.59', 7709):
    # 测试股票列表
    stocks = api.get_security_list(1, 0)
    df = api.to_df(stocks)
    print(df.head())
    
    # 测试板块
    blocks = api.get_and_parse_block_info('block_zs.dat')
    if blocks:
        df_blocks = api.to_df(blocks)
        print(df_blocks.head())
```

## 文件结构

```
pytdx/
├── util/
│   ├── encoding.py          # 新增：统一编码处理
│   └── __init__.py          # 修改：导出编码函数
├── parser/
│   ├── get_security_list.py # 修改：支持新版协议
│   └── get_block_info.py    # 修改：添加错误处理
├── reader/
│   └── block_reader.py      # 修改：硬化解析逻辑
├── hq.py                    # 修改：添加 get_block_dat_ver_up
├── tests/
│   ├── test_encoding.py     # 新增：编码测试
│   └── test_quantaxis_compatibility.py  # 新增：QA 兼容性测试
├── examples/
│   └── usage_examples.py    # 新增：使用示例
├── .gitignore               # 新增
└── docs/
    └── refactor/
        ├── REFACTOR_REPORT.md       # 新增：详细报告
        └── README_REFACTOR.md       # 本文件
```

## 后续计划

根据 `docs/pytdx-refresh/pytdx_refresh_plan_for_quantaxis.md`，后续阶段包括：

- **第 2 阶段**: 主行情与扩展行情协议翻新
- **第 3 阶段**: 连接、host、并发和稳定性
- **第 4 阶段**: gotdx 增强能力的 Python 化

## 参考文档

- `docs/pytdx-refresh/pytdx_refresh_plan_for_quantaxis.md` - 完整翻新计划
- `docs/refactor/REFACTOR_REPORT.md` - 详细执行报告
- `docs/pytdx-refresh/gotdx_pytdx_feature_comparison.md` - gotdx 与 pytdx 功能对比

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
