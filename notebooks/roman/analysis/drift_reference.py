"""Reference drift: similarity between calls against time lag, per bank and view.

Same masking, short-sentence filter (at least 4 words) and views as contrast.py. Each quarter becomes
one document; TF-IDF is fitted on the eight documents of a bank and view. The statistic is Spearman rho
between time lag and cosine similarity over all 28 call pairs. The p-value is one-sided (rho at most the
observed value) from 5000 random permutations of the quarter order, numpy default_rng(0) per bank and view.

Run from the repository root: python notebooks/roman/analysis/drift_reference.py
"""
import itertools, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman"))
OUT = ROOT / "notebooks" / "roman" / "data" / "phase0"
OUT.mkdir(parents=True, exist_ok=True)

import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import contrast

N_PERM, SEED = 5000, 0
EXPECTED = {("analyst_qa", "UBS"): (-0.32, 0.055), ("analyst_qa", "JPM"): (-0.47, 0.008),
            ("constant_mgmt", "UBS"): (-0.61, 0.003), ("constant_mgmt", "JPM"): (-0.85, 0.001)}


def call_similarity(d):
    docs = d.groupby("quarter").text.apply(" ".join).sort_index()
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")
    return list(docs.index), cosine_similarity(vec.fit_transform(docs.values))


def drift_test(S, rng):
    pairs = list(itertools.combinations(range(len(S)), 2))
    sim = np.array([S[i, j] for i, j in pairs])
    lag = lambda t: np.array([abs(t[i] - t[j]) for i, j in pairs])
    obs = spearmanr(lag(np.arange(len(S))), sim).statistic
    null = np.array([spearmanr(lag(rng.permutation(len(S))), sim).statistic for _ in range(N_PERM)])
    return obs, np.mean(null <= obs), len(pairs)


if __name__ == "__main__":
    rows, sims = [], []
    for view, f in contrast.VIEWS.items():
        for bank in ["UBS", "JPM"]:
            calls, S = call_similarity(f(contrast.s[contrast.s.bank == bank]))
            rho, p, n = drift_test(S, np.random.default_rng(SEED))
            rho0, p0 = EXPECTED[(view, bank)]
            rows.append(dict(view=view, bank=bank, n_calls=len(calls), n_call_pairs=n, rho=round(rho, 3), p=p,
                             rho_brief=rho0, p_brief=p0))
            for (i, a), (j, b) in itertools.combinations(enumerate(calls), 2):
                sims.append(dict(view=view, bank=bank, call_a=a, call_b=b, lag=j - i, similarity=S[i, j]))
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "drift_reference.csv", index=False)
    pd.DataFrame(sims).to_csv(OUT / "drift_reference_pairs.csv", index=False)
    print(res.to_string(index=False))
