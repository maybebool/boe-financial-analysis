import hashlib
import json

import pandas as pd
import pytest

import phase3i_check as c

OUT = c.OUT
needs_run = pytest.mark.skipif(not (OUT / "summary.json").exists(), reason="phase 3i not run")


def test_norm_changes_only_quotes_and_whitespace():
    assert c.norm("  We’ll  reach “around” 14%\n by 2026. ") == "We'll reach \"around\" 14% by 2026."
    assert c.norm("Non-core and Legacy") == "Non-core and Legacy"
    assert c.norm("CET1") != c.norm("cet1")


def test_pair_multiset_pairs_repeats_one_to_one():
    pairs, only_old, only_new = c.pair_multiset(["a", "b", "a", "c"], ["a", "d", "a", "a"])
    assert pairs == [(0, 0), (2, 2)]
    assert only_old == [1, 3]
    assert only_new == [1, 3]


def test_joined_windows_finds_a_split():
    w = c.joined_windows(["We expect 14%.", "By 2026.", "Thank you."])
    assert w["We expect 14%. By 2026."] == (0, 2)
    assert "We expect 14%." not in w


def test_best_match():
    j, sim = c.best_match("we expect around 14 billion by 2026", ["thank you", "we expect around 13 billion by 2026"])
    assert j == 1 and sim > 0.9
    assert c.best_match("x", []) == (None, 0.0)


@needs_run
def test_all_units_present_once():
    m = pd.read_csv(OUT / "units_match.csv")
    assert len(m) == 39 and m.unit.is_unique
    assert set(m.phase.value_counts().items()) == {("3d", 31), ("3g", 8)}


@needs_run
def test_new_statements_stay_in_window():
    s = pd.read_csv(OUT / "statements_new.csv")
    assert set(s.bank) == {"UBS"} and set(s.call_type) == {"earnings"}
    assert s.quarter.min() == "2023-Q2" and s.quarter.max() == "2024-Q4"
    assert s.new_id.is_unique
    assert (s.in_s == (s.specific & s.has_quantity & ~s.candidate)).all()


@needs_run
def test_reading_list_is_unlabelled_and_complete():
    r = pd.read_csv(OUT / "only_new_for_reading.csv", keep_default_na=False)
    assert (r[["genuine", "duplicate_of", "new_target", "notes"]] == "").all().all()
    n_new = sum((pd.read_csv(OUT / f"{name}_compare.csv").status == "only new").sum()
                for name in ("candidates", "set_s"))
    assert len(r) <= n_new and (len(r) > 0) == (n_new > 0)


@needs_run
def test_sums_match_files():
    for line in (OUT / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ")
        assert hashlib.sha256((OUT / name).read_bytes()).hexdigest() == digest


@needs_run
def test_earlier_phases_untouched():
    summary = json.loads((OUT / "summary.json").read_text())
    assert summary["statements"]["old"] == 3177  # UBS earnings statements of phase 3g, unchanged
