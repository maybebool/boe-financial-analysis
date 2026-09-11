"""Utilities for managing and loading structured data exports.

This module provides functions for listing, resolving, and loading
different kinds of structured data exports such as topics, statements,
and metrics. It ensures that the exported data meets predefined schema
requirements and provides error handling for missing files or
incomplete data.

Attributes:
    LATEST (str): A constant representing the latest version specifier.
    REQUIRED (dict): A dictionary specifying the required columns for
        each kind of data export.
    SUBDIR (dict): A dictionary mapping export kinds to their respective
        subdirectory relative to the base data directory.
"""
from __future__ import annotations
import pathlib
import pandas as pd

LATEST = "latest"

REQUIRED = {
    "topics": ["firm", "quarter", "topic", "speaker_role",
               "n_sentences", "mean_sentiment"],
    "statements": ["firm", "quarter", "speaker_name", "speaker_role",
                   "topic", "sentiment"],
    "metrics": ["firm", "quarter", "metric_name", "value", "unit"],
}

# Where each export kind lives, relative to the Drive root.
SUBDIR = {
    "topics": "results",
    "statements": "results",
    "metrics": "results",
}


def available(data_dir: pathlib.Path, kind: str) -> list[str]:
    """List the export versions on disk for this kind, oldest first."""
    folder = data_dir / SUBDIR.get(kind, "")
    return [p.stem.rsplit("_", 1)[-1] for p in sorted(folder.glob(f"{kind}_*.csv"))]


def resolve(data_dir: pathlib.Path, kind: str, version: str) -> pathlib.Path:
    """Turn a version string into a concrete file path."""
    folder = data_dir / SUBDIR.get(kind, "")
    if not folder.exists():
        raise FileNotFoundError(
            f"[CONTRACT] folder not found: {folder}. "
            "In Colab, check that Drive is mounted and 'boe-data' is shared with you."
        )
    if version == LATEST:
        hits = sorted(folder.glob(f"{kind}_*.csv"))
        if not hits:
            raise FileNotFoundError(f"[CONTRACT] no '{kind}_*.csv' in {folder}.")
        return hits[-1]

    path = folder / f"{kind}_{version}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"[CONTRACT] {path.name} not found in {folder}. "
            f"Available: {', '.join(available(data_dir, kind)) or 'none'}"
        )
    return path


def load(data_dir: pathlib.Path, kind: str, version: str) -> pd.DataFrame:
    """Load one export. Pass an explicit version, or loading.LATEST to float."""
    path = resolve(data_dir, kind, version)
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED[kind] if c not in df.columns]
    if missing:
        raise ValueError(
            f"[CONTRACT] {path.name} is missing columns {missing}. "
            "Ask Roman which export this notebook should use."
        )
    print(f"loaded {path.name}  {len(df)} rows")
    return df


def load_topics(data_dir: pathlib.Path, version: str) -> pd.DataFrame:
    """One row per topic, quarter and speaker role."""
    return load(data_dir, "topics", version)


def load_statements(data_dir: pathlib.Path, version: str) -> pd.DataFrame:
    """One row per statement, with speaker, role, topic and sentiment."""
    return load(data_dir, "statements", version)


def load_metrics(data_dir: pathlib.Path, version: str) -> pd.DataFrame:
    """Reported figures, one row per firm, quarter and metric."""
    return load(data_dir, "metrics", version)