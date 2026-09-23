"""Phase 2 validation sample: management sentences with their nearest earlier sentence, blind.

Run from the repository root after phase2_inference.py: python notebooks/roman/analysis/phase2_labelling.py
"""
import numpy as np
import pandas as pd

from phase1_common import LABEL_DIR
from phase2_novelty import OUT, SEED


def main():
    rng = np.random.default_rng(SEED)
    m = pd.read_csv(OUT / "management_scored.csv")
    m["quartile"] = m.groupby("bank").novelty.transform(lambda x: pd.qcut(x, 4, labels=[1, 2, 3, 4])).astype(int)
    parts = []
    for k, ((bank, qt), g) in enumerate(m.groupby(["bank", "quartile"])):
        n = 13 if k % 2 == 0 else 12  # 8 cells, 100 items
        parts.append(g.iloc[rng.choice(len(g), n, replace=False)].assign(
            weight=len(g) / n))
    s = pd.concat(parts)
    s = s.iloc[rng.permutation(len(s))].reset_index(drop=True)
    s["item_id"] = [f"N{i:03d}" for i in range(1, len(s) + 1)]
    blind = s[["item_id", "plain", "nearest_text"]].rename(
        columns={"plain": "sentence", "nearest_text": "nearest_earlier_sentence"})
    blind["label_new"] = ""
    blind["notes"] = ""
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    blind.to_csv(LABEL_DIR / "novelty.csv", index=False)
    s[["item_id", "row", "bank", "quarter", "section", "speaker_name", "novelty", "quartile", "weight",
       "nearest_quarter", "nearest_sim_full_pool"]].to_csv(LABEL_DIR / "novelty_key.csv", index=False)
    print(s.groupby(["bank", "quartile"]).size())


if __name__ == "__main__":
    main()
