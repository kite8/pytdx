import struct

from pytdx.parser.ex_get_instrument_info import GetInstrumentInfo
from pytdx.parser.ex_get_markets import GetMarkets


def test_get_markets_parser_decodes_mixed_names():
    body = struct.pack(
        "<H",
        1,
    ) + struct.pack(
        "<B32sB2s26s2s",
        1,
        "香港主板".encode("gb18030").ljust(32, b"\x00"),
        31,
        b"KH",
        b"\x00" * 26,
        b"\x00" * 2,
    )

    result = GetMarkets(None).parseResponse(body)

    assert len(result) == 1
    assert result[0]["category"] == 1
    assert result[0]["market"] == 31
    assert result[0]["name"] == "香港主板"
    assert result[0]["short_name"] == "KH"


def test_get_instrument_info_parser_decodes_mixed_names():
    body = struct.pack("<IH", 0, 1) + struct.pack(
        "<BB3s9s17s9s",
        3,
        47,
        b"\x00" * 3,
        b"IF2409\x00\x00\x00",
        "科创综指ETF".encode("gb18030").ljust(17, b"\x00"),
        "中金所".encode("gb18030").ljust(9, b"\x00"),
    )

    result = GetInstrumentInfo(None).parseResponse(body)

    assert len(result) == 1
    assert result[0]["category"] == 3
    assert result[0]["market"] == 47
    assert result[0]["code"] == "IF2409"
    assert result[0]["name"] == "科创综指ETF"
    assert result[0]["desc"] == "中金所"
