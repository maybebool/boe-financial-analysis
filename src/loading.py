"""Loading interface for the shared CSV exports on Drive.

Layout on Drive:

    boe-data/results/<FIRM>_<YYYY-MM-DD>/<file>.csv

Example:

    boe-data/results/UBS_2026-09-12/UBS_2023-Q1_call_utterances.csv

Pick the bank with `firm`, pin the export folder with a date, and name the
file you want. Use `firms`, `exports` and `files` to see what is there.
"""
from __future__ import annotations
import pathlib
import pandas as pd

LATEST = "latest"
RESULTS = "results"

# Required columns per file kind. The kind is the last part of the file name:
# "UBS_2023-Q1_call_utterances.csv" -> "utterances", "all_metrics.csv" -> "metrics".
# A kind that is empty or missing here is loaded without a schema check.
REQUIRED: dict[str, list[str]] = {
    "utterances": [],
    "sentences": [],
    "metrics": [],
}


def _results_dir(data_dir: pathlib.Path) -> pathlib.Path:
    """The results folder, with a readable error if Drive is not there."""
    folder = data_dir / RESULTS
    if not folder.exists():
        raise FileNotFoundError(
            f"[CONTRACT] folder not found: {folder}. "
            "In Colab, check that Drive is mounted and that 'boe-data' is in "
            "My Drive (Shared with me, right click, Organise, Add shortcut)."
        )
    return folder


def firms(data_dir: pathlib.Path) -> list[str]:
    """Banks that have at least one export, e.g. ['UBS']."""
    return sorted({p.name.rsplit("_", 1)[0]
                   for p in _results_dir(data_dir).iterdir()
                   if p.is_dir() and "_" in p.name})


def exports(data_dir: pathlib.Path, firm: str) -> list[str]:
    """Export dates available for one bank, oldest first."""
    return sorted(p.name.rsplit("_", 1)[-1]
                  for p in _results_dir(data_dir).glob(f"{firm}_*") if p.is_dir())


def resolve(data_dir: pathlib.Path, firm: str, export: str) -> pathlib.Path:
    """Turn a bank plus an export date into the folder holding the CSV files."""
    folder = _results_dir(data_dir)
    known = exports(data_dir, firm)
    if not known:
        raise FileNotFoundError(
            f"[CONTRACT] no folder '{firm}_<date>' in {folder}. "
            f"Banks available: {', '.join(firms(data_dir)) or 'none'}"
        )
    if export == LATEST:
        export = known[-1]
    if export not in known:
        raise FileNotFoundError(
            f"[CONTRACT] no export '{export}' for {firm}. "
            f"Available: {', '.join(known)}"
        )
    return folder / f"{firm}_{export}"


def files(data_dir: pathlib.Path, firm: str, export: str = LATEST) -> list[str]:
    """File names inside one export folder, ready to copy into `load`."""
    return sorted(p.name for p in resolve(data_dir, firm, export).glob("*.csv"))


def _kind(filename: str) -> str:
    """Last token of the file name, used to look up the column contract."""
    return pathlib.Path(filename).stem.rsplit("_", 1)[-1].lower()


def load(data_dir: pathlib.Path, firm: str, filename: str,
         export: str = LATEST) -> pd.DataFrame:
    """Load one CSV out of one export folder.

    Pass an explicit export date so a rerun of this notebook gives the same
    numbers. `loading.LATEST` floats to the newest export on purpose.
    """
    folder = resolve(data_dir, firm, export)
    path = folder / filename
    if not path.exists():
        raise FileNotFoundError(
            f"[CONTRACT] {filename} not found in {folder.name}. "
            f"Available: {', '.join(files(data_dir, firm, export))}"
        )
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED.get(_kind(filename), []) if c not in df.columns]
    if missing:
        raise ValueError(
            f"[CONTRACT] {folder.name}/{path.name} is missing columns {missing}. "
            "Ask Roman which export this notebook should use."
        )
    print(f"loaded {folder.name}/{path.name}  {len(df)} rows")
    return df