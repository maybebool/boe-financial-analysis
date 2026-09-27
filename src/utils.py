import sys
import os
import pathlib
import pandas as pd
import re

# import importlib
# # importlib.reload()

from src import loading

def load_raw_data():
    EXPORT = "2026-09-13"

    project_root = pathlib.Path(__file__).resolve().parent.parent
    DATA = project_root / "data"

    raw_utterances = loading.load(DATA, "all_utterances.csv", EXPORT)
    raw_sentences = loading.load(DATA, "all_sentences.csv", EXPORT)
    raw_metrics = loading.load(DATA, "all_metrics.csv", EXPORT)

    return raw_sentences, raw_utterances, raw_metrics


#---------------------------------------------------------------------------------------------------------------------
# The source data identifies a turn only by its position within one call "position_in_call" 
# This is fine until we want to join sentences to utterances or group utterances into Q&A excahnges
# For this we need a clean 0..N interger per call. Sortig by CALL_KEY + postion_in_call guarantees the 
# ID reflects the true chronological order of the call before we number the rows.
# This function will also tag the JPM 2023-Q2 event call so that it can be excluded from quaterly earnings comparisons
# --------------------------------------------------------------------------------------------------------------------

CALL_KEY = ["bank", "quarter", "call_type", "call_date"]



def build_structured_utterances(raw_utterances: pd.DataFrame) -> pd.DataFrame:
       
    """
    Input:  raw_utterances (untouched)
    Output: a NEW DataFrame — raw_utterances is never mutated.
    """
    df = raw_utterances.copy()  # <- work on a copy, never the raw table
    df = df.sort_values(CALL_KEY + ["position_in_call"]).reset_index(drop=True)
    df["utterance_id"] = df.groupby(CALL_KEY).cumcount()

    # Tag the one known non-routine call (JPM 2023-Q2 "event" = First
    # Republic acquisition call) so it can be excluded from quarter-over-
    # quarter earnings comparisons if need to without deleting teh data for autibility reasons
    df["is_routine_earnings"] = df["call_type"] == "earnings"

    return df

#---------------------------------------------------------------------------
# Link sentences to their parent utterances and 
# fix the contraction issue with all_sentences
#----------------------------------------------------------------------------

# CALL_KEY = ["bank", "quarter", "call_type", "call_date"]


CONTRACTION_FIX_MAP = {
    "arenot": "are not", 
    "canot": "cannot",
    "couldnot": "could not",
    "didnot": "did not", 
    "doesnot": "does not", 
    "donot": "do not",
    "hadnot": "had not", 
    "hasnot": "has not", 
    "havenot": "have not",
    "isnot": "is not", 
    "shouldnot": "should not",
    "wasnot": "was not",
    "werenot": "were not",
    "wonot": "will not", 
    "wouldnot": "would not",
}
_CONTRACTION_PATTERN = re.compile(
    r"\b(" + "|".join(CONTRACTION_FIX_MAP.keys()) + r")\b", flags=re.IGNORECASE
)


def _fix_contractions(text: str) -> str:
    """
    Replace each malformed token with its correct two-word expansion,
    preserving capitalisation of the original word.
    """
    def repl(match):
        word = match.group(0)
        fixed = CONTRACTION_FIX_MAP[word.lower()]
        return fixed.capitalize() if word[0].isupper() else fixed
    return _CONTRACTION_PATTERN.sub(repl, text)


def build_structured_sentences(
    raw_sentences: pd.DataFrame, structured_utterances: pd.DataFrame
) -> pd.DataFrame:
    """
    Input:  raw_sentences (untouched), structured_utterances
    Output: a NEW DataFrame.
    """
    df = raw_sentences.copy()

    df = df.sort_values(CALL_KEY + ["position_in_call", "sentence_number"]).reset_index(drop=True)

    # Bring in utterance_id via the shared (call, position_in_call) key.
    # drop_duplicates because multiple sentences share one utterance row.
    utterance_lookup = structured_utterances[
        CALL_KEY + ["position_in_call", "utterance_id"]
    ].drop_duplicates()
    df = df.merge(utterance_lookup, on=CALL_KEY + ["position_in_call"], how="left")

    # Keep the original text for audit, fix the contraction bug in `sentence`
    # (the column downstream sentiment/topic code will actually read).
    df["sentence_raw"] = df["sentence"]
    df["sentence"] = df["sentence"].apply(_fix_contractions)

    return df




#------------------------------------------------------------------------------------------------------------------------------------
# Group consecutive analyst turns into Q&A exchanges
# This fixes the speaker-grouping edge case found in the document-structure which originally uses the rule
# for new exchange whenever  speaker_role == analyst. T
# The rule breaks when when one analyst's closing "Thank you" is immediately followed by a different analyst's real question where 
# both roles ends up having speaker_role == 'analyst's" wit no role change in between such that the naiv erule would merge two unrelated questions into one exchange.
# We caught this by eyeballing real exchanges after a first pass and seeing two analyts' names inside what was supposedly a single exchange.
# New exchnage starts when the current row is an analyst and either the previous row was not an analyst or teh previous analyst had a different name
#
#-------------------------------------------------------------------------------------------------------------------------------------------

FILLER_PHRASES = [
    r"good morning",
    r"good afternoon",
    r"good evening",
    r"how are you",
    r"(next |first )?question comes from",
    r"your (next )?question",
    r"thank you for (participating|joining|your questions)",
    r"you may now disconnect",
    r"conference (is )?(now )?concluded",
    r"turn the (call|conference) (back )?over to",
    r"can you hear (me)?", 
    r"hear (me )?ok(ay)?", 
    r"(please )?go ahead",
    r"i'll (hop|jump) back (in|into) the queue",
]
_FILLER_PATTERN = re.compile("|".join(FILLER_PHRASES), flags=re.IGNORECASE)

BOILERPLATE_PHRASES = FILLER_PHRASES + [
    r"(please |you may )?proceed",
    r"(we'll|we will) (now )?(go ahead and )?take (our |the )?next question",
    r"(from |on )?the line of",
    r"your line is (now )?open",
]
_BOILERPLATE_PATTERN = re.compile("|".join(BOILERPLATE_PHRASES), flags=re.IGNORECASE)



def _is_mostly_scripted(text: str, min_substantive_words: int = 15) -> bool:
    """
    Strip out known call-mechanics phrases (greetings, operator handoffs,
    audio checks, sign-offs) and see how much is left. An exchange that is
    almost entirely scripted transition language should be flagged as
    filler regardless of who spoke or whether someone replied
    """
    stripped = _FILLER_PATTERN.sub("", str(text))
    substantive_words = len(re.findall(r"[a-zA-Z]+", stripped))
    return substantive_words < min_substantive_words


def clean_boilerplate(text: str) -> str:
    """
    Strip operator/call-mechanics language from text used for topic modelling
    and keyword extraction. Distinct from is_filler: this runs on EVERY
    exchange (substantive or not) to remove scripted phrases embedded inside
    otherwise-real content — it never decides whether to drop a whole exchange.
    """
    return _BOILERPLATE_PATTERN.sub(" ", str(text))

def build_qa_exchanges(structured_utterances: pd.DataFrame) -> pd.DataFrame:
    """
    Input:  structured_utterances
    Output: a NEW DataFrame, a QA-only subset with an added qa_exchange_id.
    """
    qa = structured_utterances[structured_utterances["section"] == "qa"].copy()
    qa = qa.sort_values(CALL_KEY + ["utterance_id"]).reset_index(drop=True)

    prev_role = qa.groupby(CALL_KEY)["speaker_role"].shift(1)
    prev_name = qa.groupby(CALL_KEY)["speaker_name"].shift(1)
    qa["new_exchange"] = (qa["speaker_role"] == "analyst") & (
        (prev_role != "analyst") | (prev_name != qa["speaker_name"])
    )
    qa["qa_exchange_id"] = qa.groupby(CALL_KEY)["new_exchange"].cumsum()

    # Edge case found during sanity check: rows BEFORE the first analyst
    # question (e.g. the operator's call-opening announcement) get bucketed
    # into "exchange 0" by cumsum even though no analyst ever spoke in that
    # group. That's not a real exchange, so we drop any group with zero
    # analyst turns rather than let it surface as a topic-less question.
    has_analyst = qa.groupby(CALL_KEY + ["qa_exchange_id"])["speaker_role"].transform(
        lambda roles: (roles == "analyst").any()
    )
    qa = qa[has_analyst].copy()

    # Flag (don't delete) filler exchanges: short closer/operator-handoff
    # groups with no management reply at all, e.g. "Okay, thank you." ->
    # "Next question comes from...". These carry no analysable topic, so
    # topic modelling should skip them, but we keep them in the table for
    # audit rather than silently dropping rows.
    exchange_stats = qa.groupby(CALL_KEY + ["qa_exchange_id"]).agg(
            has_mgmt_reply=("speaker_role", lambda roles: "management" in roles.values),
            total_chars=("text_length", "sum"),
            full_text=("text", lambda s: " ".join(str(x) for x in s)),
        ).reset_index()

    no_reply_and_short = ~exchange_stats["has_mgmt_reply"] & (exchange_stats["total_chars"] < 250)
    mostly_scripted = exchange_stats["full_text"].apply(_is_mostly_scripted)
    exchange_stats["is_filler"] = no_reply_and_short | mostly_scripted

    qa = qa.merge(
        exchange_stats[CALL_KEY + ["qa_exchange_id", "is_filler"]],
        on=CALL_KEY + ["qa_exchange_id"],
    )
    return qa

def run_pipeline():

    # Load the raw datasets: all_sentences.csv, all_utterances.csv, all_metrics.csv
    raw_sentences, raw_utterances, raw_metrics = load_raw_data()

    # Give every utterance a stable ID within its call
    structured_utterances = build_structured_utterances(raw_utterances)

    # Link sentences to their parent utterances and fix tokenisation issue
    structured_sentences = build_structured_sentences(raw_sentences, structured_utterances)


    # Group consecutive analyst turns into Q&A excahnges
    qa_exchanges = build_qa_exchanges(structured_utterances)

    return {
        "raw_sentences": raw_sentences,
        "raw_utterances": raw_utterances,
        "raw_metrics": raw_metrics,
        "structured_utterances": structured_utterances,
        "structured_sentences": structured_sentences,
        "qa_exchanges": qa_exchanges,
    }