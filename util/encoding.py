# coding=utf-8
"""
统一的 TDX 协议字符串编码/解码工具

参考 gotdx 的编码处理策略，提供统一的固定长度字符串解码函数。
主要解决：
1. GBK/GB18030 编码的中英混合名称
2. 固定长度字段中的 \0 填充
3. 截断的多字节字符导致的解码错误
4. 控制字符的清理
"""

import re


def _decode_fixed_width_bytes(raw, encoding, errors):
    """Decode a fixed-width TDX field and drop only an incomplete trailing char."""
    try:
        return raw.decode(encoding)
    except UnicodeDecodeError as exc:
        if exc.end >= len(raw):
            return raw[:exc.start].decode(encoding, errors='ignore')
        return raw.decode(encoding, errors=errors)


def decode_tdx_text(data, encoding='gb18030', errors='replace', strip_null=True, strip_control=True):
    """
    解码 TDX 协议中的固定长度文本字段

    Args:
        data: bytes，原始字节数据
        encoding: str，编码格式，默认 gb18030（兼容 gbk）
        errors: str，解码错误处理策略
            - 'replace': 用 � 替换无法解码的字节（推荐，不会丢失信息）
            - 'ignore': 忽略无法解码的字节（会丢失信息）
            - 'strict': 抛出异常
        strip_null: bool，是否去除 \0 填充字符
        strip_control: bool，是否去除控制字符（\x00-\x1f，\x7f）

    Returns:
        str，解码后的文本

    Examples:
        >>> decode_tdx_text(b'\xba\xec\xc0\xfbETF\x00\x00')  # 红利ETF
        '红利ETF'
        >>> decode_tdx_text(b'\xd6\xd0\xd6\xa4\xba\xec\xc0\xfbETF\xc1\xaa\xbd\xd3\x00\x00')  # 中证红利ETF联接
        '中证红利ETF联接'
        >>> decode_tdx_text(b'\xba\xec\xc0\xfb')  # 截断的多字节字符
        '红利'
    """
    if not data:
        return ''

    if isinstance(data, str):
        text = data
    else:
        raw = bytes(data)
        if strip_null:
            raw = raw.rstrip(b'\x00')

        encodings = []
        for item in (encoding, 'gb18030', 'gbk'):
            if item and item not in encodings:
                encodings.append(item)

        text = None
        for item in encodings:
            try:
                text = _decode_fixed_width_bytes(raw, item, errors)
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if text is None:
            text = raw.decode('latin1', errors='replace')

    # 去除 \0 填充
    if strip_null:
        text = text.replace('\x00', '')

    # 去除控制字符（保留换行符和制表符）
    if strip_control:
        # 移除 \x00-\x08, \x0b-\x0c, \x0e-\x1f, \x7f
        # 保留 \x09 (tab), \x0a (LF), \x0d (CR)
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

    return text.strip()


def decode_tdx_code(data, encoding='utf-8', errors='replace'):
    """
    解码 TDX 协议中的证券代码字段

    证券代码通常是 ASCII/UTF-8 编码的数字和字母，不需要 GBK 解码。

    Args:
        data: bytes，原始字节数据
        encoding: str，编码格式，默认 utf-8
        errors: str，解码错误处理策略

    Returns:
        str，解码后的代码

    Examples:
        >>> decode_tdx_code(b'000001\x00')
        '000001'
        >>> decode_tdx_code(b'sh600000')
        'sh600000'
    """
    if not data:
        return ''

    try:
        code = data.decode(encoding, errors=errors)
    except (UnicodeDecodeError, LookupError):
        # 兜底用 latin1
        code = data.decode('latin1', errors='replace')

    # 去除 \0 和空白
    return code.rstrip('\x00').strip()


def safe_encode_gbk(text, errors='replace'):
    """
    安全地将文本编码为 GBK

    Args:
        text: str，要编码的文本
        errors: str，编码错误处理策略

    Returns:
        bytes，编码后的字节
    """
    if not text:
        return b''

    try:
        return text.encode('gbk', errors=errors)
    except (UnicodeEncodeError, LookupError):
        # 兜底用 gb18030
        return text.encode('gb18030', errors=errors)


def validate_text_field(text, field_name='', max_length=None, allow_empty=True):
    """
    验证解码后的文本字段是否合法

    Args:
        text: str，要验证的文本
        field_name: str，字段名（用于错误消息）
        max_length: int，最大长度限制
        allow_empty: bool，是否允许空字符串

    Returns:
        bool，是否合法

    Raises:
        ValueError: 如果验证失败
    """
    if not allow_empty and not text:
        raise ValueError(f"字段 {field_name} 不能为空")

    if max_length and len(text) > max_length:
        raise ValueError(f"字段 {field_name} 长度超过限制 {max_length}：{len(text)}")

    # 检查是否包含过多的替换字符（可能表示解码失败）
    replacement_ratio = text.count('�') / max(len(text), 1)
    if replacement_ratio > 0.3:
        raise ValueError(f"字段 {field_name} 包含过多无法解码的字符：{text}")

    return True


if __name__ == '__main__':
    # 测试用例
    import sys
    import io

    # 设置 stdout 为 UTF-8（Windows 兼容）
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 测试 1：正常的中英混合名称
    test1 = b'\xba\xec\xc0\xfbETF\x00\x00'
    result1 = decode_tdx_text(test1)
    print(f"测试 1 - 红利ETF: {result1}")
    assert result1 == '红利ETF', f"Expected '红利ETF', got '{result1}'"

    # 测试 2：长名称
    test2 = b'\xd6\xd0\xd6\xa4\xba\xec\xc0\xfbETF\xc1\xaa\xbd\xd3\x00\x00'
    result2 = decode_tdx_text(test2)
    print(f"测试 2 - 中证红利ETF联接: {result2}")
    assert result2 == '中证红利ETF联接', f"Expected '中证红利ETF联接', got '{result2}'"

    # 测试 3：纯英文
    test3 = b'QDII\x00\x00\x00\x00'
    result3 = decode_tdx_text(test3)
    print(f"测试 3 - QDII: {result3}")
    assert result3 == 'QDII', f"Expected 'QDII', got '{result3}'"

    # 测试 4：证券代码
    test4 = b'000001\x00'
    result4 = decode_tdx_code(test4)
    print(f"测试 4 - 代码: {result4}")
    assert result4 == '000001', f"Expected '000001', got '{result4}'"

    # 测试 5：截断的多字节字符（最后一个字节不完整）
    test5 = b'\xd6\xd0\xd0\xa1\xc6\xbd\xbe'  # "中小平" 但最后一个字不完整
    result5 = decode_tdx_text(test5)
    print(f"测试 5 - 截断字符: {repr(result5)}")
    # 截断字符会被替换，只检查前面的字符
    assert '中小平' in result5, f"Expected '中小平' in result, got '{result5}'"

    # 测试 6：包含控制字符
    test6 = b'\xba\xec\xc0\xfb\x01\x02ETF\x00'
    result6 = decode_tdx_text(test6)
    print(f"测试 6 - 控制字符: {result6}")
    assert result6 == '红利ETF', f"Expected '红利ETF', got '{result6}'"

    print("\n✓ 所有测试通过")
