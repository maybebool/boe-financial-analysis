"""Phase 3h, step 4: reading result for (a) and (b), every quote verified against the exported page text.

Run from the repository root after phase3h_search.py: python notebooks/roman/analysis/phase3h_read.py
The classes and statuses below were set by reading hits_a.csv and hits_b.csv (plan: two passes for (a); for (b) first
the hits with a figure or outcome word, then the sentence giving the actual value). Writes classes_a.csv (one class per
unit and report), outcomes_b.csv (one status per unit and report), units_3h.csv (one row per unit) and quotes.csv to
notebooks/roman/data/phase3h/. The script refuses to write if a quote is not found on its page.
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
import report_text as rt  # noqa: E402
from phase3h_search import report_label  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3h"
UNITS = ["T16", "T25", "T27", "T30", "T32", "T33", "T68", "F11", "F12", "F22"]
MAIN_FINDING = {"T16", "T25", "T27", "T32", "T33", "T68", "F11", "F12", "F22"}  # T30 is reported separately
DEADLINE = {"T16": "2026-12-31", "T25": "2026-12-31", "T27": "2024-12-31", "T30": "2026-12-31",
            "T32": "2030-01-01", "T33": "2024-12-31", "T68": "2025-12-31", "F11": "2030-01-01",
            "F12": "2026-12-31", "F22": "going forward"}
Q = lambda f, p, t: (f, p, t)  # noqa: E731

# ---- (a): forward-looking sentences on the same commitment or reduction (consistency rule of 2026-09-24)
NCL_Q1 = Q("UBS_2025-Q1_report.htm", 7, "We now aim for Non-core and Legacy’s credit and market risk RWA to be below USD 8bn by the end of 2025")
NCL_Q2 = Q("UBS_2025-Q2_report.htm", 7, "We still aim for Non-core and Legacy’s credit and market risk RWA to be below USD 8bn by the end of 2025")
NCL_P3 = Q("UBS_2025-Q2_pillar3.htm", 35, "in Non-core and Legacy, where it continues to exit its remaining exposures")
NCL_Q3 = Q("UBS_2025-Q3_report.htm", 7, "we are well positioned to meet our ambition of around USD 4bn by the end of 2026")
NCL_Q4 = Q("UBS_2025-Q4_report.htm", 7, "our ambition is to reduce this further, to around USD 4bn by the end of 2026")
NCL_AR = Q("UBS_2025_annual_report.htm", 39, "we are well positioned to meet our ambition of around USD 4bn by the end of 2026")
NCL = [NCL_Q1, NCL_Q2, NCL_P3, NCL_Q3, NCL_Q4, NCL_AR]
PHASE_IN = [
    Q("UBS_2025-Q1_report.htm", 40, "The phase-in of the increased capital requirements will commence from the end of 2025 and will be completed by the beginning of 2030, at the latest."),
    Q("UBS_2025-Q2_report.htm", 45, "The phase-in of the increased capital requirements will commence from 1 January 2026 and will be completed by the beginning of 2030, at the latest."),
    Q("UBS_2025-Q3_report.htm", 8, "The phase-in of the increased capital requirements relating to the increased LRD and higher market share will commence on 1 January 2026 and will be completed by the beginning of 2030, at the latest."),
    Q("UBS_2025-Q3_pillar3.htm", 7, "The phase-in of the increased capital requirements relating to the increased LRD and higher market share will commence on 1 January 2026 and will be completed by the beginning of 2030, at the latest."),
    Q("UBS_2025-Q4_report.htm", 40, "The phase-in will be completed by the beginning of 2030."),
    Q("UBS_2025-Q4_pillar3.htm", 7, "The phase-in of the capital requirements relating to the increases in LRD and market share commenced on 1 January 2026 and will be completed by 1 January 2030."),
    Q("UBS_2025_annual_report.htm", 156, "The phase-in of the increased capital requirements commenced on 1 January 2026 and will be completed by 1 January 2030."),
    Q("UBS_2026-Q1_report.htm", 40, "The phase-in of the increased capital requirements commenced on 1 January 2026 and will be completed by 1 January 2030."),
    Q("UBS_2026-Q2_report.htm", 44, "we currently estimate that this will add around USD 6bn to the Group’s tier 1 capital requirement over the phase-in period, which commenced on 1 January 2026 and will be completed by 1 January 2030"),
]
INTEGRATION = [
    Q("UBS_2025-Q4_report.htm", 7, "We expect to have incurred cumulative integration-related expenses of around USD 15bn at the end of 2026"),
    Q("UBS_2026-Q1_report.htm", 7, "We expect to have incurred cumulative integration-related expenses of around USD 15bn at the end of 2026"),
    Q("UBS_2026-Q2_report.htm", 7, "we expect to have incurred around USD 15bn by the end of this year"),
]
# unit: (B quotes, comment)
A = {
    "T16": (NCL, "No sentence on NCL operational risk RWA; B through the NCL run-down sentences (credit and market risk "
                 "RWA ambitions, exit of securitization exposures), as the consistency rule treats the same run-down with "
                 "another scope. Found through the terms of T25 and T27."),
    "T25": (NCL, "No sentence on NCL capital release; B through the NCL run-down sentences, as for T16."),
    "T27": (NCL, "Same metric (NCL credit and market risk RWA) with new, lower figures: below USD 8bn by end-2025, "
                 "around USD 4bn by end-2026. The 2026 reports state these as achieved (backward-looking, class C)."),
    "T30": (INTEGRATION, "Revised total of around USD 15bn from 2025-Q4 (another figure). The 2025-Q1 and 2025-Q2 "
                         "sentences on USD 1.1bn expected in the next quarter are quarterly guidance, another commitment. "
                         "Found with the phase 3d phrase 'integration-related expenses'; the (b) terms add no class."),
    "T32": (PHASE_IN, "Forward-looking on the phase-in of the higher requirements from 2026 to 2030, without the 16.7% or "
                      "180 basis points; from 2025-Q3 the USD figure of the progressive requirements is given (USD 6bn, "
                      "down from USD 9bn). Found through the (b) term 'phase-in' and the F12 hits."),
    "T33": ([], "AT1 appears as actual issuances and calls, tables, DCCP awards and the glossary; no issuance plan."),
    "T68": ([], "'HoldCo' does not occur; TLAC appears as actual amounts and definitions."),
    "F11": ([], "The 18% hits are the RoCET1 ambition for 2028 and the CET1 ratio of around 18.5% under the proposed "
                "Swiss rules; the going concern capital ratio appears only as actual values."),
    "F12": ([], "LRD appears as actual values, FX sensitivities and capital add-ons. Borderline: the NCL run-down "
                "sentences concern RWA, not LRD, so they are not counted for the Group LRD reduction (unlike the NCL "
                "priority 'Reduce RWA and LRD' of the 2023 and 2024 annual reports, which no longer appears)."),
    "F22": ([], "LCR appears only as actual quarterly averages, definitions and references."),
}

# ---- (b): status per report. Default for reports not listed: "no longer mentioned".
# Per report: status, and the quote that states the outcome or actual value (or None).
ACT = {
    "T16": Q("UBS_2026-Q2_report.htm", 36, "Risk-weighted assets decreased by USD 0.3bn to USD 27.7bn"),
    "T25": None,
    "T27_q3": Q("UBS_2025-Q3_report.htm", 7, "We have already achieved our 2025 ambition to reduce credit and market risk RWA to below USD 8bn"),
    "T27_q4": Q("UBS_2025-Q4_report.htm", 7, "We have achieved a reduction of credit and market risk RWA to around USD 5bn"),
    "T27_ar": Q("UBS_2025_annual_report.htm", 39, "Having already achieved a reduction of credit and market risk RWA to around USD 5bn"),
    "T27_26q1": Q("UBS_2026-Q1_report.htm", 7, "We have achieved a reduction of credit and market risk RWA to USD 4bn in line with our year-end 2026 ambition."),
    "T27_26q2": Q("UBS_2026-Q2_report.htm", 7, "the reduction of credit and market risk RWA to USD 4bn in line with the year-end 2026 ambition had already been achieved at the end of the first quarter of 2026"),
    "T30": Q("UBS_2026-Q2_report.htm", 7, "Cumulative integration-related expenses incurred by the end of June 2026 amounted to USD 14.2bn"),
    "T32_rev": Q("UBS_2025-Q3_report.htm", 8, "The estimated effect for the progressive requirements for LRD and market share decreased to USD 6bn, from USD 9bn, following FINMA’s confirmation about the requirements that will apply to UBS."),
    "T32_act": Q("UBS_2025_annual_report.htm", 157, "of the total going concern capital requirement of 14.99% of RWA"),
    "T33": Q("UBS_2024_annual_report.htm", 165, "mainly reflecting new issuances of AT1 capital instruments of USD 3.5 bn partly offset by a call of USD 1.0 bn equivalent of AT1 capital instruments"),
    "F11": Q("UBS_2026-Q2_report.htm", 46, "Our going concern capital ratio decreased to 19.0% from 19.4%"),
    "F12": Q("UBS_2026-Q2_report.htm", 18, "The leverage ratio denominator (the LRD) decreased by USD 3.7bn to USD 1,649.8bn"),
    "F12_base": Q("UBS_2024_annual_report.htm", 169, "During 2024, the LRD decreased by USD 175.9bn to USD 1,519.5bn"),
    "F22": {
        "UBS_2025-Q1_report.htm": Q("UBS_2025-Q1_report.htm", 49, "decreased 7.4 percentage points to 181.0%"),
        "UBS_2025-Q2_report.htm": Q("UBS_2025-Q2_report.htm", 53, "increased 1.3 percentage points to 182.3%"),
        "UBS_2025-Q3_report.htm": Q("UBS_2025-Q3_report.htm", 55, "remained broadly unchanged at 182.1%"),
        "UBS_2025-Q4_report.htm": Q("UBS_2025-Q4_report.htm", 49, "remained broadly unchanged at 182.6%"),
        "UBS_2026-Q1_report.htm": Q("UBS_2026-Q1_report.htm", 48, "decreased 4.8 percentage points to 177.8%"),
        "UBS_2026-Q2_report.htm": Q("UBS_2026-Q2_report.htm", 52, "was largely unchanged at 177.3%"),
    },
}
NOTE_T25 = Q("UBS_2024_annual_report.htm", 26, "released over USD 6 billion of capital to the Group")

STATUS = {  # unit: {file: (status, quote or None)}; unlisted reports: "no longer mentioned"
    "T16": {},
    "T25": {},
    "T27": {"UBS_2024-Q4_report.htm": ("not determinable from these reports", None),
            "UBS_2024_annual_report.htm": ("not determinable from these reports", None),
            "UBS_2025-Q1_report.htm": ("revised", NCL_Q1), "UBS_2025-Q2_report.htm": ("revised", NCL_Q2),
            "UBS_2025-Q3_report.htm": ("achieved", ACT["T27_q3"]), "UBS_2025-Q4_report.htm": ("achieved", ACT["T27_q4"]),
            "UBS_2025_annual_report.htm": ("achieved", ACT["T27_ar"]),
            "UBS_2026-Q1_report.htm": ("achieved", ACT["T27_26q1"]), "UBS_2026-Q2_report.htm": ("achieved", ACT["T27_26q2"])},
    "T30": {"UBS_2025-Q4_report.htm": ("revised", INTEGRATION[0]), "UBS_2026-Q1_report.htm": ("revised", INTEGRATION[1]),
            "UBS_2026-Q2_report.htm": ("revised", ACT["T30"])},
    "T32": {"UBS_2025-Q1_report.htm": ("open", PHASE_IN[0]), "UBS_2025-Q2_report.htm": ("open", PHASE_IN[1]),
            "UBS_2025-Q3_report.htm": ("revised", ACT["T32_rev"]), "UBS_2025-Q3_pillar3.htm": ("revised", PHASE_IN[3]),
            "UBS_2025-Q4_report.htm": ("revised", PHASE_IN[4]), "UBS_2025-Q4_pillar3.htm": ("revised", PHASE_IN[5]),
            "UBS_2025_annual_report.htm": ("revised", PHASE_IN[6]), "UBS_2026-Q1_report.htm": ("revised", PHASE_IN[7]),
            "UBS_2026-Q2_report.htm": ("revised", PHASE_IN[8])},
    "T33": {"UBS_2024-Q4_report.htm": ("not determinable from these reports", None),
            "UBS_2024_annual_report.htm": ("missed", ACT["T33"])},
    "T68": {},
    "F11": {},
    "F12": {},
    "F22": {f: ("achieved", q) for f, q in ACT["F22"].items()},
}
FINAL = {  # unit: (final status, actual value as reported, quote, comment)
    "T16": ("no longer mentioned", "NCL operational risk RWA not reported; total NCL RWA USD 27.7bn at 30.6.2026 "
            "(including operational risk)", ACT["T16"],
            "No report mentions the NCL operational risk RWA target; the reports give NCL RWA only in total and credit "
            "and market risk RWA (USD 4bn), so the operational risk part is not reported."),
    "T25": ("no longer mentioned", "not reported in the 2025 and 2026 reports", None,
            "The 2024 annual report, read here only for T27 and T33, states that NCL 'released over USD 6 billion of "
            "capital to the Group' (p. 26), which would meet the figure two years early; outside the reports of (b) for T25."),
    "T27": ("achieved", "NCL credit and market risk RWA around USD 5bn at 31.12.2025, USD 4bn at 31.3.2026",
            ACT["T27_26q2"],
            "The value at the deadline (31.12.2024) is not reported; the target was replaced by lower ambitions "
            "(below USD 8bn by end-2025, around USD 4bn by end-2026), which were met and are below the call figure."),
    "T30": ("revised", "cumulative integration-related expenses USD 14.2bn at 30.6.2026 (constant FX)", ACT["T30"],
            "Around 13bn in the call of 2023-Q4, 14bn in the call of 2024-Q4, around 15bn in the reports from 2025-Q4."),
    "T32": ("revised", "total going concern capital requirement 14.99% of RWA at 31.12.2025", ACT["T32_act"],
            "The progressive requirements are phased in from 1 January 2026 to 1 January 2030; their estimated effect "
            "decreased to USD 6bn from USD 9bn after FINMA's confirmation (2025-Q3). The 16.7% is not restated."),
    "T33": ("missed", "new AT1 issuances of USD 3.5bn in 2024 (call: up to USD 2bn)", ACT["T33"],
            "The issuance exceeded the upper bound given in the call; UBS issued further AT1 in 2025 (USD 3.0bn in 1Q, "
            "USD 2.8bn in 3Q) and 2026."),
    "T68": ("no longer mentioned", "HoldCo not reported under this name", None,
            "The reports give TLAC and TLAC-eligible senior unsecured debt movements, not a HoldCo total."),
    "F11": ("no longer mentioned", "going concern capital ratio 19.0% at 30.6.2026 (18.2% at 31.3.2025)", ACT["F11"],
            "The ratio already exceeds around 18%, before the phase-in ends in 2030; the target itself is not restated."),
    "F12": ("no longer mentioned", "Group LRD USD 1,649.8bn at 30.6.2026 against USD 1,695.4bn at 31.12.2023 "
            "(current FX)", ACT["F12"],
            "The reduction at current FX is about USD 46bn; the call figure is at constant FX, and the 2025 LRD "
            "includes USD 110bn of currency effects, so the comparison is approximate."),
    "F22": ("achieved", "quarterly average LCR 177.3% in 2Q26 (all quarters 2025 and 2026 between 177.3% and 182.6%)",
            ACT["F22"]["UBS_2026-Q2_report.htm"],
            "The commitment itself is not restated; every reported quarterly average is below 188%."),
}


def norm(t):
    return re.sub(r"\s+", " ", str(t)).strip()


def main():
    manifest = pd.read_csv(OUT / "manifest.csv", keep_default_na=False)
    pages = {r.file: dict(rt.parse_export((OUT / "text" / f"{Path(r.file).stem}.txt").read_text()))
             for r in manifest.itertuples()}
    pub = dict(zip(manifest.file, manifest.publication_date))
    new = list(manifest[manifest.folder == "reports_2025_2026"].file)
    old = list(manifest[manifest.folder == "reports"].file)
    quotes = []

    def check(q, unit, use):
        f, p, text = q
        assert norm(text) in norm(pages[f][p]), (unit, f, p, "quote not found")
        quotes.append(dict(unit=unit, use=use, file=f, report=report_label(f), page=p, quote=text))

    rows_a = []
    for u in UNITS:
        bq, _ = A[u]
        by_file = {}
        for q in bq:
            check(q, u, "a: B")
            by_file.setdefault(q[0], q)
        for f in new:
            rows_a.append(dict(unit=u, file=f, report=report_label(f), publication_date=pub[f],
                               **{"class": "B" if f in by_file else "C"},
                               quote=by_file[f][2] if f in by_file else "", page=by_file[f][1] if f in by_file else "",
                               figure_named_retrospectively=False))
    ca = pd.DataFrame(rows_a)
    ca.to_csv(OUT / "classes_a.csv", index=False)

    rows_b = []
    for u in UNITS:
        files = new + (old if u in ("T27", "T33") else [])
        for f in files:
            status, q = STATUS[u].get(f, ("no longer mentioned", None))
            if q:
                check(q, u, f"b: {status}")
            rows_b.append(dict(unit=u, file=f, report=report_label(f), publication_date=pub[f], status=status,
                               quote=q[2] if q else "", page=q[1] if q else ""))
    ob = pd.DataFrame(rows_b).sort_values(["unit", "publication_date", "file"])
    ob.to_csv(OUT / "outcomes_b.csv", index=False)

    rows = []
    for u in UNITS:
        a = ca[ca.unit == u].sort_values("publication_date")
        ab = a[a["class"].isin(["A", "B"])]
        seq = ob[(ob.unit == u) & ob.file.str.contains("_report")]
        mentioned = ob[(ob.unit == u) & ~ob.status.isin(["no longer mentioned", "not determinable from these reports"])
                       & (ob.unit != "F22")]
        final, actual, q, comment = FINAL[u]
        if q:
            check(q, u, "b: actual value")
        rows.append(dict(unit=u, main_finding=u in MAIN_FINDING, deadline=DEADLINE[u],
                         class_a_overall="A" if (a["class"] == "A").any() else "B" if len(ab) else "C",
                         first_A="", first_A_or_B=f"{ab.iloc[0].report} ({ab.iloc[0].publication_date})" if len(ab) else "",
                         first_retrospective="", comment_a=A[u][1], final_status=final,
                         status_sequence=" > ".join(f"{r.report}: {r.status}" for r in seq.itertuples()),
                         last_mentioned_in=(mentioned.sort_values("publication_date").iloc[-1].report
                                            if len(mentioned) else ""),
                         actual_value=actual, actual_quote=q[2] if q else "",
                         actual_location=f"{q[0]}, page {q[1]}" if q else "", comment_b=comment))
    check(NOTE_T25, "T25", "note (2024 annual report)")
    units = pd.DataFrame(rows)
    # plan: "open" only with a deadline after 30 June 2026 and a mention in a 2026 report
    for r in ob[ob.status == "open"].itertuples():
        assert DEADLINE[r.unit] > "2026-06-30"
    units.to_csv(OUT / "units_3h.csv", index=False)
    pd.DataFrame(quotes).drop_duplicates().to_csv(OUT / "quotes.csv", index=False)
    print(units[["unit", "class_a_overall", "first_A_or_B", "final_status", "last_mentioned_in"]].to_string(index=False))


if __name__ == "__main__":
    main()
