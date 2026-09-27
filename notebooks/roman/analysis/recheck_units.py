"""Check files for Roman's recheck of phases 3e and 3g with the phase 3h version of check_terms.py.

Run from the repository root: python notebooks/roman/analysis/recheck_units.py
Writes data/phase3g/check_units_recheck.json (F12, F22: all reports phase 3g read for the unit) and
data/phase3e/check_units_recheck.json (T17: the files of the phase 3e check), in the known format, with the extra key
"pipeline_hits": [[file, term, near, hits], ...]. The hit count applies the matching rule of the phase 3h tool
(short upper-case acronyms as whole words, other terms tolerant, near-keyword window) to the page text the pipeline
read in that phase (3g: repaired reconstruction and the Pillar 3 pages of 3g and of the 2024-Q2 amendment; 3e: the
phase 3b reconstruction), pages joined with one space. The tool is copied to a temporary directory and imported
from there. File names are relative to data/reports/.
"""
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "notebooks" / "roman" / "data"
V2 = DATA / "phase3h" / "roman_check" / "check_terms.py"
SUMS = DATA / "phase3h" / "roman_check" / "SHA256SUMS"


def tool():
    sums = {line.split()[1]: line.split()[0] for line in SUMS.read_text().splitlines() if line.strip()}
    assert hashlib.sha256(V2.read_bytes()).hexdigest() == sums[str(V2.relative_to(ROOT))]
    sys.dont_write_bytecode = True
    tmp = tempfile.mkdtemp()
    copy = Path(tmp) / "check_terms_v2.py"
    shutil.copyfile(V2, copy)
    spec = importlib.util.spec_from_file_location("check_terms_v2", copy)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def texts(*page_files):
    p = pd.concat([pd.read_csv(f, keep_default_na=False)[["file", "page", "text"]] for f in page_files])
    return {f: " ".join(g.sort_values("page").text) for f, g in p.groupby("file")}


def count(mod, text, term, near):
    return sum(1 for m in mod.tolerant(term).finditer(text)
               if not near or mod.tolerant(near).search(text[max(0, m.start() - mod.NEAR):m.end() + mod.NEAR]))


def unit_entry(mod, files, terms, text):
    return {"files": files, "terms": terms,
            "pipeline_hits": [[f, t, n, count(mod, text[f], t, n)] for f in files for t, n in terms]}


def main():
    mod = tool()
    # phase 3g: F12 and F22, the reports and Pillar 3 reports read for each unit
    t3g = texts(DATA / "phase3b_repaired" / "report_pages.csv", DATA / "phase3g" / "pillar3_pages.csv",
                DATA / "phase3g" / "pillar3_2024q2" / "pages.csv")
    cu = json.loads((DATA / "phase3g" / "check_units.json").read_text())
    hits = pd.read_csv(DATA / "phase3g" / "hits.csv", keep_default_na=False)
    p3 = pd.read_csv(DATA / "phase3g" / "pillar3_hits.csv", keep_default_na=False)
    reports = sorted(hits.file.unique())
    out = {}
    for u in ["F12", "F22"]:
        pillar3 = sorted(set(p3[p3.unit == u].file) | ({"UBS_2024-Q2_pillar3.htm"} if u == "F12" else set()))
        out[u] = unit_entry(mod, reports + pillar3, cu[u]["terms"], t3g)
    (DATA / "phase3g" / "check_units_recheck.json").write_text(json.dumps(out, indent=2))
    # phase 3e: T17, files and terms of the phase 3e check
    t3e = texts(DATA / "phase3b" / "report_pages.csv")
    cu = json.loads((DATA / "phase3e" / "check_units.json").read_text())
    out3e = {"T17": unit_entry(mod, cu["T17"]["files"], cu["T17"]["terms"], t3e)}
    (DATA / "phase3e" / "check_units_recheck.json").write_text(json.dumps(out3e, indent=2))
    # comparison with the tool's own count on the raw HTML, for information
    for name, units in [("3g", out), ("3e", out3e)]:
        for u, v in units.items():
            for f, t, n, k in v["pipeline_hits"]:
                raw = count(mod, mod.report_text(f), t, n)
                if raw != k:
                    print(f"{name} {u} {f} '{t}' near {n!r}: pipeline {k}, raw HTML {raw}")
    print({u: len(v["files"]) for u, v in {**out, **out3e}.items()})


if __name__ == "__main__":
    main()
