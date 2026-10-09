"""Build the inputs of the submission section 05_call_only_targets from the result files of the analysis.

Run from the repository root: python notebooks/roman/analysis/build_final_inputs.py
Reads notebooks/roman/data/ (never modified) and writes notebooks/final/data/call_only_targets/.

The script copies the result files under neutral names, renames the column checked_by_roman to checked_manually,
rewrites personal references in free-text columns by the fixed list in REWRITES, derives four tables
(targets_39.csv, quotes_all.csv, reports_manifest.csv, report_sources.csv) and writes build_log.csv with source
file, source SHA-256, target file, target SHA-256 and the changes made. It stops if a personal reference remains.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "notebooks" / "roman" / "data"
FINAL = ROOT / "notebooks" / "final"
OUT = FINAL / "data" / "call_only_targets"
REPORT_FOLDERS = [SOURCE / "reports", SOURCE / "reports_2025_2026"]
sys.path.insert(0, str(FINAL / "notebooks" / "05_call_only_targets"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_checks as rc  # noqa: E402
from phase3h_v2 import QUOTES as CORRECTED_QUOTES  # noqa: E402

# source file -> target file
FILES = {
    "phase3d/counterparts_read.csv": "counterparts_to_2024.csv",
    "phase3g/new_units_read.csv": "targets_added_by_fls.csv",
    "phase3g/basis.csv": "class_counts_before_corrections.csv",
    "phase3f/pillar3_read.csv": "pillar3_read.csv",
    "phase3f/pillar3_2024q2/read.csv": "pillar3_2024q2_read_first_units.csv",
    "phase3g/pillar3_2024q2/read.csv": "pillar3_2024q2_read_added_units.csv",
    "phase3b/comparison.csv": "call_vs_report_cases.csv",
    "phase3e/mentions.csv": "channel_mentions.csv",
    "phase3e/first_mentions.csv": "channel_first_mentions.csv",
    "phase3e/call_first.csv": "call_first.csv",
    "phase3e/counts.csv": "channel_counts.csv",
    "phase3h/units_3h_v2.csv": "outcomes_units.csv",
    "phase3h/corrections_v2.csv": "outcome_corrections.csv",
    "phase3h/classes_a.csv": "classes_2025_2026.csv",
    "phase3h/outcomes_b.csv": "outcomes_by_report.csv",
    "phase3h/quotes.csv": "quotes_2025_2026.csv",
    "phase3i/units_match.csv": "export_match.csv",
    "phase3i/call_counts.csv": "export_call_counts.csv",
    "phase3i/summary.json": "export_check_summary.json",
    "phase3j/forms.csv": "equivalent_forms.csv",
    "phase3j/summary.csv": "equivalent_forms_summary.csv",
    "phase3j/read.csv": "equivalent_forms_read.csv",
    "phase3j/judgments_full.csv": "equivalent_forms_judgments.csv",
    "phase3j/run_log.json": "equivalent_forms_run_log.json",
}
PERSON = "Roman"
FOLDER = "roman"
# ordered rewrites of personal references: (label, pattern, replacement)
REWRITES = [
    ("column name", rf"checked_by_{FOLDER}", "checked_manually"),
    ("check folder path", rf"data/phase\w+/{FOLDER}_check/recheck_2026-09-26/", "recheck files of 2026-09-26"),
    ("check folder path", rf"data/phase\w+/{FOLDER}_check/", "the check files"),
    ("dated recheck", rf"{PERSON}, recheck (\d{{4}}-\d\d-\d\d)", r"Manual recheck \1"),
    ("dated check", rf"{PERSON} (\d{{4}}-\d\d-\d\d)", r"Manual check \1"),
    ("status", rf"confirmed by {PERSON}", "confirmed by manual check"),
    ("status", rf"checked by {PERSON}", "checked manually"),
    ("wording", rf"read by {PERSON}", "read manually"),
    ("wording", rf"\({PERSON}'s decision\)", "(decision after review)"),
    ("wording", rf"{PERSON}'s decision of", "the decision of"),
    ("wording", rf"since {PERSON}'s check", "since the manual check"),
    ("wording", rf"after {PERSON}'s check", "after the manual check"),
    ("wording", rf"{PERSON}'s check", "the manual check"),
]
NO_FIGURE = {"T16", "T25", "T27", "F12"}      # class B, the report sentence carries no figure
SEPARATE = {"T30"}                            # integration-cost total, counted separately
T32_REPORT = "around USD 10bn added to the tier 1 capital requirement when fully phased in (2024-Q1 report, p. 42)"
LOCATION_RE = re.compile(r"(UBS_[\w-]+\.htm), page (\d+)")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def neutralise(text):
    changes = []
    for label, pattern, repl in REWRITES:
        text, n = re.subn(pattern, repl, text)
        if n:
            changes.append(f"{label}: {n}")
    if re.search(FOLDER, text, re.I):
        where = re.search(FOLDER, text, re.I)
        raise SystemExit(f"personal reference left: ...{text[max(0, where.start() - 60):where.end() + 60]}...")
    return text, changes


def copy_files(source):
    log = []
    for src_name, dst_name in FILES.items():
        src = source / src_name
        text, changes = neutralise(src.read_text(encoding="utf-8"))
        (OUT / dst_name).write_text(text, encoding="utf-8")
        log.append({"source_file": src_name, "source_sha256": sha256(src), "target_file": dst_name,
                    "target_sha256": sha256(OUT / dst_name), "changes": "; ".join(changes) or "none"})
    return log


def targets():
    """The 39 targets in one table, with the status of the figure in the reports up to the end of 2024."""
    d = pd.read_csv(OUT / "counterparts_to_2024.csv", keep_default_na=False)
    d = d[(d.bank == "UBS") & (d.genuine == "yes") & (d.type == "target") & (d.pre_acquisition != "yes")]
    a = pd.DataFrame({"unit": d.unit, "found_by": "rules", "call": d.origin.str.split().str[0],
                      "call_sentence": d.call_sentence, "figure_call": d.figure_call, "class_to_2024": d.class_all,
                      "figure_report": d.figure_report, "quote": d.quote_all, "file": d.file_all, "page": d.page_all,
                      "checked_manually": d.checked_manually})
    g = pd.read_csv(OUT / "targets_added_by_fls.csv", keep_default_na=False)
    g = g[g.type == "target"]
    b = pd.DataFrame({"unit": g.unit, "found_by": "FinBERT-FLS", "call": g.quarter, "call_sentence": g.call_sentence,
                      "figure_call": g.description, "class_to_2024": g.class_all, "figure_report": "",
                      "quote": g.quote_all, "file": g.file_all, "page": g.page_all,
                      "checked_manually": g.checked_manually})
    t = pd.concat([a, b], ignore_index=True)
    if (len(a), len(b)) != (31, 8):
        raise SystemExit(f"expected 31 and 8 targets, found {len(a)} and {len(b)}")

    def status(r):
        if r.unit in SEPARATE:
            return "separate"
        if r.class_to_2024 == "A":
            return "same figure"
        if r.class_to_2024 == "C":
            return "not mentioned"
        return "no figure" if r.unit in NO_FIGURE else "another figure"

    t["report_status"] = [status(r) for r in t.itertuples()]
    t.loc[t.unit == "T32", "figure_report"] = T32_REPORT
    cols = ["unit", "found_by", "call", "call_sentence", "figure_call", "class_to_2024", "report_status",
            "figure_report", "quote", "file", "page", "checked_manually"]
    t[cols].to_csv(OUT / "targets_39.csv", index=False)
    return t


def quotes():
    """Every report quote with file and page, from all delivered tables, for the verbatim check."""
    rows = []

    def add(origin, unit, use, file, page, quote):
        if quote and file and str(page).strip():
            rows.append({"origin": origin, "unit": unit, "use": use, "file": file, "page": int(float(page)),
                         "quote": quote})

    t = pd.read_csv(OUT / "targets_39.csv", keep_default_na=False)
    for r in t.itertuples():
        add("targets_39.csv", r.unit, "counterpart to 2024", r.file, r.page, r.quote)
    d = pd.read_csv(OUT / "counterparts_to_2024.csv", keep_default_na=False)
    for r in d[d.unit.isin(t.unit)].itertuples():
        add("counterparts_to_2024.csv", r.unit, "counterpart, first window", r.file, r.page, r.quote_report)
    g = pd.read_csv(OUT / "targets_added_by_fls.csv", keep_default_na=False)
    for r in g[g.type == "target"].itertuples():
        add("targets_added_by_fls.csv", r.unit, "counterpart, first window", r.file, r.page, r.quote)
        m = LOCATION_RE.search(r.borderline_location)
        if m:
            add("targets_added_by_fls.csv", r.unit, "borderline", m.group(1), m.group(2), r.borderline_quote)
    p = pd.read_csv(OUT / "pillar3_read.csv", keep_default_na=False)
    for r in p.itertuples():
        for use, q, loc in (("Pillar 3", r.quote_pillar3, r.quote_location),
                            ("Pillar 3, borderline", r.borderline_quote, r.borderline_location)):
            m = LOCATION_RE.search(loc)
            if m:
                add("pillar3_read.csv", r.unit, use, m.group(1), m.group(2), q)
    e = pd.read_csv(OUT / "call_first.csv", keep_default_na=False)
    for r in e.itertuples():
        m = LOCATION_RE.search(r.report_location)
        if m:
            add("call_first.csv", r.unit, "first report with the figure", m.group(1), m.group(2), r.report_quote)
    c = pd.read_csv(OUT / "call_vs_report_cases.csv", keep_default_na=False)
    for r in c[c.bank == "UBS"].itertuples():
        m = LOCATION_RE.search(r.location_report)
        if m:
            add("call_vs_report_cases.csv", r.case, "call against report", m.group(1), m.group(2), r.quote_report)
    q = pd.read_csv(OUT / "quotes_2025_2026.csv", keep_default_na=False)
    for r in q.itertuples():
        add("quotes_2025_2026.csv", r.unit, r.use, r.file, r.page, r.quote)
    j = pd.read_csv(OUT / "equivalent_forms_read.csv", keep_default_na=False)
    for r in j[j.quote != ""].itertuples():
        add("equivalent_forms_read.csv", r.unit, r._8, r.file, r.page, r.quote)      # _8 is the column "class"
    for key, (file, page, quote) in CORRECTED_QUOTES.items():   # quotes of the corrected outcome table
        add("outcomes_units.csv", key.split("_")[0], "corrected outcome", file, page, quote)
    out = pd.DataFrame(rows).drop_duplicates(["unit", "use", "file", "page", "quote"]).reset_index(drop=True)
    out, _ = neutralise(out.to_csv(index=False))
    (OUT / "quotes_all.csv").write_text(out, encoding="utf-8")
    return len(rows)


def manifest(report_folders):
    """One row per UBS report used: hashes of the local file, and the source where one is recorded."""
    m = pd.read_csv(OUT.parent / "call_only_targets" / "_manifest_source.csv", keep_default_na=False)
    known = m.set_index("file")
    files = {}
    for folder in report_folders:
        for p in sorted(Path(folder).glob("UBS_*.htm")):
            files[p.name] = p
    rows = []
    for name, p in sorted(files.items()):
        raw = p.read_bytes()
        k = known.loc[name] if name in known.index else None
        rows.append({"file": name, "sha256": rc.sha256_bytes(raw), "sha256_normalized": rc.normalized_sha256(raw),
                     "bytes": len(raw), "source_url": "" if k is None else k.source_url,
                     "accession": "" if k is None else k.accession,
                     "retrieved": "" if k is None else k.download_date,
                     "publication_date": "" if k is None else k.publication_date})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "reports_manifest.csv", index=False)
    out[out.source_url != ""][["file", "source_url", "accession", "retrieved", "sha256_normalized"]].to_csv(
        OUT / "report_sources.csv", index=False)
    return out


def main():
    source, folders = SOURCE, REPORT_FOLDERS
    OUT.mkdir(parents=True, exist_ok=True)
    log = copy_files(source)
    text, _ = neutralise((source / "phase3h" / "manifest.csv").read_text(encoding="utf-8"))
    (OUT / "_manifest_source.csv").write_text(text, encoding="utf-8")
    t = targets()
    n_quotes = quotes()
    m = manifest(folders)
    (OUT / "_manifest_source.csv").unlink()
    derived = ["targets_39.csv", "quotes_all.csv", "reports_manifest.csv", "report_sources.csv"]
    for name in derived:
        log.append({"source_file": "derived by the build script", "source_sha256": "", "target_file": name,
                    "target_sha256": sha256(OUT / name), "changes": "derived"})
    pd.DataFrame(log).to_csv(OUT / "build_log.csv", index=False)
    names = sorted(p.name for p in OUT.iterdir() if p.is_file() and p.name != "SHA256SUMS")
    (OUT / "SHA256SUMS").write_text("".join(f"{sha256(OUT / n)}  {n}\n" for n in names))
    print(t.report_status.value_counts().to_dict(), "| quotes:", n_quotes,
          "| reports in manifest:", len(m), "| files:", len(names))


if __name__ == "__main__":
    main()
