import math
import struct

from pytdx.parser.get_security_list import GetSecurityList, GetSecurityListOld


def _pack_new_record(code, volunit, name, decimal_point, pre_close):
    return struct.pack(
        "<6sH16s4sBfHH",
        code.encode("ascii").ljust(6, b"\x00"),
        volunit,
        name.encode("gb18030").ljust(16, b"\x00")[:16],
        b"\x00" * 4,
        decimal_point,
        pre_close,
        0,
        0,
    )


def _pack_old_record(code, volunit, name, decimal_point, pre_close):
    return struct.pack(
        "<6sH8sHHBfHH",
        code.encode("ascii").ljust(6, b"\x00"),
        volunit,
        name.encode("gb18030").ljust(8, b"\x00")[:8],
        0,
        0,
        decimal_point,
        pre_close,
        0,
        0,
    )


def test_get_security_list_new_format_parses_mixed_name():
    body = struct.pack("<H", 2) + b"".join(
        [
            _pack_new_record("000001", 100, "红利ETF", 2, 38.0),
            _pack_new_record("600000", 100, "中证红利ETF联接", 3, 12.5),
        ]
    )

    result = GetSecurityList(None).parseResponse(body)

    assert [row["code"] for row in result] == ["000001", "600000"]
    assert [row["name"] for row in result] == ["红利ETF", "中证红利ETF联接"]
    assert result[0]["decimal_point"] == 2
    assert math.isclose(result[1]["pre_close"], 12.5, rel_tol=1e-6)


def test_get_security_list_old_format_remains_supported():
    body = struct.pack("<H", 1) + _pack_old_record("000001", 100, "红利ETF", 2, 38.0)

    result = GetSecurityList(None).parseResponse(body)

    assert len(result) == 1
    assert result[0]["code"] == "000001"
    assert result[0]["name"] == "红利ETF"
    assert result[0]["volunit"] == 100
    assert result[0]["decimal_point"] == 2
    assert math.isclose(result[0]["pre_close"], 38.0, rel_tol=1e-6)


def test_get_security_list_request_uses_new_method_and_payload():
    parser = GetSecurityList(None)
    parser.setParams(1, 2, 3)

    pkg = parser.send_pkg

    assert pkg[0] == 0x0C
    assert pkg[5] == 0x01
    assert struct.unpack("<H", pkg[6:8])[0] == 16
    assert struct.unpack("<H", pkg[8:10])[0] == 16
    assert struct.unpack("<H", pkg[10:12])[0] == 0x044D
    assert struct.unpack("<HIII", pkg[12:26]) == (1, 2, 3, 0)


def test_get_security_list_old_request_uses_old_method_and_payload():
    parser = GetSecurityListOld(None)
    parser.setParams(1, 2)

    pkg = parser.send_pkg

    assert pkg[0] == 0x0C
    assert pkg[5] == 0x01
    assert struct.unpack("<H", pkg[10:12])[0] == 0x0450
    assert struct.unpack("<HH", pkg[12:16]) == (1, 2)
