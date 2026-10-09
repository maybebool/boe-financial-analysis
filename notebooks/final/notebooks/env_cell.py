"""Environment checks used by the setup cell at the top of every notebook."""
from __future__ import annotations

import importlib.metadata as md
import pathlib
import sys

PY_EXPECTED = "3.13"


def check_python() -> None:
    have = f"{sys.version_info.major}.{sys.version_info.minor}"
    if have != PY_EXPECTED:
        print(f"WARNING: python {have}, this project assumes {PY_EXPECTED}")


def _installed(name: str) -> str | None:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def verify(root: pathlib.Path) -> None:
    """Raise if any pinned package differs from requirements.txt."""
    bad = []
    for line in (root / "requirements.txt").read_text().splitlines():
        line = line.split("#")[0].strip()
        if "==" not in line:
            continue
        name, want = line.split("==")
        have = _installed(name)
        if have != want:
            bad.append(f"  {name}: {have or 'missing'} instead of {want}")
    if bad:
        raise RuntimeError("environment mismatch:\n" + "\n".join(bad))
