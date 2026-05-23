# coding=utf-8
"""
编码处理测试

测试 pytdx.util.encoding 模块对各种边界情况的处理能力
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pytdx.util.encoding import decode_tdx_text, decode_tdx_code


def test_normal_chinese_english_mix():
    """测试正常的中英混合名称"""
    print("=" * 60)
    print("测试 1: 正常的中英混合名称")
    print("=" * 60)

    test_cases = [
        (b'\xba\xec\xc0\xfbETF\x00\x00', '红利ETF'),
        (b'\xd6\xd0\xd6\xa4\xba\xec\xc0\xfbETF\xc1\xaa\xbd\xd3\x00\x00', '中证红利ETF联接'),
        (b'QDII\x00\x00\x00\x00', 'QDII'),
        (b'\xbb\xa6\xc9\xee300ETF\x00', '沪深300ETF'),
    ]

    for raw_bytes, expected in test_cases:
        result = decode_tdx_text(raw_bytes)
        status = "✓" if result == expected else "✗"
        print(f"{status} 输入: {raw_bytes.hex()}")
        print(f"  期望: {expected}")
        print(f"  实际: {result}")
        print()


def test_truncated_multibyte():
    """测试截断的多字节字符"""
    print("=" * 60)
    print("测试 2: 截断的多字节字符")
    print("=" * 60)

    test_cases = [
        # "中小平" 但最后一个字不完整
        (b'\xd6\xd0\xd0\xa1\xc6\xbd\xbe', '中小平'),
        # "红利" 完整
        (b'\xba\xec\xc0\xfb', '红利'),
        # "红" 后面截断
        (b'\xba\xec\xc0', '红'),
    ]

    for raw_bytes, expected_prefix in test_cases:
        result = decode_tdx_text(raw_bytes)
        # 截断的字符可能被替换为 �，所以只检查前缀
        status = "✓" if result.startswith(expected_prefix) or expected_prefix in result else "✗"
        print(f"{status} 输入: {raw_bytes.hex()}")
        print(f"  期望前缀: {expected_prefix}")
        print(f"  实际: {result}")
        print()


def test_control_characters():
    """测试包含控制字符的情况"""
    print("=" * 60)
    print("测试 3: 包含控制字符")
    print("=" * 60)

    test_cases = [
        (b'\xba\xec\xc0\xfb\x01\x02ETF\x00', '红利ETF'),
        (b'\x00\x00\xba\xec\xc0\xfbETF', '红利ETF'),
        (b'ETF\x00\x00\x00\x00', 'ETF'),
    ]

    for raw_bytes, expected in test_cases:
        result = decode_tdx_text(raw_bytes)
        status = "✓" if result == expected else "✗"
        print(f"{status} 输入: {raw_bytes.hex()}")
        print(f"  期望: {expected}")
        print(f"  实际: {result}")
        print()


def test_security_codes():
    """测试证券代码解码"""
    print("=" * 60)
    print("测试 4: 证券代码解码")
    print("=" * 60)

    test_cases = [
        (b'000001\x00', '000001'),
        (b'600000', '600000'),
        (b'sh600000', 'sh600000'),
        (b'159915\x00', '159915'),
    ]

    for raw_bytes, expected in test_cases:
        result = decode_tdx_code(raw_bytes)
        status = "✓" if result == expected else "✗"
        print(f"{status} 输入: {raw_bytes.hex()}")
        print(f"  期望: {expected}")
        print(f"  实际: {result}")
        print()


def test_empty_and_null():
    """测试空数据和全 null 的情况"""
    print("=" * 60)
    print("测试 5: 空数据和全 null")
    print("=" * 60)

    test_cases = [
        (b'', ''),
        (b'\x00\x00\x00\x00', ''),
        (b'\x00\x00\x00\x00\x00\x00\x00\x00', ''),
    ]

    for raw_bytes, expected in test_cases:
        result = decode_tdx_text(raw_bytes)
        status = "✓" if result == expected else "✗"
        print(f"{status} 输入: {raw_bytes.hex() if raw_bytes else '(empty)'}")
        print(f"  期望: '{expected}'")
        print(f"  实际: '{result}'")
        print()


def test_long_names():
    """测试长名称（16 字节）"""
    print("=" * 60)
    print("测试 6: 长名称（16 字节）")
    print("=" * 60)

    # 16 字节可以容纳更长的中英混合名称
    test_cases = [
        # "中证红利ETF联接" 约 14 字节（GBK）
        (b'\xd6\xd0\xd6\xa4\xba\xec\xc0\xfbETF\xc1\xaa\xbd\xd3\x00\x00', '中证红利ETF联接'),
        # "嘉实沪深300ETF" 约 15 字节
        (b'\xbc\xce\xca\xb5\xbb\xa6\xc9\xee300ETF\x00\x00\x00', '嘉实沪深300ETF'),
    ]

    for raw_bytes, expected in test_cases:
        result = decode_tdx_text(raw_bytes)
        status = "✓" if result == expected else "✗"
        print(f"{status} 输入长度: {len(raw_bytes)} 字节")
        print(f"  期望: {expected}")
        print(f"  实际: {result}")
        print()


def test_gb18030_specific():
    """测试 GB18030 特有字符"""
    print("=" * 60)
    print("测试 7: GB18030 特有字符")
    print("=" * 60)

    # 一些只在 GB18030 中存在的字符
    test_cases = [
        # "𠮷" (U+20BB7) 需要 GB18030
        (b'\x95\x32\x82\x36', '𠮷'),
    ]

    for raw_bytes, expected in test_cases:
        result = decode_tdx_text(raw_bytes)
        # GB18030 字符可能无法正确显示，但不应该抛异常
        print(f"输入: {raw_bytes.hex()}")
        print(f"  期望: {expected}")
        print(f"  实际: {result}")
        print(f"  状态: 解码成功（无异常）")
        print()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("pytdx 编码处理测试")
    print("=" * 60 + "\n")

    test_normal_chinese_english_mix()
    test_truncated_multibyte()
    test_control_characters()
    test_security_codes()
    test_empty_and_null()
    test_long_names()
    test_gb18030_specific()

    print("=" * 60)
    print("所有测试完成")
    print("=" * 60)
