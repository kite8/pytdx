from pytdx.hq import TdxHq_API


def test_get_report_file_by_size_returns_empty_bytearray_when_no_chunks(monkeypatch):
    api = TdxHq_API()

    monkeypatch.setattr(
        api,
        "get_report_file",
        lambda filename, offset: {"chunksize": 0, "chunkdata": b""},
    )

    assert api.get_report_file_by_size("incon.dat", filesize=5) == bytearray()


def test_get_block_dat_ver_up_delegates_to_report_download(monkeypatch):
    api = TdxHq_API()
    called = {}

    def fake(self, filename, filesize=0, reporthook=None):
        called["args"] = (filename, filesize, reporthook)
        return bytearray(b"abc")

    monkeypatch.setattr(TdxHq_API, "get_report_file_by_size", fake)

    result = api.get_block_dat_ver_up("incon.dat", filesize=123)

    assert result == bytearray(b"abc")
    assert called["args"] == ("incon.dat", 123, None)
