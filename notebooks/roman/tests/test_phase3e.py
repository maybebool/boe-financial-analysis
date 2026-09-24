import json
import re

import pandas as pd
import pytest

import phase3e_channel as p3e

OUT = p3e.OUT
pytestmark = pytest.mark.skipif(not (OUT / "call_first.csv").exists(), reason="phase 3e not run")
REPORTS = p3e.DATA / "reports"


def test_mentions_are_ubs_management_earnings_statements():
    m = pd.read_csv(OUT / "mentions.csv", keep_default_na=False)
    st = pd.read_csv(p3e.DATA / "phase3" / "statements.csv").set_index("stmt_id")
    s = st.loc[m.stmt_id].reset_index()
    assert (s.bank == "UBS").all() and (s.call_type == "earnings").all()
    from config import RELEASE_DIR
    rel = pd.read_csv(RELEASE_DIR / "all_sentences.csv").set_index(p3e.KEY)
    roles = rel.loc[list(map(tuple, s[p3e.KEY].values)), "speaker_role"]
    assert (roles == "management").all()


def test_qa_mentions_have_a_question_from_the_same_call():
    for f in ["mentions.csv", "first_mentions.csv"]:
        m = pd.read_csv(OUT / f, keep_default_na=False)
        qa = m[m.section == "qa"]
        assert (qa.analyst_question != "").all()
        assert qa.classification.isin(["qa, asked", "qa, unprompted", "qa, outside a pair"]).all()


def test_check_units_files_span_call_to_first_report():
    cu = json.loads((OUT / "check_units.json").read_text())
    cf = pd.read_csv(OUT / "call_first.csv").set_index("unit")
    assert set(cu) == set(cf.index)
    label = lambda f: re.match(r"UBS_(.+)_report\.htm", f).group(1).replace("_annual", " annual report")  # noqa: E731
    for unit, v in cu.items():
        assert all((REPORTS / f).exists() for f in v["files"])
        assert label(v["files"][0]) == cf.loc[unit, "call_quarter"]
        assert label(v["files"][-1]) == cf.loc[unit, "first_report"]
        assert all(len(t) == 2 for t in v["terms"])


def test_report_quotes_found_on_page():
    cf = pd.read_csv(OUT / "call_first.csv")
    pages = pd.read_csv(p3e.DATA / "phase3b" / "report_pages.csv", keep_default_na=False).set_index(["file", "page"])
    norm = lambda s: re.sub(r"\s+", " ", str(s)).strip()  # noqa: E731
    for _, r in cf.iterrows():
        f, p = r.report_location.split(", page ")
        assert norm(r.report_quote) in norm(pages.loc[(f, int(p)), "text"])
