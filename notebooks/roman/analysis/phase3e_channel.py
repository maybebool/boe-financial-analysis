"""Phase 3e, step 2: disclosure channel of the call-only figures, and units where the call is earlier than the reports.

Run from the repository root after phase3e_terms.py: python notebooks/roman/analysis/phase3e_channel.py
Rules as in plans/phase_3e.md. The judgement between "qa, asked" and "qa, unprompted" was made by reading the
analyst question, which is written out verbatim next to every Q&A mention.
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase3b_reports import file_hashes  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3e"
KEY = ["bank", "quarter", "call_type", "position_in_call", "sentence_number"]
ORDER = ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4", "2023 annual report", "2024-Q1", "2024-Q2", "2024-Q3",
         "2024-Q4", "2024 annual report"]

# figure and topic patterns of the plan (Part 1)
PATTERNS = {
    "T16": (r"\b14 ?(?:billion|bn)\b", r"operational risk"),
    "T25": (r"\b6 ?(?:billion|bn)\b", r"capital release|releas|free up|freeing"),
    "T27": (r"\b40 ?(?:billion|bn)\b", r"risk-weighted|\bRWA\b|credit and market risk"),
    "T32": (r"16\.7|180 (?:basis points|bps)", r"going concern|going-concern|capital requirement"),
    "T33": (r"(?<![\d.])2 ?(?:billion|bn)\b", r"\bAT1\b|additional tier 1"),
    "T68": (r"\b90 ?(?:billion|bn)\b", r"HoldCo|holding company"),
    "C2": (r"\b1[34] ?(?:billion|bn)\b", r"integration-related|integration related|costs? to achieve"),
}
# reading result for retrieved candidates that are not a mention of the unit's commitment (none were found)
NOT_THE_COMMITMENT = {}
# reading of the analyst question for every Q&A statement classified here: stmt_id -> (class, reason)
QA_READING = {
    4064: ("qa, asked", "Question 2 asks about the profit trajectory from 2Q to 3Q and cites '750 million of savings'."),
    4065: ("qa, asked", "Same answer to the same question as statement 4064."),
    6601: ("qa, asked", "The analyst asks about 'an extra 1 billion in cumulative integration cost by year end 2026'."),
}
CONTEXT = [  # analyst statements that bear on a unit without stating its figure pattern (context, not mentions)
    ("C2", "UBS", "2023-Q2", "Andrew Coombs",
     "So, can we assume restructuring charges of the magnitude of 12.5?"),
]


# Independent manual check of part 2 (2026-09-24, evidence in data/phase3e/roman_check/) and the strength of each case
STRENGTH = {
    "T10": ("confirmed by Roman", "No guidance in the 2023-Q2 and 2023-Q3 reports; 2023-Q4: 'We confirm our capital guidance and aim to maintain ... around 14%'."),
    "T36": ("confirmed by Roman", "No 40% in the 2023-Q4 report and the 2023 annual report, only 'significantly higher than the Group's structural rate of 23%'; 2024-Q1: 'still expected to be around 40% by the end of 2024'."),
    "T17": ("weak, checked by Roman", "The 2023-Q4 report already gives the Basel III effect as USD 25bn, an equivalent quantity in another unit. Recheck 2026-09-26 (phase 3h tool, all hits shown, filtered on forward-looking words, hits pre-sorted by machine, borderline cases read by Roman; data/phase3h/roman_check/recheck_2026-09-26/): the hits not shown in the first check (2023 annual report) contain the USD 25bn estimate, not the 5%; the first report with 5% remains 2024-Q2."),
    "T34": ("weak, not checked", "Timing artefact: the first report is the annual report, which follows the fourth-quarter call by construction."),
    "T55": ("weak, not checked", "Wording: 'around 5%' is in the reports from 2023-Q4; only 'below 5%' appears later."),
}
DATE_RE = re.compile(r"Date:\s*([A-Z][a-z]+ \d{1,2}, \d{4})")


def report_date(file):
    """Signature date of the filing ('Date: Month D, YYYY'), the last one in the file."""
    import html
    raw = (DATA / "reports" / file).read_text(encoding="utf-8", errors="replace")
    text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)))
    return pd.Timestamp(DATE_RE.findall(text)[-1])


def question_of(pairs, questions, r):
    k = (r.bank, r.quarter, r.call_type, r.position_in_call, r.sentence_number)
    pid = pairs.get(k)
    if pid is None:
        return None, "", ""
    q = questions[questions.pair_id == pid].sort_values(KEY)
    return pid, q.speaker_name.iloc[0], " ".join(q.text.fillna(""))


def classify(r, pid):
    if r.section == "prepared":
        return "prepared", ""
    if pid is None:
        return "qa, outside a pair", ""
    return QA_READING[r.stmt_id]


def main():
    before = file_hashes()
    st = pd.read_csv(DATA / "phase3" / "statements.csv")
    st["text"] = st.text.fillna("")
    ubs = st[(st.bank == "UBS") & (st.call_type == "earnings")]
    ans = pd.read_csv(DATA / "phase1" / "answer_sentences.csv")
    pairs = dict(zip(map(tuple, ans[KEY].values), ans.pair_id))
    questions = pd.read_csv(DATA / "phase1" / "question_sentences.csv")

    # Part 1a: every mention of the call-only figures and of the C2 total
    rows = []
    for unit, (fig, topic) in PATTERNS.items():
        hit = ubs[ubs.text.str.contains(fig, case=False) & ubs.text.str.contains(topic, case=False)]
        for _, r in hit.iterrows():
            if r.stmt_id in NOT_THE_COMMITMENT:
                continue
            if unit == "C2" and re.search(r"gross (cost )?sav", r.text, re.I) and not re.search(
                    r"integration-related|costs? to achieve", r.text, re.I):
                continue  # the 13bn savings target shares the number
            pid, analyst, q = question_of(pairs, questions, r)
            cls, reason = classify(r, pid)
            rows.append(dict(unit=unit, stmt_id=r.stmt_id, quarter=r.quarter, section=r.section,
                             speaker=r.speaker_name, statement=r.text, classification=cls, reason=reason,
                             analyst=analyst, analyst_question=q if r.section == "qa" else ""))
    mentions = pd.DataFrame(rows)
    mentions.to_csv(OUT / "mentions.csv", index=False)
    pd.DataFrame(CONTEXT, columns=["unit", "bank", "quarter", "analyst", "sentence"]).to_csv(
        OUT / "analyst_context.csv", index=False)

    # Part 1b: first mention of all 31 genuine UBS targets set after the acquisition
    d = pd.read_csv(DATA / "phase3d" / "counterparts_read.csv", keep_default_na=False)
    t = d[(d.bank == "UBS") & (d["type"] == "target") & (d.genuine == "yes") & (d.pre_acquisition != "yes")]
    assert len(t) == 31
    fr = []
    for _, u in t.iterrows():
        r = st.set_index("stmt_id").loc[u.stmt_id]
        r = r.copy(); r["stmt_id"] = u.stmt_id
        pid, analyst, q = question_of(pairs, questions, r)
        cls, reason = classify(r, pid)
        fr.append(dict(unit=u.unit, w1_class=u["class"], all_class=u.class_all, quarter=r.quarter,
                       section=r.section, speaker=r.speaker_name, classification=cls, reason=reason,
                       statement=r.text, analyst=analyst, analyst_question=q if r.section == "qa" else ""))
    first = pd.DataFrame(fr)
    first.to_csv(OUT / "first_mentions.csv", index=False)
    counts = pd.concat([
        mentions.groupby(["unit", "classification"]).size().rename("mentions").reset_index()
        .assign(table="call-only figures and C2 total, all mentions"),
        first.groupby(["w1_class", "classification"]).size().rename("mentions").reset_index()
        .rename(columns={"w1_class": "unit"}).assign(table="first mention of the 31 UBS targets, by W1 class")])
    counts.to_csv(OUT / "counts.csv", index=False)

    # Part 2: units whose figure is first in the call and only later in a report
    g = d[(d.bank == "UBS") & (d.genuine == "yes") & (d.class_all == "A")].copy()
    g["call_quarter"] = g.origin.str[:7]
    g["gap"] = [ORDER.index(f) - ORDER.index(o) for f, o in zip(g.first_report_all, g.call_quarter)]
    g = g[g.gap > 0]
    pages = pd.read_csv(DATA / "phase3b" / "report_pages.csv", keep_default_na=False).set_index(["file", "page"])
    norm = lambda s: re.sub(r"\s+", " ", str(s)).strip()  # noqa: E731
    out = []
    for _, u in g.iterrows():
        assert norm(u.quote_all) in norm(pages.loc[(u.file_all, int(u.page_all)), "text"]), u.unit
        r = st.set_index("stmt_id").loc[u.stmt_id]
        out.append(dict(unit=u.unit, type=u["type"], call_quarter=u.call_quarter, first_report=u.first_report_all,
                        gap_steps=u.gap, annual_report_after_q4_call=u.first_report_all.endswith("annual report"),
                        call_quote=u.call_sentence,
                        call_location=f"{r.quarter} call, {r.section}, {r.speaker_name}, statement {r.position_in_call}",
                        report_quote=u.quote_all, report_location=f"{u.file_all}, page {u.page_all}",
                        comment=u.comment))
    call_first = pd.DataFrame(out).sort_values(["call_quarter", "unit"])
    call_dates = st[st.bank == "UBS"].groupby("quarter").call_date.first()
    # quarterly reports are signed on the day of the call; checked here for every UBS quarter
    for q in [x for x in ORDER if "annual" not in x]:
        assert report_date(f"UBS_{q}_report.htm") == pd.Timestamp(call_dates[q]), q
    call_first["call_date"] = pd.to_datetime(call_first.call_quarter.map(call_dates))
    call_first["report_date"] = [report_date(f.split(", page")[0]) for f in call_first.report_location]
    call_first["lead_days"] = (call_first.report_date - call_first.call_date).dt.days
    call_first["lead_months"] = (call_first.lead_days / 30.44).round(1)
    call_first["strength"] = call_first.unit.map(lambda u: STRENGTH[u][0])
    call_first["strength_note"] = call_first.unit.map(lambda u: STRENGTH[u][1])
    call_first.to_csv(OUT / "call_first.csv", index=False)
    assert file_hashes() == before, "report files changed"
    print(mentions[["unit", "stmt_id", "quarter", "section", "speaker", "classification"]].to_string(index=False))
    print(first.groupby(["w1_class", "classification"]).size())
    print(call_first[["unit", "call_date", "first_report", "report_date", "lead_months", "strength"]].to_string(index=False))


if __name__ == "__main__":
    main()
