import sys
import os
import pathlib
import pandas as pd
import re

# import importlib
# # importlib.reload()

from src import loading

# --------------------------------------------------------------------------
# STEP 0 — load Raw Data
# --------------------------------------------------------------------------

def load_raw_data():
    EXPORT = "2026-09-30"

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

# --------------------------------------------------------------------------
# STEP 1 — Add a stable, per-call utterance_id
# --------------------------------------------------------------------------

def build_structured_utterances(raw_utterances: pd.DataFrame, raw_sentences: pd.DataFrame) -> pd.DataFrame:
       
    """
    Input:  raw_utterances (untouched)
    Output: a NEW DataFrame — raw_utterances is never mutated.

    Why we need utterance_id at all:
    The source data identifies a turn only by its position within one call
    (`position_in_call`). That's fine until we want to join sentences to
    utterances, or group utterances into Q&A exchanges — for that we want a
    clean 0..N integer per call. Sorting by CALL_KEY + position_in_call
    first guarantees the id reflects the true chronological order of the
    call before we number the rows.


    Why raw_sentences is needed here too, for `is_filler_utterance`:
    Jack asked whether a whole utterance can be flagged as filler, the
    same way individual sentences and whole Q&A exchanges already are; e.g.
    a lone "Thank you." turn. The natural answer is "every sentence in this
    utterance is itself a filler sentence",This function flags filler on the
    RAW sentence text directly (via the same _flag_filler_sentences() used later) 
    and rolls that up by CALL_KEY + position_in_call, the one key raw_sentences and raw_utterances 
    share before utterance_id even exists.
    """

    df = raw_utterances.copy()
    df = df.sort_values(CALL_KEY + ["position_in_call"]).reset_index(drop=True)
    df["utterance_id"] = df.groupby(CALL_KEY).cumcount()

    # Tag the one known non-routine call (JPM 2023-Q2 "event" = First
    # Republic acquisition call) so it can be excluded from quarter-over-
    # quarter earnings comparisons if we need to without deleting teh data for autibility reasons
    df["is_routine_earnings"] = df["call_type"] == "earnings"

    # An utterance is filler if EVERY sentence inside it is filler whereas a
    # multi-sentence turn with even one real sentence is not pure filler.

    sentence_filler = _flag_filler_sentences(raw_sentences["sentence"], raw_sentences["speaker_name"])
    utterance_filler = (
        raw_sentences.assign(is_filler_sentence=sentence_filler)
        .groupby(CALL_KEY + ["position_in_call"])["is_filler_sentence"]
        .all()
        .rename("is_filler_utterance")
        .reset_index()
    )

    df = df.merge(utterance_filler, on=CALL_KEY + ["position_in_call"], how="left")
    # An utterance with no sentences linked to it (shouldn't happen, but
    # guard against it) is NOT assumed filler: False, not True, on no data.
    df["is_filler_utterance"] = df["is_filler_utterance"].fillna(False)

    return df


#---------------------------------------------------------------------------
# STEP 2  - sentences: Link sentences to their parent utterances and 
# fix the contraction issue with all_sentences
# 
# This appears to have been fixed in the new version 2026-09-30. 
# "cannot" is deliberately excluded: it's already the standard, correct
# expansion of "can't" and must be left alone.
# We will leave it any way, in case we need it later
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

    Linking logic: sentences and utterances were both extracted per speaker
    turn, so a sentence's parent utterance is "whichever utterance shares
    the same call and the same position_in_call". We merge on CALL_KEY +
    position_in_call.
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
    df["is_filler_sentence"] = _flag_filler_sentences(df["sentence"], df["speaker_name"])

    return df

# --------------------------------------------------------------------------
# Sentence-level filler flag
# --------------------------------------------------------------------------
# This is the sentence-grain analogue of qa_exchanges' is_filler, but the
# definition has to be narrower, not just "the same rule at a smaller unit":
# an EXCHANGE is filler when the whole thing carries no real question. A
# SENTENCE can be filler even inside an otherwise substantive exchange: 
# e.g. "Hi. Good morning. Jeremy, I wanted to ask about capital..." has one
# filler sentence and one real question in the very same utterance. So this
# flags individual courtesy/greeting/operator-transition sentences by
# matching normalised text against a small curated set, rather than reusing
# any length or reply-based rule from the exchange-level version.
#
# Matching is intentionally exact-set + one narrow regex (greeting + name),
# not a short-sentence-length heuristic; a length cutoff would also catch
# genuine short financial fragments like "NII ex." (a real sentence-splitter
# artefact from "NII ex. Markets"), which is not filler and must survive.
FILLER_SENTENCE_EXACT = {
    "thank you", "thanks", "thanks very much", "thank you very much",
    "yeah", "okay", "ok", "good morning", "morning", "you may proceed",
    "hi", "hey", "hello", "got it", "yes", "no", "great", "sure", "all right",
    "alright", "right", "please stand by", "please go ahead", "very good",
    "perfect", "excellent", "absolutely", "of course", "no problem",
    "appreciate it", "yeah sure", "sounds good", "fair enough",
}
_GREETING_NAME_PATTERN = re.compile(r"^(hi|hey|hello|good morning|morning)\s+\w+$")


# Found by Rachel - reporting: "UBS Q1 2023 - first greetings remain as non-filler sentences but rest are removed."
# Actual misses: "Good morning, ladies and gentlemen." and "Thank you, Sarah, good morning, everyone.", 
# the exact match check above requires the WHOLE sentence to equal one known phrase,
# so it misses compound greetings strung together with commas (thanks +
# name + greeting + address-term, in any combination). Checking against the
# whole sentence can't generalise to every such combination; checking
# CLAUSE BY CLAUSE can: if every comma-separated clause is either a known
# filler phrase or a way of addressing the audience (a name, "everyone",
# "ladies and gentlemen"), the whole sentence is filler, however the clauses
# are ordered or combined. This still can't false-positive on real content:
# a sentence like "Thanks, Jeremy, can you walk us through RWA?" has a last
# clause that matches neither category, so the `all()` check correctly
# leaves it unflagged.

ADDRESS_TERMS = {
    "everyone", "everybody", "all", "guys", "folks", "sir", "ma'am", "team",
    "ladies and gentlemen",
}



def _flag_filler_sentences(sentence_col: pd.Series, speaker_name_col: pd.Series) -> pd.Series:
    def normalise(text: str) -> str:
        t = text.strip().lower()
        t = re.sub(r"[.,!?]+$", "", t)  # drop trailing punctuation only —
        t = re.sub(r"\s+", " ", t)      # keep internal punctuation/words intact
        return t
    


    # Built from the data (first names of every speaker in THIS call set)
    # rather than hardcoded, it stays correct automatically as new speakers
    # appear in future quarters, so its future proof.

    known_first_names = set(speaker_name_col.dropna().str.split().str[0].str.lower().unique())

    normalised = sentence_col.apply(normalise)
    whole_sentence_match = normalised.isin(FILLER_SENTENCE_EXACT) | normalised.str.match(_GREETING_NAME_PATTERN)

    def all_clauses_are_filler(norm_text: str) -> bool:
        clauses = [c.strip() for c in norm_text.split(",") if c.strip()]
        if not clauses:
            return False
        return all(c in FILLER_SENTENCE_EXACT or c in ADDRESS_TERMS or c in known_first_names
                    for c in clauses)


    clause_match = normalised.apply(all_clauses_are_filler)
    return whole_sentence_match | clause_match    

#------------------------------------------------------------------------------------------------------------------------------------
#  STEP 3: Group consecutive analyst turns into Q&A exchanges
# 
# This fixes the speaker-grouping edge case found in the document-structure which originally uses the rule
# for new exchange whenever  speaker_role == analyst. 
# The rule breaks when when one analyst's closing "Thank you" is immediately followed by a different analyst's real question where 
# both roles ends up having speaker_role == 'analyst's" with no role change in between such that 
# the naive rule would merge two unrelated questions into one exchange.
# We caught this by eyeballing real exchanges after a first pass and seeing two analyts' names inside what was supposedly a single exchange.
# New exchnage starts when the current row is an analyst and either the previous row was not an analyst or teh previous analyst had 
# a different name
#-------------------------------------------------------------------------------------------------------------------------------------------



def build_qa_exchanges(structured_utterances: pd.DataFrame, structured_sentences: pd.DataFrame) -> pd.DataFrame:
    """
    Input:  structured_utterances from Step 1
    Output: a NEW DataFrame, a QA-only subset with an added qa_exchange_id.

    Why we need our own grouping instead of just using speaker_role:
    A naive rule ("new exchange whenever speaker_role becomes 'analyst'")
    breaks when one analyst's closing "Thank you." is immediately followed
    by a DIFFERENT analyst's real question — both rows have speaker_role ==
    'analyst' with no role change in between, so the naive rule would merge
    two unrelated questions into one exchange. We caught this by eyeballing
    real exchanges after the first pass and seeing two analysts' names
    inside what was supposedly a single exchange.

    Fix: a new exchange starts when the current row is an analyst AND
    EITHER the previous row wasn't an analyst, OR the previous analyst had
    a different name. This isolates each analyst's ask correctly even when
    two analysts speak back-to-back with no management turn between them.
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

    # Flag (don't delete) filler exchanges: we need to isolate and catch problematic patterns:
    #   (a) short closer/operator-handoff groups with no management reply at all, e.g. "Okay, thank you." ->
    #   "Next question comes from...". 
    #
    #   (B) Pure greeting exchanges that do not get a management reply but carry no actual question,
    #        e.g "Hi. Good Morning." -> 
    #       "Hey Betsy." (found by eyeballing the shortest "substantive" exchanges). If left in, these may impact topic modelling
    #        Using pattern (A) only will miss these  because a one-word reply still counts as "has a management reply").
    #
    #   (C) a closing remark from the SAME analyst right after management's
    #       answer gets mis-split into its own "exchange" by the boundary
    #       rule above (prev_role is 'management', not 'analyst', so a new
    #       exchange starts) — e.g. "Okay. Thanks, Jeremy." -> "Thanks,
    #       John." -> operator transition. This slipped past (a) and (b)
    # if every sentence the analyst spoke in the exchange is itself a filler sentence,
    # the exchange has no real question regardless of how long management or the operator talk afterward.
    # None of the three carry an analysable topic, so all are excluded from
    # topic modelling / sentiment aggregation, but kept in the table for audit
    
    exchange_stats = qa.groupby(CALL_KEY + ["qa_exchange_id"]).agg(
            has_mgmt_reply=("speaker_role", lambda roles: "management" in roles.values),
            total_chars=("text_length", "sum"),
            # full_text=("text", lambda s: " ".join(str(x) for x in s)),
        ).reset_index()

    analyst_sentence_filler = (
        qa[qa["speaker_role"] == "analyst"]
        .merge(structured_sentences[CALL_KEY + ["utterance_id", "is_filler_sentence"]],
               on=CALL_KEY + ["utterance_id"])
               .groupby(CALL_KEY + ["qa_exchange_id"])["is_filler_sentence"]
               .all()
               .rename("analyst_content_is_all_filler")
               .reset_index()
    )

    exchange_stats = exchange_stats.merge(analyst_sentence_filler, on=CALL_KEY + ["qa_exchange_id"], how="left")
    exchange_stats["analyst_content_is_all_filler"] = exchange_stats["analyst_content_is_all_filler"].fillna(False)
    
    exchange_stats["is_filler"] = (
        (~exchange_stats["has_mgmt_reply"] & (exchange_stats["total_chars"] < 250))
        | (exchange_stats["total_chars"] < 80)
        | exchange_stats["analyst_content_is_all_filler"]
    )
    
    qa = qa.merge(
        exchange_stats[CALL_KEY + ["qa_exchange_id", "is_filler"]],
        on=CALL_KEY + ["qa_exchange_id"],
    )
    return qa


def build_exchange_texts(qa_exchanges: pd.DataFrame) -> pd.DataFrame:
    """
    Input:  qa_exchanges (from build_qa_exchanges)
    Output: a NEW DataFrame, one row per substantive exchange, with the
    analyst's question text concatenated into a single `question_text` field.
    Filler exchanges are dropped here (they were only ever kept for audit).
    """
    df = qa_exchanges[~qa_exchanges["is_filler"]].copy()
    df = df[df["speaker_role"] == "analyst"]

    exchange_texts = (
        df.sort_values(CALL_KEY + ["utterance_id"])
        .groupby(CALL_KEY + ["qa_exchange_id"])["text"]
        .apply(lambda texts: " ".join(texts))
        .rename("question_text")
        .reset_index()
    )
    return exchange_texts



# --------------------------------------------------------------------------
# TOPIC Related helper function: speaker name stopword curator
# --------------------------------------------------------------------------


def _speaker_name_stopwords(structured_utterances: pd.DataFrame) -> list:
    """
    Analysts and management constantly address each other by first name
    ("Thanks, Jeremy", "Hey, Betsy") — found by inspecting the first topic
    model fit, where several "topics" turned out to just be a first name.
    Building this list FROM THE DATA (rather than hardcoding it) means it
    stays correct automatically if future quarters bring in new speakers.
    """
    first_names = structured_utterances["speaker_name"].dropna().str.split().str[0].str.lower()
    return sorted(first_names.unique())



def run_pipeline():

    """
    Runs the full load and clean stage structring pass and returns every DataFrame we might 
    need downstream (raw + structured) so that a caller can inspect any stage without re-reading a CSV
    
    """    

    # Load the raw datasets: all_sentences.csv, all_utterances.csv, all_metrics.csv
    raw_sentences, raw_utterances, raw_metrics = load_raw_data()

    # Give every utterance a stable ID within its call
    structured_utterances = build_structured_utterances(raw_utterances, raw_sentences)

    # Link sentences to their parent utterances and fix tokenisation issue
    structured_sentences = build_structured_sentences(raw_sentences, structured_utterances)


    # Group consecutive analyst turns into Q&A excahnges
    qa_exchanges = build_qa_exchanges(structured_utterances, structured_sentences)

    exchange_texts = build_exchange_texts(qa_exchanges)

    return {
        "raw_sentences": raw_sentences,
        "raw_utterances": raw_utterances,
        "raw_metrics": raw_metrics,
        "structured_utterances": structured_utterances,
        "structured_sentences": structured_sentences,
        "qa_exchanges": qa_exchanges,
        "exchange_texts": exchange_texts
    }


if __name__ == "__main__":
    data = run_pipeline()

    print("Row counts:")
    for name in ["raw_sentences", "raw_utterances", "raw_metrics",
                 "structured_utterances", "structured_sentences", "qa_exchanges"]:
        print(f"  {name:24s} {len(data[name])} rows")

    # NB: is_filler is repeated on every TURN within an exchange, so we must
    # de-duplicate down to one row per exchange before counting, summing
    # the raw column would double-count any multi-turn exchange.
    distinct_exchanges = data["qa_exchanges"].drop_duplicates(CALL_KEY + ["qa_exchange_id"])
    print(f"\nQ&A exchanges: {len(distinct_exchanges)} total, "
          f"{distinct_exchanges['is_filler'].sum()} filler, "
          f"{(~distinct_exchanges['is_filler']).sum()} substantive")


    # Persist Load & Clean Stage structured outputs for downstream stages / sharing.
    data["structured_utterances"].to_csv("./data/output/structured_utterances.csv", index=False)
    data["structured_sentences"].to_csv("./data/output/structured_sentences.csv", index=False)
    data["qa_exchanges"].to_csv("./data/output/qa_exchanges_utterance_level.csv", index=False)
    data["exchange_texts"].to_csv("./data/output/exchange_texts.csv", index=False)
