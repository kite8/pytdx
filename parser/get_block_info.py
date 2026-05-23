# coding=utf-8

from pytdx.parser.base import BaseParser
from pytdx.reader.block_reader import BlockReader,BlockReader_TYPE_FLAT
from pytdx.helper import get_datetime, get_volume, get_price
from collections import OrderedDict
import struct
import six



class GetBlockInfoMeta(BaseParser):
    def setParams(self, block_file):
        if type(block_file) is six.text_type:
            block_file = block_file.encode("utf-8")
        pkg = bytearray.fromhex(u'0C 39 18 69 00 01 2A 00 2A 00 C5 02')
        pkg.extend(struct.pack(u"<{}s".format(0x2a - 2), block_file))
        self.send_pkg = pkg


    def parseResponse(self, body_buf):
        (size, _, hash_value, _ ) = struct.unpack(u"<I1s32s1s", body_buf)
        return {
            "size": size,
            "hash_value" : hash_value
        }

class GetBlockInfo(BaseParser):

    def setParams(self, block_file, start, size):
        if type(block_file) is six.text_type:
            block_file = block_file.encode("utf-8")
        pkg = bytearray.fromhex(u'0c 37 18 6a 00 01 6e 00 6e 00 b9 06')
        #pkg = bytearray.fromhex(u'0c 33 18 6a 00 01 6e 00 6e 00 b9 06 60 ea 00 00 30 75 00 00')
        pkg.extend(struct.pack(u"<II{}s".format(0x6e-10), start, size, block_file))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        return body_buf[4:]



def get_and_parse_block_info(client, blockfile):
    """
    从服务器下载并解析板块文件

    Args:
        client: TdxHq_API 客户端实例
        blockfile: 板块文件名（如 "block_zs.dat"）

    Returns:
        list: 板块数据列表，失败返回 None

    Raises:
        可能抛出 BlockReaderError 如果文件格式错误
    """
    import logging

    try:
        meta = client.get_block_info_meta(blockfile)
    except Exception as e:
        logging.warning(f"获取板块文件 {blockfile} 元信息失败: {e}")
        return None

    if not meta:
        logging.warning(f"板块文件 {blockfile} 元信息为空")
        return None

    size = meta['size']

    # 验证文件大小合理性
    if size == 0:
        logging.info(f"板块文件 {blockfile} 大小为 0")
        return []

    if size > 10 * 1024 * 1024:  # 10MB
        logging.warning(f"板块文件 {blockfile} 大小异常: {size} 字节")
        return None

    one_chunk = 0x7530

    chuncks = size // one_chunk
    if size % one_chunk != 0:
        chuncks += 1

    file_content = bytearray()

    try:
        for seg in range(chuncks):
            start = seg * one_chunk
            piece_data = client.get_block_info(blockfile, start, size)

            if not piece_data:
                logging.warning(f"板块文件 {blockfile} 分片 {seg+1}/{chuncks} 下载失败")
                return None

            file_content.extend(piece_data)
    except Exception as e:
        logging.error(f"下载板块文件 {blockfile} 失败: {e}")
        return None

    # 验证下载的数据大小
    if len(file_content) < size:
        logging.warning(f"板块文件 {blockfile} 下载不完整: {len(file_content)}/{size} 字节")
        return None

    try:
        return BlockReader().get_data(file_content, BlockReader_TYPE_FLAT)
    except Exception as e:
        logging.error(f"解析板块文件 {blockfile} 失败: {e}")
        return None


if __name__ == '__main__':
    from pytdx.hq import TdxHq_API
    api = TdxHq_API()
    with api.connect():
        # ret = api.get_block_info("block_zs.dat", 0, 100)
        # print(len(ret))
        # ret = api.get_and_parse_block_info("block_fg.dat")
        # ret = api.get_and_parse_block_info("block_zs.dat")
        # ret = api.get_and_parse_block_info("block_gn.dat")
        # ret = api.get_and_parse_block_info("block.dat")
        ret = api.get_and_parse_block_info("block.dat")
        print(api.to_df(ret))


