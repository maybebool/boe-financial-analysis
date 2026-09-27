from datetime import date

import pandas as pd
import pytest

import phase3_extract as p3


def test_quantities():
    assert p3.quantities("around 13 billion in gross cost reductions") == [(13.0, "amount_bn")]
    assert p3.quantities("a CET1 ratio of 14%") == [(14.0, "pct")]
    assert p3.quantities("about $88 billion") == [(88.0, "amount_bn")]
    assert p3.quantities("an increase of 50 basis points") == [(50.0, "bps")]
    assert p3.quantities("$500 million of net income") == [(0.5, "amount_bn")]
    assert p3.quantities("in 2025 and 2026") == []  # years alone are not quantities


def test_horizons_relative_to_call_date():
    feb24 = date(2024, 2, 6)
    assert (date(2025, 12, 31), "next_year") in p3.horizons("we expect this next year", feb24)
    assert (date(2024, 12, 31), "this_year") in p3.horizons("by the end of the year", feb24)
    assert p3.first_horizon("From 2026, our aim is 200 billion by 2028.", "", feb24)[0] == date(2028, 12, 31)
    assert p3.horizons("as we did in 2023", feb24) == []  # past years are no horizon
    assert p3.first_horizon("in the first quarter of 2024", "", date(2023, 5, 1))[0] == date(2024, 3, 31)


def test_candidate_needs_all_three_parts():
    d = date(2024, 2, 6)
    assert p3.is_candidate("We expect around 13 billion in gross cost reductions by the end of 2026.", d)
    assert not p3.is_candidate("We achieved 13 billion in 2023.", d)  # no future horizon
    assert not p3.is_candidate("We expect costs to fall by the end of 2026.", d)  # no quantity


@pytest.fixture(scope="module")
def st():
    return p3.load_statements()


def test_management_only_and_event_flag(st):
    assert set(st.speaker_role) == {"management"}
    assert (st.origin_only == (st.call_type == "event")).all()


def test_ex_joined_no_not(st):
    assert not st.text.str.endswith(" ex.").any()
    raw = pd.read_csv(p3.RELEASE_DIR / "all_sentences.csv")
    raw = raw[raw.speaker_role == "management"]
    n_no = raw.sentence.str.strip().str.endswith("No.").sum()
    assert st.text.str.endswith("No.").sum() == n_no  # sentences ending in "No." are left alone
    assert st.joined_with_next.sum() > 0


@pytest.mark.skipif(not (p3.OUT / "followups.csv").exists(), reason="phase3_track.py not run")
def test_followups_later_earnings_same_bank():
    f = pd.read_csv(p3.OUT / "followups.csv")
    t = pd.read_csv(p3.OUT / "threads.csv").set_index("thread")
    s = pd.read_csv(p3.OUT / "statements.csv").set_index("stmt_id")
    fs = s.loc[f.stmt_id]
    assert (fs.call_type == "earnings").all()  # the event call is never a follow-up
    assert (fs.bank.values == f.bank.values).all()
    assert (fs.call_date.values > t.loc[f.thread, "first_call_date"].values).all()
