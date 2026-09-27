"""Phase 3d, step 3: the reading result per unit, with every quote verified against the report page.

Run from the repository root after phase3d_search.py: python notebooks/roman/analysis/phase3d_read.py
The classifications below were made by reading the hits in hits.csv (both windows). The script refuses to write
counterparts_read.csv if a quote is not found verbatim (whitespace normalised) on the stated page, or if a W1
quote comes from a report outside the unit's window W1.
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase3d_search import w1  # noqa: E402

PHASE3B = ROOT / "notebooks" / "roman" / "data" / "phase3b"
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3d"
ORDER = ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4", "2023 annual report", "2024-Q1", "2024-Q2", "2024-Q3",
         "2024-Q4", "2024 annual report"]
Q = lambda f, p, t: (f, p, t)  # noqa: E731

# report quotes used more than once
UBS23Q2_10BN = Q("UBS_2023-Q2_report.htm", 8, "We further aim to achieve gross cost reductions of over USD 10bn by that time")
UBS23Q2_CI = Q("UBS_2023-Q2_report.htm", 8, "we aim to achieve an exit-rate cost income ratio of less than 70% by end-2026")
UBS23Q4_NNA = Q("UBS_2023-Q4_report.htm", 8, "with around USD 100bn of net new assets annually through 2025")
UBS23Q4_NCL5 = Q("UBS_2023-Q4_report.htm", 8, "and a share of around 5% of Group RWA, all by the end of 2026")
UBS23AR_FUND = Q("UBS_2023_annual_report.htm", 46, "Additionally, we expect up to USD 1bn of funding cost")
UBS23AR_ETR = Q("UBS_2023_annual_report.htm", 106, "effective tax rate is expected to decrease towards the structural rate in subsequent years")
UBS23AR_NCLPRIO = Q("UBS_2023_annual_report.htm", 56, "Reduce RWA and LRD, freeing up capital for the UBS Group")
UBS23Q4_NCLRUN = Q("UBS_2023-Q4_report.htm", 47, "The core business-led reductions in RWA, coupled with the run-down of "
                  "positions in the Non-core and Legacy business division, are expected to more than offset the effects of "
                  "model updates and revised Basel III standards in 2024 and")

# unit: genuine, reason, class W1, figure call, figure report, quote W1, class ALL, quote ALL, comment
R = {
    # ---- UBS targets
    "T3": (True, "", "C", "1.1bn standalone gross cost saving programme (2023)", "", None, "C", None,
           "The UBS standalone programme is superseded by the combined target and does not appear in the reports."),
    "T9": (True, "", "A", "cost/income ratio below 70% in 2026", "less than 70% by end-2026", UBS23Q2_CI, "A", UBS23Q2_CI, ""),
    "T10": (True, "", "A", "CET1 ratio around 14% over the medium term", "around 14% throughout the integration timeline",
            Q("UBS_2023_annual_report.htm", 28, "we expect to maintain a CET1 capital ratio of around 14% throughout the integration timeline"),
            "A", Q("UBS_2023-Q4_report.htm", 7, "capital ratio of around 14%"),
            "Stated in the call from 2023-Q2; the first report with the guidance is 2023-Q4."),
    "T11": (False, "Filed under cost saves in phase 3; the CET1 statement duplicates T10 and the thread mixes metrics.",
            "", "", "", None, "", None, ""),
    "T12": (True, "", "B", "over 3bn exit-rate saves by end-2023", "over USD 10bn by end-2026", UBS23Q2_10BN, "B", UBS23Q2_10BN,
            "The end-2023 milestone is not in any report; progress (around USD 4bn) is reported only afterwards."),
    "T13": (True, "", "B", "over 3bn exit-rate saves by end-2023", "over USD 10bn by end-2026", UBS23Q2_10BN, "B", UBS23Q2_10BN,
            "Same commitment as T12 in the same call."),
    "T14": (True, "", "A", "NCL reduction of around 50% by end-2026", "about half of NCL RWA to run off by end-2026",
            Q("UBS_2023-Q2_report.htm", 8, "About half of these RWA are expected to run-off by the end of 2026"), "A",
            Q("UBS_2023-Q2_report.htm", 8, "About half of these RWA are expected to run-off by the end of 2026"),
            "Found through the search terms of T50 (the sentence contains neither the T14 phrases nor '50%')."),
    "T16": (True, "", "B", "NCL operational risk RWA around 14bn by end-2026", "NCL key priority: reduce RWA and LRD, no figure",
            UBS23AR_NCLPRIO, "B", UBS23AR_NCLPRIO,
            "B since the consistency rule of 2026-09-24 (Roman's decision): the NCL key priority 'Reduce RWA and LRD' "
            "in the 2023 and 2024 annual reports is forward-looking on the same run-down, without the operational risk "
            "figure. Until 2026-09-24 C."),
    "T17": (True, "", "B", "roughly 5% RWA increase from final Basel III in 2025", "USD 25bn day-1 increase",
            Q("UBS_2023_annual_report.htm", 46, "including an estimated USD 25bn day-1 increase for the finalization of Basel III in 2025"),
            "A", Q("UBS_2024-Q2_report.htm", 8, "will lead to an increase of around 5% in UBS Group risk-weighted assets"),
            "The percentage appears in a report only from 2024-Q2; the call states it in 2023-Q3."),
    "T18": (True, "", "A", "RoCET1 around 15% and C/I below 70% by end-2026", "around 15% RoCET1 in 2026",
            Q("UBS_2023-Q2_report.htm", 8, "progress towards a 2026 exit rate return on CET1 capital of around 15%"), "A",
            Q("UBS_2023-Q2_report.htm", 8, "progress towards a 2026 exit rate return on CET1 capital of around 15%"), ""),
    "T24": (True, "", "A", "around 13bn gross cost reductions by end-2026", "approximately USD 13bn by end-2026",
            Q("UBS_2023-Q4_report.htm", 7, "exit rate gross cost savings of approximately USD 13bn by the end of 2026"), "A",
            Q("UBS_2023-Q4_report.htm", 7, "exit rate gross cost savings of approximately USD 13bn by the end of 2026"), ""),
    "T25": (True, "", "B", "NCL capital release over 6bn by end-2026", "capital released from the NCL unwinding, no figure",
            Q("UBS_2023_annual_report.htm", 62, "We plan to fund this growth organically from the capital released from the unwinding of the"), "B",
            Q("UBS_2023_annual_report.htm", 62, "We plan to fund this growth organically from the capital released from the unwinding of the"),
            "Changed from C to B after Roman's check (amendment of 2026-09-23). Realised later: the 2024 annual report states that NCL 'released over USD 6 billion of capital'."),
    "T26": (True, "", "A", "around 100bn NNA per annum through 2025", "around USD 100bn annually through 2025", UBS23Q4_NNA, "A", UBS23Q4_NNA, ""),
    "T27": (True, "", "B", "NCL credit and market risk RWA substantially below 40bn by end-2024",
            "NCL run-down offsets Group RWA effects in 2024 and 2025, no figure", UBS23Q4_NCLRUN, "B",
            UBS23Q4_NCLRUN,
            "B since the consistency rule of 2026-09-24 (a forward-looking statement on the same reduction counts as B, "
            "also with another scope or without a figure). The 2023-Q4 report (p47) and the 2023 annual report (p193) "
            "expect the NCL run-down to offset model and Basel III effects on Group RWA in 2024 and 2025; no NCL level "
            "and no figure. Until 2026-09-24 kept as C (borderline case)."),
    "T28": (True, "", "A", "buybacks up to 1bn in 2024", "up to USD 1bn in 2024",
            Q("UBS_2023-Q4_report.htm", 8, "In 2024, we plan to repurchase up to USD 1bn of our shares"), "A",
            Q("UBS_2023-Q4_report.htm", 8, "In 2024, we plan to repurchase up to USD 1bn of our shares"), ""),
    "T29": (True, "", "B", "more than 2bn further gross exit-rate saves by end-2024", "around 45% of cumulative reductions by end-2024",
            Q("UBS_2023_annual_report.htm", 29, "with around 45% of the cumulative gross cost reductions expected by the end of 2024"), "B",
            Q("UBS_2023_annual_report.htm", 29, "with around 45% of the cumulative gross cost reductions expected by the end of 2024"), ""),
    "T30": (True, "", "B", "integration-related expenses around 13bn by end-2026", "no total; estimate to be revised",
            Q("UBS_2023-Q2_report.htm", 8, "We expect to revise our initial estimates of cumulative integration-related expenses"), "B",
            Q("UBS_2023-Q2_report.htm", 8, "We expect to revise our initial estimates of cumulative integration-related expenses"),
            "The explicit total (13bn, later 14bn) appears in no report; the 2023-Q2 report gives an indirect order of magnitude (offset by accretion-to-par effects of approximately USD 12bn) and announces a revised estimate."),
    "T31": (True, "", "B", "NCL 2024 operating expenses and pre-tax loss around 4bn", "NCL loss below USD 1bn exit rate by end-2026",
            Q("UBS_2023-Q4_report.htm", 8, "an underlying profit-before-tax loss of less than USD 1bn (exit rate)"), "B",
            Q("UBS_2023-Q4_report.htm", 8, "an underlying profit-before-tax loss of less than USD 1bn (exit rate)"), ""),
    "T32": (True, "", "B", "going-concern requirement +180bp to 16.7% between 2026 and 2030", "higher TBTF requirements phased in from end-2025 to 2030, no figure",
            Q("UBS_2023_annual_report.htm", 186, "The phase-in of these increased capital requirements will commence from the end of 2025 and will be completed by the beginning of 2030, at the latest"),
            "B", Q("UBS_2023_annual_report.htm", 186, "The phase-in of these increased capital requirements will commence from the end of 2025 and will be completed by the beginning of 2030, at the latest"),
            "Changed from C to B after Roman's check (amendment of 2026-09-23)."),
    "T33": (True, "", "C", "AT1 issuance up to 2bn in 2024", "", None, "C", None,
            "Consistent with phase 3b: the plan is only in the call; the reports show issued amounts (1.5, 0.4, 1.6bn) as actuals. Broader search (AT1 with 2024 and issu, 2026-09-23): no forward-looking sentence."),
    "T35": (True, "", "B", "Group RWA down 35bn over three years, freeing around 5bn CET1", "Group RWA around USD 510bn by end-2026",
            Q("UBS_2023-Q4_report.htm", 7, "We expect Group RWA to be around USD 510bn by the end of 2026"), "B",
            Q("UBS_2023-Q4_report.htm", 7, "We expect Group RWA to be around USD 510bn by the end of 2026"), ""),
    "T36": (True, "", "B", "effective tax rate around 40% by end-2024", "tax rate to decrease towards the structural 23%", UBS23AR_ETR,
            "A", Q("UBS_2024-Q1_report.htm", 18, "with our effective tax rate still expected to be around 40% by the end of 2024"),
            "The 40% appears in a report from 2024-Q1."),
    "T39": (False, "Reported actual (another 1bn achieved in the quarter); the 13bn target is T24.", "", "", "", None, "", None, ""),
    "T40": (True, "", "A", "NCL RWA around 5% of Group by end-2026", "around 5% of Group RWA by end-2026", UBS23Q4_NCL5, "A", UBS23Q4_NCL5, ""),
    "T42": (True, "", "A", "another 1.5bn gross cost saves by end-2024", "USD 1.5bn additional in the remainder of 2024",
            Q("UBS_2024-Q1_report.htm", 7, "we aim to achieve USD 1.5bn of additional exit rate gross cost savings in the remainder of 2024"), "A",
            Q("UBS_2024-Q1_report.htm", 7, "we aim to achieve USD 1.5bn of additional exit rate gross cost savings in the remainder of 2024"), ""),
    "T47": (False, "Progress report (467m executed); the 1bn buyback plan is T28.", "", "", "", None, "", None, ""),
    "T50": (True, "", "A", "NCL around 5% of Group RWA by 2026", "around 5% of Group RWA by end-2026", UBS23Q4_NCL5, "A", UBS23Q4_NCL5, ""),
    "T51": (True, "", "A", "transaction to reduce RWA by around 1.3bn, LRD by 1.7bn", "RWA around USD 1.3bn, LRD around USD 1.7bn",
            Q("UBS_2024-Q2_report.htm", 8, "the completion of the transaction would reduce the Group’s risk-weighted assets by around USD 1.3bn"), "A",
            Q("UBS_2024-Q2_report.htm", 8, "the completion of the transaction would reduce the Group’s risk-weighted assets by around USD 1.3bn"), ""),
    "T53": (True, "", "A", "cost/income ratio under 70% by end-2026", "less than 70% by end-2026", UBS23Q2_CI, "A", UBS23Q2_CI, ""),
    "T55": (True, "", "A", "NCL below 5% of Group RWA by end-2026", "below 5% of Group RWA by end-2026",
            Q("UBS_2024_annual_report.htm", 52, "We aim to achieve a share of below 5% of Group RWA by the end of 2026"), "A",
            Q("UBS_2024_annual_report.htm", 52, "We aim to achieve a share of below 5% of Group RWA by the end of 2026"),
            "Earlier reports state 'around 5%' (2023-Q4)."),
    "T56": (False, "Reported actual (5bn RWA de-risked in the quarter); the ambition is not quantified.", "", "", "", None, "", None, ""),
    "T63": (False, "Reported actual (net new money of 45bn in 2024).", "", "", "", None, "", None, ""),
    "T64": (True, "", "B", "effective tax rate around 20% for 2025", "tax rate to decrease towards the structural 23%", UBS23AR_ETR, "B", UBS23AR_ETR, ""),
    "T65": (True, "", "A", "NNA around 100bn for 2025", "around USD 100bn of NNA in 2025",
            Q("UBS_2024-Q4_report.htm", 7, "with around USD 100bn of net new assets in 2025"), "A", UBS23Q4_NNA, ""),
    "T67": (True, "", "A", "P&C cost/income below 50% and pre-tax RoE near 20% by end-2026", "P&C cost / income below 50% by end-2026",
            Q("UBS_2023-Q4_report.htm", 8, "Personal & Corporate Banking: an underlying cost / income ratio of less than 50% by the end of 2026"), "A",
            Q("UBS_2023-Q4_report.htm", 8, "Personal & Corporate Banking: an underlying cost / income ratio of less than 50% by the end of 2026"),
            "The RoE of near 20% is not in the reports (the 2024-Q4 report gives a return on attributed equity of around 19%)."),
    "T68": (True, "", "C", "Group HoldCo around 90bn by end-2025", "", None, "C", None,
            "Broader search (senior unsecured, HoldCo, TLAC, 2026-09-23): only generic capital management statements, no reduction target."),
    # ---- UBS guidance
    "T8": (True, "", "A", "over 10bn gross expense take-out vs 2022 base", "gross cost reductions of over USD 10bn", UBS23Q2_10BN, "A", UBS23Q2_10BN,
           "Phase 3 filed this as expense guidance; it is the first form of the cost-reduction target."),
    "T15": (True, "", "B", "PPA accretion mostly by end-2026, 500m in the next quarter", "accretion-to-par of approximately USD 12bn offsetting integration costs",
            Q("UBS_2023-Q2_report.htm", 8, "expected to be broadly offset by accretion-to-par effects of approximately USD 12bn"), "B",
            Q("UBS_2023-Q2_report.htm", 8, "expected to be broadly offset by accretion-to-par effects of approximately USD 12bn"),
            "The 2024-Q3 and 2024-Q4 reports give next-quarter accretion of USD 0.5bn for other quarters."),
    "T41": (True, "", "B", "around 7.4bn additional revenues through 2028, 0.6bn in 2Q24", "USD 0.6bn next quarter, no total",
            Q("UBS_2024-Q1_report.htm", 18, "We also expect our reported revenues to include around USD 0.6bn of pull-to-par and other PPA accretion effects"),
            "B", Q("UBS_2024-Q1_report.htm", 18, "We also expect our reported revenues to include around USD 0.6bn of pull-to-par and other PPA accretion effects"),
            "The next-quarter figure matches; the 7.4bn total through 2028 is not in the reports."),
    "T46": (True, "", "A", "effective tax rate around 35% in 2H24", "around 35% for 2H24",
            Q("UBS_2024-Q2_report.htm", 20, "we continue to expect our effective tax rate for the second half of 2024 to be around 35%"), "A",
            Q("UBS_2024-Q2_report.htm", 20, "we continue to expect our effective tax rate for the second half of 2024 to be around 35%"), ""),
    "T49": (True, "", "C", "sweep deposit repricing to reduce PBT by around 50m annually", "", None, "C", None, ""),
    "T54": (False, "No new figure; qualitative update of the 50m guidance of T49.", "", "", "", None, "", None, ""),
    "T62": (True, "", "C", "credit loss expense around CHF 350m in 2025 (P&C)", "", None, "C", None, ""),
    # ---- UBS other
    "T37": (True, "", "A", "NNA building to 200bn by 2028", "around USD 200bn annually by 2028",
            Q("UBS_2023-Q4_report.htm", 8, "building to around USD 200bn annually by 2028"), "A",
            Q("UBS_2023-Q4_report.htm", 8, "building to around USD 200bn annually by 2028"), ""),
    "T43": (True, "", "A", "funding costs lower by around 1bn by 2026", "up to USD 1bn of funding cost savings by 2026", UBS23AR_FUND, "A", UBS23AR_FUND, ""),
    "T48": (True, "", "A", "NNA guidance 100bn for 2024 and 2025", "around USD 100bn annually through 2025", UBS23Q4_NNA, "A", UBS23Q4_NNA, ""),
    "T66": (True, "", "C", "GWM Americas pre-tax margin above 30% by end-2026", "", None, "C", None, ""),
    "T34": (True, "", "A", "funding cost saves up to 1bn by 2026", "up to USD 1bn of funding cost savings by 2026", UBS23AR_FUND, "A", UBS23AR_FUND, ""),
    # ---- JPMorgan
    "T0": (True, "", "C", "2023 NII ~$81bn", "", None, "C", None, "The supplements contain no outlook."),
    "T1": (True, "", "C", "2023 Card NCO rate ~2.6%", "", None, "C", None, "The supplements contain no outlook."),
    "T7": (True, "", "C", "2023 expense ~$84.5bn", "", None, "C", None, "The supplements contain no outlook."),
    "T19": (True, "", "C", "2024 NII ex. Markets ~$88bn", "", None, "C", None, "The supplements contain no outlook."),
    "T20": (True, "", "C", "2024 NII guidance ~$88bn", "", None, "C", None, "Restates T19 in the same call."),
    "T21": (True, "", "C", "2024 adjusted expense ~$90bn", "", None, "C", None, "The supplements contain no outlook."),
    "T22": (True, "", "C", "2024 Card NCO rate below 3.5%", "", None, "C", None, "The supplements contain no outlook."),
    "T23": (False, "Reported run rate ($94bn exit rate); the guidance figure belongs to T19.", "", "", "", None, "", None, ""),
    "T38": (True, "", "C", "Card loan growth 12% for 2024", "", None, "C", None, "Hits for '12%' are unrelated table values."),
    "T45": (True, "", "C", "Card allowance build ~$2bn for 2024", "", None, "C", None, ""),
    "T52": (False, "Figure attributed to consensus, not to management.", "", "", "", None, "", None, ""),
    "T57": (True, "", "C", "2025 NII ex. Markets ~$90bn", "", None, "C", None, "The supplements contain no outlook."),
    "T58": (False, "Refers to past rate cuts (100bp in 2H24) and market expectations, not a management figure.", "", "", "", None, "", None, ""),
    "T59": (True, "", "C", "2025 Card loan growth below 12%", "", None, "C", None, ""),
    "T60": (True, "", "C", "2025 expense ~$95bn", "", None, "C", None, "The supplements contain no outlook."),
    "T61": (True, "", "C", "2025 Card NCO rate ~3.6%", "", None, "C", None, "The supplements contain no outlook."),
    "T2": (True, "", "C", "CET1 target 13.5% in 1Q24", "", None, "C", None, "Phase 3 filed this under 'other'; it is JPMorgan's CET1 target."),
    "T5": (True, "", "C", "CET1 target 13.5% in 1Q24 (event call)", "", None, "C", None, ""),
    "T44": (True, "", "C", "dividend to rise from $1.15 to $1.25 in 3Q24", "", None, "C", None,
            "Realised: the 2024-Q3 supplement reports the declared $1.25 dividend (reported, not forward-looking)."),
    "T4": (True, "", "C", "First Republic restructuring costs ~$2bn post-tax over 2023-2024", "", None, "C", None,
           "Consistent with phase 3b."),
    "T6": (True, "", "C", "First Republic incremental net income of $500m+ per year", "", None, "C", None,
           "Merged with stmt_id 771; the supplements report quarterly First Republic net income until 2024-Q1 but no target."),
    "E766": (True, "", "B", "one-time gain at closing ~$2.6bn post-tax", "estimated bargain purchase gain of $2.7bn (preliminary)",
             Q("JPM_2023-Q2_report.htm", 32, "resulting in an estimated bargain purchase gain of $2.7 billion recorded in other income"), "B",
             Q("JPM_2023-Q2_report.htm", 32, "resulting in an estimated bargain purchase gain of $2.7 billion recorded in other income"),
             "Later supplements revise the gain to $2.8bn (phase 3b)."),
}


# Roman's check of the seven UBS target units of class C (2026-09-23), with his own search script
CHECKED = {
    "T3": "Roman 2026-09-23: C confirmed. Programme announced before the acquisition (4Q22 call, 1.1bn); 2022 reports outside the window.",
    "T16": "Roman 2026-09-23: C confirmed. Roman 2026-09-24: B under the consistency rule ('Reduce RWA and LRD, freeing up capital for the UBS Group', 2023 and 2024 annual reports).",
    "T25": "Roman 2026-09-23: B instead of C (2023 annual report, capital released from the NCL unwinding, no figure).",
    "T27": "Roman 2026-09-23: C confirmed. Roman 2026-09-24: B under the consistency rule (forward-looking statement on the same reduction, other scope, no figure; 2023-Q4 report p47 and 2023 annual report p193).",
    "T32": "Roman 2026-09-23: B instead of C (2023 annual report, going concern capital requirements, phase-in end-2025 to 2030, no figure).",
    "T33": "Roman 2026-09-23: C confirmed.",
    "T68": "Roman 2026-09-23: C confirmed.",
}
PRE_ACQUISITION = {"T3"}  # announced before the acquisition; counted separately


def norm(t):
    return re.sub(r"\s+", " ", str(t)).strip()


def report_of(file):
    m = re.match(r"(UBS|JPM)_(\d{4}(?:-Q\d)?)_(annual_)?report", file)
    return f"{m.group(2)} annual report" if m.group(3) else m.group(2)


def main():
    units = pd.read_csv(OUT / "units.csv")
    terms = pd.read_csv(OUT / "search_terms.csv")
    pages = pd.read_csv(PHASE3B / "report_pages.csv", keep_default_na=False).set_index(["file", "page"])
    missing = set(units.unit) - set(R)
    assert not missing, f"units without a reading: {missing}"
    rows = []
    for _, u in units.iterrows():
        genuine, reason, cls, fig_c, fig_r, q1, cls_all, qa, comment = R[u.unit]
        row = dict(unit=u.unit, bank=u.bank, type=u.type, metric=u.metric,
                   origin=f"{u.quarter} {u.call_type}", stmt_id=u.stmt_id, call_sentence=u.call_sentence,
                   genuine="yes" if genuine else "no", reason_not_genuine=reason, **{"class": cls},
                   figure_call=fig_c, figure_report=fig_r, quote_report="", file="", page="",
                   class_all=cls_all, first_report_all="", quote_all="", file_all="", page_all="",
                   search_terms=" | ".join(f"[{t.group}{'' if t.round == 1 else ' r2'}] {t.term}"
                                           for t in terms[terms.unit == u.unit].itertuples()),
                   merged_with=u.merged_with if isinstance(u.merged_with, str) else "", comment=comment,
                   pre_acquisition="yes" if u.unit in PRE_ACQUISITION else "", checked_by_roman=CHECKED.get(u.unit, ""))
        for q, prefix, window in [(q1, "", w1(u)), (qa, "_all", None)]:
            if q is None:
                continue
            f, p, text = q
            assert norm(text) in norm(pages.loc[(f, p), "text"]), (u.unit, f, p, "quote not found")
            rep = report_of(f)
            if window is not None:
                assert rep in window, (u.unit, rep, "W1 quote outside W1")
            key = "quote_report" if prefix == "" else "quote_all"
            row[key] = text
            row["file" + prefix] = f
            row["page" + prefix] = p
            if prefix == "_all":
                row["first_report_all"] = rep
        if genuine:
            assert cls in "ABC" and cls_all in "ABC", u.unit
            assert (cls == "C") == (q1 is None) and (cls_all == "C") == (qa is None), u.unit
        rows.append(row)
    df = pd.DataFrame(rows)
    # the block of UBS targets checked by Roman stays first
    df["_block"] = [0 if u in CHECKED else
                    1 if (b == "UBS" and t == "target") else 2 if b == "UBS" else 3
                    for u, b, t in zip(df.unit, df.bank, df.type)]
    df["_q"] = df.origin.str[:7]
    df = df.sort_values(["_block", "_q", "unit"]).drop(columns=["_block", "_q"])
    df.to_csv(OUT / "counterparts_read.csv", index=False)

    g = df[df.genuine == "yes"]
    cell = lambda d: d.bank + " " + d["type"] + d.pre_acquisition.map({"yes": ", pre-acquisition", "": ""})  # noqa: E731
    counts = (df.assign(cell=cell(df)).groupby("cell")
              .agg(units=("unit", "size"), not_genuine=("genuine", lambda x: int((x == "no").sum())))
              .join(g.assign(cell=cell(g)).pivot_table(index="cell", columns="class", values="unit", aggfunc="size",
                                                       fill_value=0))
              .join(g.assign(cell=cell(g)).pivot_table(index="cell", columns="class_all", values="unit",
                                                       aggfunc="size", fill_value=0), rsuffix="_all"))
    ev = df[df.origin.str.contains("event")]
    counts.loc["JPM event call"] = [len(ev), int((ev.genuine == "no").sum())] + [
        int(((ev.genuine == "yes") & (ev["class"] == c)).sum()) for c in "ABC"] + [
        int(((ev.genuine == "yes") & (ev.class_all == c)).sum()) for c in "ABC"]
    counts = counts.fillna(0).astype(int)
    counts.to_csv(OUT / "counts.csv")
    print(counts.to_string())


if __name__ == "__main__":
    main()
