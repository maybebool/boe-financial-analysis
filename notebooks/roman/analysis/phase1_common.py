"""Phase 1 data handling: sentence-level pairs, question segments, topic and phrase rules.

All rules are the ones written in plans/phase_1.md.
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "notebooks" / "roman" / "data" / "phase1"
LABEL_DIR = ROOT / "notebooks" / "roman" / "data" / "labelling"
sys.path.insert(0, str(ROOT / "notebooks" / "roman"))

from config import RELEASE_DIR  # noqa: E402
from qa_pairs import NA_RE  # phrase list fixed before phase 0  # noqa: E402

SEED = 0
NLI_MODEL = "MoritzLaurer/deberta-v3-large-zeroshot-v2.0"
EMB_MODEL = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
CE_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
REVISIONS = {NLI_MODEL: "cf44676c28ba7312e5c5f8f8d2c22b3e0c9cdae2",
             EMB_MODEL: "17997f24dca0df1a4fed68894fb0e1e133e60482",
             CE_MODEL: "233902d25c440f23af6f7d6e94d2946bac0bee0a"}
NLI_HYPOTHESES = {
    "nli_a": "The speaker declines to give the requested information.",
    "nli_b": "The speaker says it is too early to say or to give details.",
}
NLI_THRESHOLD = 0.9
TOPIC_PROTOTYPE = "The question is about regulatory capital requirements for the bank."
PROTOTYPE_THRESHOLD = 0.5

BRACKET_RE = re.compile(r"\[[^\]]*\]")
SEG_START_RE = re.compile(
    r"^\W*((and|so|then|maybe|okay|ok)\W+)*(first|firstly|second|secondly|third|the other question|"
    r"my second question|a follow-up|and then|just on|on the|lastly|finally)\b", re.I)
GREETING_RE = re.compile(r"^\W*(thanks|thank you|hi|hello|hey|good (morning|afternoon|evening))\b", re.I)

CAPITAL_TERMS = ["capital requirement", "capital regime", "regulatory capital", "capital rules", "basel", "endgame",
                 "too big to fail", "tbtf", "federal council", "parliament", "finma", "swiss regime", "parent bank",
                 "subsidiar* capital", "g-sib", "gsib", "surcharge", "slr", "supplementary leverage",
                 "stress capital buffer", "scb", "at1", "additional tier 1", "guarantee", "loss protection",
                 "regulator", "regulation"]
SWISS_TERMS = ["federal council", "parliament", "swiss regime", "too big to fail", "parent bank", "finma"]
INTEGRATION_TERMS = ["credit suisse", "integration", "non-core", "migration", "combined", "cost save"]


def term_regex(terms):
    parts = [re.escape(t).replace(r"\*", r"\w*") for t in terms]
    return re.compile(r"\b(?:" + "|".join(parts) + ")", re.I)


CAPITAL_RE, SWISS_RE, INTEGRATION_RE = map(term_regex, [CAPITAL_TERMS, SWISS_TERMS, INTEGRATION_TERMS])


def clean_text(t):
    return re.sub(r"\s+", " ", BRACKET_RE.sub(" ", t)).strip()


def n_words(t):
    return len(t.split())


def load_qa_sentences():
    """Q&A sentences of the earnings calls with the stable key, bracket-free text and word counts."""
    s = pd.read_csv(RELEASE_DIR / "all_sentences.csv")
    s = s[(s.call_type == "earnings") & (s.section == "qa")].copy()
    s = s.sort_values(["bank", "quarter", "position_in_call", "sentence_number"]).reset_index(drop=True)
    s["text"] = s.sentence.map(clean_text)
    s["n_words"] = s.text.map(n_words)
    return s


def build_sentence_pairs(s):
    """Assign each analyst turn a pair id and each following management/IR sentence the same id.

    Same rule as qa_pairs.build_pairs: an analyst turn followed by the consecutive management or IR turns of
    the same call. Returns question sentences and answer sentences, both with pair_id.
    """
    turns = s.groupby(["bank", "quarter", "position_in_call"], sort=True).speaker_role.first().reset_index()
    pair_of_turn = {}
    for (bank, q), call in turns.groupby(["bank", "quarter"], sort=True):
        call = call.sort_values("position_in_call").to_dict("records")
        i = 0
        while i < len(call):
            if call[i]["speaker_role"] != "analyst":
                i += 1
                continue
            j = i + 1
            while j < len(call) and call[j]["speaker_role"] in ("management", "ir"):
                j += 1
            if j > i + 1:
                pid = f"{bank}_{q}_{call[i]['position_in_call']:03d}"
                for k in range(i, j):
                    pair_of_turn[(bank, q, call[k]["position_in_call"])] = pid
            i = j
    key = list(zip(s.bank, s.quarter, s.position_in_call))
    s = s.assign(pair_id=[pair_of_turn.get(k) for k in key])
    s = s[s.pair_id.notna()]
    return s[s.speaker_role == "analyst"].copy(), s[s.speaker_role.isin(["management", "ir"])].copy()


def split_turn(texts):
    """Split one analyst turn (list of sentence texts) into segments; returns a segment index per sentence."""
    segs = [[0]]
    for i in range(1, len(texts)):
        if texts[i - 1].rstrip(" \"'”’").endswith("?") or SEG_START_RE.match(texts[i]):
            segs.append([i])
        else:
            segs[-1].append(i)

    def weak(seg):
        no_long = all(n_words(texts[i]) < 4 for i in seg)
        greeting = all(GREETING_RE.match(texts[i]) for i in seg)
        return no_long or greeting

    while len(segs) > 1:
        k = next((k for k, seg in enumerate(segs) if weak(seg)), None)
        if k is None:
            break
        if k < len(segs) - 1:
            segs[k + 1] = segs[k] + segs[k + 1]
        else:
            segs[k - 1] = segs[k - 1] + segs[k]
        del segs[k]
    out = [0] * len(texts)
    for n, seg in enumerate(segs):
        for i in seg:
            out[i] = n
    return out


def build_segments(questions):
    """Question sentences with segment ids, and one row per question segment."""
    questions = questions.copy()
    questions["segment_no"] = 0
    for pid, g in questions.groupby("pair_id", sort=False):
        questions.loc[g.index, "segment_no"] = split_turn(g.text.tolist())
    questions["segment_id"] = questions.pair_id + "_s" + questions.segment_no.astype(str)
    seg = (questions.groupby(["segment_id"], sort=False)
           .agg(bank=("bank", "first"), quarter=("quarter", "first"), pair_id=("pair_id", "first"),
                segment_no=("segment_no", "first"), analyst=("speaker_name", "first"),
                institution=("speaker_institution", "first"), text=("text", " ".join),
                n_sentences=("text", "size"))
           .reset_index())
    seg["capital_kw"] = seg.text.str.contains(CAPITAL_RE)
    seg["swiss_kw"] = seg.text.str.contains(SWISS_RE)
    seg["integration_kw"] = seg.text.str.contains(INTEGRATION_RE)
    return questions, seg


def phrase_flag(t):
    return bool(NA_RE.search(t))
