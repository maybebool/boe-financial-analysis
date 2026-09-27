"""Phase 3d, step 2: search every unit's terms in all reports of the same bank up to the end of 2024.

Run from the repository root after phase3d_terms.py: python notebooks/roman/analysis/phase3d_search.py
Records the hash of search_terms.csv in run_log.json before searching and writes hits.csv. A hit is a report
sentence that contains a phrase (group 2) or a figure (group 3); metric keywords (group 1) alone are too broad to
count as a hit and are used to rank hits. Figures are matched with word boundaries, so "13bn" never hits "113bn".
"""
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase3_extract import FORWARD_RE, horizons  # noqa: E402
from phase3b_reports import file_hashes  # noqa: E402
from phase3c_counterparts import QUARTERS, period_end, split_sentences  # noqa: E402

PHASE3B = ROOT / "notebooks" / "roman" / "data" / "phase3b"
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3d"
TERMS_DIR = OUT  # units, search terms and the round-1 hash always come from here
# --repaired: same terms on the repaired reconstruction (hyphen fix of 2026-09-23), output to its own folder,
# so that counterparts_read.csv and the hits it was read from stay unchanged
REPAIRED = "--repaired" in sys.argv
if REPAIRED:
    PHASE3B = ROOT / "notebooks" / "roman" / "data" / "phase3b_repaired"
    OUT = ROOT / "notebooks" / "roman" / "data" / "phase3d" / "repaired"
LONG = 500


def w1(u):
    """Same-quarter report, all earlier reports (including earlier annual reports) and, for UBS, the annual
    report of the same fiscal year."""
    q = "2023-Q2" if u.call_type == "event" else u.quarter
    w = [x for x in QUARTERS if x <= q]
    if u.bank == "UBS":
        w += [f"{y} annual report" for y in (2023, 2024) if y <= int(q[:4])]
    return w


def sentences():
    p = pd.read_csv(PHASE3B / "report_pages.csv", keep_default_na=False)
    rows = []
    for _, r in p.iterrows():
        for s in split_sentences(r.text):
            rows.append(dict(bank=r.bank, report=r.quarter, file=r.file, page=r.page, text=s))
    return pd.DataFrame(rows)


def compile_term(t):
    if t.regex:
        return re.compile(t.term, re.I)
    if t.group == 3:
        return re.compile(r"(?<![\d.])" + re.escape(t.term) + r"(?![\d])", re.I)
    return re.compile(re.escape(t.term), re.I)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    terms_path = TERMS_DIR / "search_terms.csv"
    prev = json.loads((TERMS_DIR / "run_log.json").read_text())
    terms_now = pd.read_csv(terms_path)
    round1 = terms_now[terms_now["round"] == 1].to_csv(index=False).encode()
    log = dict(round1_sha256=prev.get("round1_sha256", hashlib.sha256(round1).hexdigest()),
               round1_rows=prev.get("round1_rows", int((terms_now["round"] == 1).sum())),
               search_terms_sha256=hashlib.sha256(terms_path.read_bytes()).hexdigest(),
               rounds=sorted(terms_now["round"].unique().tolist()),
               started=datetime.now().isoformat(timespec="seconds"), report_hashes=file_hashes())
    assert hashlib.sha256(round1).hexdigest() == log["round1_sha256"], "round 1 search terms were changed"
    (OUT / "run_log.json").write_text(json.dumps(log, indent=2))
    units = pd.read_csv(TERMS_DIR / "units.csv")
    terms = pd.read_csv(terms_path)
    rs = sentences()
    rows = []
    for _, u in units.iterrows():
        tu = terms[terms.unit == u.unit]
        comp = {g: [(t.term, compile_term(t)) for t in tu[tu.group == g].itertuples()] for g in (1, 2, 3)}
        win1 = set(w1(u))
        for _, r in rs[rs.bank == u.bank].iterrows():
            found = {g: [term for term, rx in comp[g] if rx.search(r.text)] for g in (1, 2, 3)}
            if not (found[2] or found[3]):
                continue
            text = r.text
            if len(text) > LONG:  # table block: show a window around the first phrase or figure hit
                rx = next(rx for g in (3, 2) for term, rx in comp[g] if term in found[g])
                m = rx.search(text)
                text = "[...] " + text[max(0, m.start() - 300):m.end() + 300] + " [...]"
            fwd = bool(FORWARD_RE.search(r.text)) or bool(horizons(r.text, period_end(r.report)))
            prio = 3 if found[3] and (found[1] or found[2]) else 2 if found[2] and fwd else 1 if found[2] else 0
            rows.append(dict(unit=u.unit, bank=u.bank, report=r.report, in_W1=r.report in win1, file=r.file,
                             page=r.page, priority=prio, forward=fwd, g1=bool(found[1]), g2="; ".join(found[2]),
                             g3="; ".join(found[3]), table_block=len(r.text) > LONG, text=text))
    hits = pd.DataFrame(rows)
    hits.to_csv(OUT / "hits.csv", index=False)
    assert file_hashes() == log["report_hashes"], "report files changed"
    print(hits.groupby("unit").size().describe())
    print(hits.groupby(["unit", "priority"]).size().unstack(fill_value=0).head(80).to_string())


if __name__ == "__main__":
    main()
