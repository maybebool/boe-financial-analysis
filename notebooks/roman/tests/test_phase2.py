import numpy as np
import pandas as pd
import pytest

import phase2_novelty as p2


@pytest.fixture(scope="module")
def s():
    return p2.load_sentences()


def test_no_event_call_no_operator(s):
    assert set(s.call_type) == {"earnings"}
    assert "operator" not in set(s.speaker_role)


def test_eligibility_filter(s):
    assert (s.eligible == (s.n_words >= 4)).all()


def test_masking_applied(s):
    assert not s.masked.str.contains(r"\d").any()


def test_reference_pool_is_earlier_same_bank(s):
    for bank in ["UBS", "JPM"]:
        for q in p2.TARGETS:
            pool = p2.pool_index(s, bank, q, s.eligible)
            sub = s.iloc[pool]
            assert (sub.bank == bank).all()
            assert (sub.quarter < q).all()
            assert sub.eligible.all()
            lag = s.iloc[p2.pool_index(s, bank, q, s.eligible, lag1=True)]
            assert set(lag.quarter) == {p2.QUARTERS[p2.QUARTERS.index(q) - 1]}


def test_reference_size_and_sampling(s):
    R = p2.reference_size(s, s.eligible)
    assert R == 415
    rng = np.random.default_rng(0)
    pool = p2.pool_index(s, "UBS", "2023-Q2", s.eligible)
    assert len(rng.choice(pool, R, replace=False)) == R


def test_targets():
    assert p2.TARGETS == ["2023-Q2", "2023-Q3", "2023-Q4", "2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]


@pytest.mark.skipif(not (p2.OUT / "novelty_mpnet.csv").exists(), reason="phase2_novelty.py not run")
def test_scores_only_for_target_calls(s):
    n = pd.read_csv(p2.OUT / "novelty_mpnet.csv")
    scored = s.iloc[n[n.novelty.notna()].row.values]
    assert set(scored.quarter) == set(p2.TARGETS)
    assert scored.eligible.all()
