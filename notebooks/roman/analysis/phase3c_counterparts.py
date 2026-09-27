"""Phase 3c: counterparts of the phase 3 commitment candidates in the banks' reports.

Run from the repository root after phase3_track.py and phase3b_reports.py:
    python notebooks/roman/analysis/phase3c_counterparts.py
Writes to notebooks/roman/data/phase3c/ and the blind labelling sample to notebooks/roman/data/labelling/.
Rules as in plans/phase_3c.md.
"""
import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman"))
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
from phase2_novelty import MPNET, REVISIONS  # noqa: E402
from phase3_extract import FORWARD_RE, METRIC_RE, QTY_RE, horizons  # noqa: E402
from phase3b_reports import file_hashes  # noqa: E402

PHASE3 = ROOT / "notebooks" / "roman" / "data" / "phase3"
PHASE3B = ROOT / "notebooks" / "roman" / "data" / "phase3b"
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3c"
LABEL_DIR = ROOT / "notebooks" / "roman" / "data" / "labelling" / "discarded_phase3c"  # sample discarded, see plan status
SEED, N_BOOT, SIM_THRESHOLD = 0, 2000, 0.6
QUARTERS = [f"{y}-Q{q}" for y in (2023, 2024) for q in (1, 2, 3, 4)]
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
METRIC_OF = {g: rx for g, _, rx in METRIC_RE}


def split_sentences(text):
    """Split at . ! ? followed by whitespace and a capital letter. A full stop between two digits (3.5, 91.5)
    is never followed by whitespace, so decimals always stay intact."""
    return [s.strip() for s in SENT_SPLIT_RE.split(str(text)) if s.strip()]


def quantities_precise(text):
    """Quantities with unit class, value in the unit class and rounding tolerance of the displayed figure."""
    out = []
    for m in QTY_RE.finditer(text):
        cur, num, unit = m.group("cur"), m.group("num"), (m.group("unit") or "").lower()
        if not cur and not unit:
            continue
        v = float(num.replace(",", ""))
        dec = len(num.split(".")[1]) if "." in num else 0
        half = 0.5 * 10 ** (-dec)
        if unit in ("%", "percent", "per cent"):
            out.append((v, "pct", half))
        elif unit.startswith("bps") or unit.startswith("basis point"):
            out.append((v, "bps", half))
        elif unit in ("billion", "bn"):
            out.append((v, "amount_bn", half))
        elif unit in ("million", "mn"):
            out.append((v / 1000, "amount_bn", half / 1000))
        elif unit in ("trillion", "tn"):
            out.append((v * 1000, "amount_bn", half * 1000))
        else:
            out.append((v, "currency", half))
    return out


def matches(a, b, exact=False):
    """a, b: (value, unit, half-unit tolerance). Primary: within the tolerance of the less precise figure."""
    if a[1] != b[1]:
        return False
    if exact:
        return abs(a[0] - b[0]) < 1e-9
    return abs(a[0] - b[0]) <= max(a[2], b[2]) + 1e-12


def period_end(quarter_label):
    if "annual" in quarter_label:
        return date(int(quarter_label[:4]), 12, 31)
    y, q = int(quarter_label[:4]), int(quarter_label[-1])
    return date(y, 3 * q, [31, 30, 30, 31][q - 1])


def report_sentences():
    p = pd.read_csv(PHASE3B / "report_pages.csv", keep_default_na=False)
    rows = []
    for _, r in p.iterrows():
        pe = period_end(r.quarter)
        for s in split_sentences(r.text):
            if len(s) > 1500:  # long table dumps: keep, but cap for embedding
                s = s[:1500]
            hz = horizons(s, pe)
            rows.append(dict(bank=r.bank, report=r.quarter, file=r.file, page=r.page, text=s,
                             forward=bool(FORWARD_RE.search(s)) or bool(hz),
                             horizon_years=sorted({d.year for d, _ in hz if d is not None})))
    rs = pd.DataFrame(rows)
    for g, rx in METRIC_OF.items():
        rs[f"kw_{g}"] = rs.text.str.contains(rx)
    rs["qty"] = rs.text.map(quantities_precise)
    return rs


def window(bank, quarter, call_type, name):
    """Report labels in window W0, W1 or W2 for a candidate."""
    q = "2023-Q2" if call_type == "event" else quarter
    w = [q]
    if name in ("W1", "W2"):
        w += [x for x in QUARTERS if x < q]
        if bank == "UBS":
            w.append(f"{q[:4]} annual report")
    if name == "W2":
        i = QUARTERS.index(q)
        if i + 1 < len(QUARTERS):
            w.append(QUARTERS[i + 1])
    return w


def classify(cand, rs, S, setting):
    """Class A, B or C for one candidate under one setting; returns class and index of the best sentence."""
    win = rs[(rs.bank == cand.bank) & rs.report.isin(window(cand.bank, cand.quarter, cand.call_type, setting["window"]))]
    if win.empty:
        return "C", None
    sims = S[win.index.values]
    if setting["similarity_instead_of_keyword"] or cand.metric == "other":
        topic = sims >= SIM_THRESHOLD
    else:
        topic = win[f"kw_{cand.metric}"].values
    fwd = win.forward.values
    cq = quantities_precise(cand.text)
    targets = cq if setting["any_quantity"] else cq[:1]
    cand_years = {d.year for d, _ in horizons(cand.text, pd.Timestamp(cand.call_date).date()) if d is not None}
    a_idx = []
    eligible = topic & (fwd if setting["a_needs_forward"] else True)
    for k in np.flatnonzero(eligible):
        idx = win.index.values[k]
        if not any(matches(t, x, setting["exact"]) for t in targets for x in win.qty.values[k]):
            continue
        ry = win.horizon_years.values[k]
        if setting["horizon_check"] and cand_years and ry and not (cand_years & set(ry)):
            continue
        a_idx.append((sims[k], idx))
    if a_idx:
        return "A", max(a_idx)[1]
    b = topic & fwd
    if b.any():
        k = int(np.argmax(np.where(b, sims, -1)))
        return "B", win.index.values[k]
    return "C", None


SETTINGS = {
    "primary": dict(window="W0", exact=False, any_quantity=False, similarity_instead_of_keyword=False,
                    a_needs_forward=True, horizon_check=False),
}
for name, change in {"W1": dict(window="W1"), "W2": dict(window="W2"), "exact_tolerance": dict(exact=True),
                     "any_quantity": dict(any_quantity=True), "similarity_instead_of_keyword":
                     dict(similarity_instead_of_keyword=True), "A_without_forward_context": dict(a_needs_forward=False),
                     "horizon_check": dict(horizon_check=True)}.items():
    SETTINGS[name] = {**SETTINGS["primary"], **change}


def embed(texts):
    import contrast
    import torch
    from sentence_transformers import SentenceTransformer
    torch.manual_seed(SEED)
    m = SentenceTransformer(MPNET, device="cuda" if torch.cuda.is_available() else "cpu", revision=REVISIONS[MPNET])
    return m.encode([contrast.clean(t) for t in texts], batch_size=256, normalize_embeddings=True,
                    convert_to_numpy=True)


def cell_of(r):
    return f"{r.bank} {r['type']}"


def bootstrap(df, rng):
    """Shares of A, B, C per cell with a cluster bootstrap over calls."""
    rows = []
    groups = [(cell, g) for cell, g in df.groupby("cell")]
    groups += [("JPM event call", df[df.call_type == "event"])]
    for cell, g in groups:
        calls = g.call_id.unique()
        n = len(g)
        row = dict(cell=cell, candidates=n, calls=len(calls))
        for c in "ABC":
            row[f"n_{c}"] = int((g.cls == c).sum()); row[f"share_{c}"] = (g.cls == c).mean() if n else np.nan
        if len(calls) >= 3:
            by = {cid: gg.cls.values for cid, gg in g.groupby("call_id")}
            boots = {c: [] for c in "ABC"}
            for _ in range(N_BOOT):
                draw = np.concatenate([by[cid] for cid in rng.choice(calls, len(calls), replace=True)])
                for c in "ABC":
                    boots[c].append((draw == c).mean())
            for c in "ABC":
                row[f"ci_{c}"] = f"{np.percentile(boots[c], 2.5):.2f} to {np.percentile(boots[c], 97.5):.2f}"
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = file_hashes()
    cand = pd.read_csv(PHASE3 / "candidates_threaded.csv")
    cand["call_id"] = cand.bank + " " + cand.quarter + " " + cand.call_type
    cand["cell"] = cand.apply(cell_of, axis=1)
    first = cand.sort_values(["call_date", "position_in_call", "sentence_number"]).groupby("thread").head(1)
    cand["first_of_thread"] = cand.index.isin(first.index)
    rs = report_sentences()
    X = embed(cand.text.tolist() + rs.text.tolist())
    XC, XR = X[:len(cand)], X[len(cand):]
    rs.to_csv(OUT / "report_sentences.csv", index=False)

    results = []
    for name, setting in SETTINGS.items():
        for i, r in cand.reset_index(drop=True).iterrows():
            S = XR @ XC[i]
            cls, best = classify(r, rs, S, setting)
            if name == "primary":
                win = rs[(rs.bank == r.bank) & rs.report.isin(window(r.bank, r.quarter, r.call_type, "W0"))]
                top3 = win.index.values[np.argsort(-S[win.index.values])[:3]] if len(win) else []
            results.append(dict(stmt_id=r.stmt_id, setting=name, cls=cls, best=best,
                                top3=list(top3) if name == "primary" else None))
    res = pd.DataFrame(results).merge(cand[["stmt_id", "bank", "quarter", "call_type", "call_id", "cell", "type",
                                            "metric", "value", "unit", "thread", "first_of_thread", "text"]],
                                      on="stmt_id")
    res["best_text"] = res.best.map(lambda k: rs.text[k] if pd.notna(k) else "")
    res["best_location"] = res.best.map(lambda k: f"{rs.file[k]}, page {rs.page[k]}" if pd.notna(k) else "")
    res.drop(columns=["top3"]).to_csv(OUT / "matches.csv", index=False)

    tables = []
    for name in SETTINGS:
        for level, sub in [("candidates", res), ("threads", res[res.first_of_thread])]:
            s = sub[sub.setting == name]
            tables.append(bootstrap(s, np.random.default_rng(SEED)).assign(setting=name, level=level))
    shares = pd.concat(tables, ignore_index=True)
    shares.to_csv(OUT / "shares.csv", index=False)

    # blind labelling sample: about 20 per class from the primary candidate table, balanced by bank
    rng = np.random.default_rng(SEED)
    prim = res[res.setting == "primary"].reset_index(drop=True)
    parts = []
    for c in "ABC":
        g = prim[prim.cls == c]
        n_bank = {b: min(10, int((g.bank == b).sum())) for b in ["UBS", "JPM"]}
        for b in ["UBS", "JPM"]:  # fill up to 20 per class from the other bank where one bank has fewer
            other = "JPM" if b == "UBS" else "UBS"
            n_bank[b] = min(int((g.bank == b).sum()), n_bank[b] + (10 - n_bank[other]))
        for b, n in n_bank.items():
            gb = g[g.bank == b]
            parts.append(gb.iloc[rng.choice(len(gb), n, replace=False)])
    smp = pd.concat(parts)
    smp = smp.iloc[rng.permutation(len(smp))].reset_index(drop=True)
    st = pd.read_csv(PHASE3 / "statements.csv").set_index("stmt_id")
    top3 = {r.stmt_id: r.top3 for r in pd.DataFrame(results).query("setting == 'primary'").itertuples()}

    def shown(r):
        if r.cls in "AB":
            return [rs.text[int(r.best)]]
        return [rs.text[k] for k in top3[r.stmt_id]]
    blind = pd.DataFrame({
        "item_id": [f"P{i:03d}" for i in range(1, len(smp) + 1)],
        "call_sentence": smp.text.values,
        "call_context": [st.context.fillna("").get(sid, "") for sid in smp.stmt_id],
        "report_sentences": [" || ".join(shown(r)) for _, r in smp.iterrows()],
        "label_counterpart": "", "notes": ""})
    key = smp[["stmt_id", "bank", "quarter", "call_type", "type", "metric", "cls", "best_location"]].copy()
    key.insert(0, "item_id", blind.item_id.values)
    LABEL_DIR.mkdir(parents=True, exist_ok=True)
    blind.to_csv(LABEL_DIR / "counterparts.csv", index=False)
    key.to_csv(LABEL_DIR / "counterparts_key.csv", index=False)

    assert file_hashes() == before, "report files changed"
    show = ["cell", "candidates", "calls", "n_A", "n_B", "n_C", "share_A", "ci_A", "share_C", "ci_C"]
    for level in ["candidates", "threads"]:
        print(level); print(shares[(shares.setting == "primary") & (shares.level == level)][show].round(2).to_string(index=False))
    print(key.groupby(["cls", "bank"]).size())


if __name__ == "__main__":
    main()
