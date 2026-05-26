# coding=utf-8
"""Diagnose QUANTAXIS `save stock_block` in a real conda environment.

This script runs the stock block save flow in isolated steps:
1. TDX block fetch
2. TDX industry/incon parsing
3. Tushare block fetch
4. JSON conversion

It is intended to be run inside the QUANTAXIS conda environment after setting
the QA env file and a writable HOME/USERPROFILE.
"""

from __future__ import annotations

import argparse
import inspect
import sys
import traceback
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _format_obj(value):
    if value is None:
        return "None"
    try:
        return f"type={type(value).__name__}, len={len(value)}"
    except Exception:
        return f"type={type(value).__name__}"


def _print_frame(label, frame):
    print(f"\n[{label}]")
    print(_format_obj(frame))
    if frame is None:
        return
    if hasattr(frame, "shape"):
        print(f"shape={frame.shape}")
    if hasattr(frame, "columns"):
        print(f"columns={list(frame.columns)}")
    if hasattr(frame, "index"):
        print(f"index_name={getattr(frame.index, 'names', getattr(frame.index, 'name', None))}")
    try:
        print(frame.head(3).to_string())
    except Exception:
        pass


def _load_qa_environment(env_file, qa_home):
    from scripts import qa_compat_smoke

    qa_compat_smoke.prepare_qa_environment(env_file, qa_home)


def _inspect_tushare():
    import tushare as ts

    print("\n[tushare]")
    print(f"tushare_file={getattr(ts, '__file__', None)}")
    print(f"tushare_version={getattr(ts, '__version__', None)}")
    get_zz500s = getattr(ts, "get_zz500s", None)
    print(f"get_zz500s={get_zz500s}")
    if get_zz500s is not None:
        try:
            src = inspect.getsource(get_zz500s)
            print("get_zz500s_source:")
            print(src)
        except Exception as exc:
            print(f"could not read get_zz500s source: {type(exc).__name__}: {exc}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Diagnose QUANTAXIS stock block save flow")
    parser.add_argument("--qa-env-file", default=None, help="path to QA .env file")
    parser.add_argument("--qa-home", default=None, help="writable QA home directory")
    parser.add_argument("--stock-ip", default="119.97.185.59")
    parser.add_argument("--stock-port", type=int, default=7709)
    parser.add_argument("--future-ip", default="121.37.232.167")
    parser.add_argument("--future-port", type=int, default=7727)
    parser.add_argument("--run-save-func", action="store_true", help="run QA_SU_save_stock_block with a fake client")
    parser.add_argument("--save-only", action="store_true", help="only run QA_SU_save_stock_block with a fake client")
    args = parser.parse_args(argv)

    _load_qa_environment(args.qa_env_file, args.qa_home)

    print(f"python={sys.executable}")
    print(f"sys.path[0:5]={sys.path[0:5]}")

    from QUANTAXIS.QAFetch.QATdx import (
        QA_fetch_get_stock_block as qa_fetch_get_stock_block_tdx,
        QA_fetch_get_tdx_industry,
    )
    from QUANTAXIS.QAFetch.QATushare import QA_fetch_get_stock_block as qa_fetch_get_stock_block_tushare
    from QUANTAXIS.QASU.save_tdx import QA_SU_save_stock_block as qa_save_stock_block
    from QUANTAXIS.QAUtil.QATransform import QA_util_to_json_from_pandas
    import QUANTAXIS
    import pytdx

    print(f"QUANTAXIS={getattr(QUANTAXIS, '__file__', None)}")
    print(f"pytdx={getattr(pytdx, '__file__', None)} version={getattr(pytdx, '__version__', None)}")

    if not args.save_only:
        _inspect_tushare()

        print("\n[tdx stock_block]")
        try:
            tdx_block = qa_fetch_get_stock_block_tdx(args.stock_ip, args.stock_port)
            _print_frame("tdx_block", tdx_block)
            if tdx_block is not None:
                try:
                    json_data = QA_util_to_json_from_pandas(tdx_block)
                    print(f"tdx json rows={len(json_data)}")
                except Exception as exc:
                    print(f"tdx json conversion failed: {type(exc).__name__}: {exc}")
        except Exception:
            traceback.print_exc()

        print("\n[tdx industry]")
        try:
            industry = QA_fetch_get_tdx_industry()
            _print_frame("tdx_industry", industry)
        except Exception:
            traceback.print_exc()

        print("\n[tushare stock_block]")
        try:
            tushare_block = qa_fetch_get_stock_block_tushare()
            _print_frame("tushare_block", tushare_block)
            if tushare_block is not None:
                try:
                    json_data = QA_util_to_json_from_pandas(tushare_block)
                    print(f"tushare json rows={len(json_data)}")
                except Exception as exc:
                    print(f"tushare json conversion failed: {type(exc).__name__}: {exc}")
        except Exception:
            traceback.print_exc()

    if args.run_save_func or args.save_only:
        print("\n[QA_SU_save_stock_block]")

        class _DummyCollection:
            def create_index(self, *args, **kwargs):
                print(f"create_index args={args} kwargs={kwargs}")

            def insert_many(self, rows):
                print(f"insert_many rows={len(rows)}")

        class _DummyClient:
            def __init__(self):
                self.stock_block = _DummyCollection()

            def drop_collection(self, name):
                print(f"drop_collection name={name}")

        try:
            qa_save_stock_block(client=_DummyClient())
        except Exception:
            traceback.print_exc()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
