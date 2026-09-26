"""Phase 3h, step 3: search the text export for (a) and (b).

Run from the repository root after phase3h_terms.py: python notebooks/roman/analysis/phase3h_search.py
Refuses to run while the manifest is incomplete (plan: no search before the manifest is complete) or when a raw file,
text export or term file differs from its recorded hash. Writes hits_a.csv and hits_b.csv to
notebooks/roman/data/phase3h/.

Matching (plans/phase_3h.md): short upper-case acronyms (at most six characters without whitespace) as whole words,
case-sensitive, optional plural s; other phrases case-insensitive; figures with number boundaries, as in phase 3d.
(a) hit: a sentence with a phrase (group 2) or a figure (group 3); group 1 keywords rank. (b) hit: a sentence with a
metric phrase, flagged for figures and outcome words.
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
import report_text as rt  # noqa: E402
from phase3_extract import FORWARD_RE, horizons  # noqa: E402
from phase3c_counterparts import split_sentences  # noqa: E402
from phase3d_search import LONG  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3h"
FOR_2024 = {"T27", "T33"}


def is_acronym(term):
    s = "".join(term.split())
    return any(c.isalpha() for c in term) and term == term.upper() and len(s) <= 6


def compile_term(term, kind, regex=False):
    if regex:
        return re.compile(term, re.I)
    if is_acronym(term):
        return re.compile(r"(?<![A-Za-z])" + re.escape(term) + r"s?(?![A-Za-z])")
    if kind == "figure":
        return re.compile(r"(?<![\d.])" + re.escape(term) + r"(?![\d])", re.I)
    if kind == "outcome":
        return re.compile(r"\b" + re.escape(term) + r"\b", re.I)
    return re.compile(re.escape(term), re.I)


def report_label(name):
    m = re.match(r"UBS_(\d{4})(?:-(Q\d))?_(report|annual_report|pillar3)", name)
    y, q, kind = m.groups()
    return f"{y} annual report" if kind == "annual_report" else f"{y}-{q}" + (" Pillar 3" if kind == "pillar3" else "")


def period_end(name):
    m = re.match(r"UBS_(\d{4})(?:-Q(\d))?", name)
    y, q = int(m.group(1)), int(m.group(2) or 4)
    return pd.Timestamp(year=y, month=3 * q, day=1) + pd.offsets.MonthEnd(0)


def check_inputs():
    manifest = pd.read_csv(OUT / "manifest.csv", keep_default_na=False)
    inc = rt.incomplete(manifest)
    assert inc.empty, f"manifest incomplete, no search before it is complete: {list(inc.file)}"
    log = json.loads((OUT / "run_log.json").read_text())
    for f, key in [("a_terms.csv", "a_terms_sha256"), ("outcome_terms.csv", "outcome_terms_sha256"),
                   ("check_units_a.json", "check_units_a_sha256"), ("check_units_b.json", "check_units_b_sha256")]:
        assert hashlib.sha256((OUT / f).read_bytes()).hexdigest() == log[key], f"{f} changed after its hash"
    pages = {}
    for r in manifest.itertuples():
        raw = DATA / r.folder / r.file
        assert rt.sha256_bytes(raw.read_bytes()) == r.raw_sha256, f"{r.file} changed"
        t = (OUT / "text" / f"{Path(r.file).stem}.txt").read_bytes()
        assert rt.sha256_bytes(t) == r.text_sha256, f"text export of {r.file} changed"
        pages[r.file] = rt.parse_export(t.decode("utf-8"))
    return manifest, pages, log


def sentences(pages):
    for n, text in pages:
        for s in split_sentences(text):
            yield n, s


def shown(s, rx):
    if len(s) <= LONG:
        return s
    m = rx.search(s)
    return "[...] " + s[max(0, m.start() - 300):m.end() + 300] + " [...]"


def main():
    manifest, pages, log = check_inputs()
    pub = dict(zip(manifest.file, manifest.publication_date))
    new = [f for f in manifest.file if manifest.set_index("file").loc[f, "folder"] == "reports_2025_2026"]
    a = pd.read_csv(OUT / "a_terms.csv", keep_default_na=False)
    b = pd.read_csv(OUT / "outcome_terms.csv", keep_default_na=False)

    rows_a = []
    for u, tu in a.groupby("unit", sort=False):
        comp = {g: [(t.term, compile_term(t.term, "figure" if g == 3 else "phrase", str(t.regex) == "True"))
                    for t in tu[tu.group == g].itertuples()] for g in (1, 2, 3)}
        for f in new:
            for n, s in sentences(pages[f]):
                found = {g: [term for term, rx in comp[g] if rx.search(s)] for g in (1, 2, 3)}
                if not (found[2] or found[3]):
                    continue
                rx = next(rx for g in (3, 2) for term, rx in comp[g] if term in found[g])
                fwd = bool(FORWARD_RE.search(s)) or bool(horizons(s, period_end(f).date()))
                prio = 3 if found[3] and (found[1] or found[2]) else 2 if found[2] and fwd else 1 if found[2] else 0
                rows_a.append(dict(unit=u, file=f, report=report_label(f), publication_date=pub[f], page=n,
                                   priority=prio, forward=fwd, g1=bool(found[1]), g2="; ".join(found[2]),
                                   g3="; ".join(found[3]), table_block=len(s) > LONG, text=shown(s, rx)))
    hits_a = pd.DataFrame(rows_a)
    hits_a.to_csv(OUT / "hits_a.csv", index=False)

    rows_b = []
    for u, tu in b.groupby("unit", sort=False):
        comp = {k: [(t.term, compile_term(t.term, k)) for t in tu[tu.kind == k].itertuples()]
                for k in ("metric", "figure", "outcome")}
        files = new + ([f for f in manifest.file if f not in new] if u in FOR_2024 else [])
        for f in files:
            for n, s in sentences(pages[f]):
                found = {k: [term for term, rx in comp[k] if rx.search(s)] for k in comp}
                if not found["metric"]:
                    continue
                rx = next(rx for term, rx in comp["metric"] if term in found["metric"])
                fwd = bool(FORWARD_RE.search(s)) or bool(horizons(s, period_end(f).date()))
                prio = 2 if (found["figure"] or found["outcome"]) else 1
                rows_b.append(dict(unit=u, file=f, report=report_label(f), publication_date=pub[f], page=n,
                                   priority=prio, forward=fwd, metric="; ".join(found["metric"]),
                                   figure="; ".join(found["figure"]), outcome="; ".join(found["outcome"]),
                                   table_block=len(s) > LONG, text=shown(s, rx)))
    hits_b = pd.DataFrame(rows_b)
    hits_b.to_csv(OUT / "hits_b.csv", index=False)

    log["search_started"] = datetime.now().isoformat(timespec="seconds")
    (OUT / "run_log.json").write_text(json.dumps(log, indent=2))
    print(hits_a.groupby(["unit", "priority"]).size().unstack(fill_value=0).to_string())
    print(hits_b.groupby(["unit", "priority"]).size().unstack(fill_value=0).to_string())


if __name__ == "__main__":
    main()
