"""Shared configuration for the analysis in notebooks/roman."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

# Data release that all analysis reads (read only). Change only this value when a new release arrives.
RELEASE_DIR = ROOT / "data" / "results" / "2026-09-23"
