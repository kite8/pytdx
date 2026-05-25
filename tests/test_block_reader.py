import struct

import pytest

from pytdx.parser.get_block_info import get_and_parse_block_info
from pytdx.reader.block_reader import (
    BlockReader,
    BlockReaderError,
    BlockReader_TYPE_GROUP,
    BlockReader_TYPE_FLAT,
)


def _pack_block_file(blocks):
    data = bytearray(b"\x00" * 384)
    data.extend(struct.pack("<H", len(blocks)))

    for blockname, block_type, codes in blocks:
        block_start = len(data)
        data.extend(blockname.encode("gb18030").ljust(9, b"\x00")[:9])
        data.extend(struct.pack("<HH", len(codes), block_type))

        code_bytes = bytearray()
        for code in codes:
            code_bytes.extend(code.encode("ascii").ljust(7, b"\x00")[:7])
        code_bytes.extend(b"\x00" * (2800 - len(code_bytes)))
        data.extend(code_bytes)
        assert len(data) - block_start == 2813

    return bytes(data)


def test_block_reader_parses_flat_records():
    data = _pack_block_file([
        ("红利ETF", 1, ["000001", "600000"]),
        ("概念板", 2, ["300001"]),
    ])

    result = BlockReader().get_data(data, BlockReader_TYPE_FLAT)

    assert [row["code"] for row in result] == ["000001", "600000", "300001"]
    assert [row["code_index"] for row in result] == [0, 1, 0]
    assert result[0]["blockname"] == "红利ETF"
    assert result[0]["block_type"] == 1
    assert result[2]["blockname"] == "概念板"
    assert result[2]["block_type"] == 2


def test_block_reader_parses_group_records():
    data = _pack_block_file([("红利ETF", 2, ["000001", "600000"])])

    result = BlockReader().get_data(data, BlockReader_TYPE_GROUP)

    assert result[0]["blockname"] == "红利ETF"
    assert result[0]["block_type"] == 2
    assert result[0]["stock_count"] == 2
    assert result[0]["code_list"] == "000001,600000"


def test_block_reader_raises_on_truncated_data():
    data = _pack_block_file([("红利ETF", 1, ["000001", "600000"])])

    with pytest.raises(BlockReaderError):
        BlockReader().get_data(data[:409], BlockReader_TYPE_FLAT)


def test_get_and_parse_block_info_uses_chunk_sizes(monkeypatch):
    requested = []
    captured = {}

    class DummyClient:
        def get_block_info_meta(self, blockfile):
            return {"size": 0x7530 + 17}

        def get_block_info(self, blockfile, start, size):
            requested.append((start, size))
            return b"x" * size

    def fake_get_data(self, data, result_type):
        captured["length"] = len(data)
        captured["result_type"] = result_type
        return [{"length": len(data)}]

    monkeypatch.setattr(BlockReader, "get_data", fake_get_data)

    result = get_and_parse_block_info(DummyClient(), "block_gn.dat")

    assert requested == [(0, 0x7530), (0x7530, 17)]
    assert captured["length"] == 0x7530 + 17
    assert result == [{"length": 0x7530 + 17}]
