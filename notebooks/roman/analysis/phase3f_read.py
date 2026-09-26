"""Phase 3f: reading result for the six call-only figures in the Pillar 3 reports, quotes verified.

Run from the repository root after phase3f_pillar3.py: python notebooks/roman/analysis/phase3f_read.py
Writes pillar3_read.csv to notebooks/roman/data/phase3f/. The classes were set by reading every hit with the figure
and every forward-looking hit with a phrase (hits.csv). Borderline sentences are quoted and verified like A and B
quotes, but do not change the class.
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3f"

P7 = ("UBS_2023-Q4_pillar3.htm", 7, "The core business-led reductions in RWA, coupled with the run-down of positions in "
      "Non-core and Legacy during 2024 and 2025, are expected to more than offset the effects of revised Basel III standards")
P70 = ("UBS_2023-Q4_pillar3.htm", 70, "We plan to exit the exposures in Non-core and Legacy in near-to-mid term")

# unit: (class in Pillar 3, quote or None, comment); for class B the quote is the counterpart, for C a borderline case
R = {
    "T16": ("B", P7, "B since Roman's decision of 2026-09-24 under the consistency rule: the Group-RWA sentence on the "
                     "NCL run-down in 2024 and 2025 is forward-looking on the same run-down, without a figure. Hits with "
                     "the figure are actual EAD and LRD amounts; operational risk RWA appears only as quarterly movements "
                     "of phase-in RWA. Until 2026-09-24 C."),
    "T25": ("B", P70, "B since Roman's decision of 2026-09-24 under the consistency rule: the sentence on exiting the NCL "
                      "securitization exposures is forward-looking on the same run-down (another scope), without a "
                      "figure. The hits with 'USD 6.0bn' are an actual capital return and an actual RWA decrease. Until "
                      "2026-09-24 C with this sentence as borderline case."),
    "T27": ("B", P7, "B since the consistency rule of 2026-09-24: the Group-RWA sentence on the NCL run-down in 2024 and "
                     "2025 (the same sentence that makes T27 B in phase 3d) is forward-looking on the same run-down, "
                     "without a figure. NCL RWA otherwise appear only as actual values. Until 2026-09-24 C with this "
                     "sentence as borderline case."),
    "T32": ("C", None, "The 'Swiss SRB going and gone concern requirements' tables give the required going concern "
                       "capital as of each quarter end, i.e. actual requirements; no phase-in to 16.7% and no 180 "
                       "basis points."),
    "T33": ("C", None, "AT1 appears as DCCP amounts, instrument tables and actual changes in tier 1 capital; no issuance "
                       "plan. 'USD 2bn' hits are bail-in debt issued and a share repurchase programme."),
    "T68": ("C", None, "Only the 2024-Q4 report is in the window; TLAC appears as actual balances and resolution "
                       "definitions, with no HoldCo target."),
}


# Roman's check (2026-09-24): his search script on the five files of check_units.json, output filtered on
# forward-looking words (expect, plan to, we plan, aim, target, by the end of, intend, will be, ambition);
# evidence in data/phase3f/roman_check/
CHECK = "Roman 2026-09-24 (forward-filtered check): C confirmed."
CHECKED = {
    "T16": CHECK + " Roman 2026-09-24, later: B under the consistency rule, with the sentence on p. 7 (no figure).",
    "T25": CHECK + " Roman 2026-09-24, later: B under the consistency rule, with the sentence on p. 70 (no figure). At the first check: 'We plan to exit the exposures in Non-core and Legacy in near-to-mid term' (2023-Q4, p. 70) concerns securitizations only, no figure, no counterpart.",
    "T27": "Roman 2026-09-24 (forward-filtered check): C confirmed at first; later the same day B under the consistency rule, with the sentence on p. 7." + " Group-RWA sentence on the NCL run-down in 2024 and 2025 (2023-Q4, p. 7) is the same borderline case as T27 in phase 3d, no counterpart; the Basel III estimate of USD 25bn (of which 10bn in NCL, 2023-Q4) and the 'low single-digit percentage increases' (2024-Q4) concern T17.",
    "T32": CHECK,
    "T33": CHECK + " AT1 issued in the second half of 2024 (USD 1.6bn) is an actual value, not an issuance plan.",
    "T68": CHECK,
}
RECHECK = ("Roman, recheck 2026-09-26 (phase 3h tool, all hits shown, filtered on forward-looking words, hits pre-sorted by machine, borderline cases read by Roman; data/phase3h/roman_check/recheck_2026-09-26/): no figure of the six units in any Pillar 3 report; forward-looking without a figure only the NCL sentences in 2023-Q4 (p. 7 run-down in 2024 and 2025, p. 70 exit from NCL securitization exposures) and 2024-Q4 (p. 69 'in Non-core and Legacy, where we continue to exit our remaining exposures'). Classes unchanged.")
CHECKED = {u: f"{c} {RECHECK}" for u, c in CHECKED.items()}


def norm(t):
    return re.sub(r"\s+", " ", str(t)).strip()


def main():
    pages = pd.read_csv(OUT / "pillar3_pages.csv", keep_default_na=False).set_index(["file", "page"])
    d3 = pd.read_csv(DATA / "phase3d" / "counterparts_read.csv", keep_default_na=False).set_index("unit")
    terms = pd.read_csv(DATA / "phase3d" / "search_terms.csv")
    hits = pd.read_csv(OUT / "hits.csv", keep_default_na=False)
    rows = []
    for unit, (cls, q, comment) in R.items():
        row = dict(unit=unit, call_figure=d3.loc[unit, "figure_call"], class_phase3d_w1=d3.loc[unit, "class"],
                   class_phase3d_all=d3.loc[unit, "class_all"], class_pillar3=cls,
                   pillar3_files=", ".join(sorted(hits[hits.unit == unit].file.unique())),
                   hits=int((hits.unit == unit).sum()), hits_with_figure=int(((hits.unit == unit) & (hits.g3 != "")).sum()),
                   quote_pillar3="", quote_location="", borderline_quote="", borderline_location="", comment=comment,
                   search_terms=" | ".join(f"[{t.group}] {t.term}" for t in terms[(terms.unit == unit)
                                                                                 & (terms["round"] == 1)].itertuples()),
                   checked_by_roman=CHECKED[unit])
        if q:
            f, p, text = q
            assert norm(text) in norm(pages.loc[(f, p), "text"]), (unit, "quote not found")
            if cls == "B":
                row.update(quote_pillar3=text, quote_location=f"{f}, page {p}")
            else:
                row.update(borderline_quote=text, borderline_location=f"{f}, page {p}")
        assert (cls == "B") == bool(row["quote_pillar3"]), (unit, "B needs a quote")
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "pillar3_read.csv", index=False)
    print(out[["unit", "class_phase3d_w1", "class_pillar3", "hits", "hits_with_figure", "borderline_location"]].to_string(index=False))


if __name__ == "__main__":
    main()
