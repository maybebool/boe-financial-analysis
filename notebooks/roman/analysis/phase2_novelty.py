"""Phase 2 novelty: embeddings and sentence novelty against a fixed-size sample of earlier calls.

Run from the repository root: python notebooks/roman/analysis/phase2_novelty.py
Writes sentences.csv, novelty_<config>.csv, nearest.csv and models.json to notebooks/roman/data/phase2/.
All rules are the ones written in plans/phase_2.md.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman"))
from config import RELEASE_DIR  # noqa: E402

OUT = ROOT / "notebooks" / "roman" / "data" / "phase2"
SEED, DRAWS = 0, 20
MPNET = "sentence-transformers/all-mpnet-base-v2"
MINILM = "sentence-transformers/all-MiniLM-L6-v2"
REVISIONS = {MPNET: "e8c3b32edf5434bc2275fc9bab85f82640a19130",
             MINILM: "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"}
QUARTERS = [f"{y}-Q{q}" for y in (2023, 2024) for q in (1, 2, 3, 4)]
TARGETS = QUARTERS[1:]
CONSTANT = ["Sergio P. Ermotti", "Jeremy Barnum"]
KEY = ["bank", "quarter", "call_type", "position_in_call", "sentence_number"]


def load_sentences():
    """Earnings-call sentences without operator lines, with masked text and word counts (event call excluded)."""
    import contrast  # masking of phase 0
    from phase1_common import clean_text
    s = pd.read_csv(RELEASE_DIR / "all_sentences.csv")
    s = s[(s.call_type == "earnings") & (s.speaker_role != "operator")].copy()
    s = s.sort_values(KEY).reset_index(drop=True)
    s["plain"] = s.sentence.map(clean_text)
    s["n_words"] = s.plain.str.split().str.len().fillna(0).astype(int)
    s["masked"] = s.sentence.map(contrast.clean)
    s["eligible"] = s.n_words >= 4
    s["qidx"] = s.quarter.map({q: i for i, q in enumerate(QUARTERS)})
    return s


def pool_index(s, bank, quarter, pool_mask, lag1=False):
    """Row positions of the reference pool: same bank, strictly earlier calls (or only the previous call)."""
    q = QUARTERS.index(quarter)
    earlier = s.qidx == q - 1 if lag1 else s.qidx < q
    return np.flatnonzero(((s.bank == bank) & earlier & pool_mask).values)


def reference_size(s, pool_mask):
    """R = smallest pool at the first target call, i.e. the smaller 2023-Q1 call under this pool definition."""
    return int(min(len(pool_index(s, b, TARGETS[0], pool_mask)) for b in ["UBS", "JPM"]))


def novelty(s, X, target_mask, pool_mask, R=None, lag1=False, seed=SEED, draws=DRAWS):
    """Mean over draws of 1 - max cosine to a random sample of R pool sentences, per target sentence.

    X holds L2-normalised rows (dense array or sparse matrix). With lag1 the whole previous call is the
    reference and nothing is sampled. Returns novelty and the mean share of draws with max similarity < 0.5.
    """
    rng = np.random.default_rng(seed)
    nov = np.full(len(s), np.nan); low = np.full(len(s), np.nan)
    for bank in ["UBS", "JPM"]:
        for q in TARGETS:
            tgt = np.flatnonzero(((s.bank == bank) & (s.quarter == q) & target_mask).values)
            pool = pool_index(s, bank, q, pool_mask, lag1)
            if len(tgt) == 0:
                continue
            samples = [pool] if lag1 else [rng.choice(pool, R, replace=False) for _ in range(draws)]
            acc_n = np.zeros(len(tgt)); acc_l = np.zeros(len(tgt))
            for ref in samples:
                sim = X[tgt] @ X[ref].T
                sim = sim.toarray() if hasattr(sim, "toarray") else sim
                m = sim.max(1)
                acc_n += 1 - m; acc_l += m < 0.5
            nov[tgt] = acc_n / len(samples); low[tgt] = acc_l / len(samples)
    return nov, low


def embed(s, model):
    from sentence_transformers import SentenceTransformer
    import torch
    torch.manual_seed(SEED)
    m = SentenceTransformer(model, device="cuda" if torch.cuda.is_available() else "cpu",
                            revision=REVISIONS[model])
    return m.encode(s.masked.tolist(), batch_size=128, normalize_embeddings=True, convert_to_numpy=True)


def tfidf(s):
    from scipy.sparse import csr_matrix, vstack
    from sklearn.feature_extraction.text import TfidfVectorizer
    parts, order = [], []
    for bank in ["UBS", "JPM"]:
        idx = np.flatnonzero((s.bank == bank).values)
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")
        parts.append(vec.fit_transform(s.masked.values[idx])); order.append(idx)
    # each bank has its own vocabulary; novelty only compares within a bank, so rows are padded to one width
    width = max(p.shape[1] for p in parts)
    padded = [csr_matrix((p.data, p.indices, p.indptr), shape=(p.shape[0], width)) for p in parts]
    X = vstack(padded).tocsr()
    inv = np.argsort(np.concatenate(order))
    return X[inv]


def nearest_earlier(s, X, target_mask, pool_mask):
    """Most similar sentence in the full earlier pool (no sampling), for reading and validation."""
    rows = []
    for bank in ["UBS", "JPM"]:
        for q in TARGETS:
            tgt = np.flatnonzero(((s.bank == bank) & (s.quarter == q) & target_mask).values)
            pool = pool_index(s, bank, q, pool_mask)
            sim = X[tgt] @ X[pool].T
            j = sim.argmax(1)
            for t, k, v in zip(tgt, pool[j], sim.max(1)):
                rows.append((t, k, v))
    t, k, v = map(np.array, zip(*rows))
    return pd.DataFrame({"row": t, "nearest_row": k, "nearest_sim_full_pool": v})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = load_sentences()
    elig, allrows = s.eligible, pd.Series(True, index=s.index)
    mgmt_pool = elig & (s.speaker_role == "management")
    X = {"mpnet": embed(s, MPNET), "minilm": embed(s, MINILM), "tfidf": tfidf(s)}
    configs = {  # name: (vectors, target mask, pool mask, lag1)
        "mpnet": ("mpnet", elig, elig, False),
        "minilm": ("minilm", elig, elig, False),
        "tfidf": ("tfidf", elig, elig, False),
        "lag1": ("mpnet", elig, elig, True),
        "ref_mgmt": ("mpnet", elig, mgmt_pool, False),
        "short_kept": ("mpnet", allrows, allrows, False),
    }
    sizes = {}
    for name, (vec, tmask, pmask, lag1) in configs.items():
        R = None if lag1 else reference_size(s, pmask)
        sizes[name] = R
        nov, low = novelty(s, X[vec], tmask, pmask, R, lag1)
        pd.DataFrame({"row": np.arange(len(s)), "novelty": nov, "share_below_05": low}).to_csv(
            OUT / f"novelty_{name}.csv", index=False)
        print(name, "R =", R, "scored", int(np.isfinite(nov).sum()))
    nearest_earlier(s, X["mpnet"], elig, elig).to_csv(OUT / "nearest.csv", index=False)
    s.assign(row=np.arange(len(s)))[["row"] + KEY + ["sentence_id", "section", "speaker_role", "speaker_name",
                                                     "plain", "masked", "n_words", "eligible", "qidx"]].to_csv(
        OUT / "sentences.csv", index=False)
    (OUT / "models.json").write_text(json.dumps(dict(revisions=REVISIONS, reference_sizes=sizes, draws=DRAWS,
                                                     seed=SEED, release=str(RELEASE_DIR.relative_to(ROOT))), indent=2))


if __name__ == "__main__":
    main()
