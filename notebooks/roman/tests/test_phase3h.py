import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

import phase3h_search as s
import phase3h_terms as t
import report_text as rt

OUT = t.OUT
pytestmark = pytest.mark.skipif(not (OUT / "check_units_b.json").exists(), reason="phase 3h not run")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def manifest():
    return pd.read_csv(OUT / "manifest.csv", keep_default_na=False)


def test_manifest_hashes_match_raw_files_and_export():
    m = manifest()
    assert list(m.columns[:len(rt.MANIFEST_COLUMNS)]) == rt.MANIFEST_COLUMNS and len(m) == 15
    for r in m.itertuples():
        assert sha(t.DATA / r.folder / r.file) == r.raw_sha256
        assert sha(OUT / "text" / f"{Path(r.file).stem}.txt") == r.text_sha256
    assert (m[m.folder == "reports_2025_2026"].download_date == "2026-09-26").all()


def test_a_terms_equal_phase3d_and_3g_terms():
    a = pd.read_csv(OUT / "a_terms.csv", keep_default_na=False)
    pd.testing.assert_frame_equal(a.astype(str), t.a_terms().astype(str))
    assert set(a.unit) == set(t.UNITS)


def test_term_files_unchanged_after_hash():
    log = json.loads((OUT / "run_log.json").read_text())
    for f, key in [("a_terms.csv", "a_terms_sha256"), ("outcome_terms.csv", "outcome_terms_sha256"),
                   ("check_units_a.json", "check_units_a_sha256"), ("check_units_b.json", "check_units_b_sha256")]:
        assert sha(OUT / f) == log[key], f
    b = pd.read_csv(OUT / "outcome_terms.csv", keep_default_na=False)
    pd.testing.assert_frame_equal(b, t.b_terms())


def test_pipeline_hits_equal_recount_on_export():
    sys.dont_write_bytecode = True
    tmp = Path(tempfile.mkdtemp()) / "check_terms_v2.py"
    shutil.copyfile(t.TOOL, tmp)
    spec = importlib.util.spec_from_file_location("check_terms_v2", tmp)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    text = {}
    for name in ("check_units_a.json", "check_units_b.json"):
        for u, v in json.loads((OUT / name).read_text()).items():
            for f, term, near, k in v["pipeline_hits"]:
                assert f in v["files"] and [term, near] in v["terms"]
                if f not in text:
                    p = t.DATA / "reports" / f
                    text[f] = " ".join(x for _, x in rt.parse_export((OUT / "text" / f"{p.stem}.txt").read_text()))
                n = sum(1 for m in mod.tolerant(term).finditer(text[f])
                        if not near or mod.tolerant(near).search(text[f][max(0, m.start() - mod.NEAR):m.end() + mod.NEAR]))
                assert n == k, (name, u, f, term, near)
                assert (t.DATA / "reports" / f).exists()


def test_every_deviation_has_a_cause():
    d = pd.read_csv(OUT / "deviations.csv", keep_default_na=False)
    assert (d.cause != "").all() and (d.pipeline != d.tool_raw).all()


def test_search_refuses_incomplete_manifest():
    if rt.incomplete(manifest()).empty:
        pytest.skip("manifest complete")
    with pytest.raises(AssertionError, match="manifest incomplete"):
        s.check_inputs()


def test_acronym_matching():
    rx = s.compile_term("LCR", "phrase")
    assert rx.search("the LCR was") and rx.search("LCRs") and not rx.search("financial crisis")
    assert not rx.search("the lcr") and s.compile_term("AT1", "phrase").search("AT1 capital")
    assert not s.compile_term("2bn", "figure").search("12bn")


READ_DONE = (OUT / "units_3h.csv").exists()


@pytest.mark.skipif(not READ_DONE, reason="phase 3h reading not run")
def test_quotes_found_on_their_pages():
    m = manifest().set_index("file")
    norm = lambda s: " ".join(str(s).split())  # noqa: E731
    q = pd.read_csv(OUT / "quotes.csv", keep_default_na=False)
    assert len(q) > 0
    for r in q.itertuples():
        pages = dict(rt.parse_export((OUT / "text" / f"{Path(r.file).stem}.txt").read_text()))
        assert norm(r.quote) in norm(pages[int(r.page)]), (r.unit, r.file, r.page)
        assert r.file in m.index


@pytest.mark.skipif(not READ_DONE, reason="phase 3h reading not run")
def test_one_class_per_unit_and_report_and_one_final_status():
    ca = pd.read_csv(OUT / "classes_a.csv", keep_default_na=False)
    new = manifest().query("folder == 'reports_2025_2026'").file
    assert len(ca) == 10 * len(new) and not ca.duplicated(["unit", "file"]).any()
    assert ca["class"].isin(["A", "B", "C"]).all()
    assert ((ca["class"] == "C") == (ca.quote == "")).all()
    u = pd.read_csv(OUT / "units_3h.csv", keep_default_na=False)
    assert len(u) == 10 and u.unit.is_unique
    ok = {"achieved", "missed", "revised", "open", "no longer mentioned", "not determinable from these reports"}
    assert u.final_status.isin(ok).all()
    ob = pd.read_csv(OUT / "outcomes_b.csv", keep_default_na=False)
    assert ob.status.isin(ok).all() and not ob.duplicated(["unit", "file"]).any()


@pytest.mark.skipif(not READ_DONE, reason="phase 3h reading not run")
def test_open_only_with_later_deadline_and_2026_mention():
    import phase3h_read as r
    ob = pd.read_csv(OUT / "outcomes_b.csv", keep_default_na=False)
    u = pd.read_csv(OUT / "units_3h.csv", keep_default_na=False).set_index("unit")
    for unit in ob[ob.status == "open"].unit.unique():
        assert r.DEADLINE[unit] > "2026-06-30"
    for unit, row in u.iterrows():
        if row.final_status == "open":
            assert r.DEADLINE[unit] > "2026-06-30" and row.last_mentioned_in.startswith("2026")
