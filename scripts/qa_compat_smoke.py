# coding=utf-8
"""QUANTAXIS compatibility smoke test for a pytdx fork.

Run this in a QUANTAXIS environment to validate the stock and future paths
without changing QA code. When QUANTAXIS is not installed, the script can
still run a direct pytdx smoke against the same servers.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


STOCK_DEFAULT = ("119.97.185.59", 7709)
FUTURE_DEFAULT = ("121.37.232.167", 7727)


def configure_stdio():
    if sys.platform == "win32":
        for stream_name in ("stdout", "stderr"):
            stream = getattr(sys, stream_name)
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")


def load_qa_fetchers():
    from QUANTAXIS.QAFetch.QATdx import (
        QA_fetch_get_extensionmarket_list,
        QA_fetch_get_stock_block,
        QA_fetch_get_stock_day,
        QA_fetch_get_stock_list,
        QA_fetch_get_stock_realtime,
    )

    return {
        "QA_fetch_get_extensionmarket_list": QA_fetch_get_extensionmarket_list,
        "QA_fetch_get_stock_block": QA_fetch_get_stock_block,
        "QA_fetch_get_stock_day": QA_fetch_get_stock_day,
        "QA_fetch_get_stock_list": QA_fetch_get_stock_list,
        "QA_fetch_get_stock_realtime": QA_fetch_get_stock_realtime,
    }


def has_replacement_text(df, column):
    if df is None or len(df) == 0 or column not in df.columns:
        return False
    return df[column].astype(str).str.contains("\ufffd", na=False).any()


def describe_exception(exc):
    original = getattr(exc, "original_exception", None)
    if original is not None:
        return f"{type(exc).__name__}: {exc} (original {type(original).__name__}: {original})"
    return f"{type(exc).__name__}: {exc}"


def check_value(results, label, func, predicate, detail_func=str):
    try:
        value = func()
    except Exception as exc:
        results.append((label, False, describe_exception(exc)))
        return None

    ok = bool(predicate(value))
    results.append((label, ok, detail_func(value)))
    return value


def check_frame_call(results, label, func, required_columns, min_rows=1):
    try:
        frame = func()
    except Exception as exc:
        results.append((label, False, describe_exception(exc)))
        return None
    return check_frame(results, label, frame, required_columns, min_rows=min_rows)


def check_frame(results, label, frame, required_columns, min_rows=1):
    if frame is None:
        results.append((label, False, "returned None"))
        return None

    if hasattr(frame, "empty") and frame.empty:
        results.append((label, False, "empty frame"))
        return None

    missing = [col for col in required_columns if col not in frame.columns]
    if missing:
        results.append((label, False, f"missing columns: {missing}"))
        return None

    if len(frame) < min_rows:
        results.append((label, False, f"row count < {min_rows}"))
        return None

    if "name" in frame.columns and has_replacement_text(frame, "name"):
        results.append((label, False, "name contains replacement char"))
        return None

    results.append((label, True, f"{len(frame)} rows"))
    return frame


def run_direct_smoke(stock_ip, stock_port, future_ip, future_port, timeout):
    from pytdx.exhq import TdxExHq_API
    from pytdx.hq import TdxHq_API

    results = []

    api = TdxHq_API(raise_exception=True, auto_retry=False)
    try:
        with api.connect(stock_ip, stock_port, time_out=timeout):
            check_value(results, "stock_count_sz", lambda: api.get_security_count(0), lambda v: v is not None and v > 0)
            check_value(results, "stock_count_sh", lambda: api.get_security_count(1), lambda v: v is not None and v > 0)

            new_list = check_frame_call(
                results,
                "stock_list_new",
                lambda: api.to_df(api.get_security_list_range(0, 0, 20)),
                ["code", "volunit", "decimal_point", "name", "pre_close"],
            )
            if new_list is not None:
                sample_names = "".join(new_list["name"].head(20).astype(str))
                results.append(("stock_list_new_sample", len(sample_names) > 0, sample_names[:80]))

            check_frame_call(
                results,
                "stock_list_old",
                lambda: api.to_df(api.get_security_list_old(0, 0)),
                ["code", "volunit", "decimal_point", "name", "pre_close"],
            )

            check_frame_call(
                results,
                "block_gn",
                lambda: api.to_df(api.get_and_parse_block_info("block_gn.dat")),
                ["blockname", "block_type", "code_index", "code"],
            )

            check_value(
                results,
                "incon_dat",
                lambda: api.get_block_dat_ver_up("incon.dat"),
                lambda v: isinstance(v, (bytes, bytearray)),
                lambda v: f"{len(v) if v else 0} bytes",
            )

            check_frame_call(
                results,
                "quotes",
                lambda: api.to_df(api.get_security_quotes([(0, "000001"), (1, "600000")])),
                ["code", "open", "high", "low", "price", "last_close"],
            )

            check_frame_call(
                results,
                "bars",
                lambda: api.to_df(api.get_security_bars(9, 0, "000001", 0, 10)),
                ["open", "close", "high", "low", "vol", "amount", "datetime"],
            )
    except Exception as exc:
        results.append(("stock_connection", False, describe_exception(exc)))

    for label, func, columns in (
        (
            "future_markets",
            lambda ex: ex.to_df(ex.get_markets()),
            ["market", "category", "name", "short_name"],
        ),
        (
            "future_instruments",
            lambda ex: ex.to_df(ex.get_instrument_info(0, 100)),
            ["category", "market", "code", "name", "desc"],
        ),
    ):
        exapi = TdxExHq_API(raise_exception=True)
        try:
            with exapi.connect(future_ip, future_port, time_out=timeout):
                check_frame(results, label, func(exapi), columns)
        except Exception as exc:
            results.append((label, False, describe_exception(exc)))

    return results


def run_qa_smoke(stock_ip, stock_port, future_ip, future_port):
    qa = load_qa_fetchers()
    results = []

    check_frame_call(
        results,
        "qa_stock_list_etf",
        lambda: qa["QA_fetch_get_stock_list"](type_="etf", ip=stock_ip, port=stock_port),
        ["code", "volunit", "decimal_point", "name", "pre_close", "sse"],
    )

    check_frame_call(
        results,
        "qa_stock_block",
        lambda: qa["QA_fetch_get_stock_block"](ip=stock_ip, port=stock_port),
        ["blockname", "block_type", "code_index", "code"],
    )

    check_frame_call(
        results,
        "qa_stock_realtime",
        lambda: qa["QA_fetch_get_stock_realtime"](["000001", "600000"], ip=stock_ip, port=stock_port),
        ["datetime", "servertime", "code", "open", "high", "low", "price", "vol"],
    )

    check_frame_call(
        results,
        "qa_stock_day",
        lambda: qa["QA_fetch_get_stock_day"]("000001", "2020-01-01", "2020-01-10", ip=stock_ip, port=stock_port),
        ["open", "close", "high", "low", "vol", "amount", "datetime"],
    )

    future_list = check_frame_call(
        results,
        "qa_extension_market",
        lambda: qa["QA_fetch_get_extensionmarket_list"](ip=future_ip, port=future_port),
        ["market", "category", "name", "short_name"],
    )

    if future_list is not None:
        futures = future_list.query("market == 42 or market == 28 or market == 29 or market == 30 or market == 47")
        results.append(("qa_future_subset", len(futures) > 0, f"{len(futures)} rows"))

    return results


def print_summary(title, results):
    print(f"\n{title}")
    print("=" * len(title))
    for name, ok, detail in results:
        print(f"{'OK' if ok else 'FAIL'} {name}: {detail}")

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\nSummary: {passed}/{total} passed")
    return passed == total


def main():
    configure_stdio()

    parser = argparse.ArgumentParser(description="QUANTAXIS compatibility smoke test")
    parser.add_argument("--stock-ip", default=STOCK_DEFAULT[0])
    parser.add_argument("--stock-port", type=int, default=STOCK_DEFAULT[1])
    parser.add_argument("--ip", dest="stock_ip", help=argparse.SUPPRESS)
    parser.add_argument("--port", dest="stock_port", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--future-ip", default=FUTURE_DEFAULT[0])
    parser.add_argument("--future-port", type=int, default=FUTURE_DEFAULT[1])
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument(
        "--mode",
        choices=("auto", "direct", "qa", "both"),
        default="both",
        help="run direct pytdx smoke, QUANTAXIS smoke, or both",
    )

    args = parser.parse_args()

    overall = True

    if args.mode in ("direct", "both", "auto"):
        try:
            direct_results = run_direct_smoke(args.stock_ip, args.stock_port, args.future_ip, args.future_port, args.timeout)
            overall = print_summary("Direct pytdx smoke", direct_results) and overall
        except Exception as exc:
            overall = False
            print(f"\nDirect pytdx smoke failed: {exc}")

    if args.mode in ("qa", "both", "auto"):
        try:
            qa_results = run_qa_smoke(args.stock_ip, args.stock_port, args.future_ip, args.future_port)
            overall = print_summary("QUANTAXIS smoke", qa_results) and overall
        except ImportError as exc:
            if args.mode == "qa":
                print(f"\nQUANTAXIS is not installed: {exc}")
                overall = False
            else:
                print(f"\nQUANTAXIS not available, skipping QA smoke: {exc}")
        except Exception as exc:
            overall = False
            print(f"\nQUANTAXIS smoke failed: {exc}")

    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
