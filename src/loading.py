"""Load the frozen CSV exports that the pipeline writes to Drive.

Nobody parses PDFs here. Analysis reads exports, never raw documents.
"""
from __future__ import annotations

import pathlib
import pandas as pd


def latest(data_dir: pathlib.Path, prefix: str) -> pathlib.Path:
    """Return the newest export matching '<prefix>_YYYY-MM-DD.csv'."""
    hits = sorted(data_dir.glob(f"{prefix}_*.csv"))
    if not hits:
        raise FileNotFoundError(
            f"no export '{prefix}_*.csv' in {data_dir}. "
            "Check that the Drive folder is mounted and shared with you."
        )
    return hits[-1]


def load_topics(data_dir: pathlib.Path) -> pd.DataFrame:
    """One row per topic, quarter and speaker role."""
    return pd.read_csv(latest(data_dir, "topics"))


def load_statements(data_dir: pathlib.Path) -> pd.DataFrame:
    """One row per statement, with speaker, role, topic and sentiment."""
    return pd.read_csv(latest(data_dir, "statements"))


def load_metrics(data_dir: pathlib.Path) -> pd.DataFrame:
    """Reported figures, one row per firm, quarter and metric."""
    return pd.read_csv(latest(data_dir, "metrics"))
