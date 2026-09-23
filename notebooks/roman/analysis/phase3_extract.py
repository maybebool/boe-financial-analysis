"""Phase 3 extraction: commitment candidates, metric groups, values and horizons.

Run from the repository root: python notebooks/roman/analysis/phase3_extract.py
Writes statements.csv and candidates.csv to notebooks/roman/data/phase3/. Rules as in plans/phase_3.md;
the regular expressions below were fixed before the first run and amended once (see the plan amendment).
"""
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman"))
from config import RELEASE_DIR  # noqa: E402

OUT = ROOT / "notebooks" / "roman" / "data" / "phase3"
KEY = ["bank", "quarter", "call_type", "position_in_call", "sentence_number"]

# (a) quantity: a number with a unit, or a currency amount
QTY_RE = re.compile(
    r"(?P<cur>[$€£]|\bUSD\s?|\bCHF\s?|\bEUR\s?)?(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s?"
    r"(?P<unit>%|percent\b|per cent\b|bps\b|basis points?\b|billion\b|bn\b|million\b|mn\b|trillion\b|tn\b)?", re.I)
# (b) horizon
YEAR_RE = re.compile(r"\b(20[2-3]\d)\b")
QUARTER_RE = re.compile(r"\b(first|second|third|fourth|1st|2nd|3rd|4th)\s+quarter(?:\s+of)?\s+(20[2-3]\d)\b|"
                        r"\b([1-4])Q\s?'?(\d{2})\b", re.I)
MID_RE = re.compile(r"\bmid[- ](20[2-3]\d)\b", re.I)
STARTING_RE = re.compile(r"\b(from|since|starting|beginning in)\s+(the\s+)?(start of\s+)?$", re.I)
RELATIVE = {
    "next_year": re.compile(r"\bnext year\b", re.I),
    "this_year": re.compile(r"\b(this year|full[- ]year|rest of the year|remainder of the year|second half|"
                            r"back half|year[- ]end|end of (the|this) year)\b", re.I),
    "next_quarter": re.compile(r"\bnext quarter\b", re.I),
    "medium_term": re.compile(r"\b(medium[- ]term|over the next (few|two|three|four|five|\d) years)\b", re.I),
    "run_rate": re.compile(r"\b(run[- ]rate|exit rate|exit[- ]year)\b", re.I),
}
# (c) forward-looking verb or noun
FORWARD_RE = re.compile(r"\b(target(s|ed|ing)?|aim(s|ing)?|ambitions?|expect(s|ed|ing|ation|ations)?|"
                        r"plan(s|ned|ning)?|commit(s|ted|ment|ments)?|deliver(s|ed|ing)?|achiev(e|es|ed|ing)|"
                        r"reach(es|ed|ing)?|guidance|guid(e|es|ed|ing)|intend(s|ed)?|on track|remain(s|ed|ing)?)\b",
                        re.I)

# metric dictionary, in priority order: (group, type, pattern)
METRICS = [
    ("cost_saves", "target", r"cost sav|gross cost|run-rate saves|cost reduction|\bsavings\b|\bsaves\b"),
    ("capital", "target", r"\bcet ?1\b|common equity tier 1|capital ratio|leverage ratio|capital target|\btlac\b"),
    ("non_core", "target", r"non-core|\bncl\b|run-down|rundown|wind-down|run-off|runoff"),
    ("distributions", "target", r"buy ?back|repurchase|dividend|capital return|distribution"),
    ("returns", "target", r"return on cet ?1|\brocet ?1|\brotce\b|return on tangible|through[- ]the[- ]cycle|"
                          r"cost/income|cost[- ]income ratio|cost-to-income"),
    ("integration", "target", r"integration|migrat|legal entit|merger of|decommission|systems conversion|"
                              r"substantially complete"),
    ("headcount", "target", r"headcount|\bftes?\b|\bemployees\b|\bstaff\b"),
    ("net_new_assets", "target", r"net new assets|net new money|\bnna\b|\bnnm\b|invested assets"),
    ("nii", "guidance", r"net interest income|\bnii\b"),
    ("expenses", "guidance", r"expense|\bopex\b|operating costs?"),
    ("loans", "guidance", r"loan growth|card loans|\bloans\b"),
    ("credit", "guidance", r"charge[- ]offs?|\bncos?\b|credit costs?|allowance|reserve build"),
    ("tax", "guidance", r"tax rate"),
    ("revenue", "guidance", r"revenues?|\bfees\b"),
]
METRIC_RE = [(g, t, re.compile(p, re.I)) for g, t, p in METRICS]

ACHIEVED_RE = re.compile(r"\b(achieved|reached|completed|delivered|exceeded|surpassed|accomplished)\b", re.I)
PROGRESS_RE = re.compile(r"\b(towards?|on track|progress)\b", re.I)
BRACKET_RE = re.compile(r"\[[^\]]*\]")


def clean(t):
    return re.sub(r"\s+", " ", BRACKET_RE.sub(" ", str(t))).strip()


def quantities(text):
    """All quantities with a unit or currency: list of (value, unit_class)."""
    out = []
    for m in QTY_RE.finditer(text):
        cur, num, unit = m.group("cur"), m.group("num"), (m.group("unit") or "").lower()
        if not cur and not unit:
            continue
        v = float(num.replace(",", ""))
        if unit in ("%", "percent", "per cent"):
            out.append((v, "pct"))
        elif unit.startswith("bps") or unit.startswith("basis point"):
            out.append((v, "bps"))
        elif unit in ("billion", "bn"):
            out.append((v, "amount_bn"))
        elif unit in ("million", "mn"):
            out.append((v / 1000, "amount_bn"))
        elif unit in ("trillion", "tn"):
            out.append((v * 1000, "amount_bn"))
        else:
            out.append((v, "currency"))
    return out


def quarter_end(y, q):
    return date(y, 3 * q, [31, 30, 30, 31][q - 1])


def horizons(text, call_date):
    """Future horizons in the text relative to the call date: list of (date or None, label)."""
    out = []
    for m in QUARTER_RE.finditer(text):
        if m.group(1):
            q = {"first": 1, "1st": 1, "second": 2, "2nd": 2, "third": 3, "3rd": 3, "fourth": 4, "4th": 4}[
                m.group(1).lower()]
            y = int(m.group(2))
        else:
            q, y = int(m.group(3)), 2000 + int(m.group(4))
        d = quarter_end(y, q)
        if d >= call_date:
            out.append((d, "quarter"))
    for m in MID_RE.finditer(text):
        d = date(int(m.group(1)), 6, 30)
        if d >= call_date:
            out.append((d, "mid_year"))
    for m in YEAR_RE.finditer(text):
        y = int(m.group(1))
        if STARTING_RE.search(text[max(0, m.start() - 25):m.start()]):
            continue  # a starting point, not a horizon
        if y >= call_date.year:
            out.append((date(y, 12, 31), "year"))
    for label, rx in RELATIVE.items():
        if rx.search(text):
            if label == "next_year":
                out.append((date(call_date.year + 1, 12, 31), label))
            elif label == "this_year":
                out.append((date(call_date.year, 12, 31), label))
            elif label == "next_quarter":
                q = (call_date.month - 1) // 3 + 1
                y, q = (call_date.year + 1, 1) if q == 4 else (call_date.year, q + 1)
                out.append((quarter_end(y, q), label))
            else:
                out.append((None, label))
    return out


def first_horizon(text, context, call_date):
    """Earliest dated horizon in the sentence, else in the context; else an undated label."""
    for t in (text, context):
        h = horizons(t, call_date)
        dated = sorted(d for d, _ in h if d is not None)
        if dated:
            return dated[0], "dated"
        if h:
            return None, h[0][1]
    return None, None


def metric_of(text, context=""):
    for t in (text, context):
        for g, typ, rx in METRIC_RE:
            if rx.search(t):
                return g, typ
    return "other", "other"


def is_candidate(text, call_date):
    return bool(quantities(text)) and bool(horizons(text, call_date)) and bool(FORWARD_RE.search(text))


def load_statements():
    """Management sentences of earnings calls and the event call, with 'ex.' splits joined and context."""
    s = pd.read_csv(RELEASE_DIR / "all_sentences.csv")
    s = s[s.speaker_role == "management"].sort_values(KEY).reset_index(drop=True)
    s["text"] = s.sentence.map(clean)
    rows = []
    for _, g in s.groupby(["bank", "quarter", "call_type", "position_in_call"], sort=False):
        recs = g.to_dict("records")
        i = 0
        while i < len(recs):
            r = dict(recs[i]); r["joined_with_next"] = False
            while r["text"].endswith(" ex.") and i + 1 < len(recs):
                i += 1
                r["text"] = r["text"] + " " + recs[i]["text"]; r["joined_with_next"] = True
            rows.append(r); i += 1
    d = pd.DataFrame(rows)
    grp = d.groupby(["bank", "quarter", "call_type", "position_in_call"], sort=False).text
    d["context"] = (grp.shift(1).fillna("") + " " + grp.shift(-1).fillna("")).str.strip()
    d["call_date_d"] = pd.to_datetime(d.call_date).dt.date
    d["origin_only"] = d.call_type == "event"
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = load_statements()
    d["candidate"] = [is_candidate(t, cd) for t, cd in zip(d.text, d.call_date_d)]
    met = [metric_of(t, c) for t, c in zip(d.text, d.context)]
    d["metric"], d["type"] = zip(*met)
    vals = [quantities(t) for t in d.text]
    d["value"] = [v[0][0] if v else np.nan for v in vals]
    d["unit"] = [v[0][1] if v else None for v in vals]
    hz = [first_horizon(t, c, cd) for t, c, cd in zip(d.text, d.context, d.call_date_d)]
    d["horizon"] = [h[0] for h in hz]
    d["horizon_label"] = [h[1] for h in hz]
    d["has_quantity"] = [bool(v) for v in vals]
    d["has_horizon"] = [bool(horizons(t, cd)) for t, cd in zip(d.text, d.call_date_d)]
    d["stmt_id"] = np.arange(len(d))
    cols = ["stmt_id"] + KEY + ["call_date", "section", "speaker_name", "origin_only", "joined_with_next", "text",
                                "context", "candidate", "metric", "type", "value", "unit", "horizon", "horizon_label",
                                "has_quantity", "has_horizon"]
    d[cols].to_csv(OUT / "statements.csv", index=False)
    c = d[d.candidate]
    c[cols].to_csv(OUT / "candidates.csv", index=False)
    print("joined ex.:", int(d.joined_with_next.sum()))
    print(c.groupby(["bank", "call_type", "type"]).size())


if __name__ == "__main__":
    main()
