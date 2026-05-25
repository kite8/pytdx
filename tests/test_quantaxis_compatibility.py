# coding=utf-8
"""Legacy QUANTAXIS smoke-test entrypoint.

The real network/QUANTAXIS smoke test lives in ``scripts/qa_compat_smoke.py`` so
pytest can run the unit suite without touching external servers. This wrapper
keeps the old documented command working:

    python tests/test_quantaxis_compatibility.py --mode qa
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_PARENT = REPO_ROOT.parent


def _ensure_import_paths():
    package_parent = str(PACKAGE_PARENT)
    repo_root = str(REPO_ROOT)

    if package_parent not in sys.path:
        sys.path.insert(0, package_parent)
    if repo_root not in sys.path:
        sys.path.insert(1, repo_root)


_ensure_import_paths()

from scripts import qa_compat_smoke  # noqa: E402


def test_qa_compat_smoke_script_is_importable():
    assert qa_compat_smoke.STOCK_DEFAULT == ("119.97.185.59", 7709)
    assert qa_compat_smoke.FUTURE_DEFAULT == ("121.37.232.167", 7727)
    assert qa_compat_smoke.DEFAULT_QA_ENV_FILE.name == ".env"
    assert qa_compat_smoke.DEFAULT_QA_HOME.name == ".qa_home"
    assert callable(qa_compat_smoke.run_direct_smoke)
    assert callable(qa_compat_smoke.run_qa_smoke)


def test_qa_frame_check_accepts_required_index_names():
    frame = pd.DataFrame(
        [
            {
                "datetime": "2026-05-25 09:30:00",
                "code": "000001",
                "price": 10.0,
                "vol": 100,
            }
        ]
    ).set_index(["datetime", "code"])
    results = []

    returned = qa_compat_smoke.check_frame(
        results,
        "qa_stock_realtime",
        frame,
        ["price", "vol"],
        required_index_names=["datetime", "code"],
    )

    assert returned is frame
    assert results == [("qa_stock_realtime", True, "1 rows")]


def main():
    return qa_compat_smoke.main()


if __name__ == "__main__":
    raise SystemExit(main())
