"""Phase 3j, step 1: equivalent forms of the call figures and the search terms for check_terms.py.

Run from the repository root, before the search: python notebooks/roman/analysis/phase3j_terms.py
Writes forms.csv, check_units_3j.json and term_index.csv to notebooks/roman/data/phase3j/. Plan: plans/phase_3j.md.
A form is a function of the call figure x; its band is the image of 0.9x to 1.1x (tolerance of 10% on the call
figure), and every grid value in the band becomes a term that must occur near a keyword of the unit.
"""
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3j"
REPORTS = ROOT / "notebooks" / "roman" / "data" / "reports"

RWA23, RWA24, LRD23, LRD24 = 546.5, 498.5, 1695.4, 1519.5     # USD bn, 2024 annual report p. 32
CET1, GC23, AT1_23 = 0.14, 17.0, 2.5                           # calls 2023-Q4: statements 4697 and 4791
GONE24, GONE24_REPORT, AT1_24 = 98.0, 97.7, 16.4               # call 2024-Q4 statement 6559; 2024-Q4 report p. 41
NCL_OP, GROUP_OP, SPENT23, CHF = 30.0, 145.0, 4.5, 1.19        # call statements 4301, 4299, 4762; annual report p. 390

# unit -> (call figure x, keywords, [(form, calculation, kind, function of x)])
UNITS = {
    "T33": (2.0, ["AT1", "additional tier 1"], [
        ("amount", "USD 2bn", "bn", lambda x: x),
        ("amount in CHF", "2 / 1.19", "bn", lambda x: x / CHF),
        ("share of RWA", "2 / 546.5", "pct", lambda x: 100 * x / RWA23),
        ("share of RWA in basis points", "2 / 546.5", "bp", lambda x: 1e4 * x / RWA23),
        ("share of LRD", "2 / 1,695.4", "pct", lambda x: 100 * x / LRD23),
        ("share of LRD in basis points", "2 / 1,695.4", "bp", lambda x: 1e4 * x / LRD23),
        ("resulting AT1 stock", "2.5% x 546.5 + 2", "bn", lambda x: AT1_23 / 100 * RWA23 + x),
        ("resulting AT1 ratio", "2.5% + 2 / 546.5", "pct", lambda x: AT1_23 + 100 * x / RWA23)]),
    "T68_r1": (90.0, ["HoldCo", "TLAC", "total loss-absorbing", "gone concern", "senior unsecured"], [
        ("amount", "USD 90bn", "bn", lambda x: x),
        ("reduction", "98 - 90", "bn", lambda x: GONE24 - x),
        ("reduction in percent", "(98 - 90) / 98", "pct", lambda x: 100 * (GONE24 - x) / GONE24),
        ("share of RWA", "90 / 498.5", "pct", lambda x: 100 * x / RWA24),
        ("share of LRD", "90 / 1,519.5", "pct", lambda x: 100 * x / LRD24)]),
    "T68_r2": (90.0, ["holding company", "funding plan", "AT1", "additional tier 1"], [
        ("amount", "USD 90bn", "bn", lambda x: x),
        ("reduction", "114.0 - 90", "bn", lambda x: GONE24_REPORT + AT1_24 - x),
        ("reduction in percent", "(114.0 - 90) / 114.0", "pct",
         lambda x: 100 * (GONE24_REPORT + AT1_24 - x) / (GONE24_REPORT + AT1_24)),
        ("gone concern part", "90 - 16.4", "bn", lambda x: x - AT1_24),
        ("gone concern part, share of RWA", "(90 - 16.4) / 498.5", "pct", lambda x: 100 * (x - AT1_24) / RWA24),
        ("gone concern part, share of LRD", "(90 - 16.4) / 1,519.5", "pct", lambda x: 100 * (x - AT1_24) / LRD24)]),
    "F11": (18.0, ["going concern", "AT1", "additional tier 1"], [
        ("ratio", "18%", "pct", lambda x: x),
        ("increase in basis points", "18.0 - 17.0", "bp", lambda x: 100 * (x - GC23)),
        ("AT1 ratio", "18 - 14", "pct", lambda x: x - 100 * CET1),
        ("going concern capital", "18% x 546.5", "bn", lambda x: x / 100 * RWA23),
        ("AT1 capital", "4% x 546.5", "bn", lambda x: (x / 100 - CET1) * RWA23),
        ("AT1 increase", "1.5% x 546.5", "bn", lambda x: (x - 100 * CET1 - AT1_23) / 100 * RWA23),
        ("share of LRD", "98.4 / 1,695.4", "pct", lambda x: 100 * x / 100 * RWA23 / LRD23)]),
    "F22": (188.0, ["LCR", "liquidity coverage ratio", "HQLA", "high-quality liquid assets"], [
        ("ratio", "188%", "pct", lambda x: x)]),
    "T16": (14.0, ["operational risk"], [
        ("amount", "USD 14bn", "bn", lambda x: x),
        ("reduction", "30 - 14", "bn", lambda x: NCL_OP - x),
        ("reduction in percent", "(30 - 14) / 30", "pct", lambda x: 100 * (NCL_OP - x) / NCL_OP),
        ("share of Group operational risk RWA", "14 / 145", "pct", lambda x: 100 * x / GROUP_OP),
        ("share of Group RWA", "14 / 546.5", "pct", lambda x: 100 * x / RWA23),
        ("CET1 equivalent of the reduction", "(30 - 14) x 14%", "bn", lambda x: (NCL_OP - x) * CET1)]),
    "T25": (6.0, ["capital release", "capital released", "released capital", "freeing up capital", "free up",
                  "attributed equity"], [
        ("amount", "USD 6bn", "bn", lambda x: x),
        ("RWA equivalent at 14% CET1", "6 / 0.14", "bn", lambda x: x / CET1),
        ("effect on the CET1 ratio", "6 / 546.5", "pct", lambda x: 100 * x / RWA23),
        ("effect on the CET1 ratio in basis points", "6 / 546.5", "bp", lambda x: 1e4 * x / RWA23)]),
    "T27": (40.0, ["Non-core and Legacy", "credit and market risk"], [
        ("amount", "USD 40bn", "bn", lambda x: x),
        ("total NCL RWA", "40 + 30", "bn", lambda x: x + NCL_OP),
        ("share of Group RWA", "40 / 546.5", "pct", lambda x: 100 * x / RWA23),
        ("total NCL RWA, share of Group RWA", "70 / 546.5", "pct", lambda x: 100 * (x + NCL_OP) / RWA23),
        ("reduction from 31.12.2023", "44.0 - 40", "bn", lambda x: 44.0 - x),
        ("reduction in percent", "(44.0 - 40) / 44.0", "pct", lambda x: 100 * (44.0 - x) / 44.0)]),
    "F12": (100.0, ["LRD", "leverage ratio denominator"], [
        ("amount", "USD 100bn", "bn", lambda x: x),
        ("share", "100 / 1,695.4", "pct", lambda x: 100 * x / LRD23),
        ("resulting level", "1,695.4 - 100", "level", lambda x: LRD23 - x),
        ("capital equivalent at 5.0%", "100 x 5.0%", "bn", lambda x: x * 0.05),
        ("CET1 equivalent at 3.5%", "100 x 3.5%", "bn", lambda x: x * 0.035)]),
    "T30": (13.0, ["integration-related expenses", "costs to achieve", "integration costs"], [
        ("amount", "USD 13bn", "bn", lambda x: x),
        ("amount as raised in 2024-Q4", "USD 14bn", "bn", lambda x: x + 1),
        ("remaining at end-2023", "13 - 4.5", "bn", lambda x: x - SPENT23),
        ("ratio to gross cost saves of 13bn", "13 / 13", "pct", lambda x: 100 * x / 13.0)]),
}
# keywords of pass B that need a second word nearby (reading 2 of T68)
EXTRA_PASS_B = {"T68_r2": [("UBS Group AG", n) for n in ("issuance", "issued", "funding", "debt")]}


def num(v):
    return f"{v:.1f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))


def grid(lo, hi, kind):
    """Search strings for all grid values in the band, as fixed in the plan."""
    lo, hi = min(lo, hi), max(lo, hi)
    eps = 1e-9
    if kind == "bn":
        step = 0.5 if hi < 10 else 1.0
        vals = [v * step for v in range(math.ceil(lo / step - eps), math.floor(hi / step + eps) + 1) if v * step > 0]
        if not vals:                                           # band narrower than the grid: nearest grid value
            vals = [max(step, round((lo + hi) / 2 / step) * step)]
        out = []
        for v in vals:
            out += [f"{num(v)}bn", f"{num(v)} billion"]
            if v == int(v):
                out += [f"{int(v)}.0bn", f"{int(v)}.0 billion"]
        return out
    if kind == "pct":
        if hi >= 100:                                          # ratios above 100%: integers only
            vals = list(range(math.ceil(lo - eps), math.floor(hi + eps) + 1))
        else:
            vals = [v / 10 for v in range(math.ceil(lo * 10 - eps), math.floor(hi * 10 + eps) + 1) if v > 0]
            if not vals:
                vals = [round((lo + hi) / 2, 1)]
        out = []
        for v in vals:
            out.append(f"{num(v)}%")
            if v == int(v) and hi < 100:
                out.append(f"{int(v)}.0%")
        return out
    if kind == "bp":
        vals = [v for v in range(5 * math.ceil(lo / 5 - eps), 5 * math.floor(hi / 5 + eps) + 1, 5) if v > 0]
        if not vals:
            vals = [round((lo + hi) / 2)]
        return [s for v in vals for s in (f"{v} basis points", f"{v}bps", f"{v}bp")]
    if kind == "level":                                        # levels above 1,000bn: the integer part, any unit
        return [f"{v:,}" for v in range(math.ceil(lo - eps), math.floor(hi + eps) + 1)] + ["1.6 trillion", "1.6trn"]
    raise ValueError(kind)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(p.name for p in REPORTS.glob("UBS_*.htm"))
    assert len(files) == 16, files
    forms, index, units = [], [], {}
    for unit, (x, keywords, defs) in UNITS.items():
        terms = []
        for form, calc, kind, f in defs:
            lo, hi = sorted((f(0.9 * x), f(1.1 * x)))
            strings = grid(lo, hi, kind)
            forms.append({"unit": unit, "form": form, "calculation": calc, "kind": kind, "call_figure": x,
                          "central_value": round(f(x), 2), "band_low": round(lo, 2), "band_high": round(hi, 2),
                          "terms": " | ".join(strings)})
            for s in strings:
                for k in keywords:
                    if [s, k] not in terms:
                        terms.append([s, k])
                        index.append({"unit": unit, "search_pass": "A", "term": s, "near": k, "form": form})
        for k in keywords:
            terms.append([k, None])
            index.append({"unit": unit, "search_pass": "B", "term": k, "near": "", "form": ""})
        for k, near in EXTRA_PASS_B.get(unit, []):
            terms.append([k, near])
            index.append({"unit": unit, "search_pass": "B", "term": k, "near": near, "form": ""})
        units[unit] = {"files": files, "terms": terms}
    pd.DataFrame(forms).to_csv(OUT / "forms.csv", index=False)
    pd.DataFrame(index).to_csv(OUT / "term_index.csv", index=False)
    (OUT / "check_units_3j.json").write_text(json.dumps(units, indent=1))
    print(pd.DataFrame(index).groupby(["unit", "search_pass"]).size().unstack(fill_value=0))
    print(pd.DataFrame(forms)[["unit", "form", "central_value", "band_low", "band_high"]].to_string())


if __name__ == "__main__":
    main()
