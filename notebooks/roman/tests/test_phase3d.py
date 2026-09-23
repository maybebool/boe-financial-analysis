import hashlib
import json
import re

import pandas as pd
import pytest

import phase3b_reports as p3b
import phase3d_read as p3d

OUT = p3d.OUT
pytestmark = pytest.mark.skipif(not (OUT / "counterparts_read.csv").exists(), reason="phase 3d not run")


def test_quotes_found_on_stated_page():
    df = pd.read_csv(OUT / "counterparts_read.csv", keep_default_na=False)
    pages = pd.read_csv(p3d.PHASE3B / "report_pages.csv", keep_default_na=False).set_index(["file", "page"])
    for prefix in ["", "_all"]:
        q = df[df["quote_report" if prefix == "" else "quote_all"] != ""]
        for _, r in q.iterrows():
            text = r["quote_report" if prefix == "" else "quote_all"]
            assert p3d.norm(text) in p3d.norm(pages.loc[(r["file" + prefix], int(r["page" + prefix])), "text"])


def test_c_rows_list_search_terms():
    df = pd.read_csv(OUT / "counterparts_read.csv", keep_default_na=False)
    for _, r in df[(df.genuine == "yes") & (df["class"] == "C")].iterrows():
        groups = set(re.findall(r"\[(\d)", r.search_terms))
        assert {"2", "3"} <= groups
        if r.metric != "other":
            assert "1" in groups


def test_round1_terms_unchanged_and_reports_unchanged():
    log = json.loads((OUT / "run_log.json").read_text())
    t = pd.read_csv(OUT / "search_terms.csv")
    r1 = t[t["round"] == 1].to_csv(index=False).encode()
    assert hashlib.sha256(r1).hexdigest() == log["round1_sha256"]
    assert len(t[t["round"] == 1]) == log["round1_rows"]
    assert p3b.file_hashes() == log["report_hashes"]


def test_sort_order_ubs_target_c_first():
    df = pd.read_csv(OUT / "counterparts_read.csv", keep_default_na=False)
    first = (df.bank == "UBS") & (df["type"] == "target") & (df.genuine == "yes") & (df["class"] == "C")
    n = int(first.sum())
    assert first.iloc[:n].all() and not first.iloc[n:].any()
