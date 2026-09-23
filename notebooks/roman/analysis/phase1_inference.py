"""Phase 1 inference: primary tests P1-1 and P1-2, robustness variants and exploratory analyses E1 to E4.

Run from the repository root after phase1_score.py: python notebooks/roman/analysis/phase1_inference.py
"""
import itertools, json, re

import numpy as np
import pandas as pd

from phase1_common import CAPITAL_RE, NA_RE, NLI_THRESHOLD, OUT, SEED, ROOT

REGISTER = ROOT / "notebooks" / "roman" / "plans" / "test_register.csv"
N_PERM = 10_000
CONTRACTION_RE = re.compile(r"\b(do|does|did|wo|ca|would|could|should|is|are|was|were|have|has|had)not\b", re.I)


def load():
    a = pd.read_csv(OUT / "answer_sentences.csv")
    a = a[a.speaker_role == "management"].copy()
    a["text"] = a.text.fillna("")  # sentences that consist only of a bracket insertion
    seg = pd.read_csv(OUT / "segments.csv")
    a["phrase_restored"] = a.text.map(lambda t: bool(NA_RE.search(CONTRACTION_RE.sub(r"\1n't", t))))
    a["capital_kw"] = a.segment_id.map(seg.set_index("segment_id").capital_kw)
    return a, seg


def flags(a, variant):
    nli = lambda th: a.nli_max >= th
    return {"primary": a.phrase | nli(NLI_THRESHOLD), "phrase_only": a.phrase, "nli_only": nli(NLI_THRESHOLD),
            "nli_0.8": a.phrase | nli(0.8), "nli_0.95": a.phrase | nli(0.95), "short_kept": a.phrase | nli(NLI_THRESHOLD),
            "per_10k_words": a.phrase | nli(NLI_THRESHOLD), "topic_prototype": a.phrase | nli(NLI_THRESHOLD),
            "E4_contractions_restored": a.phrase_restored | nli(NLI_THRESHOLD)}[variant]


# E4 (contractions restored) was only needed on release 2026-09-13 and is dropped on the corrected release.
VARIANTS = ["primary", "phrase_only", "nli_only", "nli_0.8", "nli_0.95", "short_kept", "per_10k_words",
            "topic_prototype"]


def call_rates(a, variant, only_capital=False):
    d = a.assign(defl=flags(a, variant))
    if variant != "short_kept":
        d = d[d.n_words >= 4]
    num = d.defl & d.capital_kw if only_capital else d.defl
    g = d.assign(num=num).groupby(["bank", "quarter"])
    if variant == "per_10k_words":
        r = g.num.sum() / g.n_words.sum() * 1e4
    else:
        r = g.num.sum() / g.size() * 100
    return r.rename("rate").reset_index()


def exact_bank_test(r):
    """Exact permutation of bank labels over 16 calls; two-sided on |mean UBS - mean JPM|."""
    v = r.rate.values; ubs = (r.bank == "UBS").values
    obs = v[ubs].mean() - v[~ubs].mean()
    null = np.array([v[list(c)].mean() - np.delete(v, list(c)).mean()
                     for c in itertools.combinations(range(len(v)), int(ubs.sum()))])
    return obs, np.mean(np.abs(null) >= abs(obs) - 1e-12), len(null)


def segment_flags(a, seg, variant):
    d = a.assign(defl=flags(a, variant))
    if variant != "short_kept":
        d = d[d.n_words >= 4]
    s = seg.copy()
    s["deflected"] = s.segment_id.isin(d[d.defl].segment_id)
    s["capital"] = s.capital_proto if variant == "topic_prototype" else s.capital_kw
    return s


def concentration_test(s, rng, n_perm=N_PERM):
    """Excess share of deflections on capital segments, UBS minus JPM, flags permuted within calls."""
    def excess(df_bank, flag_matrix=None):
        O = X = D = 0.0
        out = []
        for (_, _), call in df_bank.groupby(["bank", "quarter"]):
            cap = call.capital.values.astype(float); f = call.deflected.values.astype(float)
            X += f.sum() * cap.sum() / len(cap); D += f.sum(); O += (f * cap).sum()
            if flag_matrix is not None:
                perm = np.argsort(rng.random((n_perm, len(f))), axis=1)
                out.append((f[perm] * cap).sum(1))
        E = (O - X) / D if D else np.nan
        Eperm = (np.sum(out, axis=0) - X) / D if flag_matrix is not None and D else None
        return E, Eperm
    Eu, Pu = excess(s[s.bank == "UBS"], True)
    Ej, Pj = excess(s[s.bank == "JPM"], True)
    T = Eu - Ej; Tp = Pu - Pj
    p = (np.sum(np.abs(Tp) >= abs(T) - 1e-12) + 1) / (n_perm + 1)
    return dict(E_UBS=Eu, E_JPM=Ej, T=T, p=p,
                D_UBS=int(s[(s.bank == "UBS")].deflected.sum()), D_JPM=int(s[(s.bank == "JPM")].deflected.sum()))


def did_test(r, post_start="2024-Q1"):
    """Exploratory E1: (UBS post - pre) - (JPM post - pre), year labels permuted within each bank."""
    def split_stats(v, k):
        return {c: v[list(c)].mean() - np.delete(v, list(c)).mean()
                for c in itertools.combinations(range(len(v)), k)}
    out = {}
    per_bank = {}
    for bank in ["UBS", "JPM"]:
        rb = r[r.bank == bank].sort_values("quarter")
        post = (rb.quarter >= post_start).values
        v = rb.rate.values
        per_bank[bank] = (v[post].mean() - v[~post].mean(), np.array(list(split_stats(v, int(post.sum())).values())))
        out[f"{bank}_post_minus_pre"] = per_bank[bank][0]
    obs = per_bank["UBS"][0] - per_bank["JPM"][0]
    null = (per_bank["UBS"][1][:, None] - per_bank["JPM"][1][None, :]).ravel()
    out.update(did=obs, p=np.mean(np.abs(null) >= abs(obs) - 1e-12), n_splits=len(null), post_start=post_start)
    return out


def e5_turn_topic(a, seg):
    """Exploratory E5: topic assigned to the whole analyst turn, deflection at pair level."""
    turn = seg.groupby("pair_id").agg(bank=("bank", "first"), quarter=("quarter", "first"), text=("text", " ".join))
    turn["capital"] = turn.text.str.contains(CAPITAL_RE)
    d = a[a.n_words >= 4].assign(defl=flags(a, "primary"))
    turn["deflected"] = turn.index.isin(d[d.defl].pair_id)
    conc = concentration_test(turn.reset_index(), np.random.default_rng(SEED))
    d = d.assign(capital_turn=d.pair_id.map(turn.capital))
    g = d.assign(num=d.defl & d.capital_turn).groupby(["bank", "quarter"])
    r = (g.num.sum() / g.size() * 100).rename("rate").reset_index()
    timing = [did_test(r, start) for start in ["2024-Q1", "2023-Q4"]]
    summary = turn.groupby("bank").agg(pairs=("capital", "size"), capital_pairs=("capital", "sum"),
                                       deflected_pairs=("deflected", "sum"),
                                       deflected_capital_pairs=("deflected", lambda x: (x & turn.loc[x.index, "capital"]).sum()))
    return turn.reset_index(), conc, pd.DataFrame(timing), summary.reset_index(), r


def holm(p):
    p = np.asarray(p, float); order = np.argsort(p); m = len(p)
    adj = np.empty(m); running = 0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i]); adj[i] = min(1, running)
    return adj


def main():
    a, seg = load()
    rows_p1, rows_p2 = [], []
    rates_all = []
    for v in VARIANTS:
        if v != "topic_prototype":
            r = call_rates(a, v)
            obs, p, n = exact_bank_test(r)
            rows_p1.append(dict(variant=v, T=obs, p=p, n_splits=n,
                                mean_UBS=r[r.bank == "UBS"].rate.mean(), mean_JPM=r[r.bank == "JPM"].rate.mean()))
            rates_all.append(r.assign(variant=v))
        if v != "per_10k_words":
            res = concentration_test(segment_flags(a, seg, v), np.random.default_rng(SEED))
            rows_p2.append(dict(variant=v, **res))
    p1, p2 = pd.DataFrame(rows_p1), pd.DataFrame(rows_p2)
    p1.to_csv(OUT / "p1_deflection_rate.csv", index=False)
    p2.to_csv(OUT / "p2_capital_concentration.csv", index=False)
    pd.concat(rates_all).to_csv(OUT / "call_rates.csv", index=False)

    # register: primary rows only, Holm across all primary tests in the register
    reg = pd.read_csv(REGISTER)
    reg = reg[reg.phase != 1]
    new = pd.DataFrame([
        dict(phase=1, test_id="P1-1", hypothesis="UBS deflection rate differs from JPM (call level)",
             statistic="mean UBS - mean JPM, deflection sentences per 100 answer sentences",
             p_raw=p1.set_index("variant").loc["primary", "p"]),
        dict(phase=1, test_id="P1-2", hypothesis="UBS deflections concentrate more on capital regulation than JPM",
             statistic="excess share of deflected segments on capital regulation, UBS minus JPM",
             p_raw=p2.set_index("variant").loc["primary", "p"])])
    reg = new if reg.empty else pd.concat([reg, new], ignore_index=True)
    reg["p_holm"] = holm(reg.p_raw)
    reg.to_csv(REGISTER, index=False)

    # E1 timing, exploratory
    e1 = []
    for start in ["2024-Q1", "2023-Q4"]:
        for cap in [False, True]:
            r = call_rates(a, "primary", only_capital=cap)
            e1.append(dict(deflections="capital regulation only" if cap else "all", **did_test(r, start)))
    pd.DataFrame(e1).to_csv(OUT / "e1_timing.csv", index=False)
    s = segment_flags(a, seg, "primary")
    s["year"] = s.quarter.str[:4]
    content = (s[s.deflected].groupby(["bank", "year"])
               .agg(deflected_segments=("segment_id", "size"), capital=("capital", "sum"),
                    swiss_terms=("swiss_kw", "sum"), integration_terms=("integration_kw", "sum")).reset_index())
    content.to_csv(OUT / "e1_content.csv", index=False)
    s.to_csv(OUT / "segments_flagged.csv", index=False)

    # E3 detector agreement, exploratory
    d = a[a.n_words >= 4]
    e3 = (d.assign(phrase_only=d.phrase & (d.nli_max < NLI_THRESHOLD), nli_only=~d.phrase & (d.nli_max >= NLI_THRESHOLD),
                   both=d.phrase & (d.nli_max >= NLI_THRESHOLD), restored_phrase=d.phrase_restored)
          .groupby("bank")[["both", "phrase_only", "nli_only", "restored_phrase"]].sum().reset_index())
    e3["answer_sentences"] = d.groupby("bank").size().values
    e3.to_csv(OUT / "e3_agreement.csv", index=False)

    # E2 relevance, exploratory: call-level mean lift by bank and topic
    rel = pd.read_csv(OUT / "relevance.csv").merge(s[["segment_id", "capital", "deflected"]], on="segment_id")
    rel["log_words"] = np.log(rel.answer_words.clip(lower=1))
    res = []
    for (m, v), g in rel.groupby(["model", "answer_variant"]):
        beta = np.polyfit(g.log_words, g.lift, 1)
        res.append(g.assign(lift_resid=g.lift - np.polyval(beta, g.log_words)))
    rel = pd.concat(res)
    rel.to_csv(OUT / "relevance_scored.csv", index=False)
    e2 = rel.groupby(["model", "answer_variant", "bank", "quarter", "capital"]).agg(
        lift=("lift", "mean"), lift_resid=("lift_resid", "mean"), n=("lift", "size")).reset_index()
    e2.to_csv(OUT / "e2_relevance_by_call.csv", index=False)

    turn, conc, timing, summary, r5 = e5_turn_topic(a, seg)
    turn.drop(columns="text").to_csv(OUT / "e5_pairs.csv", index=False)
    pd.DataFrame([conc]).to_csv(OUT / "e5_concentration.csv", index=False)
    timing.to_csv(OUT / "e5_timing.csv", index=False)
    summary.to_csv(OUT / "e5_summary.csv", index=False)
    r5.to_csv(OUT / "e5_call_rates.csv", index=False)
    print(summary.to_string(index=False)); print(conc); print(timing.round(4).to_string(index=False))

    short = a.assign(short=a.n_words < 4).groupby("bank").short.mean()
    (OUT / "phase1_meta.json").write_text(json.dumps(dict(short_answer_share=short.round(4).to_dict(),
                                                          n_perm_p2=N_PERM, seed=SEED), indent=2))
    print(p1.round(4).to_string(index=False)); print(p2.round(4).to_string(index=False))
    print(reg.to_string(index=False)); print(pd.DataFrame(e1).round(4).to_string(index=False))
    print(content.to_string(index=False)); print(e3.to_string(index=False))


if __name__ == "__main__":
    main()
