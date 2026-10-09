import hashlib
import json

import pandas as pd
import pytest

import phase3j_read as r
import phase3j_terms as t

OUT = r.OUT
needs_terms = pytest.mark.skipif(not (OUT / "check_units_3j.json").exists(), reason="phase 3j terms not written")
needs_read = pytest.mark.skipif(not (OUT / "read.csv").exists(), reason="phase 3j not read")


def test_grid_amounts():
    assert t.grid(12.6, 15.4, "bn")[:4] == ["13bn", "13 billion", "13.0bn", "13.0 billion"]
    assert "5.5bn" in t.grid(5.4, 6.6, "bn") and "6 billion" in t.grid(5.4, 6.6, "bn")
    assert t.grid(-1.0, 2.0, "bn")[0] == "0.5bn" and not any(s.startswith(("-", "0bn", "0 ")) for s in t.grid(-1.0, 2.0, "bn"))
    assert t.grid(15.46, 15.86, "bn") == ["16bn", "16 billion", "16.0bn", "16.0 billion"]   # nearest grid value


def test_grid_percent_and_basis_points():
    assert t.grid(0.33, 0.40, "pct") == ["0.4%"]
    assert "18%" in t.grid(16.2, 19.8, "pct") and "18.0%" in t.grid(16.2, 19.8, "pct")
    assert t.grid(169.2, 206.8, "pct")[0] == "170%" and "188%" in t.grid(169.2, 206.8, "pct")
    assert t.grid(32.9, 40.3, "bp") == ["35 basis points", "35bps", "35bp", "40 basis points", "40bps", "40bp"]
    assert t.grid(10.6, 13.0, "bp") == ["12 basis points", "12bps", "12bp"]


def test_bands_come_from_the_call_figure():
    x, _, defs = t.UNITS["F12"]
    level = next(f for name, _, _, f in defs if name == "resulting level")
    assert round(level(0.9 * x), 1) == 1605.4 and round(level(1.1 * x), 1) == 1585.4


def test_forward_pattern_extends_phase3():
    for word in ("expect", "target", "will", "aim", "intends", "estimate", "ambition"):
        assert r.FORWARD.search(f"we {word} this")
    assert not r.FORWARD.search("RWA decreased by USD 3bn")


@needs_terms
def test_terms_cover_all_units_and_files():
    u = json.loads((OUT / "check_units_3j.json").read_text())
    assert set(u) == {"T33", "T68_r1", "T68_r2", "F11", "F22", "T16", "T25", "T27", "F12", "T30"}
    assert all(len(v["files"]) == 16 for v in u.values())
    idx = pd.read_csv(OUT / "term_index.csv", keep_default_na=False)
    assert (idx[idx.search_pass == "A"].near != "").all()


@needs_read
def test_every_passage_has_one_class():
    read = pd.read_csv(OUT / "read.csv", keep_default_na=False)
    assert read["class"].isin(r.CLASSES).all()
    counted = read[read["class"].isin(r.CLASSES[:4])]
    assert read.drop_duplicates("text_id").shape[0] == 768
    assert (counted.quote != "").all() and (counted.page != "").all()
    assert (counted.forward_looking == "yes").all()


@needs_read
def test_sums_match_files():
    for line in (OUT / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ")
        assert hashlib.sha256((OUT / name).read_bytes()).hexdigest() == digest
