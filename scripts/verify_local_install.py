# coding=utf-8
"""Verify that ``import pytdx`` resolves to this local checkout."""

from __future__ import annotations

import argparse
import importlib.util
import site
import sys
from pathlib import Path


DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def _format_path(value):
    return str(value) if value else "<unknown>"


def _site_package_dirs():
    seen = set()
    candidates = []
    for getter in (site.getsitepackages,):
        try:
            values = getter()
        except Exception:
            values = []
        for value in values:
            path = Path(value)
            if path not in seen:
                candidates.append(path)
                seen.add(path)

    try:
        user_site = Path(site.getusersitepackages())
    except Exception:
        user_site = None
    if user_site is not None and user_site not in seen:
        candidates.append(user_site)

    return candidates


def _print_shadow_hints(expected_root):
    print("Potential stale package directories:")
    for site_dir in _site_package_dirs():
        package_dir = site_dir / "pytdx"
        if package_dir.exists():
            print(f"  {package_dir}")

    print("")
    print("Suggested repair in the same Python environment:")
    if sys.platform == "win32":
        print("  python -m pip uninstall -y pytdx")
        print("  Remove-Item -Recurse -Force <site-packages>\\pytdx")
        print(f"  python -m pip install -e {expected_root}")
    else:
        print("  python -m pip uninstall -y pytdx")
        print("  mv <site-packages>/pytdx <site-packages>/pytdx.shadow")
        print(f"  python -m pip install -e {expected_root} --no-deps")


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

    spec = importlib.util.find_spec("pytdx")
    package_file_text = getattr(pytdx, "__file__", "")
    package_file = Path(package_file_text).resolve() if package_file_text else None
    version = getattr(pytdx, "__version__", "<no version>")
    package_path = [str(Path(path).resolve()) for path in getattr(pytdx, "__path__", [])]

    print(f"pytdx spec     = {spec}")
    print(f"pytdx.__file__ = {_format_path(package_file)}")
    print(f"pytdx.__version__ = {version}")
    print(f"pytdx.__path__ = {package_path}")
    print(f"expected       = {expected_init}")

    if package_file != expected_init:
        print("")
        print("FAIL import does not point to this checkout.")
        if package_file is None:
            print("pytdx was imported as a namespace package. This usually means a")
            print("stale site-packages/pytdx directory is shadowing the editable install.")
        else:
            print("A stale site-packages pytdx copy is shadowing the editable install.")
        _print_shadow_hints(expected_root)
        return 1

    print("OK local checkout is active")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
