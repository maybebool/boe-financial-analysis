"""Phase 3g, step 2: reading of the set S, search for the new genuine commitments, classes and updated basis.

Run from the repository root after phase3g_fls.py, in this order:
    python notebooks/roman/analysis/phase3g_read.py terms     # reading of S, new units, search terms, hash
    python notebooks/roman/analysis/phase3g_read.py search    # UBS quarterly and annual reports, windows W1 and ALL
    python notebooks/roman/analysis/phase3g_read.py pillar3 F11 F12 F22  # amendment 1: new UBS targets of class C
    python notebooks/roman/analysis/phase3g_read.py classify  # classes with verified quotes, updated basis
    python notebooks/roman/analysis/phase3g_read.py checkfiles  # check files for the independent check (new UBS C targets)
    python notebooks/roman/analysis/phase3g_read.py spotcheck   # blind spot check against the reading of S
Outputs in notebooks/roman/data/phase3g/. Rules as in plans/phase_3g.md.
"""
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase3_extract import FORWARD_RE, METRICS, horizons  # noqa: E402
from phase3b_reports import file_hashes, pages_positioned  # noqa: E402
from phase3c_counterparts import period_end, split_sentences  # noqa: E402
from phase3d_search import LONG, compile_term, w1  # noqa: E402
from phase3d_terms import figure_formats  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3g"
PHASE3B = DATA / "phase3b_repaired"
REPORTS = DATA / "reports"
PILLAR3 = ["2023-Q3", "2023-Q4", "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]
PILLAR3_PENDING = {"2024-Q2"}  # filed 23 August 2024, not yet available (phase 3f)

N, Y = False, True
# Reading of S. stmt_id: (genuine, reason if not genuine or comment, duplicate_of, type, new unit)
# duplicate_of names the phase 3d unit (T.., E766) or, for a candidate that phase 3 filed under another thread,
# the candidate's stmt_id and its thread; "new" units get an id F.. and go to the report search.
READ = {
    # ---- JPMorgan event call
    754: (N, "Contractual transaction term (payment to the FDIC), not an expectation about a metric; the figure is "
             "marked (sic) in the transcript.", "", "", ""),
    757: (N, "Contractual transaction term (repayment of the deposits from large US banks).", "", "", ""),
    766: (Y, "", "E766", "other", ""),
    771: (Y, "", "T6", "other", ""),
    773: (N, "Pro forma effect at closing, which took place on the day of the call; no future horizon.", "", "", ""),
    # ---- UBS 2023-Q2
    3593: (N, "5.5 trillion is the current combined size; the forward part has no figure.", "", "", ""),
    3675: (N, "13% is the pro forma share of the transferred business in current RWA, not a forward figure.", "", "", ""),
    3676: (N, "Allocation of the current portfolio to NCL at set-up; no future horizon.", "", "", ""),
    3678: (N, "Pro forma composition of NCL at set-up; no future horizon.", "", "", ""),
    3691: (Y, "Same NCL reduction of 50% by 2026 as T14, one quarter before the phase 3 origin of T14.", "T14",
           "target", ""),
    3766: (N, "13 billion is an actual flow; the expectation has no figure.", "", "", ""),
    4068: (N, "The figure (300 million improvement) describes the past; the forward part (break even in 3Q) names "
              "no metric. Borderline.", "", "", ""),
    # ---- UBS 2023-Q3
    4197: (Y, "Group Items benefit from the repaid Credit Suisse liquidity measures (context).", "new", "guidance", "F01"),
    4203: (Y, "Remaining PPA accretion balance; the next sentence is the T15 origin.", "T15", "guidance", ""),
    4205: (Y, "NII from the eliminated cash flow hedge; not part of the pull-to-par balance of T15.", "new",
           "guidance", "F02"),
    4214: (Y, "Quarterly guidance; T30 is the total to end-2026.", "new", "guidance", "F03"),
    4220: (Y, "", "T10", "target", ""),
    4226: (Y, "", "new", "guidance", "F04"),
    4299: (Y, "Horizon from context: final Basel III effective 1 January 2025.", "new", "guidance", "F05"),
    4301: (N, "30 billion is the current NCL operational risk RWA; the forward part has no figure (the figure "
              "follows in the next sentence, T16).", "", "", ""),
    4463: (N, "Speculative and hedged; 20 billion refers to past outflows.", "", "", ""),
    # ---- UBS 2023-Q4 (investor update)
    4654: (Y, "Horizon from context: 'medium-term priorities and ambitions' (two sentences earlier).", "new",
           "target", "F06"),
    4665: (Y, "Surpass 5 trillion by 2028, also candidate 4728.", "T26", "target", ""),
    4666: (Y, "GWM divisional ratio, not the Group ratio of T9; horizon from context (medium-term ambitions).",
           "new", "target", "F07"),
    4686: (Y, "Horizon 'over the cycle', within the medium-term ambitions.", "new", "target", "F08"),
    4687: (Y, "Same IB ambition as F08, second metric.", "new", "target", "F09"),
    4697: (Y, "", "T10", "target", ""),
    4700: (Y, "Dividend proposal for the 2023 financial year.", "new", "other", "F10"),
    4723: (Y, "Effective tax rate of 23% by 2026, also candidates 4822, 5190, 5551.", "T36", "target", ""),
    4771: (Y, "Share of the 13 billion gross saves achieved through NCL; component of T24.", "T24", "target", ""),
    4777: (Y, "NCL cost below 1 billion exiting 2026; restated as candidate 5221 (NCL opex exit rate below "
              "1 billion, filed under thread 40).", "T40 (candidate 5221)", "target", ""),
    4793: (Y, "Horizon from context: between 2026 and 2030 (previous sentence, T32); a ratio target, not the "
              "requirement of T32 or the 2024 issuance of T33.", "new", "target", "F11"),
    4805: (Y, "Horizon from context: over the next 3 years (previous sentence).", "new", "target", "F12"),
    4814: (Y, "Core share (15 of 25 billion) of the Basel III increase of T17.", "T17", "target", ""),
    4815: (Y, "Component of the three-year Group RWA walk of T35.", "T35", "target", ""),
    4816: (Y, "Component of the three-year Group RWA walk of T35.", "T35", "target", ""),
    4825: (Y, "Remainder of the DTA plan of candidate 4824 (filed under thread 10).", "T10 (candidate 4824)",
           "guidance", ""),
    4955: (N, "Illustrative and hedged ('over time'), and withdrawn two sentences later ('we are not talking about "
              "15% to 18%').", "", "", ""),
    5049: (Y, "", "T37", "other", ""),
    # ---- UBS 2024-Q1
    5144: (Y, "", "T28", "target", ""),
    5170: (Y, "Additional capital requirement for the parent bank from the phase-in of progressive add-ons; the "
              "Group requirement of T32 is the same phase-in in another unit.", "new", "other", "F13"),
    5311: (Y, "", "new", "other", "F14"),
    5334: (Y, "Around 100 billion per year through 2025.", "T26", "target", ""),
    5422: (Y, "Restates F13 (10 billion) together with the 9 billion of the previous paragraph.", "F13", "other", ""),
    # ---- UBS 2024-Q2
    5569: (Y, "", "T17", "target", ""),
    5580: (N, "Actual value for the quarter just ended, published the following week.", "", "", ""),
    5626: (N, "Assumption about the central bank's policy rate.", "", "", ""),
    5641: (Y, "", "new", "guidance", "F15"),
    5737: (Y, "", "T17", "target", ""),
    5738: (Y, "", "T17", "target", ""),
    5763: (Y, "", "T49", "guidance", ""),
    # ---- UBS 2024-Q3
    5870: (Y, "Tax rate of around 35% as T46; the quarterly PPA and integration figures belong to T41 and T30.",
           "T46", "guidance", ""),
    5900: (Y, "Revised total of the acquisition-related revenues of T41 (7.4 billion through 2028).", "T41",
           "guidance", ""),
    5901: (Y, "Schedule of the same total.", "T41", "guidance", ""),
    5904: (N, "Actual value for the quarter just ended, published the following week.", "", "", ""),
    5956: (Y, "", "new", "guidance", "F16"),
    6067: (Y, "", "T18", "target", ""),
    6150: (N, "The parent bank share has no figure; the 30 basis points are the Group effect (candidate 5907).",
           "", "", ""),
    # ---- UBS 2024-Q4
    6212: (Y, "Dividend proposal for the 2024 financial year.", "new", "other", "F17"),
    6279: (N, "Expectation about the central bank's policy rate.", "", "", ""),
    6282: (Y, "", "new", "guidance", "F18"),
    6380: (Y, "", "T10", "target", ""),
    6436: (Y, "Revised total (13 to 14 billion).", "T30", "target", ""),
    6533: (Y, "Restates F08 and F09.", "F08, F09", "target", ""),
    6541: (Y, "", "new", "guidance", "F19"),
    6542: (Y, "Component of the 2025 NCL outlook of candidate 6543 (filed under thread 31).", "T31 (candidate 6543)",
           "guidance", ""),
    6548: (Y, "Components of the NCL pre-tax loss below 1 billion exiting 2026 of candidate 6547 (filed under "
              "thread 12).", "T12 (candidate 6547)", "target", ""),
    6550: (Y, "Companion of candidate 6549 (NCL legacy opex below 250 million by end-2028), another cost line.",
           "new", "guidance", "F20"),
    6563: (N, "Actual value for the year just ended, published later.", "", "", ""),
    6564: (Y, "Horizon 'for the foreseeable future'.", "new", "target", "F21"),
    6576: (Y, "Operating level with an upper bound, 'going forward'.", "new", "target", "F22"),
    6581: (N, "The day-1 impact occurred on 1 January 2025, before the call; a figure to be reported, not a "
              "forward-looking one.", "", "", ""),
    6621: (N, "Target for the US intermediate holding company without a horizon, even in context. Borderline.",
           "", "", ""),
}

# new unit: short description, phrases (group 2), metric key for group 1 (None: no metric of phase 3 fits),
# extra report spellings of the figure (group 3) that the quantity parser does not produce
NEW = {
    "F01": ("Group Items additional 100m benefit in 4Q23 from repaid liquidity measures",
            ["Group Items", "liquidity measures"], "revenue", []),
    "F02": ("around 900m additional NII from the eliminated cash flow hedge, 150m in 4Q23",
            ["cash flow hedge", "cash flow hedges"], "nii", []),
    "F03": ("integration-related expenses over 1bn in 4Q23", ["integration-related expenses"], "integration", []),
    "F04": ("around CHF 80m annualized NII reduction from SNB reserve and remuneration changes",
            ["minimum reserve requirement", "sight deposit"], "nii", []),
    "F05": ("Group operational risk RWA broadly unchanged at 145bn under final Basel III",
            ["operational risk RWA", "operational risk risk-weighted assets"], None, []),
    "F06": ("GWM pre-tax margins above 40% in Switzerland, EMEA and APAC",
            ["pre-tax margin", "PBT margin", "profit before tax margin"], None, []),
    "F07": ("GWM underlying cost/income ratio below 70%",
            ["cost / income ratio", "cost/income ratio", "cost income ratio"], "returns", []),
    "F08": ("Investment Bank around 15% return on attributed equity over the cycle",
            ["return on attributed equity", "over the cycle", "through the cycle"], "returns", []),
    "F09": ("Investment Bank no more than 25% of Group RWA",
            ["of Group risk-weighted assets", "of the Group's risk-weighted assets", "of Group RWA"], None, []),
    "F10": ("dividend of USD 0.70 per share for 2023", ["ordinary dividend", "dividend of USD"], "distributions",
            ["0.70"]),
    "F11": ("going concern capital ratio around 18% by building out AT1",
            ["going concern capital ratio", "going-concern capital ratio", "AT1 bucket"], "capital", []),
    "F12": ("leverage ratio denominator down by over 100bn over three years",
            ["leverage ratio denominator", "LRD"], None, []),
    "F13": ("parent bank capital requirement up by about 10bn from progressive capital add-ons",
            ["progressive", "capital add-on", "parent bank"], "capital", []),
    "F14": ("repay the remaining 9bn of ELA in the coming months",
            ["emergency liquidity assistance", "ELA"], None, []),
    "F15": ("additional 60m pre-tax profit in 3Q24 from disposal gains in Asset Management",
            ["gains from disposals", "gain on disposal", "disposal"], "revenue", []),
    "F16": ("mid-single-digit percentage sequential drop in NII in 4Q24",
            ["mid-single-digit", "mid-single digit", "mid single-digit"], "nii", []),
    "F17": ("dividend of USD 0.90 per share for 2024", ["ordinary dividend", "dividend of USD"], "distributions",
            ["0.90"]),
    "F18": ("P&C Swiss franc NII down around 10% sequentially in 1Q25",
            ["Swiss franc net interest income", "CHF net interest income", "Swiss franc NII"], "nii", []),
    "F19": ("gain of around 100m in 1Q25 from the sale of the US mortgage servicing company",
            ["mortgage servicing"], "revenue", []),
    "F20": ("NCL legacy funding costs around 100m per year by end-2028, run down by 2033",
            ["legacy funding costs", "legacy funding"], None, []),
    "F21": ("UBS AG standalone CET1 capital ratio 12.5% to 13% for the foreseeable future",
            ["standalone CET1 capital ratio", "standalone CET1 ratio", "UBS AG standalone"], "capital", []),
    "F22": ("LCR below the 4Q24 level of 188% going forward",
            ["liquidity coverage ratio", "LCR"], None, []),
}


def reading():
    s = pd.read_csv(OUT / "set_s.csv")
    assert set(s.stmt_id) == set(READ), "reading does not cover S exactly"
    r = pd.DataFrame([dict(stmt_id=k, genuine="yes" if v[0] else "no", comment=v[1], duplicate_of=v[2], type=v[3],
                           new_unit=v[4]) for k, v in READ.items()])
    s = s.rename(columns={c: f"phase3_{c}" for c in ["metric", "type", "value", "unit", "horizon", "horizon_label"]})
    return s.merge(r, on="stmt_id")


def units(read):
    u = read[read.new_unit != ""].copy()
    u["unit"] = u.new_unit
    u["description"] = u.unit.map(lambda x: NEW[x][0])
    u["metric"] = u.unit.map(lambda x: NEW[x][2] or "other")
    u["call_sentence"] = u.text
    return u[["unit", "bank", "type", "metric", "quarter", "call_type", "call_date", "stmt_id", "description",
              "call_sentence"]].sort_values("unit").reset_index(drop=True)


def cmd_terms():
    read = reading()
    read.to_csv(OUT / "set_s_read.csv", index=False)
    u = units(read)
    assert set(u.unit) == set(NEW)
    u.to_csv(OUT / "new_units.csv", index=False)
    kw = {g: p for g, _, p in METRICS}
    rows = []
    for _, x in u.iterrows():
        phrases, metric, extra = NEW[x.unit][1], NEW[x.unit][2], NEW[x.unit][3]
        if metric:
            rows.append(dict(unit=x.unit, group=1, term=kw[metric], regex=True))
        rows += [dict(unit=x.unit, group=2, term=p, regex=False) for p in phrases]
        rows += [dict(unit=x.unit, group=3, term=f, regex=False)
                 for f in dict.fromkeys(figure_formats(x.call_sentence) + extra)]
    terms = pd.DataFrame(rows)
    terms.to_csv(OUT / "search_terms.csv", index=False)
    log = dict(search_terms_sha256=hashlib.sha256((OUT / "search_terms.csv").read_bytes()).hexdigest(),
               terms_written=datetime.now().isoformat(timespec="seconds"))
    (OUT / "run_log.json").write_text(json.dumps(log, indent=2))
    print(read.groupby(["call", "genuine"]).size())
    print(read[read.genuine == "yes"].assign(new=lambda d: d.duplicate_of == "new").groupby(["call", "new"]).size())
    print(u[["unit", "type", "quarter", "description"]].to_string(index=False))
    print(len(terms), "terms")


def search(pages, u, terms, window=None):
    tu = terms[terms.unit == u.unit]
    comp = {g: [(t.term, compile_term(t)) for t in tu[tu.group == g].itertuples()] for g in (1, 2, 3)}
    rows = []
    for _, p in pages.iterrows():
        for s in split_sentences(p.text):
            found = {g: [term for term, rx in comp[g] if rx.search(s)] for g in (1, 2, 3)}
            if not (found[2] or found[3]):
                continue
            text = s
            if len(s) > LONG:  # table block: window around the first figure or phrase hit
                rx = next(rx for g in (3, 2) for term, rx in comp[g] if term in found[g])
                m = rx.search(s)
                text = "[...] " + s[max(0, m.start() - 300):m.end() + 300] + " [...]"
            fwd = bool(FORWARD_RE.search(s)) or bool(horizons(s, period_end(p.quarter)))
            prio = 3 if found[3] and (found[1] or found[2]) else 2 if found[2] and fwd else 1 if found[2] else 0
            rows.append(dict(unit=u.unit, report=p.quarter, in_W1=window is None or p.quarter in window, file=p.file,
                             page=p.page, priority=prio, forward=fwd, g1=bool(found[1]), g2="; ".join(found[2]),
                             g3="; ".join(found[3]), table_block=len(s) > LONG, text=text))
    return rows


def check_hash():
    log = json.loads((OUT / "run_log.json").read_text())
    now = hashlib.sha256((OUT / "search_terms.csv").read_bytes()).hexdigest()
    assert now == log["search_terms_sha256"], "search terms were changed after they were recorded"
    return log


def cmd_search():
    log = check_hash()
    log["report_hashes"] = file_hashes()
    log["search_started"] = datetime.now().isoformat(timespec="seconds")
    (OUT / "run_log.json").write_text(json.dumps(log, indent=2))
    u = pd.read_csv(OUT / "new_units.csv")
    terms = pd.read_csv(OUT / "search_terms.csv")
    pages = pd.read_csv(PHASE3B / "report_pages.csv", keep_default_na=False)
    rows = []
    for _, x in u.iterrows():
        rows += search(pages[pages.bank == x.bank], x, terms, set(w1(x)))
    hits = pd.DataFrame(rows)
    hits.to_csv(OUT / "hits.csv", index=False)
    assert file_hashes() == log["report_hashes"], "report files changed"
    print(hits.groupby(["unit", "in_W1", "priority"]).size().unstack(fill_value=0).to_string())


def pillar3_window(quarter):
    return [q for q in PILLAR3 if q >= quarter and q not in PILLAR3_PENDING]


def cmd_pillar3(unit_ids):
    """Amendment 1: new UBS targets of class C in W1 and ALL, searched in the Pillar 3 reports (procedure of 3f)."""
    log = check_hash()
    u = pd.read_csv(OUT / "new_units.csv").set_index("unit").loc[unit_ids].reset_index()
    terms = pd.read_csv(OUT / "search_terms.csv")
    files = sorted({f"UBS_{q}_pillar3.htm" for q in u.quarter.map(pillar3_window).sum()})
    before = {f: hashlib.sha256((REPORTS / f).read_bytes()).hexdigest() for f in files}
    log["pillar3_units"] = list(unit_ids)
    log["pillar3_hashes"] = before
    (OUT / "run_log.json").write_text(json.dumps(log, indent=2))
    pages = []
    for f in files:
        html = (REPORTS / f).read_text(encoding="utf-8", errors="replace")
        pages += [dict(file=f, quarter=f.split("_")[1], page=n, text=t) for n, t in pages_positioned(html, repair=True)]
    pages = pd.DataFrame(pages)
    pages.to_csv(OUT / "pillar3_pages.csv", index=False)
    rows = []
    for _, x in u.iterrows():
        rows += search(pages[pages.quarter.isin(pillar3_window(x.quarter))], x, terms)
    hits = pd.DataFrame(rows).drop(columns="in_W1")
    hits.to_csv(OUT / "pillar3_hits.csv", index=False)
    assert {f: hashlib.sha256((REPORTS / f).read_bytes()).hexdigest() for f in files} == before
    print(hits.groupby(["unit", "priority"]).size().unstack(fill_value=0).to_string())


Q = lambda f, p, t: (f, p, t)  # noqa: E731
UBS23Q4_DIV = Q("UBS_2023-Q4_report.htm", 8, "The Investment Bank: an underlying return on attributed equity of "
                                             "approximately 15% through the cycle, while operating with no more than 25%")
NCL_PRIO = Q("UBS_2023_annual_report.htm", 56, "Reduce RWA and LRD, freeing up capital for the UBS Group")
SPS = Q("UBS_2024-Q2_report.htm", 8, "UBS Group does not expect to recognize a material profit or loss upon completion "
                                     "of the transaction")
# unit: class W1, quote W1, class ALL, quote ALL, class Pillar 3 ("" if not searched), borderline quote, comment
# Read in two passes: hits with a figure and a phrase, then every forward-looking hit with a phrase or figure; in the
# second pass the full hit text was scanned around every term, because the first pass had shown truncated text
# (F13, F14 and F16 were first read as C and corrected before any class was recorded).
CLS = {
    "F01": ("C", None, "C", None, "", Q("UBS_2024-Q1_report.htm", 20, "to average approximately USD 100m per quarter"),
            "Group Items appear forward-looking only with a later quarterly loss outlook (2024-Q1), another commitment."),
    "F02": ("C", None, "C", None, "", None, "Cash flow hedges appear only in accounting policy text and OCI tables."),
    "F03": ("C", None, "C", None, "", Q("UBS_2023-Q4_report.htm", 21, "including around USD 1bn of integration-related expenses"),
            "The report gives the quarterly outlook for 1Q24, not for 4Q23."),
    "F04": ("C", None, "C", None, "", Q("UBS_2024-Q1_report.htm", 8, "UBS expects a negative impact of USD 70m to USD 80m "
                                                                  "per annum on net interest income to result from these changes"),
            "The 2024-Q1 figure concerns the SNB's later change of April 2024 (minimum reserve ratio from 2.5% to 4%), "
            "not the change of autumn 2023."),
    "F05": ("C", None, "B", Q("UBS_2024_annual_report.htm", 158, "is expected to lead to a USD 7bn decrease in operation al "
                                                                 "risk RWA to USD 138bn from USD 145bn under the AMA"), "",
            None, "ALL only, with another figure (138bn instead of broadly unchanged at 145bn); the split word "
                  "'operation al' is in the reconstructed page text."),
    "F06": ("A", Q("UBS_2023_annual_report.htm", 28, "We expect Global Wealth Management margins in the region to "
                                                   "eventually exceed 40%"), "A",
            Q("UBS_2023_annual_report.htm", 28, "We expect Global Wealth Management margins in the region to eventually "
                                                "exceed 40%"), "", None,
            "The report states it for Asia Pacific only; Switzerland and EMEA were not found. Borderline A."),
    "F07": ("A", Q("UBS_2023-Q4_report.htm", 8, "and an underlying cost / income ratio of less than 70% by the end of "
                                               "2026 (exit rate)"), "A",
            Q("UBS_2023-Q4_report.htm", 8, "and an underlying cost / income ratio of less than 70% by the end of 2026 "
                                           "(exit rate)"), "", None, "GWM ambition in the business division list."),
    "F08": ("A", UBS23Q4_DIV, "A", UBS23Q4_DIV, "", None, ""),
    "F09": ("A", UBS23Q4_DIV, "A", UBS23Q4_DIV, "", None,
            "Already in the 2023-Q1 report as a plan ('around 25% of Group risk-weighted assets')."),
    "F10": ("A", Q("UBS_2023-Q4_report.htm", 8, "For 2023, the Board of Directors plans to propose a dividend to UBS "
                                                "Group AG shareholders of USD 0.70 per share"), "A",
            Q("UBS_2023-Q4_report.htm", 8, "For 2023, the Board of Directors plans to propose a dividend to UBS Group AG "
                                           "shareholders of USD 0.70 per share"), "", None, ""),
    "F11": ("C", None, "C", None, "C", None,
            "The phrase appears only in tables of actual ratios; the 18% hits are the RoCET1 ambition for 2028."),
    "F12": ("B", NCL_PRIO, "B", NCL_PRIO, "C", None,
            "B since Roman's check and the consistency rule of 2026-09-24: the NCL key priority 'Reduce RWA and LRD' "
            "(2023 and 2024 annual reports) is forward-looking on the same reduction without the 100 billion. It covers "
            "only the NCL part; the call sentence concerns Group LRD (NCL wind-down and core divisions)."),
    "F13": ("A", Q("UBS_2024-Q1_report.htm", 42, "We currently estimate that this will add around USD 10bn to the "
                                                "Group"), "A",
            Q("UBS_2024-Q1_report.htm", 42, "We currently estimate that this will add around USD 10bn to the Group"), "",
            None, "The report attributes the 10bn to the Group's tier 1 requirement, the call to the parent bank."),
    "F14": ("A", Q("UBS_2024-Q1_report.htm", 7, "The remaining CHF 9bn are expected to be repaid in the coming months"),
            "A", Q("UBS_2024-Q1_report.htm", 7, "The remaining CHF 9bn are expected to be repaid in the coming months"),
            "", None, ""),
    "F15": ("A", Q("UBS_2024-Q2_report.htm", 30, "We expect to record in the third quarter of 2024 an additional USD 60m "
                                                "in pre-tax profit on gains from disposals"), "A",
            Q("UBS_2024-Q2_report.htm", 30, "We expect to record in the third quarter of 2024 an additional USD 60m in "
                                            "pre-tax profit on gains from disposals"), "", None, ""),
    "F16": ("A", Q("UBS_2024-Q3_report.htm", 19, "In the fourth quarter, we anticipate a mid-single digit decline in net "
                                                "interest income in Global Wealth Management"), "A",
            Q("UBS_2024-Q3_report.htm", 19, "In the fourth quarter, we anticipate a mid-single digit decline in net "
                                            "interest income in Global Wealth Management"), "", None,
            "The call sentence concerns GWM (context: GWM NII of 1.6 billion)."),
    "F17": ("A", Q("UBS_2024-Q4_report.htm", 8, "For the 2024 financial year, the Board of Directors plans to propose a "
                                                "dividend to UBS Group AG shareholders of USD 0.90 per share"), "A",
            Q("UBS_2024-Q4_report.htm", 8, "For the 2024 financial year, the Board of Directors plans to propose a "
                                           "dividend to UBS Group AG shareholders of USD 0.90 per share"), "", None, ""),
    "F18": ("A", Q("UBS_2024-Q4_report.htm", 20, "around a 10% sequential decline in Personal & Corporate Banking"), "A",
            Q("UBS_2024-Q4_report.htm", 20, "around a 10% sequential decline in Personal & Corporate Banking"), "", None,
            ""),
    "F19": ("B", SPS, "B", SPS, "", None,
            "Same transaction forward-looking with another figure: the reports (2024-Q2 to the 2024 annual report) "
            "expect no material profit or loss on completion, the call a gain of around 100 million."),
    "F20": ("C", None, "C", None, "", None, "No hit on legacy funding costs; the figure hits are unrelated."),
    "F21": ("A", Q("UBS_2024_annual_report.htm", 59, "a UBS AG standalone CET1 capital ratio between 12.5% and 13.0%"), "A",
            Q("UBS_2024_annual_report.htm", 59, "a UBS AG standalone CET1 capital ratio between 12.5% and 13.0%"), "",
            None, "Only in the 2024 annual report (signed 17 March 2025), six weeks after the call."),
    "F22": ("C", None, "C", None, "C", Q("UBS_2024-Q4_pillar3.htm", 16, "decreased 10.9 percentage points to 188.4%"),
            "The 188% appears only as the actual quarterly average LCR; the direction 'below' is a bound, not a level."),
}


# Independent manual check (2026-09-24) of the three new UBS targets of class C with check_units.json and a separate search script;
# the hits were pre-sorted by machine per unit, the borderline cases were read manually plus a sample of the
# pre-sorting. Evidence in data/phase3g/roman_check/.
PRESORT = "Roman 2026-09-24: hits pre-sorted by machine per unit, only the borderline cases (and a sample of the pre-sorting) read by Roman. "
CHECKED = {
    "F11": PRESORT + "C confirmed; all hits are tables with actual values.",
    "F12": PRESORT + "B instead of C: 2023 and 2024 annual reports, 'Reduce RWA and LRD, freeing up capital for the UBS Group' pursues the same reduction without the 100 billion.",
    "F22": PRESORT + "C confirmed; hits are LCR tables and definitions.",
}
RE = "Roman, recheck 2026-09-26 (phase 3h tool, all hits shown, filtered on forward-looking words, hits pre-sorted by machine, borderline cases read by Roman; data/phase3h/roman_check/recheck_2026-09-26/): "
CHECKED["F11"] += " " + RE + "no figure, C unchanged."
CHECKED["F12"] += " " + RE + "no 100bn figure; the only forward-looking sentence on the same reduction is the NCL priority 'Reduce RWA and LRD ... around 5% (2024: below 5%) of Group RWA by the end of 2026' in the 2023 and 2024 annual reports, without an LRD figure; B unchanged."
CHECKED["F22"] += " " + RE + "only definitions, references and actual values, also in the 2023 and 2024 annual reports; C confirmed."


def norm(t):
    return re.sub(r"\s+", " ", str(t)).strip()


def cmd_classify():
    check_hash()
    u = pd.read_csv(OUT / "new_units.csv")
    assert set(u.unit) == set(CLS)
    pages = pd.read_csv(PHASE3B / "report_pages.csv", keep_default_na=False)
    report_of = dict(zip(pages.file, pages.quarter))
    pages = pages.set_index(["file", "page"])
    p3 = pd.read_csv(OUT / "pillar3_pages.csv", keep_default_na=False).set_index(["file", "page"])
    terms = pd.read_csv(OUT / "search_terms.csv")

    def found(q):
        f, p, text = q
        src = p3 if "pillar3" in f else pages
        return norm(text) in norm(src.loc[(f, p), "text"])

    rows = []
    for _, x in u.iterrows():
        c1, q1, ca, qa, cp, qb, comment = CLS[x.unit]
        for cls, q in [(c1, q1), (ca, qa)]:
            assert (cls in "AB") == (q is not None), (x.unit, "A and B need a quote, C none")
            if q:
                assert found(q), (x.unit, "quote not found", q[:2])
        if q1:
            assert report_of[q1[0]] in set(w1(x)), (x.unit, "W1 quote outside W1")
        if qb:
            assert found(qb), (x.unit, "borderline quote not found")
        rows.append(dict(unit=x.unit, bank=x.bank, type=x.type, quarter=x.quarter, stmt_id=x.stmt_id,
                         description=x.description, call_sentence=x.call_sentence, **{"class": c1},
                         quote=q1[2] if q1 else "", file=q1[0] if q1 else "", page=q1[1] if q1 else "",
                         class_all=ca, quote_all=qa[2] if qa else "", file_all=qa[0] if qa else "",
                         page_all=qa[1] if qa else "", class_pillar3=cp,
                         borderline_quote=qb[2] if qb else "", borderline_location=f"{qb[0]}, page {qb[1]}" if qb else "",
                         comment=comment, checked_by_roman=CHECKED.get(x.unit, ""),
                         search_terms=" | ".join(f"[{t.group}] {t.term}" for t in terms[terms.unit == x.unit].itertuples())))
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "new_units_read.csv", index=False)

    # comparison basis: genuine UBS targets set after the acquisition (phase 3d) plus the new targets
    d3 = pd.read_csv(DATA / "phase3d" / "counterparts_read.csv", keep_default_na=False)
    old = d3[(d3.bank == "UBS") & (d3.genuine == "yes") & (d3.type == "target") & (d3.pre_acquisition != "yes")]
    new = out[(out.bank == "UBS") & (out.type == "target")]
    basis = []
    for window, col in [("W1", "class"), ("ALL", "class_all")]:
        for name, b in [("phase 3d", old), ("phase 3g added", new), ("phase 3d + 3g", pd.concat([old, new]))]:
            n = b[col].value_counts()
            basis.append(dict(window=window, basis=name, n=len(b), A=int(n.get("A", 0)), B=int(n.get("B", 0)),
                              C=int(n.get("C", 0))))
    basis = pd.DataFrame(basis)
    basis.to_csv(OUT / "basis.csv", index=False)
    print(out[["unit", "type", "class", "class_all", "class_pillar3", "file", "page"]].to_string(index=False))
    print(basis.to_string(index=False))


def cmd_checkfiles():
    """Check files for the independent check of the new UBS targets of class C, in the format of phase 3f: all UBS quarterly and
    annual reports (window ALL) and the available Pillar 3 reports of the unit's window; the 2024-Q2 Pillar 3 report
    in a file of its own. Terms: each phrase alone, each figure with the unit's first phrase nearby."""
    r = pd.read_csv(OUT / "new_units_read.csv", keep_default_na=False)
    c = r[(r.bank == "UBS") & (r.type == "target") & (r["class"] == "C") & (r.class_all == "C")]
    terms = pd.read_csv(OUT / "search_terms.csv")
    reports = sorted(pd.read_csv(PHASE3B / "report_pages.csv", usecols=["bank", "file"]).query("bank == 'UBS'").file.unique())
    cu, cu2 = {}, {}
    for _, x in c.iterrows():
        t = terms[terms.unit == x.unit]
        phrases, figures = t[t.group == 2].term.tolist(), t[t.group == 3].term.tolist()
        tt = [[p, None] for p in phrases] + [[f, phrases[0]] for f in figures]
        cu[x.unit] = {"files": reports + [f"UBS_{q}_pillar3.htm" for q in pillar3_window(x.quarter)], "terms": tt}
        if x.quarter <= "2024-Q2":
            cu2[x.unit] = {"files": ["UBS_2024-Q2_pillar3.htm"], "terms": tt}
    (OUT / "check_units.json").write_text(json.dumps(cu, indent=2))
    (OUT / "check_units_2024q2.json").write_text(json.dumps(cu2, indent=2))
    print({u: len(v["files"]) for u, v in cu.items()}, list(cu2))


def cmd_spotcheck():
    """Compare the blind labels of the ten spot-check sentences with the reading of S (plan amendment 2)."""
    sp = pd.read_csv(DATA / "labelling" / "phase3g_spotcheck.csv", keep_default_na=False)
    key = pd.read_csv(OUT / "spotcheck_key.csv")
    mine = pd.read_csv(OUT / "set_s_read.csv", keep_default_na=False)[["stmt_id", "genuine", "duplicate_of", "comment"]]
    m = sp.merge(key, on="item_id").merge(mine, on="stmt_id", suffixes=("_roman", "_mine"))
    assert len(m) == len(sp) == 10 and m.genuine_roman.isin(["yes", "no"]).all()
    m["agree_genuine"] = m.genuine_roman == m.genuine_mine
    m[["item_id", "stmt_id", "call", "quarter", "sentence", "genuine_roman", "genuine_mine", "agree_genuine",
       "duplicate_of_roman", "duplicate_of_mine", "notes", "comment"]].to_csv(OUT / "spotcheck_comparison.csv", index=False)
    po = m.agree_genuine.mean()
    pr, pm = (m.genuine_roman == "yes").mean(), (m.genuine_mine == "yes").mean()
    pe = pr * pm + (1 - pr) * (1 - pm)
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    out = dict(n=len(m), agree=int(m.agree_genuine.sum()), observed_agreement=po, expected_agreement=pe,
               cohen_kappa=kappa, roman_yes=int((m.genuine_roman == "yes").sum()),
               mine_yes=int((m.genuine_mine == "yes").sum()),
               duplicate_of_filled_by_roman=int((m.duplicate_of_roman != "").sum()))
    (OUT / "spotcheck_agreement.json").write_text(json.dumps(out, indent=2))
    print(out)
    print(m[~m.agree_genuine][["item_id", "stmt_id", "genuine_roman", "genuine_mine", "comment"]].to_string(index=False))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "terms":
        cmd_terms()
    elif cmd == "search":
        cmd_search()
    elif cmd == "pillar3":
        cmd_pillar3(sys.argv[2:])
    elif cmd == "classify":
        cmd_classify()
    elif cmd == "checkfiles":
        cmd_checkfiles()
    elif cmd == "spotcheck":
        cmd_spotcheck()
