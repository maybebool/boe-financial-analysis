"""Phase 3b comparison table: call against quarterly report per case and quarter.

Run from the repository root after phase3b_reports.py: python notebooks/roman/analysis/phase3b_compare.py
The entries were compiled by reading the passages in hits_reports.csv, hits_calls.csv and the phase 3 statements.
Every quote is checked verbatim against its source (call statement by stmt_id, report page by file and page),
so the table cannot cite text that is not there. Writes comparison.csv to notebooks/roman/data/phase3b/.
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3b"
PHASE3 = ROOT / "notebooks" / "roman" / "data" / "phase3"

# case, quarter, figure_call, call quote (stmt_id, text), figure_report, report quote (file page, text),
# first_or_more_precise, comment
ROWS = [
    # C1 UBS gross cost saves
    ("C1", "2023-Q1", "1.1bn (UBS standalone programme)", (3316, "we are on track to deliver on our gross cost saving program of 1.1 billion"),
     "", None, "call", "Before completion; the report has only generic risk-factor wording on cost reductions."),
    ("C1", "2023-Q2", "over 10bn target; over 3bn exit rate by end-2023", (3697, "We aim to take out over 10 billion dollars in gross expenses"),
     "over USD 10bn by end-2026", ("UBS_2023-Q2_report.htm", 8, "We further aim to achieve gross cost reductions of over USD 10bn by that time"),
     "call", "Same target; the call adds the year-end 2023 milestone of over 3bn."),
    ("C1", "2023-Q3", "around 3bn achieved", (4216, "we’ve achieved around 3 billion to date in gross run-rate cost saves"),
     "over USD 10bn target, no achieved figure", ("UBS_2023-Q3_report.htm", 7, "to achieve gross cost reductions of over USD 10bn by that time"),
     "call", "Only the call reports progress."),
    ("C1", "2023-Q4", "13bn target; around 4bn achieved", (4752, "around 4 billion, or one-third, are already reflected in our 2023 exit rate"),
     "USD 13bn target; around USD 4bn achieved", ("UBS_2023-Q4_report.htm", 7, "exit rate gross cost savings of approximately USD 13bn by the end of 2026"),
     "same", "Target raised from over 10bn to 13bn in both documents on the same day."),
    ("C1", "2024-Q1", "5bn achieved, nearly 40%", (5208, "we have achieved 5 billion in gross saves, or nearly 40% of our 2026 exit-rate ambition of 13 billion"),
     "USD 5bn of USD 13bn; USD 1.5bn more in 2024", ("UBS_2024-Q1_report.htm", 7, "We have achieved USD 5bn of exit rate gross cost savings"),
     "same", ""),
    ("C1", "2024-Q2", "6bn, around 45%", (5553, "bringing the cumulative total since the end of 2022 to 6 billion, or around 45% of our total gross cost save ambition"),
     "around USD 6bn; around USD 7bn expected by end-2024 (55%)", ("UBS_2024-Q2_report.htm", 7, "We now expect to achieve around USD 7bn of gross cost savings by the end of 2024"),
     "report", "The report adds the raised year-end 2024 expectation."),
    ("C1", "2024-Q3", "750m in the quarter; 7.5bn expected by end-2024", (5887, "we plan to have delivered around 7.5 billion in annualized gross cost saves"),
     "USD 6.8bn; USD 7.5bn expected (58%)", ("UBS_2024-Q3_report.htm", 7, "for a total of around USD 6.8bn in annualized exit rate gross cost savings"),
     "report", "The report gives the cumulative level (6.8bn) and the share (58%)."),
    ("C1", "2024-Q4", "7.5bn, almost 60%", (6338, "we have captured almost 60% of our targeted 13 billion gross cost savings"),
     "USD 7.5bn, around 58%", ("UBS_2024-Q4_report.htm", 7, "Cumulative gross cost savings at the end of 2024 amounted to USD 7.5bn"),
     "same", ""),
    ("C1", "2023 annual report", "2023-Q4 call: 13bn target, around 4bn achieved", (4752, "around 4 billion, or one-third, are already reflected in our 2023 exit rate"),
     "USD 13bn target, around USD 4bn achieved, around 45% expected by end-2024", ("UBS_2023_annual_report.htm", 29, "with around 45% of the cumulative gross cost reductions expected by the end of 2024"),
     "same", "Target and progress as in the fourth-quarter call; the annual report adds a 45% milestone for end-2024, the call a milestone for end-2025 (a further 4bn)."),
    ("C1", "2024 annual report", "2024-Q4 call: 7.5bn, almost 60%", (6338, "we have captured almost 60% of our targeted 13 billion gross cost savings"),
     "USD 7.5bn cumulative, USD 3.4bn in 2024, around 58% of USD 13bn", ("UBS_2024_annual_report.htm", 39, "Cumulative gross cost savings at the end of 2024 amounted to USD 7.5bn"),
     "same", "Same figures as the fourth-quarter call and report."),
    # C2 UBS integration-related expenses
    ("C2", "2023-Q1", "", None, "", None, "neither", "Before completion; no hit in either document."),
    ("C2", "2023-Q2", "broadly similar to 3bn saves in 2H23", (3841, "to incur a broadly similar amount of integration-related expenses in 2H23"),
     "no total; offset by accretion of approx. USD 12bn; estimate to be revised with 4Q23", ("UBS_2023-Q2_report.htm", 8, "We expect to revise our initial estimates of cumulative integration-related expenses"),
     "report", "Indirect order of magnitude: the report expects cumulative integration-related expenses to be broadly offset by accretion-to-par effects of approximately USD 12bn and announces a revised estimate around the 4Q23 results (precision added 2026-09-23 after Roman's check)."),
    ("C2", "2023-Q3", "2bn in the quarter; over 1bn expected in 4Q", (4214, "we expect integration-related expenses in excess of 1 billion"),
     "USD 2,003m in the quarter", ("UBS_2023-Q3_report.htm", 13, "The third quarter of 2023 included total integration-related expenses of USD 2,003m"),
     "call", "Only the call gives the next-quarter expectation."),
    ("C2", "2023-Q4", "around 13bn total by end-2026", (4762, "which we expect to total to around 13 billion by the end of 2026"),
     "USD 1,751m in the quarter; around USD 1bn expected in 1Q24; no total", ("UBS_2023-Q4_report.htm", 21, "including around USD 1bn of integration-related expenses"),
     "call", "The explicit expected total (around 13bn) appears only in the call; the 2023-Q2 report had given only an indirect order of magnitude (offset by accretion of about USD 12bn)."),
    ("C2", "2024-Q1", "13bn total restated; 5.5bn to date", (5213, "reached a total of 5.5 billion since the Credit Suisse acquisition"),
     "quarterly amount only, no total", ("UBS_2024-Q1_report.htm", 12, "integration-related expenses and PPA effects of USD 1,021m from operating expenses"),
     "call", "Cumulative and total figures only in the call."),
    ("C2", "2024-Q2", "2.3bn in 2H24, of which 1.1bn in 3Q24; about 70% of total incurred by end-2024",
     (5562, "In the second half, we expect to book 2.3 billion of integration-related expenses, of which 1.1 billion in the third quarter"),
     "around USD 1.1bn expected in 3Q24 (p. 20); no total", ("UBS_2024-Q2_report.htm", 20,
     "we expect to incur in the third quarter of 2024 around USD 1.1bn of integration-related expenses"),
     "call", "Amended 2026-09-23: the report states the same next-quarter figure (p. 20), which the first version of this row omitted. "
             "The call is still more precise: it adds 2.3bn for the second half of 2024 and that about 70% of total costs to achieve will be incurred by the end of 2024, neither of which is in the report."),
    ("C2", "2024-Q3", "cumulative around 9bn by end-2024; 1.2bn in 4Q", (5887, "cumulative integration-related expenses of around 9 billion"),
     "around USD 1.2bn expected in 4Q, no total", ("UBS_2024-Q3_report.htm", 19, "Integration-related expenses are expected to be around USD 1.2bn"),
     "call", "The report matches the next-quarter figure but not the cumulative one."),
    ("C2", "2024-Q4", "total raised to around 14bn", (6436, "We now expect cumulative integration-related expenses to total around 14 billion"),
     "around USD 1.1bn expected in 1Q25, no total", ("UBS_2024-Q4_report.htm", 20, "integration-related expenses are expected to be around USD 1.1bn"),
     "call", "The 1bn increase of the expected total is disclosed only in the call."),
    ("C2", "2023 annual report", "2023-Q4 call: around 13bn total by end-2026", (4762, "which we expect to total to around 13 billion by the end of 2026"),
     "annual amounts by division, no expected total", ("UBS_2023_annual_report.htm", 101, "Integration-related expenses by business division and Group Items"),
     "call", "No expected total in the 20-F; searched with the case terms and for USD 13bn or 14bn near integration or cost."),
    ("C2", "2024 annual report", "2024-Q4 call: total raised to around 14bn", (6436, "We now expect cumulative integration-related expenses to total around 14 billion"),
     "annual amounts only, no expected total and no increase", ("UBS_2024_annual_report.htm", 98, "after excluding from operating expenses USD 1,807m of integration-related expenses"),
     "call", "The increase to around 14bn does not appear in the 20-F either; the only USD 13bn figures there refer to the savings target."),
    # C3 UBS Basel III final / FRTB
    ("C3", "2023-Q1", "", None, "", None, "neither", "No hit in either document."),
    ("C3", "2023-Q2", "", None,
     "qualitative: final Basel III and FRTB expected to increase RWA", ("UBS_2023-Q2_report.htm", 138, "Fundamental Review of the Trading Book promulgated by the BCBS, which are expected to increase UBS’s RWA"),
     "report", "Risk-factor wording only, no figure in either document."),
    ("C3", "2023-Q3", "roughly 5% RWA increase in 2025, mainly FRTB", (4303, "we continue to expect a roughly 5% increase from day-1 effects in 2025"),
     "", None, "call", "No Basel III final estimate in the report of this quarter. The call says \"as a reminder\", so the figure may have been given earlier outside these documents."),
    ("C3", "2023-Q4", "around 15bn in core businesses", (4814, "we expect Basel 3 to increase RWA by around 15 billion beginning in 2025"),
     "approx. USD 25bn, of which USD 10bn in Non-core and Legacy", ("UBS_2023-Q4_report.htm", 47, "will lead to a further increase in RWA of approximately USD 25bn, of which USD 10bn in Non-core and Legacy"),
     "report", "The call names only the core-business part; the report gives the Group total."),
    ("C3", "2024-Q1", "", None,
     "FINMA ordinances published, no figure", ("UBS_2024-Q1_report.htm", 8, "published five new ordinances to implement the final Basel III standards in Switzerland"),
     "report", "Regulatory update only."),
    ("C3", "2024-Q2", "around 5% of RWA, USD 25bn", (5737, "we still expect a USD 25 billion impact is 5% of risk-weighted assets"),
     "around 5% of Group RWA", ("UBS_2024-Q2_report.htm", 51, "will lead to an increase of around 5% in UBS Group risk-weighted assets"),
     "call", "The call adds the dollar amount."),
    ("C3", "2024-Q3", "low single-digit % of Group RWA", (5906, "our latest estimate is that the RWA impact will be a low single digit percentage of total Group RWA"),
     "low single-digit %, CET1 ratio about -30bp, leverage ratio about -10bp", ("UBS_2024-Q3_report.htm", 9, "reducing the CET1 capital ratio by around 30 basis points"),
     "report", "Downward revision from 5% in both documents; the report quantifies the capital-ratio effect."),
    ("C3", "2024-Q4", "around 1bn; FRTB +9bn, op risk -7bn, credit -1bn", (6582, "This amount of RWA includes increases related to FRTB of 9 billion"),
     "USD 1bn; market risk +7bn, CVA +3bn, op risk -7bn, credit -1bn; model updates +3bn in 2025", ("UBS_2024-Q4_report.htm", 46, "The USD 1bn increase was primarily driven by a USD 7bn increase in market risk RWA"),
     "report", "Same total; the report splits FRTB into market risk and CVA (10bn against 9bn in the call) and adds 3bn of model updates."),
    # C4 UBS AT1
    ("C4", "2023-Q1", "", None, "", None, "neither", "No hit in either document."),
    ("C4", "2023-Q2", "", None, "", None, "neither", "No hit in either document."),
    ("C4", "2023-Q3", "", None,
     "redemption of an AT1 instrument announced", ("UBS_2023-Q3_report.htm", 47, "we announced that we would redeem an AT1 capital instrument on 28 November 2023"),
     "report", ""),
    ("C4", "2023-Q4", "plan: up to 2bn AT1 in 2024", (4794, "we expect to issue up to 2 billion in AT1 in 2024"),
     "USD 3.5bn issued in 4Q23; no 2024 plan", ("UBS_2023-Q4_report.htm", 43, "mainly reflecting two issuances of AT1 capital instruments of USD 3.5bn"),
     "call", "The issuance plan appears only in the call."),
    ("C4", "2024-Q1", "1.5bn in two transactions", (5306, "1.5 billion in AT1 across two transactions in February"),
     "USD 1.5bn, two instruments", ("UBS_2024-Q1_report.htm", 43, "mainly reflecting the issuance of two AT1 capital instruments equivalent to a total of USD 1.5bn"),
     "same", ""),
    ("C4", "2024-Q2", "", None,
     "USD 0.4bn, one instrument", ("UBS_2024-Q2_report.htm", 47, "mainly reflecting the issuance of one AT1 capital instrument equivalent to USD 0.4bn"),
     "report", "Only the report shows this issuance."),
    ("C4", "2024-Q3", "2024 issuance completed, part of 2025 prefunded", (5919, "already having completed our issuances for 2024 and prefunded some of our 2025 AT1 build"),
     "USD 1.6bn issued, USD 1.0bn called", ("UBS_2024-Q3_report.htm", 46, "reflecting the issuance of new AT1 capital instruments equivalent to USD 1.6bn"),
     "report", "The report has the amounts; the call says the 2024 plan is complete."),
    ("C4", "2024-Q4", "3.5bn issued in 2024; ambition 4.3% of RWA", (6557, "we successfully issued 3.5 billion in AT1"),
     "", None, "call", "Annual total and ambition only in the call; the quarterly report amounts sum to 3.5bn (1.5 + 0.4 + 1.6)."),
    # C5 JPMorgan First Republic
    ("C5", "2023-Q1", "", None, "", None, "neither", "Before the acquisition. In no quarter does the supplement contain an outlook: all its hits for \"guidance\" refer to accounting guidance, while NII and expense guidance appear only in the calls."),
    ("C5", "2023-Q2 event", "gain 2.6bn post-tax; restructuring about 2bn post-tax; over 500m net income per year", (767, "total restructuring costs of approximately $2 billion post-tax"),
     "", None, "call", "Event call of 1 May 2023; no supplement for this call."),
    ("C5", "2023-Q2", "gain 2.7bn; FRC revenue 4bn, expense 599m, net income 2.4bn", (387, "First Republic contributed $4 billion of revenue, $599 million of expense, and $2.4 billion of net income"),
     "gain USD 2.7bn (preliminary); segment table: revenue 4,045m, expense 599m, net income 2,386m", ("JPM_2023-Q2_report.htm", 32, "resulting in an estimated bargain purchase gain of $2.7 billion recorded in other income"),
     "report", "The supplement adds a segment split and balance sheet data; neither document restates the 2bn restructuring costs or the 500m target."),
    ("C5", "2023-Q3", "revenue 2.2bn, expense 858m, net income 1.1bn", (937, "First Republic contributed $2.2 billion of revenue, $858 million of expense and $1.1 billion of net income"),
     "gain revised to USD 2.8bn (measurement period adjustment of 100m)", ("JPM_2023-Q3_report.htm", 32, "resulting in an estimated bargain purchase gain of $2.8 billion for the nine months ended September 30, 2023"),
     "report", "Only the supplement shows the revision of the gain."),
    ("C5", "2023-Q4", "revenue 1.9bn, expense 890m, net income 647m", (1322, "First Republic contributed $1.9 billion of revenue, $890 million of expense and $647 million of net income"),
     "gain USD 2.8bn for full year 2023; full-year FRC net income 4,110m", ("JPM_2023-Q4_report.htm", 32, "resulting in an estimated bargain purchase gain of $2.8 billion for the full year 2023"),
     "report", ""),
    ("C5", "2024-Q1", "revenue 1.7bn, expense 806m, net income 668m", (1631, "First Republic contributed $1.7 billion of revenue, $806 million of expense and $668 million of net income"),
     "same figures, last separate First Republic page", ("JPM_2024-Q1_report.htm", 32, "resulting in an estimated bargain purchase gain of $2.8 billion"),
     "same", "Last quarter with separate disclosure in both documents."),
    ("C5", "2024-Q2", "gain referred to as 2.7bn in a year-on-year comparison", (2082, "last year's First Republic bargain purchase gain of $2.7 billion"),
     "no separate First Republic page; footnote cites the preliminary 2.7bn", ("JPM_2024-Q2_report.htm", 26, "Included preliminary estimated bargain purchase gain of $2.7 billion associated with First Republic"),
     "neither", "Separate disclosure ends in both documents; the final 2.8bn is not used."),
    ("C5", "2024-Q3", "", None, "acquisition footnote only, no figures", ("JPM_2024-Q3_report.htm", 3, "acquired certain assets and assumed certain liabilities of First Republic Bank"),
     "neither", "First Republic is no longer reported separately."),
    ("C5", "2024-Q4", "", None, "acquisition footnote only, no figures", ("JPM_2024-Q4_report.htm", 3, "acquired certain assets and assumed certain liabilities of First Republic Bank"),
     "neither", "First Republic is no longer reported separately."),
]


def norm(t):
    return re.sub(r"\s+", " ", str(t)).strip()


def main():
    st = pd.read_csv(PHASE3 / "statements.csv").set_index("stmt_id")
    pages = pd.read_csv(OUT / "report_pages.csv").set_index(["file", "page"])
    out = []
    for case, quarter, fig_c, cq, fig_r, rq, first, comment in ROWS:
        bank = "JPM" if case == "C5" else "UBS"
        row = dict(case=case, bank=bank, quarter=quarter, in_call="yes" if cq else "no", in_report="yes" if rq else "no",
                   figure_call=fig_c, figure_report=fig_r, first_or_more_precise=first, quote_call="", location_call="",
                   quote_report="", location_report="", comment=comment, checked_by_roman="")
        if cq:
            sid, q = cq
            assert norm(q) in norm(st.loc[sid, "text"]), (case, quarter, "call quote not found")
            r = st.loc[sid]
            row.update(quote_call=q, location_call=f"{r.quarter} {r.call_type} call, {r.speaker_name}, "
                                                   f"statement {r.position_in_call}, stmt_id {sid}")
        if rq:
            f, pg, q = rq
            assert norm(q) in norm(pages.loc[(f, pg), "text"]), (case, quarter, "report quote not found")
            row.update(quote_report=q, location_report=f"{f}, page {pg}")
        out.append(row)
    df = pd.DataFrame(out)
    df.to_csv(OUT / "comparison.csv", index=False)
    print(df.groupby(["case", "first_or_more_precise"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
