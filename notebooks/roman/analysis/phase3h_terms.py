"""Phase 3h, step 2: search terms for (a) and (b), check files for Roman with pipeline hit counts, deviation list.

Run from the repository root after phase3h_text.py: python notebooks/roman/analysis/phase3h_terms.py
- a_terms.csv: the phase 3d round-1 terms (T16, T25, T27, T30, T32, T33, T68) and the phase 3g terms (F11, F12, F22),
  unchanged; both source hashes are checked.
- outcome_terms.csv: the (b) terms fixed in plans/phase_3h.md.
- check_units_a.json, check_units_b.json: known format plus "pipeline_hits" [[file, term, near, hits], ...], counted
  on the text export with the matching rule of Roman's phase 3h tool (copied to a temporary directory).
- deviations.csv: every term and file where the tool's count on the raw HTML differs from the pipeline count.
Hashes of all written files go into run_log.json before any search.
"""
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
import report_text as rt  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3h"
TOOL = OUT / "roman_check" / "check_terms.py"
UNITS_3D = ["T16", "T25", "T27", "T30", "T32", "T33", "T68"]
UNITS_3G = ["F11", "F12", "F22"]
UNITS = UNITS_3D[:3] + ["T30"] + UNITS_3D[4:] + UNITS_3G
FOR_2024 = {"T27", "T33"}  # (b) also reads the 2024-Q4 report and the 2024 annual report

# (b) terms, as tabled in plans/phase_3h.md: metric phrases, figures
OUTCOME = {
    "T16": (["operational risk RWA", "operational risk risk-weighted assets", "Non-core and Legacy"],
            ["14bn", "14 billion"]),
    "T25": (["capital release", "capital released", "released capital", "Non-core and Legacy"], ["6bn", "6 billion"]),
    "T27": (["credit and market risk", "market and credit risk", "Non-core and Legacy"], ["40bn", "40 billion"]),
    "T30": (["integration-related expenses", "costs to achieve"], ["13bn", "13 billion", "14bn", "14 billion"]),
    "T32": (["going concern capital requirement", "going concern requirement", "phase-in"],
            ["16.7%", "180 basis points", "180bps"]),
    "T33": (["AT1", "additional tier 1"], ["2bn", "2 billion"]),
    "T68": (["HoldCo", "total loss-absorbing capacity", "TLAC"], ["90bn", "90 billion"]),
    "F11": (["going concern capital ratio"], ["18%", "18 %"]),
    "F12": (["leverage ratio denominator", "LRD"], ["100bn", "100 billion"]),
    "F22": (["liquidity coverage ratio", "LCR"], ["188%", "188 %"]),
}
OUTCOME_WORDS = ["achieved", "reached", "met", "completed", "exceeded", "delivered", "below", "above", "revised",
                 "updated", "now expect", "no longer", "replaced", "discontinued", "remaining", "cumulative"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tool():
    sums = {ln.split()[1]: ln.split()[0] for ln in (OUT / "roman_check" / "SHA256SUMS").read_text().splitlines() if ln}
    assert sha(TOOL) == sums[str(TOOL.relative_to(ROOT))], "check tool changed"
    sys.dont_write_bytecode = True
    tmp = Path(tempfile.mkdtemp()) / "check_terms_v2.py"
    shutil.copyfile(TOOL, tmp)
    spec = importlib.util.spec_from_file_location("check_terms_v2", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def a_terms():
    t3d = pd.read_csv(DATA / "phase3d" / "search_terms.csv")
    r1 = t3d[t3d["round"] == 1]
    assert hashlib.sha256(r1.to_csv(index=False).encode()).hexdigest() == \
        json.loads((DATA / "phase3d" / "run_log.json").read_text())["round1_sha256"]
    assert sha(DATA / "phase3g" / "search_terms.csv") == \
        json.loads((DATA / "phase3g" / "run_log.json").read_text())["search_terms_sha256"]
    t3g = pd.read_csv(DATA / "phase3g" / "search_terms.csv")
    a = pd.concat([r1[r1.unit.isin(UNITS_3D)].drop(columns="round").assign(source="phase3d round 1"),
                   t3g[t3g.unit.isin(UNITS_3G)].assign(source="phase3g")], ignore_index=True)
    return a[["unit", "group", "term", "regex", "source"]]


def b_terms():
    rows = []
    for u, (phrases, figures) in OUTCOME.items():
        rows += [dict(unit=u, kind="metric", term=p) for p in phrases]
        rows += [dict(unit=u, kind="figure", term=f) for f in figures]
        rows += [dict(unit=u, kind="outcome", term=w) for w in OUTCOME_WORDS]
    return pd.DataFrame(rows)


def cause(r):
    """Cause of a deviation, established by reading the matches in both texts (plan: explained before reading)."""
    if r.near:
        return ("keyword window: the export orders table cells row by row, the raw HTML in document order, so the "
                "distance between term and keyword differs")
    if r.term == "phase-in" and r.file.endswith("UBS_2025-Q3_pillar3.htm"):
        return "hyphen repair: one line-end 'phase- in' is joined as 'phasein' in the export"
    return ("table or glossary layout: multi-line column headers and labels are interleaved row by row in the "
            "export (e.g. 'Non-core and Banking Management Bank Legacy'); the raw HTML keeps them together")


def rel(p):
    """File name relative to data/reports/ (Roman's tool)."""
    return p.name if p.parent.name == "reports" else f"../{p.parent.name}/{p.name}"


def main():
    import phase3h_text
    manifest = pd.read_csv(OUT / "manifest.csv", keep_default_na=False)
    new = [p for p in phase3h_text.files() if p.parent.name == "reports_2025_2026"]
    old = phase3h_text.OLD_FOR_B
    text = {}
    for p in new + old:
        t = (OUT / "text" / f"{p.stem}.txt").read_bytes()
        assert rt.sha256_bytes(t) == manifest.set_index("file").loc[p.name, "text_sha256"], p.name
        text[rel(p)] = " ".join(pg for _, pg in rt.parse_export(t.decode("utf-8")))

    a, b = a_terms(), b_terms()
    a.to_csv(OUT / "a_terms.csv", index=False)
    b.to_csv(OUT / "outcome_terms.csv", index=False)

    mod = tool()

    def count(txt, term, near):
        return sum(1 for m in mod.tolerant(term).finditer(txt)
                   if not near or mod.tolerant(near).search(txt[max(0, m.start() - mod.NEAR):m.end() + mod.NEAR]))

    def entry(files, terms):
        return {"files": files, "terms": terms,
                "pipeline_hits": [[f, t, n, count(text[f], t, n)] for f in files for t, n in terms]}

    cu_a, cu_b = {}, {}
    for u in UNITS:
        ta = a[a.unit == u]
        phrases, figures = ta[ta.group == 2].term.tolist(), ta[ta.group == 3].term.tolist()
        cu_a[u] = entry([rel(p) for p in new], [[p, None] for p in phrases] + [[f, phrases[0]] for f in figures])
        mp, fig = OUTCOME[u]
        terms_b = [[p, None] for p in mp] + [[f, mp[0]] for f in fig] + [[w, mp[0]] for w in OUTCOME_WORDS]
        cu_b[u] = entry([rel(p) for p in new + (old if u in FOR_2024 else [])], terms_b)
    (OUT / "check_units_a.json").write_text(json.dumps(cu_a, indent=2))
    (OUT / "check_units_b.json").write_text(json.dumps(cu_b, indent=2))

    # deviation list: the tool on the raw HTML against the pipeline count on the export
    dev = []
    for name, cu in [("a", cu_a), ("b", cu_b)]:
        for u, v in cu.items():
            for f, t, n, k in v["pipeline_hits"]:
                r = count(mod.report_text(f), t, n)
                if r != k:
                    dev.append(dict(check_file=name, unit=u, file=f, term=t, near=n or "", pipeline=k, tool_raw=r))
    dev = pd.DataFrame(dev, columns=["check_file", "unit", "file", "term", "near", "pipeline", "tool_raw"])
    dev["cause"] = [cause(r) for r in dev.itertuples()]
    dev.to_csv(OUT / "deviations.csv", index=False)

    log = json.loads((OUT / "run_log.json").read_text())
    log.update(terms_written=datetime.now().isoformat(timespec="seconds"),
               a_terms_sha256=sha(OUT / "a_terms.csv"), outcome_terms_sha256=sha(OUT / "outcome_terms.csv"),
               check_units_a_sha256=sha(OUT / "check_units_a.json"),
               check_units_b_sha256=sha(OUT / "check_units_b.json"), check_tool_sha256=sha(TOOL))
    (OUT / "run_log.json").write_text(json.dumps(log, indent=2))
    print(len(a), "(a) terms,", len(b), "(b) terms;", len(dev), "deviations")


if __name__ == "__main__":
    main()
