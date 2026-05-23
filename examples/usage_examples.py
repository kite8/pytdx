# coding=utf-8
"""
pytdx 翻新后的使用示例

演示如何使用翻新后的 pytdx 获取股票数据
"""

import sys
import os

# 添加 pytdx 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pytdx.hq import TdxHq_API


def example_stock_list():
    """示例：获取股票列表"""
    print("\n" + "="*60)
    print("示例 1: 获取股票列表")
    print("="*60)

    api = TdxHq_API()

    with api.connect('119.97.185.59', 7709):
        # 获取上海市场股票列表
        stocks = api.get_security_list(1, 0)

        if stocks:
            # 转换为 DataFrame
            df = api.to_df(stocks)

            print(f"\n获取 {len(df)} 条股票记录")
            print("\n前 10 条记录:")
            print(df.head(10).to_string())

            # 查找包含 "ETF" 的股票
            etf_stocks = df[df['name'].str.contains('ETF', na=False)]
            print(f"\n包含 'ETF' 的股票: {len(etf_stocks)} 个")
            print(etf_stocks.head(10)[['code', 'name']].to_string())


def example_realtime_quotes():
    """示例：获取实时行情"""
    print("\n" + "="*60)
    print("示例 2: 获取实时行情")
    print("="*60)

    api = TdxHq_API()

    with api.connect('119.97.185.59', 7709):
        # 获取几个常见股票的实时行情
        stocks = [
            (1, '600000'),  # 浦发银行
            (0, '000001'),  # 平安银行
            (1, '510300'),  # 沪深300ETF
        ]

        quotes = api.get_security_quotes(stocks)

        if quotes:
            df = api.to_df(quotes)

            print(f"\n获取 {len(df)} 条实时行情")
            print("\n实时行情数据:")
            print(df[['code', 'price', 'open', 'high', 'low', 'vol', 'amount']].to_string())


def example_kline_data():
    """示例：获取 K 线数据"""
    print("\n" + "="*60)
    print("示例 3: 获取 K 线数据")
    print("="*60)

    api = TdxHq_API()

    with api.connect('119.97.185.59', 7709):
        # 获取平安银行的日 K 线
        # category=9 表示日K线
        # market=0 表示深圳市场
        klines = api.get_security_bars(9, 0, '000001', 0, 10)

        if klines:
            df = api.to_df(klines)

            print(f"\n获取 {len(df)} 条 K 线记录")
            print("\nK 线数据:")
            print(df[['datetime', 'open', 'close', 'high', 'low', 'vol', 'amount']].to_string())


def example_block_info():
    """示例：获取板块信息"""
    print("\n" + "="*60)
    print("示例 4: 获取板块信息")
    print("="*60)

    api = TdxHq_API()

    with api.connect('119.97.185.59', 7709):
        # 获取指数板块
        blocks = api.get_and_parse_block_info('block_zs.dat')

        if blocks:
            df = api.to_df(blocks)

            print(f"\n获取 {len(df)} 条板块记录")

            # 统计每个板块的股票数量
            block_stats = df.groupby('blockname').size().reset_index(name='count')
            block_stats = block_stats.sort_values('count', ascending=False)

            print("\n板块股票数量统计（前 10）:")
            print(block_stats.head(10).to_string())


def example_encoding():
    """示例：使用编码工具"""
    print("\n" + "="*60)
    print("示例 5: 使用编码工具")
    print("="*60)

    from pytdx.util.encoding import decode_tdx_text, decode_tdx_code

    # 解码中英混合名称
    name_bytes = b'\xd6\xd0\xd6\xa4\xba\xec\xc0\xfbETF\xc1\xaa\xbd\xd3\x00\x00'
    name = decode_tdx_text(name_bytes)
    print(f"\n解码名称: {name}")

    # 解码证券代码
    code_bytes = b'000001\x00'
    code = decode_tdx_code(code_bytes)
    print(f"解码代码: {code}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("pytdx 翻新后的使用示例")
    print("="*60)

    try:
        example_stock_list()
        example_realtime_quotes()
        example_kline_data()
        example_block_info()
        example_encoding()

        print("\n" + "="*60)
        print("所有示例运行完成")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n运行示例时出错: {e}")
        import traceback
        traceback.print_exc()
