"""Phase 3f: search the UBS Pillar 3 reports for the six call-only figures with the phase 3d terms.

Run from the repository root: python notebooks/roman/analysis/phase3f_pillar3.py
Writes the check files first (before searching), then pillar3_pages.csv, hits.csv and run_log.json to
notebooks/roman/data/phase3f/. Rules as in plans/phase_3f.md.
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase3_extract import FORWARD_RE, horizons  # noqa: E402
from phase3b_reports import pages_positioned  # noqa: E402
from phase3c_counterparts import period_end, split_sentences  # noqa: E402
from phase3d_search import LONG, compile_term  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
REPORTS = DATA / "reports"
P3D = DATA / "phase3d"
OUT = DATA / "phase3f"
UNITS = ["T16", "T25", "T27", "T32", "T33", "T68"]
FIRST_QUARTER = {"T16": "2023-Q3", "T25": "2023-Q4", "T27": "2023-Q4", "T32": "2023-Q4", "T33": "2023-Q4",
                 "T68": "2024-Q4"}
PILLAR3 = ["2023-Q3", "2023-Q4", "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]
PENDING = {"2024-Q2"}  # filed 23 August 2024, added later by Roman


def pfile(q):
    return f"UBS_{q}_pillar3.htm"


def window(unit, available=True):
    qs = [q for q in PILLAR3 if q >= FIRST_QUARTER[unit]]
    return [q for q in qs if (q not in PENDING) == available]


def check_terms(terms, unit):
    t = terms[(terms.unit == unit) & (terms["round"] == 1)]
    phrases = t[t.group == 2].term.tolist()
    figures = t[t.group == 3].term.tolist()
    return [[p, None] for p in phrases] + [[f, phrases[0]] for f in figures]


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    terms = pd.read_csv(P3D / "search_terms.csv")
    log3d = json.loads((P3D / "run_log.json").read_text())
    r1 = terms[terms["round"] == 1].to_csv(index=False).encode()
    assert hashlib.sha256(r1).hexdigest() == log3d["round1_sha256"], "round 1 search terms were changed"

    # check files for Roman, written before any search
    cu = {u: {"files": [pfile(q) for q in window(u)], "terms": check_terms(terms, u)} for u in UNITS}
    cu = {u: v for u, v in cu.items() if v["files"]}
    cu2 = {u: {"files": [pfile(q) for q in window(u, available=False)], "terms": check_terms(terms, u)}
           for u in UNITS if window(u, available=False)}
    (OUT / "check_units.json").write_text(json.dumps(cu, indent=2))
    (OUT / "check_units_2024q2.json").write_text(json.dumps(cu2, indent=2))
    files = sorted({f for v in cu.values() for f in v["files"]})
    before = {f: file_hash(REPORTS / f) for f in files}
    log = dict(round1_sha256=log3d["round1_sha256"], started=datetime.now().isoformat(timespec="seconds"),
               check_units_sha256=file_hash(OUT / "check_units.json"),
               check_units_2024q2_sha256=file_hash(OUT / "check_units_2024q2.json"), report_hashes=before)
    (OUT / "run_log.json").write_text(json.dumps(log, indent=2))

    # reconstruction (positioned layout, hyphen repair) and search
    pages = []
    for f in files:
        q = f.split("_")[1]
        html = (REPORTS / f).read_text(encoding="utf-8", errors="replace")
        pages += [dict(file=f, quarter=q, page=n, text=t) for n, t in pages_positioned(html, repair=True)]
    pages = pd.DataFrame(pages)
    pages.to_csv(OUT / "pillar3_pages.csv", index=False)
    rows = []
    for u in UNITS:
        tu = terms[(terms.unit == u) & (terms["round"] == 1)]
        comp = {g: [(t.term, compile_term(t)) for t in tu[tu.group == g].itertuples()] for g in (1, 2, 3)}
        for _, p in pages[pages.file.isin([pfile(q) for q in window(u)])].iterrows():
            for s in split_sentences(p.text):
                found = {g: [term for term, rx in comp[g] if rx.search(s)] for g in (1, 2, 3)}
                if not (found[2] or found[3]):
                    continue
                text = s
                if len(s) > LONG:
                    rx = next(rx for g in (3, 2) for term, rx in comp[g] if term in found[g])
                    m = rx.search(s)
                    text = "[...] " + s[max(0, m.start() - 300):m.end() + 300] + " [...]"
                fwd = bool(FORWARD_RE.search(s)) or bool(horizons(s, period_end(p.quarter)))
                prio = 3 if found[3] and (found[1] or found[2]) else 2 if found[2] and fwd else 1 if found[2] else 0
                rows.append(dict(unit=u, file=p.file, quarter=p.quarter, page=p.page, priority=prio, forward=fwd,
                                 g1=bool(found[1]), g2="; ".join(found[2]), g3="; ".join(found[3]),
                                 table_block=len(s) > LONG, text=text))
    hits = pd.DataFrame(rows)
    hits.to_csv(OUT / "hits.csv", index=False)
    assert {f: file_hash(REPORTS / f) for f in files} == before, "report files changed"
    print(pages.groupby("file").size())
    print(hits.groupby(["unit", "priority"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
