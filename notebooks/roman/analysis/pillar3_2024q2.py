"""Amendment to phases 3f and 3g: the Pillar 3 report as of 30 June 2024 (filed 23 August 2024), added later.

Run from the repository root: python notebooks/roman/analysis/pillar3_2024q2.py
Units and terms come unchanged from data/phase3f/check_units_2024q2.json (T16, T25, T27, T32, T33; phase 3d round-1
terms) and data/phase3g/check_units_2024q2.json (F11, F12; phase 3g terms). Same reconstruction (positioned layout,
hyphen repair) and hit definition as in phase 3f. Writes pages.csv, hits.csv, read.csv and run_log.json to
data/phase3f/pillar3_2024q2/ and data/phase3g/pillar3_2024q2/; pillar3_read.csv and new_units_read.csv, the primary
results, are not touched.
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase3b_reports import pages_positioned  # noqa: E402
from phase3g_read import search  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
FILE = "UBS_2024-Q2_pillar3.htm"
PHASES = {  # phase folder: (check file, search terms, run log with the terms hash, hash key, round-1 filter)
    "phase3f": (DATA / "phase3f" / "check_units_2024q2.json", DATA / "phase3d" / "search_terms.csv",
                DATA / "phase3d" / "run_log.json", "round1_sha256", True),
    "phase3g": (DATA / "phase3g" / "check_units_2024q2.json", DATA / "phase3g" / "search_terms.csv",
                DATA / "phase3g" / "run_log.json", "search_terms_sha256", False),
}


# reading of hits.csv (every hit with a figure and a forward-looking window around every term hit, full text);
# consistency rule of 2026-09-24 applied. unit: (class, comment); no unit is A or B, so there is no quote to verify
READ = {
    "T16": ("C", "Figure hits are other amounts; no forward-looking sentence on the NCL run-down or operational risk RWA."),
    "T25": ("C", "No forward-looking sentence on NCL capital release or on exiting NCL exposures."),
    "T27": ("C", "The forward-looking RWA sentence (p. 7) is the Basel III estimate of around 5% (T17); unlike the "
                 "2023-Q4 report there is no sentence on the NCL run-down."),
    "T32": ("C", "Swiss SRB table of required going concern capital as of 30.6.24, an actual requirement."),
    "T33": ("C", "AT1 appears as DCCP amounts as of 30 June 2024, instrument tables and the glossary; no issuance plan."),
    "F11": ("C", "Going concern capital ratio only as row labels of tables with actual ratios."),
    "F12": ("C", "LRD only in tables, actual movements and the glossary; no forward-looking reduction."),
}


# Roman's check of the 2024-Q2 report, repeated with the phase 3h tool (2026-09-26)
CHECKED = "Roman 2026-09-26 (phase 3h tool, all hits shown, filtered on forward-looking words; data/phase3h/roman_check/recheck_2026-09-26/): no figure and no forward-looking sentence on the same reduction in this report; C confirmed."


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    path = DATA / "reports" / FILE
    before = sha(path.read_bytes())
    html = path.read_text(encoding="utf-8", errors="replace")
    pages = pd.DataFrame([dict(file=FILE, quarter="2024-Q2", page=n, text=t)
                          for n, t in pages_positioned(html, repair=True)])
    for phase, (check, terms_path, log_path, key, round1) in PHASES.items():
        terms = pd.read_csv(terms_path)
        if round1:
            terms = terms[terms["round"] == 1]
            h = sha(terms.to_csv(index=False).encode())
        else:
            h = sha(terms_path.read_bytes())
        assert h == json.loads(log_path.read_text())[key], (phase, "search terms were changed")
        units = list(json.loads(check.read_text()))
        out = DATA / phase / "pillar3_2024q2"
        out.mkdir(exist_ok=True)
        (out / "run_log.json").write_text(json.dumps(dict(
            started=datetime.now().isoformat(timespec="seconds"), report=FILE, report_sha256=before,
            check_file=check.name, check_file_sha256=sha(check.read_bytes()), terms_sha256=h, units=units), indent=2))
        pages.to_csv(out / "pages.csv", index=False)
        rows = []
        for u in units:
            rows += search(pages, pd.Series(dict(unit=u)), terms)
        hits = pd.DataFrame(rows).drop(columns="in_W1")
        hits.to_csv(out / "hits.csv", index=False)
        pd.DataFrame([dict(unit=u, file=FILE, class_pillar3_2024q2=READ[u][0], hits=int((hits.unit == u).sum()),
                           comment=READ[u][1], checked_by_roman=CHECKED) for u in units]).to_csv(out / "read.csv", index=False)
        print(phase, len(pages), "pages")
        print(hits.groupby(["unit", "priority"]).size().unstack(fill_value=0).to_string())
    assert sha(path.read_bytes()) == before, "report file changed"


if __name__ == "__main__":
    main()
