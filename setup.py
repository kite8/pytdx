from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).resolve().parent
EXCLUDE = ("tests", "tests.*", "scripts", "scripts.*")
PACKAGES = ["pytdx"] + [f"pytdx.{name}" for name in find_packages(where=".", exclude=EXCLUDE)]
REQUIREMENTS = [
    line.strip()
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]

setup(
    name="pytdx",
    version="1.72.1",
    description="Python client for TongDaXin market data servers",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    packages=PACKAGES,
    package_dir={"pytdx": "."},
    include_package_data=False,
    install_requires=REQUIREMENTS,
)
