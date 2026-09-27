import hashlib
import json
import re

import pandas as pd
import pytest

import phase3g_fls as g
import phase3g_read as gr

OUT = g.OUT
pytestmark = pytest.mark.skipif(not (OUT / "new_units_read.csv").exists(), reason="phase 3g not run")


def test_basis_matches_phase3_statements():
    sc = pd.read_csv(OUT / "scored.csv")
    st = pd.read_csv(g.DATA / "phase3" / "statements.csv")
    sel = ((st.bank == "UBS") & (st.call_type == "earnings") & (st.quarter >= "2023-Q2")) | \
          ((st.bank == "JPM") & (st.call_type == "event"))
    assert sorted(sc.stmt_id) == sorted(st[sel].stmt_id)
    assert sc.groupby("call").size().to_dict() == {"JPM event": 182, "UBS earnings": 3177}


def test_one_finbert_label_per_sentence():
    sc = pd.read_csv(OUT / "scored.csv")
    assert sc.stmt_id.is_unique
    assert sc.finbert.isin(["Not FLS", "Non-specific FLS", "Specific FLS"]).all()


def test_set_s_definition():
    sc = pd.read_csv(OUT / "scored.csv")
    s = pd.read_csv(OUT / "set_s.csv")
    expect = sc[(sc.finbert == "Specific FLS") & sc.has_number & ~sc.candidate]
    assert sorted(s.stmt_id) == sorted(expect.stmt_id)
    read = pd.read_csv(OUT / "set_s_read.csv", keep_default_na=False)
    assert sorted(read.stmt_id) == sorted(s.stmt_id)
    assert read.genuine.isin(["yes", "no"]).all()
    new = read[read.duplicate_of == "new"]
    assert (new.genuine == "yes").all() and new.new_unit.str.fullmatch(r"F\d\d").all()


def test_spotcheck_is_blind():
    sp = pd.read_csv(g.LAB / "phase3g_spotcheck.csv", keep_default_na=False)
    assert len(sp) == 10
    assert not {"finbert", "roberta_fls", "stmt_id"} & set(sp.columns)
    key = pd.read_csv(OUT / "spotcheck_key.csv")
    assert set(key.stmt_id) <= set(pd.read_csv(OUT / "set_s.csv").stmt_id)


def test_quotes_found_on_their_pages():
    r = pd.read_csv(OUT / "new_units_read.csv", keep_default_na=False)
    pages = pd.read_csv(gr.PHASE3B / "report_pages.csv", keep_default_na=False).set_index(["file", "page"])
    p3 = pd.read_csv(OUT / "pillar3_pages.csv", keep_default_na=False).set_index(["file", "page"])
    norm = lambda s: re.sub(r"\s+", " ", str(s)).strip()  # noqa: E731
    n = 0
    for _, x in r.iterrows():
        for q, f, p in [(x.quote, x.file, x.page), (x.quote_all, x.file_all, x.page_all)]:
            if q:
                assert norm(q) in norm(pages.loc[(f, int(p)), "text"]), (x.unit, f, p)
                n += 1
        if x.borderline_quote:
            f, p = x.borderline_location.split(", page ")
            src = p3 if "pillar3" in f else pages
            assert norm(x.borderline_quote) in norm(src.loc[(f, int(p)), "text"])
    assert n > 0
    assert set(r[r["class"].isin(["A", "B"])].unit) == set(r[r.quote != ""].unit)


def test_search_terms_unchanged_after_hash():
    log = json.loads((OUT / "run_log.json").read_text())
    assert hashlib.sha256((OUT / "search_terms.csv").read_bytes()).hexdigest() == log["search_terms_sha256"]
    assert log["terms_written"] < log["search_started"]
