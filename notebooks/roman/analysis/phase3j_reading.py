"""Phase 3j: the reading result, one row per unit and distinct passage (complete reading).

Run from the repository root, after `phase3j_read.py hits`: python notebooks/roman/analysis/phase3j_reading.py
Reads judgments_full.csv, my judgment for each of the 768 distinct passages, each read in full, and writes
reading_3j.csv, the input of `phase3j_read.py classify`, and reading_comparison.csv, the comparison with the first
reading (reading_3j_first.csv: sentence-level reading with a wording rule for the classes that do not count).

A passage that belongs to several units was judged once; the judgment was made with all its units in view. The
quotes of the passages that state the target of a unit, with or without a figure, are listed in QUOTES and are
verified against the page text by `phase3j_read.py classify`.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3j"
COUNTED = ("same target, same unit", "same target, another unit", "same target, another figure")
NO_FIGURE = "same target, no figure"

# (unit, text in the passage) -> (quote, conversion, comment)
QUOTES = [
    ("T30", "expected to be broadly offset by accretion-to-par effects of approximately USD 12bn",
     "Cumulative integration-related expenses are expected to be broadly offset by accretion-to-par effects of "
     "approximately USD 12bn",
     "12 / 13 = 0.92, inside the tolerance of 10%; indirect form: the total is equated with the accretion effects",
     "Known since phase 3b as the indirect order of magnitude in the 2023-Q2 report; published before the call "
     "figure of around 13bn (2023-Q4) and outside the tolerance for the raised figure of around 14bn (12 / 14 = 0.86)."),
    ("T25", "freeing up capital for the UBS Group", "freeing up capital for the UBS Group", "",
     "The NCL key priority: the capital release as an aim, without a figure (class B counterpart of phase 3d)."),
    ("T25", "We plan to fund this growth organically from the capital released from the unwinding of the",
     "We plan to fund this growth organically from the capital released from the unwinding of the", "",
     "The capital released by the NCL unwinding as a plan, without a figure (the phase 3d counterpart of T25)."),
    ("T27", "we expect exposures in Non-core and Legacy to reduce as a result of maturities and active unwinding",
     "we expect exposures in Non-core and Legacy to reduce as a result of maturities and active unwinding of positions",
     "", "Outlook of the credit risk RWA section: the reduction of NCL exposures as an expectation, without a "
         "figure; published before the call. T27 was already mentioned without a figure."),
    ("T27", "freeing up capital for the UBS Group", "Reduce RWA and LRD, freeing up capital for the UBS Group", "",
     "The NCL key priority: the RWA reduction as an aim, without a figure for credit and market risk RWA at the "
     "end of 2024; the target of around 5% of Group RWA in the same passage is for the end of 2026."),
    ("T27", "We will continue to actively wind down Non-core and Legacy",
     "We will continue to actively wind down Non-core and Legacy", "",
     "The continued wind-down as a plan, without a figure; published after the deadline of T27."),
    ("F12", "We intend to actively reduce the assets of the NCL business division",
     "We intend to actively reduce the assets of the NCL business division", "",
     "The NCL part of the LRD reduction as an intention, without a figure; published before the call."),
    ("F12", "freeing up capital for the UBS Group", "Reduce RWA and LRD, freeing up capital for the UBS Group", "",
     "The NCL key priority: the LRD reduction as an aim, without a figure and for NCL only (class B counterpart "
     "of phase 3g)."),
    ("F12", "We will continue to actively wind down Non-core and Legacy",
     "We will continue to actively wind down Non-core and Legacy", "",
     "The continued wind-down of NCL as a plan, without a figure for the LRD."),
]


def main():
    p = pd.read_csv(OUT / "passages.csv", keep_default_na=False).drop_duplicates(["unit", "text_id"])
    j = pd.read_csv(OUT / "judgments_full.csv", keep_default_na=False)
    if len(j) != 768 or not j.text_id.is_unique or set(j.text_id) != set(p.text_id):
        raise SystemExit("judgments_full.csv does not cover the 768 distinct passages exactly once")
    cls = dict(zip(j.text_id, j["class"]))
    rows = []
    for r in p.itertuples():
        c = cls[r.text_id]
        row = {"unit": r.unit, "text_id": r.text_id, "class": c,
               "forward_looking": "yes" if c.startswith("same target") or c == "other forward-looking target" else "no",
               "quote": "", "conversion": "", "comment": ""}
        if c in COUNTED or c == NO_FIGURE:
            hit = [q for q in QUOTES if q[0] == r.unit and q[1] in r.text]
            if not hit:
                raise SystemExit(f"no quote recorded for {r.unit} {r.text_id}")
            row.update({"quote": hit[0][2], "conversion": hit[0][3], "comment": hit[0][4]})
        rows.append(row)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "reading_3j.csv", index=False)

    first = pd.read_csv(OUT / "reading_3j_first.csv", keep_default_na=False)
    m = first[["unit", "text_id", "class"]].merge(d[["unit", "text_id", "class"]], on=["unit", "text_id"],
                                                 suffixes=("_first", "_full"), validate="one_to_one")
    m["changed"] = m.class_first != m.class_full
    m.to_csv(OUT / "reading_comparison.csv", index=False)
    print(d.groupby(["unit", "class"]).size().unstack(fill_value=0).to_string())
    print("\nclass in the first reading against the complete reading:")
    print(pd.crosstab(m.class_first, m.class_full).to_string())
    print("changed:", int(m.changed.sum()), "of", len(m))


if __name__ == "__main__":
    main()
