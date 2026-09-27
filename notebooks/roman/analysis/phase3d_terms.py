"""Phase 3d, step 1: search terms per unit, written from the call sentences alone before any report search.

Run from the repository root: python notebooks/roman/analysis/phase3d_terms.py
Writes units.csv and search_terms.csv to notebooks/roman/data/phase3d/. Groups: 1 metric keywords of phase 3,
2 phrases naming the commitment (chosen from the call sentence), 3 the call figures in report formats.
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase3_extract import METRICS, quantities  # noqa: E402

PHASE3 = ROOT / "notebooks" / "roman" / "data" / "phase3"
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3d"

PHRASES = {  # unit: phrases from the call sentence (with the spelling variants reports use, e.g. "cost / income")
    "T0": ["NII ex. Markets", "net interest income"], "T1": ["Card net charge-off rate", "net charge-off rate"],
    "T7": ["expense outlook", "adjusted expense"], "T19": ["NII ex. Markets", "net interest income"],
    "T20": ["full year guidance", "net interest income"], "T21": ["adjusted expense"],
    "T22": ["Card net charge-off rate", "net charge-off rate"], "T38": ["Card loan growth", "Card loans"],
    "T45": ["Card allowance", "allowance build", "reserve build"], "T52": ["consensus", "NII ex. Markets"],
    "T57": ["NII ex. Markets", "net interest income"], "T58": ["rate cuts", "NII decrease"],
    "T59": ["Card loan growth", "Card loans"], "T60": ["adjusted expense", "expense"],
    "T61": ["Card net charge-off rate", "net charge-off rate"], "T2": ["CET1", "SCB", "GSIB", "buffer"],
    "T4": ["restructuring costs", "First Republic"], "T6": ["incremental net income", "First Republic", "accretive"],
    "T23": ["exit rate", "NII ex. Markets"], "T5": ["CET1", "first quarter 2024"],
    "T44": ["dividend", "per share"], "E766": ["bargain purchase gain", "one-time gain"],
    "T8": ["gross cost reductions", "gross expenses", "cost base"],
    "T15": ["accrete", "accretion", "pull-to-par", "purchase price allocation"],
    "T41": ["purchase price allocation", "PPA", "acquisition-related", "additional revenues"],
    "T46": ["effective tax rate"], "T49": ["sweep deposit"], "T54": ["sweep deposit"],
    "T62": ["credit loss expense", "CLE", "allowances"], "T37": ["net new assets"], "T43": ["funding costs", "funding cost"],
    "T48": ["net new assets"], "T56": ["Non-core and Legacy", "risk-weighted assets", "RWA"],
    "T66": ["pre-tax margin", "Global Wealth Management"], "T3": ["gross cost saving", "cost saving program", "standalone"],
    "T9": ["cost / income ratio", "cost/income ratio", "exit rate"], "T10": ["CET1 capital ratio", "medium term"],
    "T11": ["CET1 capital ratio", "end of the year", "pull-to-par"], "T12": ["cost saves", "gross cost", "exit rate"],
    "T13": ["cost saves", "gross cost", "exit rate"], "T14": ["natural decay", "Non-core and Legacy", "reduction"],
    "T16": ["operational risk RWA", "operational risk"],
    "T17": ["Basel III", "final Basel", "FRTB", "Fundamental Review of the Trading Book"],
    "T18": ["return on common equity tier 1", "RoCET1", "return on CET1", "cost / income ratio"],
    "T24": ["gross cost reductions", "gross cost savings"], "T25": ["capital release", "Non-core and Legacy"],
    "T26": ["net new assets", "Global Wealth Management"],
    "T27": ["credit and market risk", "risk-weighted assets", "Non-core and Legacy"],
    "T28": ["share repurchase", "buyback", "repurchase"], "T29": ["gross cost savings", "exit rate", "exit-rate saves"],
    "T30": ["integration-related expenses", "costs to achieve"],
    "T31": ["Non-core and Legacy", "operating expenses", "pre-tax loss"],
    "T32": ["going concern capital", "going-concern capital requirement"], "T33": ["AT1", "additional tier 1"],
    "T34": ["funding cost", "funding costs"], "T35": ["RWA", "risk-weighted assets", "CET1 capital"],
    "T36": ["effective tax rate", "legal entity"], "T39": ["gross cost savings", "gross cost saves"],
    "T40": ["Non-core and Legacy", "risk-weighted assets", "RWA"], "T42": ["gross cost savings", "additional exit rate"],
    "T47": ["share repurchase", "repurchase", "buyback"], "T50": ["Non-core and Legacy", "run-down", "RWA"],
    "T51": ["transaction", "RWA", "LRD"], "T53": ["cost / income ratio", "cost/income ratio"],
    "T55": ["Non-core and Legacy", "RWA"], "T63": ["net new money"], "T64": ["effective tax rate"],
    "T65": ["net new assets", "ambition"],
    "T67": ["Personal & Corporate Banking", "cost / income ratio", "return on equity"],
    "T68": ["HoldCo", "total loss-absorbing", "TLAC"],
}
MERGED = {"T6": "771"}  # event-call statement 771 restates the 500 million of thread 6 (stmt_id 850)


def figure_formats(text):
    """Report spellings of every quantity in a call sentence."""
    out = []
    for v, unit in quantities(text):
        if unit == "pct":
            s = f"{v:g}"
            out += [f"{s}%", f"{s} %", f"{s} percent"]
        elif unit == "bps":
            s = f"{v:g}"
            out += [f"{s} basis points", f"{s}bps", f"{s} bps"]
        elif unit == "amount_bn":
            if v >= 1:
                s = f"{v:g}"
                out += [f"{s}bn", f"{s} bn", f"{s} billion"]
                if "." not in s:
                    out += [f"{s}.0bn", f"{s}.0 billion"]
            else:
                s = f"{v * 1000:g}"
                out += [f"{s}m", f"{s} million", f"{v:g}bn", f"{v:g} billion"]
        else:
            out += [f"${v:g}", f"USD {v:g}", f"{v:.2f}"]
    return list(dict.fromkeys(out))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    c = pd.read_csv(PHASE3 / "candidates_threaded.csv")
    first = c.sort_values(["call_date", "position_in_call", "sentence_number"]).groupby("thread").head(1)
    units = first.assign(unit="T" + first.thread.astype(str))
    st = pd.read_csv(PHASE3 / "statements.csv").set_index("stmt_id")
    extra = st.loc[[766]].reset_index().assign(unit="E766", thread=-1, type="other", metric="other")
    units = pd.concat([units, extra[units.columns.intersection(extra.columns)]], ignore_index=True)
    units["merged_with"] = units.unit.map(lambda u: f"stmt_id {MERGED[u]}" if u in MERGED else "")
    units["call_sentence"] = units.text.where(~units.unit.isin(MERGED), units.text + " || " +
                                              units.unit.map(lambda u: st.loc[int(MERGED[u]), "text"] if u in MERGED else ""))
    keep = ["unit", "thread", "bank", "type", "metric", "quarter", "call_type", "call_date", "stmt_id", "call_sentence",
            "merged_with"]
    units[keep].to_csv(OUT / "units.csv", index=False)
    kw = {g: p for g, _, p in METRICS}
    rows = []
    for _, u in units.iterrows():
        assert u.unit in PHRASES, u.unit
        if u.metric != "other":
            rows.append(dict(unit=u.unit, group=1, term=kw[u.metric], regex=True, round=1))
        rows += [dict(unit=u.unit, group=2, term=p, regex=False, round=1) for p in PHRASES[u.unit]]
        rows += [dict(unit=u.unit, group=3, term=f, regex=False, round=1) for f in figure_formats(u.call_sentence)]
    pd.DataFrame(rows).to_csv(OUT / "search_terms.csv", index=False)
    print(len(units), "units;", len(rows), "terms")


if __name__ == "__main__":
    main()
