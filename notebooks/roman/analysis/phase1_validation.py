"""Phase 1 validation: Roman's labels of deflection.csv against the detectors, with the pre-registered gate.

Run from the repository root: python notebooks/roman/analysis/phase1_validation.py
Estimation as in plans/phase_1.md: every sampled sentence carries the weight N_stratum / n_stratum of its stratum;
precision is the weighted share of true deflections among flagged sentences, the miss share the weighted share of
true deflections that the detector does not flag (one minus recall). Cohen's kappa is computed on the sample,
unweighted. Intervals come from a stratified bootstrap over sentences (2,000 resamples, seed 0), as a supplement.
Writes validation_metrics.csv, validation_gate.csv, validation_notes.csv and validation_items.csv to
notebooks/roman/data/phase1/.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
LAB = ROOT / "notebooks" / "roman" / "data" / "labelling"
OUT = ROOT / "notebooks" / "roman" / "data" / "phase1"
NLI_THRESHOLD, SEED, N_BOOT = 0.9, 0, 2000
DETECTORS = {"primary (phrase list or NLI)": lambda d: d.phrase | (d.nli_max >= NLI_THRESHOLD),
             "phrase list only": lambda d: d.phrase,
             "NLI only": lambda d: d.nli_max >= NLI_THRESHOLD}


def load():
    lab = pd.read_csv(LAB / "deflection.csv", keep_default_na=False)
    key = pd.read_csv(LAB / "deflection_key.csv")
    d = lab.merge(key, on="item_id", validate="one_to_one")
    d["label"] = d.label_deflection.astype(int)
    d["phrase"] = d.phrase.astype(bool)
    return d


def kappa(a, b):
    a, b = np.asarray(a, int), np.asarray(b, int)
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def estimate(d, flag):
    w, y, f = d.weight.values, d.label.values, flag.values.astype(bool)
    tp = (w * y * f).sum()
    precision = tp / (w * f).sum() if f.any() else np.nan
    recall = tp / (w * y).sum() if y.any() else np.nan
    return precision, recall


def bootstrap(d, det, rng):
    res = []
    groups = [g for _, g in d.groupby("stratum")]
    for _ in range(N_BOOT):
        s = pd.concat([g.iloc[rng.integers(0, len(g), len(g))] for g in groups])
        res.append(estimate(s, det(s)))
    res = np.array(res, float)
    return [np.nanpercentile(res[:, i], [2.5, 97.5]) for i in (0, 1)]


def main():
    d = load()
    rows = []
    for bank in ["UBS", "JPM"]:
        b = d[d.bank == bank]
        for name, det in DETECTORS.items():
            flag = det(b)
            p, r = estimate(b, flag)
            (p_lo, p_hi), (r_lo, r_hi) = bootstrap(b, det, np.random.default_rng(SEED))
            rows.append(dict(bank=bank, detector=name, items=len(b), flagged_in_sample=int(flag.sum()),
                             true_flagged=int((flag & (b.label == 1)).sum()),
                             true_unflagged=int((~flag & (b.label == 1)).sum()),
                             precision=p, precision_ci=f"{p_lo:.2f} to {p_hi:.2f}",
                             recall=r, miss_share=1 - r, miss_share_ci=f"{1 - r_hi:.2f} to {1 - r_lo:.2f}",
                             kappa=kappa(b.label, flag)))
    m = pd.DataFrame(rows)
    m.to_csv(OUT / "validation_metrics.csv", index=False)

    prim = m[m.detector.str.startswith("primary")].set_index("bank")
    gate = pd.DataFrame([
        dict(condition="precision below 0.7 in UBS", value=prim.loc["UBS", "precision"], fails=prim.loc["UBS", "precision"] < 0.7),
        dict(condition="precision below 0.7 in JPM", value=prim.loc["JPM", "precision"], fails=prim.loc["JPM", "precision"] < 0.7),
        dict(condition="precision differs by more than 0.2", value=abs(prim.loc["UBS", "precision"] - prim.loc["JPM", "precision"]),
             fails=abs(prim.loc["UBS", "precision"] - prim.loc["JPM", "precision"]) > 0.2),
        dict(condition="miss share differs by more than 0.2", value=abs(prim.loc["UBS", "miss_share"] - prim.loc["JPM", "miss_share"]),
             fails=abs(prim.loc["UBS", "miss_share"] - prim.loc["JPM", "miss_share"]) > 0.2)])
    gate.to_csv(OUT / "validation_gate.csv", index=False)

    d["primary_flag"] = DETECTORS["primary (phrase list or NLI)"](d)
    d["agree"] = d.primary_flag.astype(int) == d.label
    d["note_class"] = np.select([d.notes.str.contains("zuordnung falsch", case=False),
                                 d.notes.str.contains("unsicher|grenzfall", case=False)],
                                ["alignment wrong", "uncertain or borderline"], "no note")
    notes = d.groupby("note_class").agg(items=("item_id", "size"), agreement=("agree", "mean")).reset_index()
    notes.to_csv(OUT / "validation_notes.csv", index=False)
    d[["item_id", "bank", "quarter", "stratum", "weight", "phrase", "nli_max", "primary_flag", "label", "agree",
       "note_class", "answer_sentence"]].to_csv(OUT / "validation_items.csv", index=False)
    print(m.round(3).to_string(index=False)); print(gate.to_string(index=False)); print(notes.to_string(index=False))
    print(d.groupby(["bank", "stratum"]).agg(n=("label", "size"), true=("label", "sum"), weight=("weight", "first")))


if __name__ == "__main__":
    main()
