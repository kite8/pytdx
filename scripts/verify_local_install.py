# coding=utf-8
"""Verify that ``import pytdx`` resolves to this local checkout."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def _format_path(value):
    return str(value) if value else "<unknown>"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify local pytdx import path")
    parser.add_argument(
        "--expected-root",
        default=str(DEFAULT_ROOT),
        help="checkout root that should contain pytdx __init__.py",
    )
    args = parser.parse_args(argv)

    expected_root = Path(args.expected_root).resolve()
    expected_init = (expected_root / "__init__.py").resolve()

    try:
        import pytdx
    except Exception as exc:
        print(f"FAIL import pytdx: {type(exc).__name__}: {exc}")
        return 1

    package_file_text = getattr(pytdx, "__file__", "")
    package_file = Path(package_file_text).resolve() if package_file_text else None
    version = getattr(pytdx, "__version__", "<no version>")

    print(f"pytdx.__file__ = {_format_path(package_file)}")
    print(f"pytdx.__version__ = {version}")
    print(f"expected       = {expected_init}")

    if package_file != expected_init:
        print("")
        print("FAIL import does not point to this checkout.")
        print("Remove stale site-packages pytdx copies, then reinstall with:")
        print(f"  python -m pip install -e {expected_root}")
        return 1

    print("OK local checkout is active")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
