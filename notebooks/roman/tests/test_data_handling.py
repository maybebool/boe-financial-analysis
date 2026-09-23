import re

import pandas as pd
import pytest

import contrast
import qa_pairs
from config import RELEASE_DIR

# Sentence counts per call as listed in the release README.
README_SENTENCES = {
    ("JPM", "2023-Q1", "earnings"): 557, ("JPM", "2023-Q2", "event"): 319, ("JPM", "2023-Q2", "earnings"): 581,
    ("JPM", "2023-Q3", "earnings"): 569, ("JPM", "2023-Q4", "earnings"): 462, ("JPM", "2024-Q1", "earnings"): 641,
    ("JPM", "2024-Q2", "earnings"): 505, ("JPM", "2024-Q3", "earnings"): 665, ("JPM", "2024-Q4", "earnings"): 506,
    ("UBS", "2023-Q1", "earnings"): 539, ("UBS", "2023-Q2", "earnings"): 672, ("UBS", "2023-Q3", "earnings"): 534,
    ("UBS", "2023-Q4", "earnings"): 804, ("UBS", "2024-Q1", "earnings"): 501, ("UBS", "2024-Q2", "earnings"): 447,
    ("UBS", "2024-Q3", "earnings"): 508, ("UBS", "2024-Q4", "earnings"): 709,
}


@pytest.fixture(scope="module")
def sentences():
    return pd.read_csv(RELEASE_DIR / "all_sentences.csv")


@pytest.fixture(scope="module")
def pairs():
    return qa_pairs.build_pairs(qa_pairs.u)


def test_sentence_counts_match_release(sentences):
    counts = sentences.groupby(["bank", "quarter", "call_type"]).size().to_dict()
    assert counts == README_SENTENCES


def test_stable_key_is_unique(sentences):
    key = ["bank", "quarter", "call_type", "position_in_call", "sentence_number"]
    assert not sentences.duplicated(key).any()


def test_pairing_never_crosses_calls(pairs):
    u = qa_pairs.u
    for _, r in pairs.iterrows():
        call = " ".join(u[(u.bank == r.bank) & (u.quarter == r.quarter)].text)
        assert r.question in call and r.answer in call


def test_every_question_is_an_analyst_turn(pairs):
    u = qa_pairs.u.set_index(["bank", "quarter", "position_in_call"])
    roles = pairs.apply(lambda r: u.loc[(r.bank, r.quarter, r.position_in_call), "speaker_role"], axis=1)
    assert (roles == "analyst").all()


def test_every_answer_is_management_or_ir(pairs):
    u = qa_pairs.u
    for _, r in pairs.iterrows():
        call = u[(u.bank == r.bank) & (u.quarter == r.quarter)].sort_values("position_in_call")
        after = call[call.position_in_call > r.position_in_call]
        k = 0
        while k < len(after) and after.iloc[k].speaker_role in ("management", "ir"):
            k += 1
        block = after.iloc[:k]
        assert k > 0
        assert set(block.speaker_role) <= {"management", "ir"}
        assert " ".join(block.text) == r.answer


def test_pair_counts(pairs):
    assert pairs.groupby("bank").size().to_dict() == {"JPM": 246, "UBS": 129}


def test_masking_removes_numbers(sentences):
    cleaned = sentences.sentence.map(contrast.clean)
    assert not cleaned.str.contains(r"\d").any()


def test_masking_removes_speaker_names(sentences):
    # the name list in contrast.py is built from earnings-call speakers, so the check covers earnings calls
    earnings = sentences[sentences.call_type == "earnings"]
    cleaned = earnings.sentence.map(contrast.clean).str.replace("PERSON", "", regex=False)
    for name in earnings.speaker_name.dropna().unique():
        for token in re.split(r"[ .]+", name):
            if len(token) > 2:
                assert not cleaned.str.contains(rf"\b{re.escape(token.lower())}\b").any(), token


def test_masking_examples():
    t = contrast.clean("Thanks, Jeremy. In 2Q24 CET1 rose 40 basis points to 14.2% in 2024 [edit: 14 million].")
    assert "jeremy" not in t and not re.search(r"\d", t) and "edit" not in t
