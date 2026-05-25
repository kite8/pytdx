import pytest

from pytdx.util.encoding import decode_tdx_code, decode_tdx_text, validate_text_field


def test_decode_tdx_text_handles_mixed_names():
    assert decode_tdx_text(b'\xba\xec\xc0\xfbETF\x00\x00') == '红利ETF'
    assert decode_tdx_text(b'\xd6\xd0\xd6\xa4\xba\xec\xc0\xfbETF\xc1\xaa\xbd\xd3\x00\x00') == '中证红利ETF联接'
    assert decode_tdx_text(b'QDII\x00\x00\x00\x00') == 'QDII'


def test_decode_tdx_text_drops_truncated_tail_without_replacement():
    text = decode_tdx_text(b'\xba\xec\xc0')
    assert text == '红'
    assert '�' not in text


def test_decode_tdx_text_strips_control_bytes():
    assert decode_tdx_text(b'\xba\xec\xc0\xfb\x01\x02ETF\x00') == '红利ETF'


def test_decode_tdx_text_supports_gb18030_extension_characters():
    text = decode_tdx_text(b'\x95\x32\x82\x36')
    assert len(text) == 1
    assert ord(text) == 0x20000


def test_decode_tdx_code_strips_padding():
    assert decode_tdx_code(b'000001\x00') == '000001'
    assert decode_tdx_code(b'sh600000') == 'sh600000'


def test_validate_text_field_rejects_too_many_replacement_chars():
    with pytest.raises(ValueError):
        validate_text_field('ab��cd', field_name='name')
