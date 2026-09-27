"""Phase 3g, step 1: FLS models on the phase 3 sentence basis, cross-tables, the additional set S and the blind
spot check.

Run from the repository root: python notebooks/roman/analysis/phase3g_fls.py
Writes scored.csv, crosstabs.csv, set_s.csv and models.json to notebooks/roman/data/phase3g/, and the blind spot
check to notebooks/roman/data/labelling/phase3g_spotcheck.csv (drawn before any reading of S).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase3_extract import FORWARD_RE, horizons, quantities  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3g"
LAB = DATA / "labelling"
FINBERT = ("yiyanghkust/finbert-fls", "443586dc31c765c0aaf1c4daaed8cf3643c92fa5")
ROBERTA = ("soleimanian/fls-roberta", "aebefd6b2c23a622afaafb99efdfdafd033779d5")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
SEED, SPOT_SEED, READ_CAP = 0, 1, 150


@torch.no_grad()
def predict(model_id, texts):
    name, rev = model_id
    tok = AutoTokenizer.from_pretrained(name, revision=rev)
    model = AutoModelForSequenceClassification.from_pretrained(name, revision=rev).to(DEVICE).eval()
    probs = []
    for i in range(0, len(texts), 64):
        enc = tok(texts[i:i + 64], truncation=True, max_length=256, padding=True, return_tensors="pt").to(DEVICE)
        probs.append(torch.softmax(model(**enc).logits.float(), -1).cpu().numpy())
    return np.concatenate(probs), model.config.id2label


def basis():
    st = pd.read_csv(DATA / "phase3" / "statements.csv")
    st["text"] = st.text.fillna("")
    sel = ((st.bank == "UBS") & (st.call_type == "earnings") & (st.quarter >= "2023-Q2")) | \
          ((st.bank == "JPM") & (st.call_type == "event"))
    return st[sel].reset_index(drop=True)


def main():
    torch.manual_seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    d = basis()
    texts = d.text.tolist()
    pf, lab_f = predict(FINBERT, texts)
    pr, lab_r = predict(ROBERTA, texts)
    idx_r = {v: int(k) for k, v in lab_r.items()}
    d["finbert"] = [lab_f[int(i)] for i in pf.argmax(1)]
    d["finbert_p_specific"] = pf[:, [int(k) for k, v in lab_f.items() if v == "Specific FLS"][0]]
    d["roberta_fls"] = pr[:, idx_r["FLS"]] > pr[:, idx_r["non_FLS"]]  # placeholder label 'label' ignored
    d["specific"] = d.finbert == "Specific FLS"
    d["has_number"] = d.text.map(lambda t: bool(quantities(t)))
    d["cond_quantity"] = d.has_number
    d["cond_horizon"] = [bool(horizons(t, pd.Timestamp(c).date())) for t, c in zip(d.text, d.call_date)]
    d["cond_forward_word"] = d.text.map(lambda t: bool(FORWARD_RE.search(t)))
    d["call"] = d.bank + " " + d.call_type
    d.to_csv(OUT / "scored.csv", index=False)

    tabs = []
    for call, g in d.groupby("call"):
        for a, b in [("candidate", "specific"), ("candidate", "roberta_fls"), ("specific", "roberta_fls")]:
            ct = pd.crosstab(g[a], g[b]).stack().rename("sentences").reset_index()
            ct.columns = ["row_value", "col_value", "sentences"]
            tabs.append(ct.assign(call=call, row=a, col=b))
    pd.concat(tabs)[["call", "row", "row_value", "col", "col_value", "sentences"]].to_csv(OUT / "crosstabs.csv",
                                                                                      index=False)

    s = d[d.specific & d.has_number & ~d.candidate].copy()
    s["failed_conditions"] = [", ".join(n for n, ok in [("quantity", q), ("horizon", h), ("forward word", w)] if not ok)
                              for q, h, w in zip(s.cond_quantity, s.cond_horizon, s.cond_forward_word)]
    s["to_read"] = True
    if len(s) > READ_CAP:  # rule fixed in the plan: stratified random sample of 150, seed 0
        rng = np.random.default_rng(SEED)
        keep = []
        for _, g in s.groupby("call"):
            n = round(READ_CAP * len(g) / len(s))
            keep += list(g.index[rng.choice(len(g), min(n, len(g)), replace=False)])
        s["to_read"] = s.index.isin(keep)
    s["weight"] = s.groupby("call").to_read.transform(lambda x: len(x) / max(x.sum(), 1))
    s.to_csv(OUT / "set_s.csv", index=False)

    # blind spot check, drawn before any reading of S
    rng = np.random.default_rng(SPOT_SEED)
    spot = s.iloc[rng.choice(len(s), min(10, len(s)), replace=False)]
    allst = pd.read_csv(DATA / "phase3" / "statements.csv")
    allst["text"] = allst.text.fillna("")
    grp = allst.groupby(["bank", "quarter", "call_type", "position_in_call"], sort=False).text
    allst["before"] = grp.shift(1).fillna("")
    allst["after"] = grp.shift(-1).fillna("")
    ctx = allst.set_index("stmt_id")
    blind = pd.DataFrame({"item_id": [f"G{i:02d}" for i in range(1, len(spot) + 1)],
                          "sentence": spot.text.values, "call": spot.call.values, "quarter": spot.quarter.values,
                          "context_before": ctx.loc[spot.stmt_id, "before"].values,
                          "context_after": ctx.loc[spot.stmt_id, "after"].values,
                          "genuine": "", "duplicate_of": "", "notes": ""})
    LAB.mkdir(parents=True, exist_ok=True)
    blind.to_csv(LAB / "phase3g_spotcheck.csv", index=False)
    pd.DataFrame({"item_id": blind.item_id, "stmt_id": spot.stmt_id.values}).to_csv(
        OUT / "spotcheck_key.csv", index=False)

    (OUT / "models.json").write_text(json.dumps({"finbert": FINBERT, "roberta": ROBERTA, "device": DEVICE,
                                                 "finbert_labels": lab_f, "roberta_labels": lab_r,
                                                 "seed": SEED, "spot_seed": SPOT_SEED, "read_cap": READ_CAP},
                                                indent=2))
    print(d.groupby(["call", "candidate", "specific"]).size().unstack(fill_value=0))
    print("S:", len(s), "to read:", int(s.to_read.sum()))
    print(s.groupby(["call", "failed_conditions"]).size())


if __name__ == "__main__":
    main()
