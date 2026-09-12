"""Loading interface for the shared CSV exports on Drive.

Layout on Drive:

    boe-data/results/<YYYY-MM-DD>/all_utterances.csv     both banks
    boe-data/results/<YYYY-MM-DD>/all_sentences.csv      both banks
    boe-data/results/<YYYY-MM-DD>/all_metrics.csv        both banks
    boe-data/results/<YYYY-MM-DD>/<FIRM>/<file>.csv      single documents

Pin the export with a date and name the file you want. The combined
`all_*.csv` files are what most notebooks need. Use `exports`, `files` and
`firms` to see what is there.
"""
from __future__ import annotations
import pathlib
import pandas as pd

LATEST = "latest"
RESULTS = "results"

# Required columns per file kind. The kind is the last part of the file name:
# "all_utterances.csv" -> "utterances", "UBS_2023-Q1_call_sentences.csv" -> "sentences".
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


def exports(data_dir: pathlib.Path) -> list[str]:
    """Export dates available, oldest first."""
    return sorted(p.name for p in _results_dir(data_dir).iterdir() if p.is_dir())


def resolve(data_dir: pathlib.Path, export: str,
            firm: str | None = None) -> pathlib.Path:
    """Turn an export date, and optionally a bank, into a concrete folder."""
    known = exports(data_dir)
    if not known:
        raise FileNotFoundError(
            f"[CONTRACT] no dated export folder in {_results_dir(data_dir)}."
        )
    if export == LATEST:
        export = known[-1]
    if export not in known:
        raise FileNotFoundError(
            f"[CONTRACT] no export '{export}'. Available: {', '.join(known)}"
        )
    folder = _results_dir(data_dir) / export
    if firm is None:
        return folder
    if not (folder / firm).exists():
        raise FileNotFoundError(
            f"[CONTRACT] no folder '{firm}' in export {export}. "
            f"Banks available: {', '.join(firms(data_dir, export)) or 'none'}"
        )
    return folder / firm


def firms(data_dir: pathlib.Path, export: str = LATEST) -> list[str]:
    """Banks that have a single document folder in this export, e.g. ['JPM', 'UBS']."""
    return sorted(p.name for p in resolve(data_dir, export).iterdir() if p.is_dir())


def files(data_dir: pathlib.Path, export: str = LATEST,
          firm: str | None = None) -> list[str]:
    """File names in the export, or inside one bank folder. Copy into `load`."""
    return sorted(p.name for p in resolve(data_dir, export, firm).glob("*.csv"))


def _kind(filename: str) -> str:
    """Last token of the file name, used to look up the column contract."""
    return pathlib.Path(filename).stem.rsplit("_", 1)[-1].lower()


def load(data_dir: pathlib.Path, filename: str, export: str = LATEST,
         firm: str | None = None) -> pd.DataFrame:
    """Load one CSV out of one export.

    Leave `firm` out for the combined `all_*.csv` files. Pass a bank name to
    reach a single document inside that bank's folder. Pin `export` to a date
    so a rerun of this notebook gives the same numbers.
    """
    folder = resolve(data_dir, export, firm)
    path = folder / filename
    if not path.exists():
        raise FileNotFoundError(
            f"[CONTRACT] {filename} not found in {folder.name}. "
            f"Available: {', '.join(files(data_dir, export, firm))}"
        )
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED.get(_kind(filename), []) if c not in df.columns]
    if missing:
        raise ValueError(
            f"[CONTRACT] {path.name} is missing columns {missing}. "
            "Ask Roman which export this notebook should use."
        )
    print(f"loaded {path.name}  {len(df)} rows")
    return df