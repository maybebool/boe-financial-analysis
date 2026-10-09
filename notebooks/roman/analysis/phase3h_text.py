"""Phase 3h, step 1: text export and manifest for the 13 UBS reports of 2025 and 2026 and, for (b) of T27 and T33,
the 2024-Q4 report and the 2024 annual report.

Run from the repository root: python notebooks/roman/analysis/phase3h_text.py
Writes notebooks/roman/data/phase3h/text/<file>.txt, manifest.csv and run_log.json (raw hashes, time). Accession and
source URL come from data/phase3h/sources.csv (entered manually); the download date of the 13 files is 2026-09-26 (plan), of the
two 2024 files the file time stamps, entered manually. The script reports incomplete manifest rows; phase3h_search.py
refuses to run while any row is incomplete.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
import report_text as rt  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3h"
NEW = DATA / "reports_2025_2026"
OLD_FOR_B = [DATA / "reports" / "UBS_2024-Q4_report.htm", DATA / "reports" / "UBS_2024_annual_report.htm"]
DOWNLOAD_DATE = "2026-09-26"
DOWNLOAD_DATES_2024 = {"UBS_2024-Q4_report.htm": "2026-09-12", "UBS_2024_annual_report.htm": "2026-09-23"}  # entered manually


def files():
    return sorted(NEW.glob("*.htm")) + OLD_FOR_B


def main():
    new = sorted(NEW.glob("*.htm"))
    assert len(new) == 13, len(new)
    sources = pd.read_csv(OUT / "sources.csv", keep_default_na=False).set_index("file")
    dates = {p.name: DOWNLOAD_DATE for p in new}
    dates.update(DOWNLOAD_DATES_2024)
    m = rt.build(files(), OUT, sources, dates)
    m["folder"] = ["reports_2025_2026" if p.parent == NEW else "reports" for p in files()]
    m.to_csv(OUT / "manifest.csv", index=False)
    log_path = OUT / "run_log.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    log.update(text_export=datetime.now().isoformat(timespec="seconds"),
               manifest_sha256=rt.sha256_bytes((OUT / "manifest.csv").read_bytes()))
    log_path.write_text(json.dumps(log, indent=2))
    print(m.drop(columns=["raw_sha256", "text_sha256", "source_url"]).to_string(index=False))
    inc = rt.incomplete(m)
    print("incomplete manifest rows:", list(inc.file) if len(inc) else "none")


if __name__ == "__main__":
    main()
