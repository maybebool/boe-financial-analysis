"""Phase 2 inference: P2-2 (decay, primary), E1 (level) with robustness variants, E2 to E6.

Run from the repository root after phase2_novelty.py: python notebooks/roman/analysis/phase2_inference.py
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase1_common import CAPITAL_RE  # noqa: E402
from phase1_inference import holm  # noqa: E402
from phase2_novelty import CONSTANT, OUT, QUARTERS, TARGETS  # noqa: E402

REGISTER = ROOT / "notebooks" / "roman" / "plans" / "test_register.csv"
VARIANTS = {  # name: (novelty file, target selection, column)
    "primary": ("mpnet", "management", "novelty"),
    "constant_speakers": ("mpnet", "constant", "novelty"),
    "minilm": ("minilm", "management", "novelty"),
    "tfidf": ("tfidf", "management", "novelty"),
    "lag1_reference": ("lag1", "management", "novelty"),
    "reference_management_only": ("ref_mgmt", "management", "novelty"),
    "share_below_0.5": ("mpnet", "management", "share_below_05"),
    "short_kept": ("short_kept", "management", "novelty"),
}


def load(name):
    s = pd.read_csv(OUT / "sentences.csv")
    n = pd.read_csv(OUT / f"novelty_{name}.csv")
    return s.merge(n, on="row")


def select(d, who):
    if who == "management":
        return d[d.speaker_role == "management"]
    if who == "constant":
        return d[d.speaker_name.isin(CONSTANT)]
    return d[d.speaker_role == who]


def call_values(d, col):
    d = d[d.quarter.isin(TARGETS) & d[col].notna()]
    c = d.groupby(["bank", "quarter"])[col].mean().rename("value").reset_index()
    c["t"] = c.quarter.map({q: i for i, q in enumerate(TARGETS)})
    return c


def slope(t, v):
    return np.polyfit(t, v, 1)[0]


def stats(c):
    u, j = c[c.bank == "UBS"], c[c.bank == "JPM"]
    su, sj = slope(u.t, u.value), slope(j.t, j.value)
    return dict(slope_UBS=su, slope_JPM=sj, T_decay=su - sj,
                level_UBS=u.value.mean(), level_JPM=j.value.mean(), T_level=u.value.mean() - j.value.mean())


def permutation(c):
    """Exact permutation of bank labels over the 14 target calls (3,432 splits), two-sided."""
    t, v = c.t.values, c.value.values
    obs = stats(c)
    d_null, l_null = [], []
    for g in itertools.combinations(range(len(v)), len(v) // 2):
        a = np.zeros(len(v), bool); a[list(g)] = True
        d_null.append(slope(t[a], v[a]) - slope(t[~a], v[~a]))
        l_null.append(v[a].mean() - v[~a].mean())
    d_null, l_null = np.array(d_null), np.array(l_null)
    return dict(obs, p_decay=np.mean(np.abs(d_null) >= abs(obs["T_decay"]) - 1e-12),
                p_level=np.mean(np.abs(l_null) >= abs(obs["T_level"]) - 1e-12), n_splits=len(d_null))


def sign_flip(c):
    """Paired alternative: swap the two banks' values within quarters (2^7 = 128 flips), two-sided."""
    w = c.pivot(index="t", columns="bank", values="value").sort_index()
    t = w.index.values
    obs = stats(c)
    d_null, l_null = [], []
    for flips in itertools.product([False, True], repeat=len(w)):
        f = np.array(flips)
        u = np.where(f, w.JPM, w.UBS); j = np.where(f, w.UBS, w.JPM)
        d_null.append(slope(t, u) - slope(t, j)); l_null.append(u.mean() - j.mean())
    d_null, l_null = np.array(d_null), np.array(l_null)
    return dict(obs, p_decay=np.mean(np.abs(d_null) >= abs(obs["T_decay"]) - 1e-12),
                p_level=np.mean(np.abs(l_null) >= abs(obs["T_level"]) - 1e-12), n_splits=len(d_null))


def drift_embeddings():
    """E5: call centroids on the primary embeddings, Spearman rho of similarity on lag, as drift_reference.py."""
    import numpy as np
    from drift_reference import drift_test
    from phase2_novelty import embed, load_sentences, MPNET
    s = load_sentences()
    s = s[s.eligible]
    X = embed(s, MPNET)
    views = {"analyst_qa": (s.section == "qa") & (s.speaker_role == "analyst"),
             "constant_mgmt": s.speaker_name.isin(CONSTANT)}
    rows = []
    for view, m in views.items():
        for bank in ["UBS", "JPM"]:
            sel = (m & (s.bank == bank)).values
            cent = np.vstack([X[sel & (s.quarter == q).values].mean(0) for q in QUARTERS])
            cent /= np.linalg.norm(cent, axis=1, keepdims=True)
            rho, p, n = drift_test(cent @ cent.T, np.random.default_rng(0))
            rows.append(dict(view=view, bank=bank, rho_embeddings=rho, p_embeddings=p))
    return pd.DataFrame(rows)


def main():
    res, curves = [], []
    for name, (f, who, col) in VARIANTS.items():
        c = call_values(select(load(f), who), col)
        res.append(dict(variant=name, test="permutation_14_calls", **permutation(c)))
        curves.append(c.assign(variant=name))
        if name == "primary":
            res.append(dict(variant="paired_sign_flip", test="sign_flip_within_quarter", **sign_flip(c)))
    res = pd.DataFrame(res)
    res.to_csv(OUT / "p2_decay_and_level.csv", index=False)
    pd.concat(curves).to_csv(OUT / "call_novelty.csv", index=False)

    prim = res.iloc[0]
    reg = pd.read_csv(REGISTER)
    reg = reg[reg.phase != 2]
    reg = pd.concat([reg, pd.DataFrame([dict(
        phase=2, test_id="P2-2", hypothesis="UBS management novelty decays at a different rate than JPM after completion",
        statistic="OLS slope of call novelty on quarter index 2023-Q2..2024-Q4, UBS minus JPM",
        p_raw=prim.p_decay)])], ignore_index=True)
    reg["p_holm"] = holm(reg.p_raw)
    reg.to_csv(REGISTER, index=False)

    # E2 curves by role and section, E4 analysts
    d = load("mpnet")
    d = d[d.quarter.isin(TARGETS) & d.novelty.notna()]
    d["group"] = np.where(d.speaker_role == "management", "management " + d.section, d.speaker_role)
    e2 = d.groupby(["bank", "quarter", "group"]).agg(novelty=("novelty", "mean"), sentences=("novelty", "size"))
    e2.reset_index().to_csv(OUT / "e2_curves.csv", index=False)
    ca = call_values(select(load("mpnet"), "analyst"), "novelty")
    pd.DataFrame([permutation(ca)]).to_csv(OUT / "e4_analysts.csv", index=False)

    # E3 what is new
    s = pd.read_csv(OUT / "sentences.csv")
    near = pd.read_csv(OUT / "nearest.csv")
    m = d[d.speaker_role == "management"].merge(near, on="row")
    m["nearest_text"] = m.nearest_row.map(s.set_index("row").plain)
    m["nearest_quarter"] = m.nearest_row.map(s.set_index("row").quarter)
    top = m.sort_values("novelty", ascending=False).groupby(["bank", "quarter"]).head(10)
    top.sort_values(["bank", "quarter", "novelty"], ascending=[True, True, False])[
        ["bank", "quarter", "section", "speaker_name", "novelty", "plain", "nearest_quarter", "nearest_text",
         "nearest_sim_full_pool"]].to_csv(OUT / "e3_top_novel.csv", index=False)
    m["novel"] = m.novelty > 0.5
    m["capital_kw"] = m.plain.fillna("").str.contains(CAPITAL_RE)
    m["year"] = m.quarter.str[:4]
    e3 = m[m.novel].groupby(["bank", "year"]).agg(novel_sentences=("novel", "size"),
                                                  capital_share=("capital_kw", "mean")).reset_index()
    e3 = e3.merge(m.groupby(["bank", "year"]).agg(all_sentences=("novel", "size"),
                                                   novel_share=("novel", "mean"),
                                                   capital_share_all=("capital_kw", "mean")).reset_index())
    e3.to_csv(OUT / "e3_capital_share.csv", index=False)
    m.to_csv(OUT / "management_scored.csv", index=False)

    drift_embeddings().to_csv(OUT / "e5_drift_embeddings.csv", index=False)

    # E6 (amendment after results): prepared remarks and Q&A weighted equally per call
    mg = d[d.speaker_role == "management"]
    sec = mg.groupby(["bank", "quarter", "section"]).novelty.mean().unstack("section")
    c6 = sec.mean(axis=1).rename("value").reset_index()
    c6["t"] = c6.quarter.map({q: i for i, q in enumerate(TARGETS)})
    pd.DataFrame([permutation(c6)]).to_csv(OUT / "e6_sections_equal.csv", index=False)
    sec.reset_index().merge(c6, on=["bank", "quarter"]).to_csv(OUT / "e6_call_values.csv", index=False)
    short = pd.read_csv(OUT / "sentences.csv").assign(short=lambda x: ~x.eligible)
    (OUT / "phase2_meta.json").write_text(json.dumps(
        {"short_share": short.groupby(["bank", "speaker_role"]).short.mean().round(4).unstack().to_dict()}, indent=2))
    print(res.round(4).to_string(index=False)); print(reg.to_string(index=False))


if __name__ == "__main__":
    main()
