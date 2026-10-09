"""Phase 3h, version 2 of the unit table: corrected outcomes for T16, T25, T27 and T32.

Run from the repository root: python notebooks/roman/analysis/phase3h_v2.py
Reads units_3h.csv (unchanged), the text exports and the raw reports (read only). Writes units_3h_v2.csv,
corrections_v2.csv and SHA256SUMS (entries for the two new files only) to notebooks/roman/data/phase3h/.
Every prose quote is checked verbatim against the page text and every table value against the positioned
table in the raw report; the script refuses to write otherwise.
"""
import csv
import hashlib
import html
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3h"
TEXT = OUT / "text"
OLD_PAGES = DATA / "phase3b_repaired" / "report_pages.csv"
REPORTS = [DATA / "reports", DATA / "reports_2025_2026"]
TABLE = "Composition of Non-core and Legacy"

# (unit, file, page, quote): prose quotes, verified verbatim after whitespace normalisation
QUOTES = {
    "T25_2024": ("UBS_2024_annual_report.htm", 26, "has cut risk-weighted assets by more than half compared with the "
                 "post-acquisition starting point and released over USD 6 billion of capital to the Group"),
    "T25_2024b": ("UBS_2024_annual_report.htm", 224, "released over USD 6bn of capital to the Group"),
    "T25_2025": ("UBS_2025_annual_report.htm", 26, "Since its inception in 2023, NCL has freed up USD 8 billion of "
                 "capital"),
    "T16_basel": ("UBS_2025-Q1_report.htm", 32, "operational risk RWA decreased by USD 3bn resulting from such "
                  "implementation"),
    "T32_base": ("UBS_2023_annual_report.htm", 186, "The total going concern capital requirements applicable are "
                 "14.92% of RWA"),
    "T32_addon_old": ("UBS_2024_annual_report.htm", 162, "both unchanged at 0.72% of RWA and 0.25% of LRD, resulting "
                      "in add-ons of 1.44% of RWA and 0.50% of LRD"),
    "T32_usd10": ("UBS_2024-Q1_report.htm", 42, "We currently estimate that this will add around USD 10bn to the "
                  "Group’s tier one capital requirement, when fully phased in"),
    "T32_usd10_q4": ("UBS_2024-Q4_report.htm", 41, "We currently estimate that this will add around USD 10bn to the "
                     "Group’s tier 1 capital requirement, when fully phased in"),
    "T32_usd9": ("UBS_2025-Q2_report.htm", 45, "we currently estimate that this will add around USD 9bn to the "
                 "Group’s tier 1 capital requirement, when fully phased in"),
    "T32_usd6": ("UBS_2025-Q3_report.htm", 47, "The estimated effect decreased to USD 6bn, from USD 9bn, following "
                 "FINMA’s confirmation of the capital add-ons for market share and LRD that will apply to UBS"),
    "T32_req_2025": ("UBS_2025_annual_report.htm", 157, "The total going concern capital requirements applicable are "
                     "14.99% of RWA"),
    "F12_2024": ("UBS_2024_annual_report.htm", 169, "During 2024, the LRD decreased by USD 175.9bn to USD 1,519.5bn, "
                 "mainly due to asset size and other movements of USD 102.3bn, as well as currency effects of USD 73.6bn"),
    "F12_2025": ("UBS_2025_annual_report.htm", 93, "During 2025, the LRD increased by USD 103.0bn to USD 1,622.4bn, "
                 "mainly driven by a USD 110.2bn increase from currency effects and a USD 28.8bn increase as a result of "
                 "the implementation of the final Basel III standards, partly offset by a USD 36.1bn decrease from asset "
                 "size and other movements"),
    "F12_2026q1": ("UBS_2026-Q1_report.htm", 46, "the LRD increased by USD 31.0bn to USD 1,653.5bn, driven by a USD "
                   "40.6bn increase from asset size and other movements, partly offset by a USD 9.5bn decrease from "
                   "currency effects"),
    "F12_2026q2": ("UBS_2026-Q2_report.htm", 50, "the LRD decreased by USD 3.7bn to USD 1,649.8bn, driven by a USD 9.4bn "
                   "decrease from currency effects, partly offset by a USD 5.6bn increase from asset size and other "
                   "movements"),
    "F12_exfx": ("UBS_2026-Q2_report.htm", 50, "The LRD movements described below exclude currency effects"),
    "T32_addon_new": ("UBS_2026-Q2_report.htm", 44, "phase-in add-ons as of 1 January 2026 for RWA-based requirements "
                      "of 0.86% for increased market share (1.44% on a fully applied basis) and 0.79% for higher LRD "
                      "(1.08% on a fully applied basis)"),
}


def ws(t):
    return re.sub(r"\s+", " ", t).strip()


def page_text(file, page):
    export = TEXT / file.replace(".htm", ".txt")
    if export.exists():
        parts = re.split(r"=== page (\d+) ===", export.read_text())
        return ws(dict(zip(parts[1::2], parts[2::2]))[str(page)])
    csv.field_size_limit(sys.maxsize)
    with open(OLD_PAGES) as f:
        for r in csv.DictReader(f):
            if r["file"] == file and int(r["page"]) == page:
                return ws(r["text"])
    raise SystemExit(f"no page text for {file} page {page}")


def verify_quotes():
    for key, (file, page, quote) in QUOTES.items():
        if ws(quote) not in page_text(file, page):
            raise SystemExit(f"quote {key} not found verbatim in {file}, page {page}")


def raw(file):
    for folder in REPORTS:
        if (folder / file).exists():
            return (folder / file).read_text(errors="replace")
    raise SystemExit(f"report {file} not found")


def ncl_table(file):
    """Operational risk and total RWA of the table 'Composition of Non-core and Legacy', by reporting date."""
    h = raw(file)
    seg = h[h.index(">" + TABLE):][:60000]
    items = []
    for m in re.finditer(r'<div id="[^"]*" style="position:absolute;([^"]*)">', seg):
        left, top = re.search(r"left:([\d.]+)px", m.group(1)), re.search(r"top:([\d.]+)px", m.group(1))
        end = seg.find('<div id="', m.end())
        text = html.unescape(re.sub(r"<[^>]+>", "", seg[m.end():end if end > 0 else m.end() + 300]))
        text = text.replace("\xa0", " ").strip()
        if left and top and text:
            items.append((float(top.group(1)), float(left.group(1)), text))
    top0 = items[0][0]
    rows = {}
    for top, left, text in items:              # the seg starts after the heading div, so item 0 is a header cell
        if top < top0:
            break
        if top <= top0 + 260:
            rows.setdefault(round(top), []).append((left, text))
    rows = [sorted(r) for _, r in sorted(rows.items())]
    head = [(left, text) for top, left, text in items if top0 <= top <= top0 + 60
            and text in ("RWA", "LRD", "Total assets")]        # the three labels can sit on slightly different lines
    if sorted(t for _, t in head) != ["LRD", "RWA", "Total assets"]:
        raise SystemExit(f"{file}: column headers not found")
    dates = next(r for r in rows if sum(bool(re.fullmatch(r"\d\d?\.\d\d?\.\d\d", t)) for _, t in r) == 6)
    dates = [t for _, t in dates if re.fullmatch(r"\d\d?\.\d\d?\.\d\d", t)]
    oprisk = next(r for r in rows if r[0][1] == "Operational risk")[1:]
    total = next(r for r in rows if r[0][1] == "Total")[1:]
    order = [t for _, t in sorted(head)]                       # column groups from left to right
    i = order.index("RWA")
    rwa_total = total[2 * i:2 * i + 2]
    if len(oprisk) != 2 or len(total) != 6 or any(abs(a[0] - b[0]) > 3 for a, b in zip(oprisk, rwa_total)):
        raise SystemExit(f"{file}: operational risk values are not in the RWA columns")
    return {"dates": dates[2 * i:2 * i + 2], "operational_risk": [float(t) for _, t in oprisk],
            "total_rwa": [float(t) for _, t in rwa_total], "page": table_page(file)}


def table_page(file):
    export = TEXT / file.replace(".htm", ".txt")
    parts = re.split(r"=== page (\d+) ===", export.read_text())
    return next(int(p) for p, body in zip(parts[1::2], parts[2::2]) if TABLE in body)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    verify_quotes()
    files = ["UBS_2024-Q4_report.htm", "UBS_2024_annual_report.htm", "UBS_2025-Q1_report.htm",
             "UBS_2025-Q2_report.htm", "UBS_2025-Q3_report.htm", "UBS_2025-Q4_report.htm",
             "UBS_2025_annual_report.htm", "UBS_2026-Q1_report.htm", "UBS_2026-Q2_report.htm"]
    tab = {f: ncl_table(f) for f in files}
    op = {f: (t["dates"][0], t["operational_risk"][0], t["total_rwa"][0], t["page"]) for f, t in tab.items()}
    q4 = op["UBS_2024-Q4_report.htm"]
    if (q4[1], q4[2]) != (27.1, 41.4) or {v[1] for f, v in op.items() if "2024" not in f} != {24.0}:
        raise SystemExit(f"unexpected table values: {op}")
    non_op_2024 = round(q4[2] - q4[1], 1)                      # 41.4 - 27.1
    increase_bp = round(((1.44 + 1.08) - 1.44) * 100)          # fully applied add-ons less existing add-ons
    fully_applied = round(14.99 + increase_bp / 100, 2)

    old = pd.read_csv(OUT / "units_3h.csv", keep_default_na=False)
    new = old.copy()
    for col in ("source", "page_or_table", "quote"):
        new[col] = ""
    loc = new.actual_location.str.extract(r"^(?P<source>[^,]+), page (?P<page>\d+)$")
    new["source"], new["page_or_table"], new["quote"] = loc.source.fillna(""), \
        ("page " + loc.page).where(loc.page.notna(), ""), new.actual_quote

    series = "; ".join(f"{d}: {v:.1f}" for d, v, _, _ in op.values())
    q = {k: v[2] for k, v in QUOTES.items()}
    upd = {
        "T16": {
            "final_status": "open",
            "status_sequence": " > ".join(
                f"{f[4:].replace('_report.htm', '').replace('_annual', ' annual report')}: open" for f in files[2:]),
            "actual_value": f"NCL operational risk RWA USD 24.0bn at every reporting date from 31.3.2025 to "
                            f"30.6.2026 (USD 27.1bn at 31.12.2024); call figure around USD 14bn by end-2026",
            "actual_quote": "Operational risk 24.0 24.0",
            "actual_location": f"UBS_2026-Q2_report.htm, page {op['UBS_2026-Q2_report.htm'][3]}",
            "comment_b": "Version 2: the operational risk RWA of NCL is reported in the table 'Composition of Non-core "
                         f"and Legacy' of every quarterly and annual report ({series}). The decrease from 27.1 to 24.0 "
                         f"in 2025-Q1 came from the final Basel III standards ('{q['T16_basel']}', 2025-Q1 report, "
                         "p. 32), not from roll-off. No report mentions the target of around USD 14bn; at 30.6.2026 "
                         "the value is USD 10bn above it, six months before the deadline.",
            "source": "UBS_2025-Q1_report.htm; UBS_2025-Q2_report.htm; UBS_2025-Q3_report.htm; UBS_2025-Q4_report.htm; "
                      "UBS_2025_annual_report.htm; UBS_2026-Q1_report.htm; UBS_2026-Q2_report.htm",
            "page_or_table": "table 'Composition of Non-core and Legacy', row 'Operational risk', column RWA; pages "
                             + ", ".join(str(op[f][3]) for f in files[2:]),
            "quote": "Operational risk 24.0 24.0 (table row, 2026-Q2 report: 30.6.26 and 31.3.26)"},
        "T25": {
            "first_retrospective": "2024 annual report (2025-03-17)",
            "final_status": "achieved",
            "status_sequence": "2024 annual report: achieved > 2025-Q1: no longer mentioned > 2025-Q2: no longer "
                               "mentioned > 2025-Q3: no longer mentioned > 2025-Q4: no longer mentioned > 2025 annual "
                               "report: achieved > 2026-Q1: no longer mentioned > 2026-Q2: no longer mentioned",
            "last_mentioned_in": "2025 annual report",
            "actual_value": "over USD 6bn of capital released by end-2024 (2024 annual report); USD 8bn freed up "
                            "since inception by end-2025 (2025 annual report); call figure over USD 6bn by end-2026",
            "actual_quote": q["T25_2025"],
            "actual_location": "UBS_2025_annual_report.htm, page 26",
            "comment_a": "No forward-looking sentence on the NCL capital release in the reports of 2025 and 2026; B "
                         "through the NCL run-down sentences, as for T16. Version 2: the 2024 annual report states the "
                         "call figure retrospectively, as a result ('released over USD 6 billion of capital to the "
                         "Group', pp. 26 and 224), without calling it a target and without a deadline.",
            "comment_b": "Version 2: achieved two years before the deadline. Both sentences report a result; neither "
                         "names the target of the call. The 2025 quarterly reports and the 2026 reports do not mention "
                         "the capital release.",
            "source": "UBS_2024_annual_report.htm; UBS_2025_annual_report.htm",
            "page_or_table": "2024 annual report pages 26 and 224; 2025 annual report page 26",
            "quote": f"2024: '{q['T25_2024']}'; 2025: '{q['T25_2025']}'"},
        "T27": {
            "status_sequence": old.loc[old.unit == "T27", "status_sequence"].iloc[0]
            .replace("2024-Q4: not determinable from these reports", "2024-Q4: achieved (calculated from the table)")
            .replace("2024 annual report: not determinable from these reports",
                     "2024 annual report: achieved (calculated from the table)"),
            "actual_value": f"NCL RWA other than operational risk USD {non_op_2024}bn at 31.12.2024 (total 41.4 less "
                            "operational risk 27.1; calculated); credit and market risk RWA around USD 5bn at "
                            "31.12.2025, USD 4bn at 31.3.2026",
            "comment_b": "Version 2: the value at the deadline can be calculated from the table 'Composition of "
                         "Non-core and Legacy' in the 2024-Q4 report and the 2024 annual report: total RWA 41.4 less "
                         f"operational risk 27.1 gives USD {non_op_2024}bn, substantially below the 40bn of the call. "
                         "No sentence states this value. The target was then replaced by lower ambitions (below USD "
                         "8bn by end-2025, around USD 4bn by end-2026), which were met.",
            "source": "UBS_2024-Q4_report.htm; UBS_2024_annual_report.htm",
            "page_or_table": f"table 'Composition of Non-core and Legacy', rows 'Operational risk' and 'Total', column "
                             f"RWA; pages {q4[3]} and {op['UBS_2024_annual_report.htm'][3]}",
            "quote": "Operational risk 27.1; Total 41.4 (table rows, 31.12.24)"},
        "T32": {
            "actual_value": f"fully applied RWA add-ons 1.44% + 1.08% = 2.52% against 1.44% before: an increase of "
                            f"about {increase_bp} basis points (calculated), against around 180 in the call; on the "
                            f"14.99% of 31.12.2025 this gives about {fully_applied}% (calculated, other components "
                            "unchanged), against 16.7% in the call",
            "actual_quote": q["T32_addon_new"],
            "actual_location": "UBS_2026-Q2_report.htm, page 44",
            "comment_a": "Forward-looking on the phase-in of the higher requirements from 2026 to 2030, without the "
                         "16.7% or 180 basis points. Version 2: the estimated effect is given in USD from the 2024-Q1 "
                         "report onwards ('add around USD 10bn to the Group's tier one capital requirement, when fully "
                         "phased in'; 10bn up to 2025-Q1, 9bn in 2025-Q2, 6bn from 2025-Q3), not only from 2025-Q3 as "
                         "version 1 stated. 180 basis points on RWA of USD 546.5bn at 31.12.2023 (2024 annual report, p. 169) are USD 9.8bn, so the "
                         "USD 10bn of the reports is the call figure in another unit.",
            "comment_b": "Version 2, calculation: existing add-ons 0.72% for market share and 0.72% for LRD, together "
                         "1.44% of RWA (2024 annual report, p. 162). Fully applied add-ons 1.44% and 1.08%, together "
                         "2.52% (2026-Q1 and 2026-Q2 reports). Increase 2.52 - 1.44 = 1.08 percentage points. Call: "
                         "14.92% at 31.12.2023 (2023 annual report, p. 186) + 1.80 = 16.72%. Reports: 14.99% at "
                         "31.12.2025 (2025 annual report, p. 157) + 1.08 = 16.07%. The reports state the add-ons and "
                         "the USD effect (6bn, down from 9bn after FINMA's confirmation), not the sum in basis points "
                         "and not the resulting ratio.",
            "source": "UBS_2023_annual_report.htm; UBS_2024_annual_report.htm; UBS_2024-Q1_report.htm; "
                      "UBS_2025-Q3_report.htm; UBS_2025_annual_report.htm; UBS_2026-Q2_report.htm",
            "page_or_table": "pages 186; 162; 42; 47; 157; 44",
            "quote": f"'{q['T32_base']}' | '{q['T32_addon_old']}' | '{q['T32_usd10']}' | '{q['T32_usd6']}' | "
                     f"'{q['T32_req_2025']}' | '{q['T32_addon_new']}'"},
    }
    # F12: cumulative movement of the Group LRD from asset size and other movements (currency effects excluded)
    f12 = {"31.12.2024": -102.3, "31.12.2025": round(-102.3 - 36.1, 1),
           "31.3.2026": round(-102.3 - 36.1 + 40.6, 1), "30.6.2026": round(-102.3 - 36.1 + 40.6 + 5.6, 1)}
    f12_text = "; ".join(f"{d}: {v:+.1f}" for d, v in f12.items())
    upd["F12"] = {
        "final_status": "open",
        "status_sequence": "2024 annual report: figure reached, reported as a result > 2025-Q1 to 2025-Q4 and 2025 "
                           "annual report: figure reached, target not mentioned > 2026-Q1: below the figure > 2026-Q2: "
                           "below the figure",
        "actual_value": f"Group LRD, cumulative change from asset size and other movements since 31.12.2023, currency "
                        f"effects excluded, in USD bn (calculated): {f12_text}; call figure: a reduction of over 100 "
                        "at constant FX within three years",
        "actual_quote": q["F12_2024"],
        "actual_location": "UBS_2024_annual_report.htm, page 169",
        "comment_b": "Version 2: the reports split the change of the Group LRD into currency effects and asset size and "
                     "other movements ('The LRD movements described below exclude currency effects'). The second part "
                     "corresponds to the call figure at constant FX: same quantity (Group LRD, NCL and core divisions), "
                     "currency effects excluded. It was USD -102.3bn in 2024, so the figure of the call was reached in "
                     "the first of three years, and USD -36.1bn in 2025. In the first half of 2026 it was USD +46.2bn, "
                     "so the cumulative reduction stood at USD 92.2bn at 30.6.2026, below the call figure, six months "
                     "before the end of the three years. The final Basel III standards added USD 28.8bn in 2025, "
                     "reported separately and not included here; with them the cumulative reduction is USD 63.4bn. At "
                     "current FX the LRD is USD 45.6bn below the level of 31.12.2023. No report links these movements "
                     "to the target.",
        "source": "UBS_2024_annual_report.htm; UBS_2025_annual_report.htm; UBS_2026-Q1_report.htm; "
                  "UBS_2026-Q2_report.htm",
        "page_or_table": "pages 169 (also 96); 93; 46; 50",
        "quote": f"'{q['F12_2024']}' | '{q['F12_2025']}' | '{q['F12_2026q1']}' | '{q['F12_2026q2']}'"}
    evidence = {"F12": "2024 annual report pp. 96 and 169; 2025 annual report p. 93; 2026-Q1 report p. 46; 2026-Q2 "
                       "report p. 50",
                "T16": "table 'Composition of Non-core and Legacy', RWA column, quarterly and annual reports 2025 "
                       "and 2026",
                "T25": "2024 annual report pp. 26 and 224; 2025 annual report p. 26",
                "T27": "table 'Composition of Non-core and Legacy', 2024-Q4 report and 2024 annual report",
                "T32": "2023 annual report p. 186; 2024 annual report p. 162; 2024-Q1 report p. 42; 2025-Q3 report "
                       "p. 47; 2025 annual report p. 157; 2026-Q2 report p. 44"}
    corrections = []
    for unit, fields in upd.items():
        i = new.index[new.unit == unit][0]
        for field, value in fields.items():
            before = old.at[i, field] if field in old.columns else ""
            if value != before:
                new.at[i, field] = value
                if field in old.columns:
                    corrections.append({"unit": unit, "field": field, "old": before, "new": value,
                                        "evidence": evidence[unit]})
    # reading of phase 3d that version 2 supersedes; the phase 3d file itself is not changed
    corrections.append({
        "unit": "T32", "field": "figure_report in data/phase3d/counterparts_read.csv (file not changed)",
        "old": "higher TBTF requirements phased in from end-2025 to 2030, no figure",
        "new": "mentioned with another figure: around USD 10bn added to the tier 1 capital requirement when fully "
               "phased in (2024-Q1 report p. 42, repeated in the 2024-Q2, 2024-Q3 and 2024-Q4 reports); class B "
               "unchanged; no longer counted among the call-only figures (Roman's decision of 2026-10-09)",
        "evidence": f"'{q['T32_usd10']}' (UBS_2024-Q1_report.htm, page 42); 180 basis points on RWA of USD 546.5bn "
                    "at 31.12.2023 are USD 9.8bn"})
    new.to_csv(OUT / "units_3h_v2.csv", index=False)
    pd.DataFrame(corrections).to_csv(OUT / "corrections_v2.csv", index=False)
    (OUT / "SHA256SUMS").write_text("".join(f"{sha256(OUT / n)}  {n}\n"
                                            for n in ("corrections_v2.csv", "units_3h_v2.csv")))
    print(f"quotes verified: {len(QUOTES)}; table read in {len(tab)} reports")
    for f, v in op.items():
        print(f"  {f}: {v[0]} operational risk {v[1]}, total RWA {v[2]}, page {v[3]}")
    print(f"T27 at 31.12.2024: {non_op_2024}; T32 increase {increase_bp} bp, fully applied {fully_applied}%")
    print(f"corrections: {len(corrections)}")


if __name__ == "__main__":
    main()
