#coding: utf-8
import struct
from pytdx.reader.base_reader import BaseReader
from pytdx.util.encoding import decode_tdx_text, decode_tdx_code
from collections import OrderedDict
import pandas as pd
import os
from io import BytesIO
import logging

"""
参考这个 http://blog.csdn.net/Metal1/article/details/44352639

板块文件格式：
- Header: 384 字节
- 板块数量: 2 字节（uint16）
- 板块记录：每个板块包含
  - 板块名: 9 字节（GBK）
  - 股票数量: 2 字节（uint16）
  - 板块类型: 2 字节（uint16）
  - 股票代码列表: 每个代码 7 字节（UTF-8）
  - 固定跳转: 2800 字节对齐
"""

BlockReader_TYPE_FLAT = 0
BlockReader_TYPE_GROUP = 1


class BlockReaderError(Exception):
    """板块文件解析错误"""
    pass


class BlockReader(BaseReader):

    def get_df(self, fname, result_type=BlockReader_TYPE_FLAT):
        result = self.get_data(fname, result_type)
        return pd.DataFrame(result)

    def get_data(self, fname, result_type=BlockReader_TYPE_FLAT):
        """
        解析板块文件

        Args:
            fname: 文件路径或 bytearray 数据
            result_type: 返回格式（FLAT 或 GROUP）

        Returns:
            list: 板块数据列表

        Raises:
            BlockReaderError: 文件格式错误或解析失败
        """
        result = []

        # 读取数据
        if type(fname) is not bytearray:
            if not os.path.exists(fname):
                raise BlockReaderError(f"板块文件不存在: {fname}")

            try:
                with open(fname, "rb") as f:
                    data = f.read()
            except IOError as e:
                raise BlockReaderError(f"无法读取板块文件 {fname}: {e}")
        else:
            data = fname

        # 验证文件大小
        if len(data) < 386:  # 最小：384 header + 2 num
            raise BlockReaderError(f"板块文件太小，无效格式: {len(data)} 字节")

        # 解析板块数量
        pos = 384
        try:
            (num, ) = struct.unpack("<H", data[pos: pos+2])
        except struct.error as e:
            raise BlockReaderError(f"无法解析板块数量: {e}")

        pos += 2

        if num == 0:
            logging.info("板块文件为空（板块数量为 0）")
            return []

        # 解析每个板块
        for i in range(num):
            try:
                # 检查剩余数据是否足够
                if pos + 9 > len(data):
                    logging.warning(f"板块 {i+1}/{num} 数据不完整，停止解析")
                    break

                # 板块名（9 字节）
                blockname_raw = data[pos: pos+9]
                pos += 9
                blockname = decode_tdx_text(blockname_raw)

                if pos + 4 > len(data):
                    logging.warning(f"板块 {i+1}/{num} '{blockname}' 缺少股票数量和类型字段")
                    break

                # 股票数量和板块类型
                stock_count, block_type = struct.unpack("<HH", data[pos: pos+4])
                pos += 4

                # 验证股票数量合理性
                if stock_count > 10000:
                    logging.warning(f"板块 '{blockname}' 股票数量异常: {stock_count}，跳过")
                    pos += 2800  # 跳到下一个板块
                    continue

                block_stock_begin = pos
                codes = []

                # 解析股票代码
                for code_index in range(stock_count):
                    if pos + 7 > len(data):
                        logging.warning(f"板块 '{blockname}' 股票代码 {code_index+1}/{stock_count} 数据不完整")
                        break

                    one_code_raw = data[pos: pos+7]
                    pos += 7

                    try:
                        one_code = decode_tdx_code(one_code_raw)

                        # 过滤空代码
                        if not one_code:
                            continue

                        if result_type == BlockReader_TYPE_FLAT:
                            result.append(
                                OrderedDict([
                                    ("blockname", blockname),
                                    ("block_type", block_type),
                                    ("code_index", code_index),
                                    ("code", one_code),
                                ])
                            )
                        elif result_type == BlockReader_TYPE_GROUP:
                            codes.append(one_code)

                    except Exception as e:
                        logging.warning(f"板块 '{blockname}' 代码 {code_index+1} 解析失败: {e}")
                        continue

                if result_type == BlockReader_TYPE_GROUP:
                    result.append(
                        OrderedDict([
                            ("blockname", blockname),
                            ("block_type", block_type),
                            ("stock_count", len(codes)),  # 使用实际解析成功的数量
                            ("code_list", ",".join(codes))
                        ])
                    )

                # 跳到下一个板块（2800 字节对齐）
                pos = block_stock_begin + 2800

            except Exception as e:
                logging.error(f"解析板块 {i+1}/{num} 时发生错误: {e}")
                # 尝试跳到下一个板块
                try:
                    pos = block_stock_begin + 2800
                except:
                    break

        return result


"""
读取通达信备份的自定义板块文件夹，返回格式与通达信板块一致，在广发证券客户端上测试通过，其它未测试
"""


class CustomerBlockReader(BaseReader):

    def get_df(self, fname, result_type=BlockReader_TYPE_FLAT):
        result = self.get_data(fname, result_type)
        return pd.DataFrame(result)

    def get_data(self, fname, result_type=BlockReader_TYPE_FLAT):

        result = []

        if not os.path.isdir(fname):
            raise Exception('not a directory')

        block_file = '/'.join([fname,'blocknew.cfg'])

        if not os.path.exists(block_file):
            raise Exception('file not exists')

        block_data = open(block_file,'rb').read()

        pos = 0
        result = []
        # print(block_data.decode('gbk','ignore'))
        while pos < len(block_data):
            n1 = block_data[pos:pos + 50].decode('gbk', 'ignore').rstrip("\x00")
            n2 = block_data[pos + 50:pos + 120].decode('gbk', 'ignore').rstrip("\x00")
            pos = pos + 120
            
            n1 = n1.split('\x00')[0]
            n2 = n2.split('\x00')[0]
            bf = '/'.join([fname,n2 + '.blk'])
            if not os.path.exists(bf):
                raise Exception('file not exists')

            codes = open(bf).read().splitlines()
            if result_type == BlockReader_TYPE_FLAT:
                for index,code in enumerate(codes):
                    if code is not '':
                        result.append(
                            OrderedDict([
                                ("blockname",n1),
                                ("block_type",n2),
                                ('code_index',index),
                                ('code',code[1:])
                            ])
                        )

            if result_type == BlockReader_TYPE_GROUP:
                cc = [c[1:] for c in codes if c is not '']
                result.append(
                    OrderedDict([
                        ("blockname",n1),
                        ("block_type",n2),
                        ("stock_count",len(cc)),
                        ("code_list",",".join(cc))
                    ])
                )

        return result


if __name__ == '__main__':
    df = BlockReader().get_df("/Users/rainx/tmp/block_zs.dat")
    print(df)
    df2 = BlockReader().get_df("/Users/rainx/tmp/block_zs.dat", BlockReader_TYPE_GROUP)
    print(df2)
    df3 = CustomerBlockReader().get_df('C:/Users/fit/Desktop/blocknew')
    print(df3)
    df4 = CustomerBlockReader().get_df('C:/Users/fit/Desktop/blocknew',BlockReader_TYPE_GROUP)
    print(df4)
