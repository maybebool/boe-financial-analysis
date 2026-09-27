"""Phase 3e, step 1: check terms for the units where the call is earlier than the reports.

Run from the repository root before phase3e_channel.py: python notebooks/roman/analysis/phase3e_terms.py
Terms come from the call sentence only (the figure in report spellings and the words of the commitment), fixed before
any search of this phase. Writes check_units.json and its sha256 to notebooks/roman/data/phase3e/.
"""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3e"
REPORTS = ROOT / "notebooks" / "roman" / "data" / "reports"

# call sentences (phase 3d first mentions):
# T10 2023-Q2 "We expect to operate at around 14% CET1 capital ratio over the medium term."
# T17 2023-Q3 "... a roughly 5% increase from day-1 effects in 2025 from other final Basel 3 considerations, mainly FRTB."
# T34 2023-Q4 "... we believe we can realize funding cost saves of up to 1 billion by 2026 ..."
# T36 2023-Q4 "The legal entity mergers ... driving down our effective tax rate to around 40% by the end of 2024."
# T55 2024-Q3 "By the end of 2026 we aim to have less than 5% remaining."
CHECK = {
    "T10": (["2023-Q2", "2023-Q3", "2023-Q4"],
            [["14%", "CET1"], ["around 14", "CET1"], ["medium term", "CET1"]]),
    "T17": (["2023-Q3", "2023-Q4", "2023_annual", "2024-Q1", "2024-Q2"],
            [["5%", "Basel"], ["day-1", "Basel"], ["FRTB", None], ["2025", "Basel"]]),
    "T34": (["2023-Q4", "2023_annual"],
            [["funding cost", None], ["1bn", "funding cost"], ["1 billion", "funding cost"], ["2026", "funding cost"]]),
    "T36": (["2023-Q4", "2023_annual", "2024-Q1"],
            [["40%", "tax rate"], ["effective tax rate", "2024"], ["legal entity mergers", "tax"]]),
    "T55": (["2024-Q3", "2024-Q4", "2024_annual"],
            [["less than 5%", None], ["5%", "2026"], ["remaining", "5%"]]),
}


def file_name(label):
    return f"UBS_{label}_report.htm"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    out = {u: {"files": [file_name(f) for f in files], "terms": terms} for u, (files, terms) in CHECK.items()}
    for u in out.values():
        for f in u["files"]:
            assert (REPORTS / f).exists(), f
    path = OUT / "check_units.json"
    path.write_text(json.dumps(out, indent=2))
    (OUT / "check_units_log.json").write_text(json.dumps(
        {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
         "written": datetime.now().isoformat(timespec="seconds")}, indent=2))
    print(path.read_text())


if __name__ == "__main__":
    main()
