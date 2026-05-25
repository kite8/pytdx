# coding=utf-8

from pytdx.parser.base import BaseParser
from pytdx.util.encoding import decode_tdx_text, decode_tdx_code
from collections import OrderedDict
import struct


class GetSecurityList(BaseParser):
    """
    获取证券列表

    支持两种协议格式：
    1. 旧版：29 字节记录，8 字节名称字段
    2. 新版：37 字节记录，16 字节名称字段（支持更长的中英混合名称）

    默认发送新版协议 0x044d，返回字段保持 pytdx/QUANTAXIS 兼容。
    """

    DEFAULT_COUNT = 1000

    def setParams(self, market, start, count=DEFAULT_COUNT):
        # ReqHeader layout: zip, seq_id, packet_type, pkg_len1, pkg_len2, method.
        # pkg_len includes method(2) + payload(14). The method is already in header.
        pkg = bytearray(struct.pack("<BIBHHH", 0x0c, 0x01641801, 0x01, 16, 16, 0x044d))
        pkg.extend(struct.pack("<HIII", market, int(start), int(count), 0))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0
        if len(body_buf) < 2:
            return []

        (num, ) = struct.unpack("<H", body_buf[:2])
        pos += 2

        if num == 0:
            return []

        remaining_len = len(body_buf) - 2

        # New protocol records are 37 bytes. Old protocol records are 29 bytes.
        if remaining_len >= num * 37:
            return self._parse_new_format(body_buf, pos, num)
        if remaining_len >= num * 29:
            return self._parse_old_format(body_buf, pos, num)

        import logging
        logging.warning("无法解析证券列表：num=%s, remaining_len=%s", num, remaining_len)
        return []

    def _parse_new_format(self, body_buf, pos, num):
        """
        解析新版协议（37 字节/记录）

        字段布局：
        - code: 6 字节（UTF-8）
        - volunit: 2 字节（uint16）
        - name: 16 字节（GBK/GB18030）
        - reversed_bytes1: 4 字节
        - decimal_point: 1 字节（uint8）
        - pre_close: 4 字节（float32）
        - reversed_bytes2: 4 字节
        """
        stocks = []

        for i in range(num):
            one_bytes = body_buf[pos: pos + 37]

            if len(one_bytes) < 37:
                break

            try:
                (code_bytes, volunit, name_bytes, reversed_bytes1,
                 decimal_point, pre_close, unknown2, unknown3) = struct.unpack("<6sH16s4sBfHH", one_bytes)

                code = decode_tdx_code(code_bytes)
                name = decode_tdx_text(name_bytes)

                one = OrderedDict([
                    ('code', code),
                    ('volunit', volunit),
                    ('decimal_point', decimal_point),
                    ('name', name),
                    ('pre_close', pre_close),
                ])

                stocks.append(one)
                pos += 37

            except Exception as e:
                import logging
                logging.warning("解析新版证券列表记录失败 (index=%s): %s", i, e)
                pos += 37
                continue

        return stocks

    def _parse_old_format(self, body_buf, pos, num):
        """
        解析旧版协议（29 字节/记录）

        字段布局：
        - code: 6 字节（UTF-8）
        - volunit: 2 字节（uint16）
        - name: 8 字节（GBK）
        - legacy_unknown1: 2 字节
        - reversed_bytes1: 2 字节
        - decimal_point: 1 字节（uint8）
        - pre_close: 4 字节（float32）
        - reversed_bytes2: 2 字节
        - reversed_bytes3: 2 字节
        """
        stocks = []

        for i in range(num):
            one_bytes = body_buf[pos: pos + 29]

            if len(one_bytes) < 29:
                break

            try:
                (code_bytes, volunit, name_bytes, _legacy_unknown1,
                 _reversed_bytes1, decimal_point, pre_close,
                 unknown2, unknown3) = struct.unpack("<6sH8sHHBfHH", one_bytes)

                code = decode_tdx_code(code_bytes)
                name = decode_tdx_text(name_bytes)

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
                logging.warning("解析旧版证券列表记录失败 (index=%s): %s", i, e)
                pos += 29
                continue

        return stocks


class GetSecurityListOld(GetSecurityList):
    """旧版证券列表协议 0x0450，保留给需要兼容旧服务器的调用方。"""

    def setParams(self, market, start, count=None):
        pkg = bytearray.fromhex(u'0c 01 18 64 01 01 06 00 06 00 50 04')
        pkg.extend(struct.pack("<HH", market, int(start)))
        self.send_pkg = pkg
