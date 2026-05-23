# pytdx 翻新变更清单

## 执行日期
2026-05-23

## 修改的文件

### 1. `hq.py`
**变更**: 添加 `get_block_dat_ver_up()` 方法

**原因**: QUANTAXIS 需要此方法下载板块文件（如 incon.dat）

**影响**: 无破坏性变更，纯新增方法

---

### 2. `parser/get_security_list.py`
**变更**: 
- 支持新版协议（41 字节/记录，16 字节名称）
- 保留旧版协议兼容（29 字节/记录，8 字节名称）
- 自动检测协议版本
- 使用 `decode_tdx_text()` 和 `decode_tdx_code()` 解码

**原因**: 解决中英混合长名称解析问题

**影响**: 无破坏性变更，返回字段和结构保持不变

---

### 3. `parser/get_block_info.py`
**变更**:
- 添加文件大小验证
- 添加下载完整性检查
- 使用 logging 记录错误
- 改进错误处理逻辑

**原因**: 解决板块文件解析失败静默返回空的问题

**影响**: 无破坏性变更，返回字段和结构保持不变

---

### 4. `reader/block_reader.py`
**变更**:
- 添加 `BlockReaderError` 异常类
- 添加文件大小和边界校验
- 使用 `decode_tdx_text()` 和 `decode_tdx_code()` 解码
- 添加股票数量合理性验证
- 过滤空代码
- 详细的日志记录

**原因**: 硬化板块文件解析，防止坏数据导致崩溃

**影响**: 无破坏性变更，返回字段和结构保持不变

---

### 5. `util/__init__.py`
**变更**: 导出 `decode_tdx_text`, `decode_tdx_code`, `safe_encode_gbk`

**原因**: 使编码函数可以从 `pytdx.util` 直接导入

**影响**: 无破坏性变更，纯新增导出

---

## 新增的文件

### 1. `util/encoding.py`
**功能**: 统一的 TDX 协议字符串编码/解码工具

**提供的函数**:
- `decode_tdx_text()` - 解码固定长度文本字段（GBK/GB18030）
- `decode_tdx_code()` - 解码证券代码字段（UTF-8）
- `safe_encode_gbk()` - 安全编码为 GBK
- `validate_text_field()` - 验证解码后的文本

**特性**:
- 支持 GB18030（兼容 GBK）
- 自动去除 `\0` 填充和控制字符
- 处理截断的多字节字符
- 防止解码异常

---

### 2. `tests/test_encoding.py`
**功能**: 编码处理单元测试

**测试覆盖**:
- 正常的中英混合名称
- 截断的多字节字符
- 包含控制字符
- 证券代码解码
- 空数据和全 null
- 长名称（16 字节）
- GB18030 特有字符

---

### 3. `tests/test_quantaxis_compatibility.py`
**功能**: QUANTAXIS 兼容性集成测试

**测试覆盖**:
- 股票列表获取（深圳、上海、ETF）
- 板块信息获取（指数、风格、概念）
- 实时行情获取
- K 线数据获取
- 扩展市场列表
- DataFrame 转换和字段验证

**使用方法**:
```bash
python tests/test_quantaxis_compatibility.py --ip 119.97.185.59 --port 7709
```

---

### 4. `examples/usage_examples.py`
**功能**: 使用示例脚本

**示例内容**:
- 获取股票列表
- 获取实时行情
- 获取 K 线数据
- 获取板块信息
- 使用编码工具

---

### 5. `.gitignore`
**功能**: Git 忽略文件配置

**忽略内容**:
- Python 缓存文件（`__pycache__/`, `*.pyc`）
- 虚拟环境（`venv/`, `env/`）
- IDE 配置（`.vscode/`, `.idea/`）
- 临时文件（`*.log`, `*.tmp`）

---

### 6. `REFACTOR_REPORT.md`
**功能**: 详细的翻新执行报告

**内容**:
- 完成的工作清单
- 测试结果
- 兼容性保证
- 未完成的工作（后续阶段）
- 使用建议
- 已知问题

---

### 7. `README_REFACTOR.md`
**功能**: 翻新说明文档

**内容**:
- 概述
- 主要改进
- 兼容性保证
- 测试方法
- 在 QUANTAXIS 中使用
- 文件结构
- 后续计划

---

### 8. `CHANGELOG.md`（本文件）
**功能**: 变更清单

---

## 删除的文件

无

---

## 兼容性影响

### 无影响的部分
- ✓ 所有公开 API 的方法名和参数
- ✓ 返回值的结构和字段名
- ✓ DataFrame 的列名
- ✓ Import 路径

### 新增的部分
- 编码处理模块 `pytdx.util.encoding`
- 异常类型 `BlockReaderError`
- 日志记录（使用 Python logging）

### 行为变化
- 股票列表解析：现在能正确解析 16 字节长名称
- 板块解析：现在会记录详细的错误日志
- 编码处理：现在使用 `replace` 策略而不是 `ignore`，保留更多信息

---

## 测试验证

### 编码测试
```bash
cd E:\develop\quant\pytdx
python util/encoding.py
```

**结果**: ✓ 所有测试通过

### QA 兼容性测试
```bash
cd E:\develop\quant\pytdx
python tests/test_quantaxis_compatibility.py --ip 119.97.185.59 --port 7709
```

**结果**: 
- ✓ 股票列表获取
- ✓ 实时行情获取
- ✓ K 线数据获取
- ⚠ 部分板块数据包含非法字符（服务器数据问题）

---

## 升级建议

### 对于 QUANTAXIS 用户

1. **备份当前环境**（可选）
2. **安装本地版本**:
   ```bash
   cd E:\develop\quant\pytdx
   pip install -e .
   ```
3. **运行兼容性测试**:
   ```bash
   python tests/test_quantaxis_compatibility.py --ip 119.97.185.59 --port 7709
   ```
4. **在 QA 中验证关键功能**

### 对于其他用户

直接使用即可，所有改进都是向后兼容的。

---

## 回滚方案

如果遇到问题，可以回滚到原始版本：

```bash
cd E:\develop\quant\pytdx
git checkout HEAD~1
pip install -e .
```

---

## 后续计划

参考 `pytdx_refresh_plan_for_quantaxis.md`：

- **第 2 阶段**: 主行情与扩展行情协议翻新
- **第 3 阶段**: 连接、host、并发和稳定性
- **第 4 阶段**: gotdx 增强能力的 Python 化

---

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。
