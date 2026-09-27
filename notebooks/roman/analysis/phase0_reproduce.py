"""Phase 0: rerun contrast.py and qa_pairs.py and store every number the brief records.

Run from the repository root: python notebooks/roman/analysis/phase0_reproduce.py
"""
import itertools, json, platform, sys, warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="Unknown solver options")  # sklearn 1.6 vs scipy 1.18

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman"))
OUT = ROOT / "notebooks" / "roman" / "data" / "phase0"
OUT.mkdir(parents=True, exist_ok=True)

import numpy as np, pandas as pd
from scipy.stats import binomtest, spearmanr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import contrast, qa_pairs

EXPECTED_AUC = {("analyst_qa", "UBS"): (815, 0.489, 1.000), ("analyst_qa", "JPM"): (728, 0.489, 1.000),
                ("constant_mgmt", "UBS"): (1320, 0.562, 0.714), ("constant_mgmt", "JPM"): (2135, 0.507, 0.971)}
EXPECTED_RATE = {"UBS": 4.3, "JPM": 1.2}
EXPECTED_PAIRS = {"UBS": 129, "JPM": 246}
EXPECTED_RHO = {"UBS": -0.61, "JPM": -0.85}
CONSTANT = {"UBS": "Sergio P. Ermotti", "JPM": "Jeremy Barnum"}


def run_contrast():
    rows = []
    for view, f in contrast.VIEWS.items():
        for bank in ["UBS", "JPM"]:
            d = f(contrast.s[contrast.s.bank == bank]).reset_index(drop=True)
            auc, p, q95 = contrast.permutation_test(d)
            n0, auc0, p0 = EXPECTED_AUC[(view, bank)]
            rows.append(dict(view=view, bank=bank, n=len(d), auc=round(auc, 3), null95=round(q95, 3), p=round(p, 3),
                             n_brief=n0, auc_brief=auc0, p_brief=p0,
                             match=(len(d) == n0) and round(auc, 3) == auc0 and round(p, 3) == p0))
    return pd.DataFrame(rows)


def run_qa():
    p = qa_pairs.build_pairs(qa_pairs.u)
    p["non_answer_hits"] = p.answer.map(lambda t: len(qa_pairs.NA_RE.findall(t)))
    p["answer_words"] = p.answer.str.split().str.len()
    p.to_csv(OUT / "qa_pairs.csv", index=False)
    g = p.groupby("bank").agg(pairs=("answer", "size"), hits=("non_answer_hits", "sum"),
                              pairs_with_hit=("non_answer_hits", lambda x: int((x > 0).sum())),
                              answer_words=("answer_words", "sum")).reset_index()
    g["rate_per_10k"] = (g.hits / g.answer_words * 1e4).round(2)
    g["pairs_brief"] = g.bank.map(EXPECTED_PAIRS)
    g["rate_brief"] = g.bank.map(EXPECTED_RATE)
    g["match"] = (g.pairs == g.pairs_brief) & (g.rate_per_10k.round(1) == g.rate_brief)
    ubs = g.set_index("bank").loc["UBS"]
    share = ubs.answer_words / g.answer_words.sum()
    test = binomtest(int(ubs.hits), int(g.hits.sum()), share)
    hits = []
    for _, r in p[p.non_answer_hits > 0].iterrows():
        for m in qa_pairs.NA_RE.finditer(r.answer):
            hits.append(dict(bank=r.bank, quarter=r.quarter, position_in_call=r.position_in_call, analyst=r.analyst,
                             phrase=m.group(0), context=r.answer[max(0, m.start() - 150):m.end() + 150]))
    binom = dict(ubs_hits=int(ubs.hits), total_hits=int(g.hits.sum()), ubs_word_share=round(share, 4),
                 p_two_sided=round(test.pvalue, 4), note="not clustered by call")
    return g, pd.DataFrame(hits), binom


def run_drift():
    """Reconstruction attempt: no script for the recorded drift numbers exists."""
    s = contrast.s
    order = {q: i for i, q in enumerate(sorted(s.quarter.unique()))}
    rows = []
    for bank, spk in CONSTANT.items():
        d = s[s.speaker_name == spk]
        for variant in ["one_document_per_call", "mean_sentence_vector_per_call"]:
            vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, sublinear_tf=True, stop_words="english")
            if variant == "one_document_per_call":
                docs = d.groupby("quarter").text.apply(" ".join)
                X, calls = vec.fit_transform(docs.values), list(docs.index)
            else:
                Xs = vec.fit_transform(d.text); calls = sorted(d.quarter.unique())
                X = np.vstack([np.asarray(Xs[(d.quarter == c).values].mean(0)) for c in calls])
            S = cosine_similarity(X)
            lag, sim = zip(*[(abs(order[a] - order[b]), S[i, j])
                             for (i, a), (j, b) in itertools.combinations(enumerate(calls), 2)])
            r = spearmanr(lag, sim)
            rows.append(dict(bank=bank, speaker=spk, variant=variant, n_call_pairs=len(lag),
                             rho=round(r.statistic, 3), p=round(r.pvalue, 4), rho_brief=EXPECTED_RHO[bank]))
    return pd.DataFrame(rows)


def environment():
    import sklearn, scipy, torch, transformers, sentence_transformers
    return dict(python=platform.python_version(), platform=platform.platform(),
                numpy=np.__version__, pandas=pd.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__,
                torch=torch.__version__, transformers=transformers.__version__,
                sentence_transformers=sentence_transformers.__version__,
                cuda_available=torch.cuda.is_available(),
                cuda_device=torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
                torch_cuda_version=torch.version.cuda)


if __name__ == "__main__":
    auc = run_contrast(); auc.to_csv(OUT / "contrast_auc.csv", index=False)
    rates, hits, binom = run_qa()
    rates.to_csv(OUT / "nonanswer_by_bank.csv", index=False); hits.to_csv(OUT / "nonanswer_hits.csv", index=False)
    drift = run_drift(); drift.to_csv(OUT / "drift_reconstruction.csv", index=False)
    (OUT / "nonanswer_binomial.json").write_text(json.dumps(binom, indent=2))
    (OUT / "environment.json").write_text(json.dumps(environment(), indent=2))
    print(auc.to_string(index=False)); print(rates.to_string(index=False)); print(binom); print(drift.to_string(index=False))
