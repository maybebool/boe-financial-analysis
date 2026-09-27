"""Phase 1 validation samples: deflection sentences and question topics, blind, with separate key files.

Run from the repository root after phase1_inference.py: python notebooks/roman/analysis/phase1_labelling.py
"""
import numpy as np
import pandas as pd

from phase1_common import LABEL_DIR, NLI_THRESHOLD, OUT, SEED

KEY = ["bank", "quarter", "call_type", "position_in_call", "sentence_number"]


def stratum(r):
    nli = r.nli_max >= NLI_THRESHOLD
    if r.phrase and nli:
        return "flag_both"
    if r.phrase:
        return "flag_phrase_only"
    if nli:
        return "flag_nli_only"
    if r.nli_max >= 0.5:
        return "unflag_nli_0.5_0.9"
    return "unflag_capital" if r.capital_kw else "unflag_other"


def take(df, n, rng):
    return df if len(df) <= n else df.iloc[rng.choice(len(df), n, replace=False)]


def deflection_sample(rng):
    a = pd.read_csv(OUT / "answer_sentences.csv")
    a["text"] = a.text.fillna("")
    seg = pd.read_csv(OUT / "segments.csv").set_index("segment_id")
    a = a[a.speaker_role == "management"].sort_values(KEY).reset_index(drop=True)
    a["prev"] = a.groupby("pair_id").text.shift(1).fillna("")
    a["next"] = a.groupby("pair_id").text.shift(-1).fillna("")
    a = a[a.n_words >= 4].copy()
    a["capital_kw"] = a.segment_id.map(seg.capital_kw)
    a["question_segment"] = a.segment_id.map(seg.text)
    a["stratum"] = a.apply(stratum, axis=1)
    parts = []
    for bank, b in a.groupby("bank"):
        flagged = b[b.stratum.str.startswith("flag_")]
        # up to 50 flagged, spread over the three flagged strata
        picked = [take(g, max(1, round(50 * len(g) / len(flagged))), rng) for _, g in flagged.groupby("stratum")]
        picked.append(take(b[b.stratum == "unflag_nli_0.5_0.9"], 10, rng))
        picked.append(take(b[b.stratum == "unflag_capital"], 25, rng))
        picked.append(take(b[b.stratum == "unflag_other"], 25, rng))
        sample = pd.concat(picked)
        n_pop = b.stratum.value_counts()
        n_smp = sample.stratum.value_counts()
        sample["weight"] = sample.stratum.map(n_pop / n_smp)
        parts.append(sample)
    s = pd.concat(parts)
    s = s.iloc[rng.permutation(len(s))].reset_index(drop=True)
    s["item_id"] = [f"D{i:03d}" for i in range(1, len(s) + 1)]
    blind = s[["item_id", "question_segment", "prev", "text", "next"]].rename(
        columns={"prev": "context_before", "text": "answer_sentence", "next": "context_after"})
    blind["label_deflection"] = ""
    blind["notes"] = ""
    key = s[["item_id"] + KEY + ["sentence_id", "segment_id", "stratum", "weight", "phrase", "nli_max", "capital_kw"]]
    return blind, key, a.groupby(["bank", "stratum"]).size().rename("population").reset_index()


def topic_sample(rng):
    seg = pd.read_csv(OUT / "segments.csv")
    turn = seg.groupby("pair_id").text.apply(" ".join)
    parts = [take(g, 25, rng) for _, g in seg.groupby(["bank", "capital_kw"])]
    s = pd.concat(parts)
    pop = seg.groupby(["bank", "capital_kw"]).size()
    s["weight"] = [pop[(b, c)] / len(s[(s.bank == b) & (s.capital_kw == c)]) for b, c in zip(s.bank, s.capital_kw)]
    s = s.iloc[rng.permutation(len(s))].reset_index(drop=True)
    s["item_id"] = [f"T{i:03d}" for i in range(1, len(s) + 1)]
    s["full_question_turn"] = s.pair_id.map(turn)
    blind = s[["item_id", "text", "full_question_turn"]].rename(columns={"text": "question_segment"})
    blind["label_capital_regulation"] = ""
    blind["notes"] = ""
    key = s[["item_id", "segment_id", "bank", "quarter", "capital_kw", "capital_proto", "prototype_sim", "weight"]]
    return blind, key


if __name__ == "__main__":
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    blind, key, pop = deflection_sample(rng)
    blind.to_csv(LABEL_DIR / "deflection.csv", index=False)
    key.to_csv(LABEL_DIR / "deflection_key.csv", index=False)
    pop.to_csv(LABEL_DIR / "deflection_strata_population.csv", index=False)
    tblind, tkey = topic_sample(rng)
    tblind.to_csv(LABEL_DIR / "question_topic.csv", index=False)
    tkey.to_csv(LABEL_DIR / "question_topic_key.csv", index=False)
    print(key.groupby(["bank", "stratum"]).size(), pop, tkey.groupby(["bank", "capital_kw"]).size())
