# coding=utf-8
"""
QUANTAXIS 兼容性测试脚本

模拟 QUANTAXIS 的调用方式，验证 pytdx 翻新后的兼容性。
此脚本应在安装了 QUANTAXIS 的环境中运行。

测试覆盖：
1. 股票列表获取（包括 ETF、指数等）
2. 板块信息获取
3. 实时行情获取
4. K 线数据获取
5. 扩展市场列表（期货、期权等）
6. DataFrame 转换和字段验证

使用方法：
    python test_quantaxis_compatibility.py --ip 119.97.185.59 --port 7709
"""

import sys
import os
import io
import argparse
import traceback
from datetime import datetime

# Windows 控制台 UTF-8 支持
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加 pytdx 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API


class QACompatibilityTester:
    """QUANTAXIS 兼容性测试器"""

    def __init__(self, ip, port, timeout=10):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.api = None
        self.test_results = []

    def connect(self):
        """连接到 TDX 服务器"""
        print(f"\n{'='*60}")
        print(f"连接到 TDX 服务器: {self.ip}:{self.port}")
        print(f"{'='*60}")

        try:
            self.api = TdxHq_API(raise_exception=True, auto_retry=True)
            result = self.api.connect(self.ip, self.port, time_out=self.timeout)

            if result:
                print("✓ 连接成功")
                return True
            else:
                print("✗ 连接失败")
                return False

        except Exception as e:
            print(f"✗ 连接异常: {e}")
            traceback.print_exc()
            return False

    def disconnect(self):
        """断开连接"""
        if self.api:
            try:
                self.api.disconnect()
                print("\n✓ 已断开连接")
            except:
                pass

    def test_stock_list(self):
        """测试股票列表获取（模拟 QA_fetch_get_stock_list）"""
        print(f"\n{'='*60}")
        print("测试 1: 股票列表获取")
        print(f"{'='*60}")

        test_cases = [
            (0, 'stock', '深圳股票'),
            (1, 'stock', '上海股票'),
            (0, 'etf', '深圳ETF'),
            (1, 'etf', '上海ETF'),
        ]

        for market, type_name, desc in test_cases:
            try:
                print(f"\n测试 {desc} (market={market})...")

                # 获取数量
                count_result = self.api.get_security_count(market)
                if count_result is None:
                    print(f"  ✗ 获取 {desc} 数量失败")
                    self.test_results.append((f"{desc}数量", False, "返回 None"))
                    continue

                count = count_result
                print(f"  证券数量: {count}")

                # 获取列表（分页）
                all_stocks = []
                page_size = 1000
                for start in range(0, min(count, 2000), page_size):
                    stocks = self.api.get_security_list(market, start)

                    if stocks is None:
                        print(f"  ✗ 获取 {desc} 列表失败 (start={start})")
                        break

                    all_stocks.extend(stocks)

                if not all_stocks:
                    print(f"  ✗ {desc} 列表为空")
                    self.test_results.append((f"{desc}列表", False, "列表为空"))
                    continue

                # 转换为 DataFrame（模拟 QA 的 to_df）
                df = self.api.to_df(all_stocks)

                # 验证字段
                required_fields = ['code', 'volunit', 'decimal_point', 'name', 'pre_close']
                missing_fields = [f for f in required_fields if f not in df.columns]

                if missing_fields:
                    print(f"  ✗ 缺少字段: {missing_fields}")
                    self.test_results.append((f"{desc}字段", False, f"缺少 {missing_fields}"))
                    continue

                # 验证数据类型
                print(f"  ✓ 获取 {len(df)} 条记录")
                print(f"  字段: {list(df.columns)}")

                # 检查中英混合名称
                sample_names = df['name'].head(10).tolist()
                print(f"  样本名称: {sample_names}")

                # 验证名称是否包含非法字符
                invalid_names = df[df['name'].str.contains('\x00|�', na=False)]
                if len(invalid_names) > 0:
                    print(f"  ⚠ 发现 {len(invalid_names)} 个包含非法字符的名称")
                    print(f"    示例: {invalid_names['name'].head(3).tolist()}")
                    self.test_results.append((f"{desc}名称", False, "包含非法字符"))
                else:
                    print(f"  ✓ 所有名称解码正常")
                    self.test_results.append((f"{desc}列表", True, f"{len(df)} 条记录"))

                # 模拟 QA 的 set_index 操作
                try:
                    # QA 会添加 sse 字段并设置索引
                    df['sse'] = 'sz' if market == 0 else 'sh'
                    df_indexed = df.set_index(['code', 'sse'])
                    print(f"  ✓ DataFrame 索引设置成功")
                except Exception as e:
                    print(f"  ✗ DataFrame 索引设置失败: {e}")
                    self.test_results.append((f"{desc}索引", False, str(e)))

            except Exception as e:
                print(f"  ✗ 测试 {desc} 异常: {e}")
                traceback.print_exc()
                self.test_results.append((f"{desc}测试", False, str(e)))

    def test_block_info(self):
        """测试板块信息获取（模拟 QA_fetch_get_stock_block）"""
        print(f"\n{'='*60}")
        print("测试 2: 板块信息获取")
        print(f"{'='*60}")

        block_files = [
            ('block_zs.dat', '指数板块'),
            ('block_fg.dat', '风格板块'),
            ('block_gn.dat', '概念板块'),
        ]

        for block_file, desc in block_files:
            try:
                print(f"\n测试 {desc} ({block_file})...")

                # 获取板块信息
                result = self.api.get_and_parse_block_info(block_file)

                if result is None:
                    print(f"  ⚠ {desc} 返回 None（可能文件不存在或为空）")
                    self.test_results.append((f"{desc}", False, "返回 None"))
                    continue

                if len(result) == 0:
                    print(f"  ⚠ {desc} 为空")
                    self.test_results.append((f"{desc}", False, "列表为空"))
                    continue

                # 转换为 DataFrame
                df = self.api.to_df(result)

                # 验证字段
                required_fields = ['blockname', 'block_type', 'code_index', 'code']
                missing_fields = [f for f in required_fields if f not in df.columns]

                if missing_fields:
                    print(f"  ✗ 缺少字段: {missing_fields}")
                    self.test_results.append((f"{desc}字段", False, f"缺少 {missing_fields}"))
                    continue

                print(f"  ✓ 获取 {len(df)} 条记录")
                print(f"  字段: {list(df.columns)}")

                # 检查板块名称
                unique_blocks = df['blockname'].unique()
                print(f"  板块数量: {len(unique_blocks)}")
                print(f"  样本板块: {unique_blocks[:5].tolist()}")

                # 验证板块名称是否包含非法字符
                invalid_blocks = df[df['blockname'].str.contains('\x00|�', na=False)]
                if len(invalid_blocks) > 0:
                    print(f"  ⚠ 发现 {len(invalid_blocks)} 个包含非法字符的板块名")
                    self.test_results.append((f"{desc}名称", False, "包含非法字符"))
                else:
                    print(f"  ✓ 所有板块名解码正常")
                    self.test_results.append((f"{desc}", True, f"{len(unique_blocks)} 个板块"))

                # 模拟 QA 的处理：drop block_type 和 code_index，按 code 建索引
                try:
                    df_processed = df.drop(['block_type', 'code_index'], axis=1)
                    df_indexed = df_processed.set_index('code')
                    print(f"  ✓ DataFrame 处理成功")
                except Exception as e:
                    print(f"  ✗ DataFrame 处理失败: {e}")

            except Exception as e:
                print(f"  ✗ 测试 {desc} 异常: {e}")
                traceback.print_exc()
                self.test_results.append((f"{desc}测试", False, str(e)))

    def test_realtime_quotes(self):
        """测试实时行情获取（模拟 QA_fetch_get_stock_realtime）"""
        print(f"\n{'='*60}")
        print("测试 3: 实时行情获取")
        print(f"{'='*60}")

        # 测试几个常见股票
        test_stocks = [
            (1, '600000'),  # 浦发银行
            (0, '000001'),  # 平安银行
            (1, '510300'),  # 沪深300ETF
        ]

        try:
            print(f"\n测试批量获取实时行情...")

            result = self.api.get_security_quotes(test_stocks)

            if result is None or len(result) == 0:
                print(f"  ✗ 实时行情返回空")
                self.test_results.append(("实时行情", False, "返回空"))
                return

            # 转换为 DataFrame
            df = self.api.to_df(result)

            # 验证字段
            required_fields = ['code', 'open', 'high', 'low', 'price', 'last_close', 'vol']
            missing_fields = [f for f in required_fields if f not in df.columns]

            if missing_fields:
                print(f"  ✗ 缺少字段: {missing_fields}")
                self.test_results.append(("实时行情字段", False, f"缺少 {missing_fields}"))
                return

            print(f"  ✓ 获取 {len(df)} 条行情")
            print(f"  字段: {list(df.columns)}")
            print(f"\n  样本数据:")
            print(df[['code', 'price', 'open', 'high', 'low', 'vol']].to_string())

            self.test_results.append(("实时行情", True, f"{len(df)} 条记录"))

        except Exception as e:
            print(f"  ✗ 测试实时行情异常: {e}")
            traceback.print_exc()
            self.test_results.append(("实时行情测试", False, str(e)))

    def test_kline_data(self):
        """测试 K 线数据获取（模拟 QA_fetch_get_stock_day）"""
        print(f"\n{'='*60}")
        print("测试 4: K 线数据获取")
        print(f"{'='*60}")

        try:
            print(f"\n测试日 K 线数据...")

            # 获取平安银行日 K 线
            result = self.api.get_security_bars(9, 0, '000001', 0, 10)

            if result is None or len(result) == 0:
                print(f"  ✗ K 线数据返回空")
                self.test_results.append(("K线数据", False, "返回空"))
                return

            # 转换为 DataFrame
            df = self.api.to_df(result)

            # 验证字段
            required_fields = ['open', 'close', 'high', 'low', 'vol', 'amount', 'datetime']
            missing_fields = [f for f in required_fields if f not in df.columns]

            if missing_fields:
                print(f"  ✗ 缺少字段: {missing_fields}")
                self.test_results.append(("K线字段", False, f"缺少 {missing_fields}"))
                return

            print(f"  ✓ 获取 {len(df)} 条 K 线")
            print(f"  字段: {list(df.columns)}")
            print(f"\n  样本数据:")
            print(df[['datetime', 'open', 'close', 'high', 'low', 'vol']].head().to_string())

            self.test_results.append(("K线数据", True, f"{len(df)} 条记录"))

        except Exception as e:
            print(f"  ✗ 测试 K 线数据异常: {e}")
            traceback.print_exc()
            self.test_results.append(("K线数据测试", False, str(e)))

    def test_extension_market(self):
        """测试扩展市场列表（期货、期权等）"""
        print(f"\n{'='*60}")
        print("测试 5: 扩展市场列表")
        print(f"{'='*60}")

        try:
            print(f"\n连接扩展行情服务器...")

            # 使用期货服务器
            exapi = TdxExHq_API(raise_exception=True)
            if not exapi.connect('121.37.232.167', 7727):
                print(f"  ✗ 连接扩展行情服务器失败")
                self.test_results.append(("扩展市场连接", False, "连接失败"))
                return

            print(f"  ✓ 连接成功")

            # 获取市场列表
            markets = exapi.get_markets()

            if markets is None or len(markets) == 0:
                print(f"  ✗ 市场列表返回空")
                self.test_results.append(("扩展市场列表", False, "返回空"))
                exapi.disconnect()
                return

            print(f"  ✓ 获取 {len(markets)} 个市场")

            # 获取第一个市场的品种信息
            if len(markets) > 0:
                market_code = markets[0]
                print(f"\n  测试市场 {market_code} 的品种信息...")

                instruments = exapi.get_instrument_info(0, 100, market_code)

                if instruments and len(instruments) > 0:
                    df = exapi.to_df(instruments)
                    print(f"  ✓ 获取 {len(df)} 个品种")
                    print(f"  字段: {list(df.columns)}")

                    # 检查名称编码
                    if 'name' in df.columns:
                        sample_names = df['name'].head(5).tolist()
                        print(f"  样本名称: {sample_names}")

                        invalid_names = df[df['name'].str.contains('\x00|�', na=False)]
                        if len(invalid_names) > 0:
                            print(f"  ⚠ 发现 {len(invalid_names)} 个包含非法字符的名称")
                            self.test_results.append(("扩展市场名称", False, "包含非法字符"))
                        else:
                            print(f"  ✓ 所有名称解码正常")
                            self.test_results.append(("扩展市场", True, f"{len(df)} 个品种"))
                else:
                    print(f"  ⚠ 品种信息为空")
                    self.test_results.append(("扩展市场品种", False, "返回空"))

            exapi.disconnect()

        except Exception as e:
            print(f"  ✗ 测试扩展市场异常: {e}")
            traceback.print_exc()
            self.test_results.append(("扩展市场测试", False, str(e)))

    def print_summary(self):
        """打印测试摘要"""
        print(f"\n{'='*60}")
        print("测试摘要")
        print(f"{'='*60}\n")

        total = len(self.test_results)
        passed = sum(1 for _, success, _ in self.test_results if success)
        failed = total - passed

        print(f"总计: {total} 项测试")
        print(f"通过: {passed} 项")
        print(f"失败: {failed} 项")
        print()

        if failed > 0:
            print("失败项目:")
            for name, success, message in self.test_results:
                if not success:
                    print(f"  ✗ {name}: {message}")
        else:
            print("✓ 所有测试通过！")

        print(f"\n{'='*60}")

    def run_all_tests(self):
        """运行所有测试"""
        if not self.connect():
            print("\n✗ 无法连接到服务器，测试终止")
            return False

        try:
            self.test_stock_list()
            self.test_block_info()
            self.test_realtime_quotes()
            self.test_kline_data()
            self.test_extension_market()

        finally:
            self.disconnect()

        self.print_summary()

        return all(success for _, success, _ in self.test_results)


def main():
    parser = argparse.ArgumentParser(description='QUANTAXIS 兼容性测试')
    parser.add_argument('--ip', default='119.97.185.59', help='TDX 服务器 IP')
    parser.add_argument('--port', type=int, default=7709, help='TDX 服务器端口')
    parser.add_argument('--timeout', type=int, default=10, help='连接超时时间（秒）')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("QUANTAXIS 兼容性测试")
    print(f"{'='*60}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"服务器: {args.ip}:{args.port}")
    print(f"{'='*60}")

    tester = QACompatibilityTester(args.ip, args.port, args.timeout)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
