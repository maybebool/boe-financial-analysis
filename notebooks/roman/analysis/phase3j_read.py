"""Phase 3j, steps 2 and 3: hits of the check tool, passages to read, and the reading result.

Run from the repository root:
    python notebooks/roman/analysis/phase3j_read.py hits      # after check_terms.py: hits.csv, passages.csv
    python notebooks/roman/analysis/phase3j_read.py classify  # after reading: read.csv, summary.csv, SHA256SUMS
The raw tool output is check_hits_3j.txt. The tool prints contexts but no positions, so the hits are located
again with the tool's own functions (imported unchanged) and their number per unit, file and term is checked
against the tool output. Overlapping contexts are merged into passages; a passage is read once. Plan:
plans/phase_3j.md.
"""
import csv
import hashlib
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
import phase3_extract as p3  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3j"
TOOL = DATA / "phase3h" / "roman_check" / "check_terms.py"
TOOL_SHA = "c27228e8bee109eb636cdad7af4ae8cdc60273698e9fdb93ab6af726702f6e2d"
FORWARD = re.compile(p3.FORWARD_RE.pattern[:-3] + r"|will|would|aim(s|ed|ing)?|intend(s|ed|ing)?|anticipat(e|es|ed|ing)|"
                     r"estimat(e|es|ed|ing)|ambitions?|objectives?|goals?|outlook)\b", re.I)
CAP = 600
CLASSES = ["same target, same unit", "same target, another unit", "same target, another figure", "result",
           "definition or requirement", "other"]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tool():
    if sha256(TOOL) != TOOL_SHA:
        raise SystemExit("check_terms.py differs from the version fixed in the plan")
    spec = importlib.util.spec_from_file_location("check_terms", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tool_counts():
    """Hits per unit, file and term as printed by the tool."""
    counts, unit, file, expect_unit = {}, None, None, False
    for line in (OUT / "check_hits_3j.txt").read_text().splitlines():
        if line.startswith("=" * 100):
            expect_unit = True
        elif expect_unit:
            unit, expect_unit = line.strip(), False
        elif line.startswith("--- "):
            file = line[4:].strip()
        else:
            m = re.match(r"  '(.*?)'(?: near '(.*)')?: (\d+) hit\(s\)$", line)
            if m:
                counts[(unit, file, m.group(1), m.group(2) or "")] = int(m.group(3))
    return counts


def hits():
    ct = tool()
    units = json.loads((OUT / "check_units_3j.json").read_text())
    index = pd.read_csv(OUT / "term_index.csv", keep_default_na=False)
    info = {(r.unit, r.term, r.near): (r.search_pass, r.form) for r in index.itertuples()}
    printed, rows = tool_counts(), []
    for unit, u in units.items():
        for file in u["files"]:
            text = ct.report_text(file)
            for term, near in u["terms"]:
                near = near or ""
                found = []
                for m in ct.tolerant(term).finditer(text):
                    if near and not ct.tolerant(near).search(text[max(0, m.start() - ct.NEAR):m.end() + ct.NEAR]):
                        continue
                    found.append(m)
                if printed.get((unit, file, term, near)) != len(found):
                    raise SystemExit(f"hit count differs from the tool output: {unit} {file} {term!r} {near!r}")
                search_pass, form = info[(unit, term, near)]
                for m in found:
                    lo, hi = max(0, m.start() - ct.CONTEXT), m.end() + ct.CONTEXT
                    context = text[lo:hi]
                    forward = bool(FORWARD.search(context))
                    quantity = bool(p3.quantities(context))
                    rows.append({"unit": unit, "file": file, "search_pass": search_pass, "term": term, "near": near,
                                 "form": form, "start": m.start(), "end": m.end(), "forward_word": forward,
                                 "quantity": quantity,
                                 "to_read": search_pass == "A" or (forward and quantity), "context": context})
    h = pd.DataFrame(rows)
    h.to_csv(OUT / "hits.csv", index=False)

    # passages: merged contexts of the hits to read, per unit and file; identical passages across files read once
    passages = []
    for (unit, file), g in h[h.to_read].groupby(["unit", "file"], sort=False):
        text = ct.report_text(file)
        spans = sorted((max(0, s - ct.CONTEXT), e + ct.CONTEXT) for s, e in zip(g.start, g.end))
        merged = [list(spans[0])]
        for lo, hi in spans[1:]:
            if lo <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        for lo, hi in merged:
            inside = g[(g.start >= lo) & (g.end <= hi)]
            passages.append({"unit": unit, "file": file, "start": lo, "end": hi,
                             "passes": "".join(sorted(set(inside.search_pass))),
                             "terms": " | ".join(sorted(set(inside.term + inside.near.map(lambda n: f" ~ {n}" if n else "")))),
                             "forward_word": bool(FORWARD.search(text[lo:hi])), "text": text[lo:hi]})
    p = pd.DataFrame(passages)
    p["text_id"] = p.text.map(lambda t: hashlib.sha256(t.encode()).hexdigest()[:12])
    p.to_csv(OUT / "passages.csv", index=False)

    s = h.groupby(["unit", "search_pass"]).agg(hits=("term", "size"), hits_to_read=("to_read", "sum")).unstack(fill_value=0)
    s.columns = [f"{a}_{b}" for a, b in s.columns]
    s["passages_to_read"] = p.groupby("unit").size()
    s["distinct_passages"] = p.groupby("unit").text_id.nunique()
    s["over_cap"] = s.distinct_passages > CAP
    print(s.fillna(0).astype({"passages_to_read": int, "distinct_passages": int}).to_string())
    log = {"tool_sha256": TOOL_SHA, "check_units_sha256": sha256(OUT / "check_units_3j.json"),
           "check_hits_sha256": sha256(OUT / "check_hits_3j.txt"), "check_max_hits": 100000,
           "hits": len(h), "hits_to_read": int(h.to_read.sum()), "passages_to_read": len(p),
           "distinct_passages": int(p.text_id.nunique()), "cap": CAP}
    (OUT / "run_log.json").write_text(json.dumps(log, indent=2))


def page_texts():
    """Page texts of the 16 reports: phase 3b (repaired) for reports, phase 3f and 3g for the Pillar 3 reports."""
    csv.field_size_limit(sys.maxsize)
    pages = defaultdict(dict)
    sources = [DATA / "phase3b_repaired" / "report_pages.csv", DATA / "phase3f" / "pillar3_pages.csv",
               DATA / "phase3f" / "pillar3_2024q2" / "pages.csv"]
    for src in sources:
        with open(src) as f:
            for r in csv.DictReader(f):
                pages[r["file"]][int(r["page"])] = re.sub(r"\s+", " ", r["text"])
    return pages


def find_page(pages, file, quote):
    q = re.sub(r"\s+", " ", quote).strip()
    hit = [p for p, t in sorted(pages[file].items()) if q in t]
    if not hit:
        raise SystemExit(f"quote not found verbatim on any page of {file}: {quote[:80]}")
    return hit[0]


def classify():
    p = pd.read_csv(OUT / "passages.csv", keep_default_na=False)
    r = pd.read_csv(OUT / "reading_3j.csv", keep_default_na=False)       # my reading: one row per distinct passage
    if set(p.text_id) != set(r.text_id) or not r["class"].isin(CLASSES).all():
        raise SystemExit("reading_3j.csv does not cover the passages or uses an unknown class")
    pages = page_texts()
    read = p.merge(r[["unit", "text_id", "class", "forward_looking", "quote", "conversion", "comment"]],
                   on=["unit", "text_id"], how="left", validate="many_to_one")
    read["page"] = [find_page(pages, f, q) if q else "" for f, q in zip(read.file, read.quote)]
    read.drop(columns=["start", "end"]).to_csv(OUT / "read.csv", index=False)

    h = pd.read_csv(OUT / "hits.csv", keep_default_na=False)
    forms = pd.read_csv(OUT / "forms.csv")
    rows = []
    for unit in forms.unit.unique():
        hu, ru = h[h.unit == unit], read[read.unit == unit]
        row = {"unit": unit, "forms": int((forms.unit == unit).sum()),
               "hits_pass_A": int((hu.search_pass == "A").sum()), "hits_pass_B": int((hu.search_pass == "B").sum()),
               "hits_pass_B_read": int(((hu.search_pass == "B") & hu.to_read.astype(str).eq("True")).sum()),
               "passages_read": len(ru), "distinct_passages_read": int(ru.text_id.nunique())}
        for c in CLASSES:
            row[c] = int((ru["class"] == c).sum())
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / "summary.csv", index=False)
    names = [n for n in sorted(x.name for x in OUT.iterdir() if x.is_file()) if n != "SHA256SUMS"]
    (OUT / "SHA256SUMS").write_text("".join(f"{sha256(OUT / n)}  {n}\n" for n in names))
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    {"hits": hits, "classify": classify}[sys.argv[1]]()
