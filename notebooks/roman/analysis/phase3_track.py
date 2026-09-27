"""Phase 3 tracking: threads of commitment candidates, follow-ups in later calls, proposed statuses.

Run from the repository root after phase3_extract.py: python notebooks/roman/analysis/phase3_track.py
Writes threads.csv (main table for review), followups.csv, summary tables and the labelling sample.
"""
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman"))
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase2_novelty import MPNET, REVISIONS  # noqa: E402
from phase3_extract import (ACHIEVED_RE, OUT, PROGRESS_RE, first_horizon, quantities)  # noqa: E402

THRESHOLD, SENSITIVITY = 0.6, [0.5, 0.7]
SEED = 0
LABEL_DIR = ROOT / "notebooks" / "roman" / "data" / "labelling"


def embed(texts):
    import contrast
    import torch
    from sentence_transformers import SentenceTransformer
    torch.manual_seed(SEED)
    m = SentenceTransformer(MPNET, device="cuda" if torch.cuda.is_available() else "cpu", revision=REVISIONS[MPNET])
    return m.encode([contrast.clean(t) for t in texts], batch_size=128, normalize_embeddings=True,
                    convert_to_numpy=True)


def horizon_year(h):
    return None if pd.isna(h) else pd.Timestamp(h).year


def build_threads(c, X, th):
    """Chronological grouping: join the earliest thread of the same bank and metric whose first mention is similar."""
    order = c.sort_values(["call_date", "position_in_call", "sentence_number"]).index
    anchors, thread_of = [], {}
    for i in order:
        r = c.loc[i]
        joined = None
        for k, a in enumerate(anchors):
            ar = c.loc[a]
            if ar.bank != r.bank or ar.metric != r.metric:
                continue
            if r.type == "guidance":
                ya, yr = horizon_year(ar.horizon), horizon_year(r.horizon)
                if ya is not None and yr is not None and ya != yr:
                    continue
            if float(X[c.index.get_loc(i)] @ X[c.index.get_loc(a)]) >= th:
                joined = k
                break
        if joined is None:
            anchors.append(i); joined = len(anchors) - 1
        thread_of[i] = joined
    return anchors, pd.Series(thread_of)


def status(anchor, text, context, call_date):
    """Proposed status of one follow-up sentence relative to the thread's first mention."""
    av, au = anchor.value, anchor.unit
    fq = quantities(text) or quantities(context)
    same_unit = [v for v, u in fq if u == au]
    fh, _ = first_horizon(text, context, call_date)
    ah = None if pd.isna(anchor.horizon) else pd.Timestamp(anchor.horizon).date()
    moved = fh is not None and ah is not None and fh != ah
    if ACHIEVED_RE.search(text) and not PROGRESS_RE.search(text) and any(v >= av * 0.99 for v in same_unit):
        return "achieved", fh
    if same_unit:
        close = min(same_unit, key=lambda v: abs(v - av))
        if abs(close - av) <= 0.01 * max(abs(av), 1e-9):
            return ("horizon_moved" if moved else "restated"), fh
        return ("revised_up" if close > av else "revised_down"), fh
    return ("horizon_moved" if moved else "mentioned_no_value"), fh


def track(st, c, X_all, pos, th):
    anchors, thread_of = build_threads(c, X_all[[pos[i] for i in c.stmt_id]], th)
    c = c.assign(thread=thread_of.reindex(c.index).values)
    earnings = st[st.call_type == "earnings"]
    last_call = earnings.groupby("bank").call_date.max()
    rows, fups = [], []
    for k, a in enumerate(anchors):
        ar = c.loc[a]
        later = earnings[(earnings.bank == ar.bank) & (earnings.call_date > ar.call_date) & (earnings.metric == ar.metric)]
        statuses = {}
        for q, g in later.groupby("quarter"):
            if ar.type == "guidance":
                ya = horizon_year(ar.horizon)
                gy = g.horizon.map(horizon_year)
                g = g[~((gy.notna()) & (ya is not None) & (gy != ya))]
            if g.empty:
                continue
            sims = X_all[[pos[i] for i in g.stmt_id]] @ X_all[pos[ar.stmt_id]]
            j = int(np.argmax(sims))
            if sims[j] < th:
                continue
            f = g.iloc[j]
            stt, fh = status(ar, f.text, f.context, pd.Timestamp(f.call_date).date())
            statuses[q] = stt
            fups.append(dict(thread=k, bank=ar.bank, quarter=q, similarity=float(sims[j]), proposed_status=stt,
                             followup_value=quantities(f.text)[0][0] if quantities(f.text) else np.nan,
                             followup_horizon=fh, text=f.text, stmt_id=f.stmt_id))
        if statuses:
            final = statuses[max(statuses)]
        else:
            hz = None if pd.isna(ar.horizon) else pd.Timestamp(ar.horizon)
            if hz is None:
                final = "no_follow_up_found_horizon_unknown"
            elif hz <= pd.Timestamp(last_call[ar.bank]):
                final = "no_follow_up_found_due_within_window"
            else:
                final = "no_follow_up_found_not_due_in_window"
        members = c[c.thread == k]
        rows.append(dict(thread=k, bank=ar.bank, origin_call=f"{ar.quarter} {ar.call_type}", origin_only=ar.origin_only,
                         first_call_date=ar.call_date, speaker=ar.speaker_name, section=ar.section, metric=ar.metric,
                         type=ar.type, value=ar.value, unit=ar.unit, horizon=ar.horizon, horizon_label=ar.horizon_label,
                         first_mention=ar.text, candidate_mentions=len(members),
                         followup_calls=len(statuses), **{f"status_{q}": s for q, s in statuses.items()},
                         proposed_final_status=final, status_reviewed="", notes=""))
    return pd.DataFrame(rows), pd.DataFrame(fups), c


def labelling_sample(st, c, rng):
    """About 100 candidates by bank and type, plus 50 non-candidates with a quantity per bank."""
    parts = []
    cells = c[c.call_type == "earnings"].groupby(["bank", "type"])
    total = sum(len(g) for _, g in cells)
    for (bank, typ), g in cells:
        n = min(len(g), max(8, round(100 * len(g) / total)))
        parts.append(g.iloc[rng.choice(len(g), n, replace=False)].assign(stratum=f"candidate_{typ}"))
    for bank in ["UBS", "JPM"]:
        non = st[(st.bank == bank) & (st.call_type == "earnings") & ~st.candidate & st.has_quantity]
        for hz, name in [(True, "noncandidate_quantity_horizon"), (False, "noncandidate_quantity_only")]:
            g = non[non.has_horizon == hz]
            parts.append(g.iloc[rng.choice(len(g), min(25, len(g)), replace=False)].assign(stratum=name))
    smp = pd.concat(parts)
    pop = {}
    for (bank, typ), g in cells:
        pop[(bank, f"candidate_{typ}")] = len(g)
    for bank in ["UBS", "JPM"]:
        non = st[(st.bank == bank) & (st.call_type == "earnings") & ~st.candidate & st.has_quantity]
        pop[(bank, "noncandidate_quantity_horizon")] = int(non.has_horizon.sum())
        pop[(bank, "noncandidate_quantity_only")] = int((~non.has_horizon).sum())
    n_smp = smp.groupby(["bank", "stratum"]).size()
    smp["weight"] = [pop[(b, s)] / n_smp[(b, s)] for b, s in zip(smp.bank, smp.stratum)]
    smp = smp.iloc[rng.permutation(len(smp))].reset_index(drop=True)
    smp["item_id"] = [f"C{i:03d}" for i in range(1, len(smp) + 1)]
    blind = smp[["item_id", "text", "context"]].rename(columns={"text": "sentence"})
    blind["label_commitment"] = ""; blind["notes"] = ""
    key = smp[["item_id", "stmt_id", "bank", "quarter", "stratum", "weight", "candidate", "metric", "type"]]
    return blind, key


def main():
    st = pd.read_csv(OUT / "statements.csv")
    st["text"] = st.text.fillna("")  # statements that consist only of a bracket insertion
    st["context"] = st.context.fillna("")
    c = pd.read_csv(OUT / "candidates.csv")
    c["context"] = c.context.fillna("")
    pos = {sid: i for i, sid in enumerate(st.stmt_id)}
    X_all = embed(st.text.tolist())
    threads, fups, c = track(st, c, X_all, pos, THRESHOLD)
    threads.to_csv(OUT / "threads.csv", index=False)
    fups.to_csv(OUT / "followups.csv", index=False)
    c.to_csv(OUT / "candidates_threaded.csv", index=False)

    n_mgmt = st[st.call_type == "earnings"].groupby("bank").size()
    summ = threads.groupby(["bank", "type"]).agg(threads=("thread", "size"), candidates=("candidate_mentions", "sum"))
    summ = summ.reset_index()
    summ["threads_per_1000_mgmt_sentences"] = summ.threads / summ.bank.map(n_mgmt) * 1000
    summ.to_csv(OUT / "summary_threads.csv", index=False)
    threads.groupby(["bank", "type", "proposed_final_status"]).size().rename("threads").reset_index().to_csv(
        OUT / "summary_status.csv", index=False)

    sens = []
    for th in SENSITIVITY + [THRESHOLD]:
        t, _, _ = track(st, pd.read_csv(OUT / "candidates.csv").fillna({"context": ""}), X_all, pos, th)
        sens.append(t.groupby(["bank", "type", "proposed_final_status"]).size().rename("threads").reset_index()
                    .assign(threshold=th))
    pd.concat(sens).to_csv(OUT / "sensitivity_thresholds.csv", index=False)

    blind, key = labelling_sample(st, c, np.random.default_rng(SEED))
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    blind.to_csv(LABEL_DIR / "commitments.csv", index=False)
    key.to_csv(LABEL_DIR / "commitments_key.csv", index=False)
    (OUT / "meta.json").write_text(json.dumps(dict(threshold=THRESHOLD, sensitivity=SENSITIVITY, model=MPNET,
                                                   revision=REVISIONS[MPNET], seed=SEED,
                                                   management_statements=n_mgmt.to_dict()), indent=2))
    print(summ.to_string(index=False))
    print(threads.groupby(["bank", "type", "proposed_final_status"]).size().to_string())
    print(key.groupby(["bank", "stratum"]).size())


if __name__ == "__main__":
    main()
