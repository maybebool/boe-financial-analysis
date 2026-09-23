import pandas as pd
import pytest

import phase1_common as pc

OUT = pc.OUT


@pytest.fixture(scope="module")
def built():
    s = pc.load_qa_sentences()
    q, a = pc.build_sentence_pairs(s)
    q, seg = pc.build_segments(q)
    return s, q, a, seg


def test_pairs_match_qa_pairs_script(built):
    _, q, _, _ = built
    assert q.groupby("bank").pair_id.nunique().to_dict() == {"JPM": 246, "UBS": 129}


def test_segments_partition_each_turn(built):
    s, q, _, seg = built
    analyst = s[s.speaker_role == "analyst"]
    assert len(q) == len(q.drop_duplicates(["bank", "quarter", "position_in_call", "sentence_number"]))
    for pid, g in q.groupby("pair_id"):
        nos = sorted(g.segment_no.unique())
        assert nos == list(range(len(nos)))  # contiguous numbering
        assert g.segment_no.is_monotonic_increasing  # segments are contiguous runs of sentences
    joined = seg.groupby("pair_id").text.apply(" ".join)
    orig = q.groupby("pair_id").text.apply(" ".join)
    assert (joined == orig.loc[joined.index]).all()


def test_split_turn_rules():
    texts = ["Good morning.", "Thanks for taking my questions.", "First, on NII, where does it go from here?",
             "Second, on costs, is the target still valid for next year?", "Thank you."]
    assert pc.split_turn(texts) == [0, 0, 0, 1, 1]


def test_questions_are_analyst_and_answers_management_or_ir(built):
    _, q, a, _ = built
    assert set(q.speaker_role) == {"analyst"}
    assert set(a.speaker_role) <= {"management", "ir"}


@pytest.mark.skipif(not (OUT / "answer_sentences.csv").exists(), reason="phase1_score.py not run")
def test_alignment_stays_in_pair_and_call():
    a = pd.read_csv(OUT / "answer_sentences.csv")
    seg = pd.read_csv(OUT / "segments.csv").set_index("segment_id")
    assert a.segment_id.notna().all()
    assert (a.segment_id.map(seg.pair_id) == a.pair_id).all()
    assert (a.segment_id.map(seg.bank) == a.bank).all()
    assert (a.segment_id.map(seg.quarter) == a.quarter).all()


@pytest.mark.skipif(not (OUT / "answer_sentences.csv").exists(), reason="phase1_score.py not run")
def test_rate_uses_management_sentences_only():
    import phase1_inference as pi
    a, _ = pi.load()
    assert set(a.speaker_role) == {"management"}
    r = pi.call_rates(a, "primary")
    assert len(r) == 16


def test_capital_keywords():
    assert pc.CAPITAL_RE.search("What about the regulatory treatment?")
    assert pc.CAPITAL_RE.search("capital for the subsidiaries capital") is not None
    assert pc.CAPITAL_RE.search("Subsidiary capital is key")
    assert not pc.CAPITAL_RE.search("What is your NII outlook?")
