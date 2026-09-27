import hashlib
import json
import re

import pandas as pd
import pytest

import phase3f_pillar3 as p3f

OUT = p3f.OUT
pytestmark = pytest.mark.skipif(not (OUT / "pillar3_read.csv").exists(), reason="phase 3f not run")


def test_check_files_list_window_files_only():
    cu = json.loads((OUT / "check_units.json").read_text())
    cu2 = json.loads((OUT / "check_units_2024q2.json").read_text())
    for unit, v in cu.items():
        assert v["files"] == [p3f.pfile(q) for q in p3f.window(unit)]
        assert all((p3f.REPORTS / f).exists() for f in v["files"])
        assert all(len(t) == 2 for t in v["terms"])
    for unit, v in cu2.items():
        assert v["files"] == ["UBS_2024-Q2_pillar3.htm"]
    assert set(cu2) == {u for u in p3f.UNITS if p3f.FIRST_QUARTER[u] <= "2024-Q2"}


def test_round1_terms_unchanged():
    log = json.loads((p3f.P3D / "run_log.json").read_text())
    t = pd.read_csv(p3f.P3D / "search_terms.csv")
    assert hashlib.sha256(t[t["round"] == 1].to_csv(index=False).encode()).hexdigest() == log["round1_sha256"]


def test_quotes_found_and_reports_unchanged():
    r = pd.read_csv(OUT / "pillar3_read.csv", keep_default_na=False)
    pages = pd.read_csv(OUT / "pillar3_pages.csv", keep_default_na=False).set_index(["file", "page"])
    norm = lambda s: re.sub(r"\s+", " ", str(s)).strip()  # noqa: E731
    for _, x in r[r.borderline_quote != ""].iterrows():
        f, p = x.borderline_location.split(", page ")
        assert norm(x.borderline_quote) in norm(pages.loc[(f, int(p)), "text"])
    for _, x in r.iterrows():
        assert (x.class_pillar3 == "B") == (x.quote_pillar3 != "")
        if x.quote_pillar3:
            f, p = x.quote_location.split(", page ")
            assert norm(x.quote_pillar3) in norm(pages.loc[(f, int(p)), "text"])
    log = json.loads((OUT / "run_log.json").read_text())
    assert {f: p3f.file_hash(p3f.REPORTS / f) for f in log["report_hashes"]} == log["report_hashes"]
