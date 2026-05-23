# coding=utf-8

from pytdx.parser.base import BaseParser
from pytdx.helper import get_datetime, get_volume, get_price
from pytdx.util.encoding import decode_tdx_text, decode_tdx_code
from collections import OrderedDict
import struct


class GetSecurityList(BaseParser):
    """
    获取证券列表

    支持两种协议格式：
    1. 旧版：29 字节记录，8 字节名称字段
    2. 新版：41 字节记录，16 字节名称字段（支持更长的中英混合名称）

    自动检测协议版本并使用对应的解析逻辑。
    """

    def setParams(self, market, start):
        pkg = bytearray.fromhex(u'0c 01 18 64 01 01 06 00 06 00 50 04')
        pkg_param = struct.pack("<HH", market, start)
        pkg.extend(pkg_param)
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0
        (num, ) = struct.unpack("<H", body_buf[:2])
        pos += 2

        if num == 0:
            return []

        # 检测协议版本：根据剩余数据长度判断
        remaining_len = len(body_buf) - 2

        # 尝试新版协议（41 字节/记录）
        if remaining_len >= 41 and remaining_len % 41 == 0:
            return self._parse_new_format(body_buf, pos, num)
        # 尝试旧版协议（29 字节/记录）
        elif remaining_len >= 29 and remaining_len % 29 == 0:
            return self._parse_old_format(body_buf, pos, num)
        # 混合格式或数据不完整，尝试智能解析
        else:
            # 优先尝试新版
            try:
                if remaining_len >= num * 41:
                    return self._parse_new_format(body_buf, pos, num)
            except:
                pass

            # 回退到旧版
            try:
                if remaining_len >= num * 29:
                    return self._parse_old_format(body_buf, pos, num)
            except:
                pass

            # 都失败了，返回空列表并记录错误
            import logging
            logging.warning(f"无法解析证券列表：num={num}, remaining_len={remaining_len}")
            return []

    def _parse_new_format(self, body_buf, pos, num):
        """
        解析新版协议（41 字节/记录）

        字段布局：
        - code: 6 字节（UTF-8）
        - volunit: 2 字节（uint16）
        - name: 16 字节（GBK/GB18030）
        - reversed_bytes1: 4 字节
        - decimal_point: 1 字节（uint8）
        - pre_close: 4 字节（int32）
        - reversed_bytes2: 8 字节
        """
        stocks = []

        for i in range(num):
            one_bytes = body_buf[pos: pos + 41]

            if len(one_bytes) < 41:
                break

            try:
                (code_bytes, volunit,
                 name_bytes, reversed_bytes1, decimal_point,
                 pre_close_raw, reversed_bytes2) = struct.unpack("<6sH16s4sBI8s", one_bytes)

                code = decode_tdx_code(code_bytes)
                name = decode_tdx_text(name_bytes)
                pre_close = get_volume(pre_close_raw)

                one = OrderedDict([
                    ('code', code),
                    ('volunit', volunit),
                    ('decimal_point', decimal_point),
                    ('name', name),
                    ('pre_close', pre_close),
                ])

                stocks.append(one)
                pos += 41

            except Exception as e:
                import logging
                logging.warning(f"解析新版证券列表记录失败 (index={i}): {e}")
                pos += 41
                continue

        return stocks

    def _parse_old_format(self, body_buf, pos, num):
        """
        解析旧版协议（29 字节/记录）

        字段布局：
        - code: 6 字节（UTF-8）
        - volunit: 2 字节（uint16）
        - name: 8 字节（GBK）
        - reversed_bytes1: 4 字节
        - decimal_point: 1 字节（uint8）
        - pre_close: 4 字节（int32）
        - reversed_bytes2: 4 字节
        """
        stocks = []

        for i in range(num):
            one_bytes = body_buf[pos: pos + 29]

            if len(one_bytes) < 29:
                break

            try:
                (code_bytes, volunit,
                 name_bytes, reversed_bytes1, decimal_point,
                 pre_close_raw, reversed_bytes2) = struct.unpack("<6sH8s4sBI4s", one_bytes)

                code = decode_tdx_code(code_bytes)
                name = decode_tdx_text(name_bytes)
                pre_close = get_volume(pre_close_raw)

                one = OrderedDict([
                    ('code', code),
                    ('volunit', volunit),
                    ('decimal_point', decimal_point),
                    ('name', name),
                    ('pre_close', pre_close),
                ])

                stocks.append(one)
                pos += 29

            except Exception as e:
                import logging
                logging.warning(f"解析旧版证券列表记录失败 (index={i}): {e}")
                pos += 29
                continue

        return stocks
