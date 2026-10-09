"""Phase 3i: control run of the main finding on the export of 2026-09-30.

Run from the repository root: python notebooks/roman/analysis/phase3i_check.py
Compares the UBS earnings calls 2023-Q2 to 2024-Q4 of the old and the new export, searches the source statements
of the 39 targets in the new export and repeats the phase 3 rules and the FinBERT-FLS labelling of phase 3g on
the new export. Writes to notebooks/roman/data/phase3i/ only. Plan: plans/phase_3i.md.
"""
import difflib
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
import phase3_extract as p3  # noqa: E402

DATA = ROOT / "notebooks" / "roman" / "data"
OUT = DATA / "phase3i"
OLD = ROOT / "data" / "results" / "2026-09-23"
NEW = Path.home() / "projects" / "earnings-call-nlp-pipeline" / "exports" / "2026-09-30"
FINAL = ROOT / "notebooks" / "final" / "data" / "results" / "2026-09-30"
KEY = p3.KEY
CALL = ["bank", "quarter", "call_type"]
FIRST_Q, LAST_Q = "2023-Q2", "2024-Q4"
SIM_MIN = 0.8
QUOTES = str.maketrans({"‘": "'", "’": "'", "‚": "'", "‛": "'",
                        "“": '"', "”": '"', "„": '"', "‟": '"'})


def norm(text):
    """Straight quotation marks and single spaces; nothing else is changed."""
    return re.sub(r"\s+", " ", str(text).translate(QUOTES)).strip()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def in_window(d):
    return d[(d.bank == "UBS") & (d.call_type == "earnings") & (d.quarter >= FIRST_Q) & (d.quarter <= LAST_Q)]


def pair_multiset(old_keys, new_keys):
    """Pair equal keys one to one in the given order. Returns (pairs, only_old, only_new) as index lists."""
    slots = defaultdict(list)
    for j, k in enumerate(new_keys):
        slots[k].append(j)
    pairs, only_old, used = [], [], set()
    for i, k in enumerate(old_keys):
        if slots[k]:
            j = slots[k].pop(0)
            pairs.append((i, j)); used.add(j)
        else:
            only_old.append(i)
    only_new = [j for j in range(len(new_keys)) if j not in used]
    return pairs, only_old, only_new


def joined_windows(texts, kmax=4):
    """Map the joined text of 2..kmax consecutive sentences to the index of the first one."""
    out = {}
    for k in range(2, kmax + 1):
        for i in range(len(texts) - k + 1):
            out.setdefault(" ".join(texts[i:i + k]), (i, k))
    return out


def best_match(text, others):
    """Index and similarity of the most similar text in others (None, 0.0 if others is empty)."""
    best, sim = None, 0.0
    sm = difflib.SequenceMatcher(None, autojunk=False)
    sm.set_seq2(text)
    for j, o in enumerate(others):
        sm.set_seq1(o)
        if sm.real_quick_ratio() < sim or sm.quick_ratio() < sim:
            continue
        r = sm.ratio()
        if r > sim:
            best, sim = j, r
    return best, sim


def check_exports():
    files = {}
    for name in ("all_sentences.csv", "all_utterances.csv"):
        new_hash, final_hash = sha256(NEW / name), sha256(FINAL / name)
        if new_hash != final_hash:
            raise SystemExit(f"{name}: the new export differs from notebooks/final/data/results/2026-09-30")
        files[name] = {"old_2026-09-23": sha256(OLD / name), "new_2026-09-30": new_hash,
                       "equal_to_final_folder": True}
    (OUT / "export_hashes.json").write_text(json.dumps(files, indent=2))
    return files


def call_counts():
    rows = []
    for label, folder in (("old", OLD), ("new", NEW)):
        s = in_window(pd.read_csv(folder / "all_sentences.csv"))
        u = in_window(pd.read_csv(folder / "all_utterances.csv"))
        for unit, d in (("sentences", s), ("utterances", u)):
            for q, g in d.groupby("quarter"):
                rows.append((q, unit, "all", "all", label, len(g)))
                for (sec, role), h in g.groupby(["section", "speaker_role"]):
                    rows.append((q, unit, sec, role, label, len(h)))
    c = pd.DataFrame(rows, columns=["quarter", "unit", "section", "speaker_role", "export", "n"])
    c = c.pivot_table(index=["quarter", "unit", "section", "speaker_role"], columns="export", values="n",
                      fill_value=0).reset_index()
    c["difference"] = c["new"] - c["old"]
    c[["quarter", "unit", "section", "speaker_role", "old", "new", "difference"]].to_csv(OUT / "call_counts.csv",
                                                                                      index=False)
    return c


def sentence_diff():
    """Every sentence of the window that is not the same in both exports, with an aligned partner and a cause."""
    cols = KEY + ["section", "speaker_role", "speaker_name", "sentence_id", "sentence"]
    old = in_window(pd.read_csv(OLD / "all_sentences.csv"))[cols].sort_values(KEY)
    new = in_window(pd.read_csv(NEW / "all_sentences.csv"))[cols].sort_values(KEY)
    rows, n_same = [], 0
    for q in sorted(set(old.quarter) | set(new.quarter)):
        o, n = old[old.quarter == q].reset_index(drop=True), new[new.quarter == q].reset_index(drop=True)
        ot, nt = [norm(t) for t in o.sentence], [norm(t) for t in n.sentence]
        pairs, only_old, only_new = pair_multiset(ot, nt)
        for i, j in pairs:
            diff = [a for a in ("speaker_name", "speaker_role", "section") if str(o.at[i, a]) != str(n.at[j, a])]
            if diff:
                rows.append(row(q, "same text, other attribute", "changed " + ", ".join(diff), o.loc[i], n.loc[j], 1.0))
            else:
                n_same += 1
        new_join, old_join = joined_windows(nt), joined_windows(ot)
        new_pool, old_pool = [nt[j] for j in only_new], [ot[i] for i in only_old]
        for i in only_old:
            if ot[i] in new_join:
                j, k = new_join[ot[i]]
                rows.append(row(q, "only old", f"sentence splitting: one old sentence is {k} new sentences",
                                o.loc[i], n.loc[j], 1.0))
                continue
            b, sim = best_match(ot[i], new_pool)
            partner = n.loc[only_new[b]] if b is not None and sim >= SIM_MIN else None
            cause = "changed wording" if partner is not None else "no similar new sentence (removed or part of a split)"
            rows.append(row(q, "only old", cause, o.loc[i], partner, sim))
        for j in only_new:
            if nt[j] in old_join:
                i, k = old_join[nt[j]]
                rows.append(row(q, "only new", f"sentence splitting: {k} old sentences are one new sentence",
                                o.loc[i], n.loc[j], 1.0))
                continue
            b, sim = best_match(nt[j], old_pool)
            partner = o.loc[only_old[b]] if b is not None and sim >= SIM_MIN else None
            cause = "changed wording" if partner is not None else "no similar old sentence (added or part of a split)"
            rows.append(row(q, "only new", cause, partner, n.loc[j], sim))
    d = pd.DataFrame(rows, columns=list(row("", "", "", None, None, 0.0)))  # header also when nothing differs
    d.to_csv(OUT / "sentence_diff.csv", index=False)
    return d, n_same, len(old), len(new)


def row(quarter, status, cause, o, n, sim):
    r = {"quarter": quarter, "status": status, "proposed_cause": cause, "similarity": round(float(sim), 3)}
    for label, x in (("old", o), ("new", n)):
        for a in ("position_in_call", "sentence_number", "sentence_id", "section", "speaker_role", "speaker_name",
                  "sentence"):
            r[f"{a}_{label}"] = None if x is None else x[a]
    return r


def new_statements():
    """Phase 3 statements of the new export, built by the unchanged phase 3 functions."""
    release = p3.RELEASE_DIR
    p3.RELEASE_DIR = NEW
    try:
        d = p3.load_statements()
    finally:
        p3.RELEASE_DIR = release
    d["candidate"] = [p3.is_candidate(t, cd) for t, cd in zip(d.text, d.call_date_d)]
    met = [p3.metric_of(t, c) for t, c in zip(d.text, d.context)]
    d["metric"], d["type"] = zip(*met)
    d["has_quantity"] = [bool(p3.quantities(t)) for t in d.text]
    d["has_horizon"] = [bool(p3.horizons(t, cd)) for t, cd in zip(d.text, d.call_date_d)]
    d["has_forward_word"] = [bool(p3.FORWARD_RE.search(t)) for t in d.text]
    grp = d.groupby(CALL + ["position_in_call"], sort=False).text
    d["before"], d["after"] = grp.shift(1).fillna(""), grp.shift(-1).fillna("")
    d = in_window(d).reset_index(drop=True)
    d["new_id"] = np.arange(len(d))
    d["norm"] = d.text.map(norm)
    return d


def old_statements():
    st = pd.read_csv(DATA / "phase3" / "statements.csv")
    st["text"] = st.text.fillna("")
    ids = pd.read_csv(OLD / "all_sentences.csv")[KEY + ["sentence_id"]]
    st = st.merge(ids, on=KEY, how="left", validate="one_to_one")
    st = in_window(st).reset_index(drop=True)
    st["norm"] = st.text.map(norm)
    return st


def units():
    d3 = pd.read_csv(DATA / "phase3d" / "counterparts_read.csv", keep_default_na=False)
    d3 = d3[(d3.bank == "UBS") & (d3.genuine == "yes") & (d3.type == "target") & (d3.pre_acquisition != "yes")]
    g = pd.read_csv(DATA / "phase3g" / "new_units_read.csv", keep_default_na=False)
    g = g[g.type == "target"]
    if (len(d3), len(g)) != (31, 8):
        raise SystemExit(f"expected 31 and 8 units, found {len(d3)} and {len(g)}")
    u = pd.concat([d3[["unit", "stmt_id"]].assign(phase="3d"), g[["unit", "stmt_id"]].assign(phase="3g")])
    u["stmt_id"] = u.stmt_id.astype(int)
    return u.reset_index(drop=True)


def match_units(u, old, new):
    rows = []
    o = old.set_index("stmt_id")
    for unit, stmt_id, phase in zip(u.unit, u.stmt_id, u.phase):
        s = o.loc[stmt_id]
        call = new[new.quarter == s.quarter]
        exact = call[(call.norm == s.norm) & (call.speaker_name == s.speaker_name)]
        other_speaker = call[call.norm == s.norm]
        if len(exact) or len(other_speaker):
            n, same_wording, sim = (exact if len(exact) else other_speaker).iloc[0], True, 1.0
        else:
            b, sim = best_match(s.norm, call.norm.tolist())
            n, same_wording = (call.iloc[b] if b is not None and sim >= SIM_MIN else None), False
        found = n is not None
        rows.append({
            "unit": unit, "phase": phase, "call": f"UBS {s.quarter} earnings", "found": found,
            "same_wording": bool(found and same_wording),
            "same_speaker": bool(found and n.speaker_name == s.speaker_name),
            "same_figures": bool(found and p3.quantities(n.text) == p3.quantities(s.text)),
            "similarity": round(float(sim), 3), "stmt_id_old": stmt_id,
            "sentence_id_old": s.sentence_id, "sentence_id_new": n.sentence_id if found else None,
            "position_in_call_old": s.position_in_call, "sentence_number_old": s.sentence_number,
            "position_in_call_new": n.position_in_call if found else None,
            "sentence_number_new": n.sentence_number if found else None,
            "speaker_old": s.speaker_name, "speaker_new": n.speaker_name if found else None,
            "candidate_old": bool(s.candidate), "candidate_new": bool(n.candidate) if found else None,
            "text_old": s.text, "text_new": "" if not found or same_wording else n.text})
    m = pd.DataFrame(rows)
    m.to_csv(OUT / "units_match.csv", index=False)
    return m


def score(new):
    """FinBERT-FLS as in phase 3g: same model, revision, maximum length, batch size and seed."""
    import torch
    import phase3g_fls as g
    torch.manual_seed(g.SEED)
    probs, labels = g.predict(g.FINBERT, new.text.tolist())
    new["finbert"] = [labels[int(i)] for i in probs.argmax(1)]
    new["finbert_p_specific"] = probs[:, [int(k) for k, v in labels.items() if v == "Specific FLS"][0]]
    new["specific"] = new.finbert == "Specific FLS"
    new["in_s"] = new.specific & new.has_quantity & ~new.candidate
    return {"model": g.FINBERT[0], "revision": g.FINBERT[1], "device": g.DEVICE, "seed": g.SEED,
            "max_length": 256, "batch_size": 64}


def compare_sets(old, new, old_mask, new_mask, name):
    """Old against new members of one set, paired within the call on the normalised text."""
    rows = []
    for q in sorted(set(old.quarter) | set(new.quarter)):
        o, n = old[(old.quarter == q) & old_mask].reset_index(drop=True), \
               new[(new.quarter == q) & new_mask].reset_index(drop=True)
        pairs, only_old, only_new = pair_multiset(o.norm.tolist(), n.norm.tolist())
        rows += [(q, "same", o.at[i, "stmt_id"], n.at[j, "new_id"], n.at[j, "text"]) for i, j in pairs]
        rows += [(q, "only old", o.at[i, "stmt_id"], None, o.at[i, "text"]) for i in only_old]
        rows += [(q, "only new", None, n.at[j, "new_id"], n.at[j, "text"]) for j in only_new]
    c = pd.DataFrame(rows, columns=["quarter", "status", "stmt_id_old", "new_id", "text"])
    c.to_csv(OUT / f"{name}_compare.csv", index=False)
    return c


def old_status(old, scored_old):
    """Per old statement: rule candidate, in S, or neither; and its FinBERT-FLS label."""
    sc = scored_old.set_index("stmt_id")
    old["finbert"] = old.stmt_id.map(sc.finbert)
    s_ids = set(pd.read_csv(DATA / "phase3g" / "set_s.csv").stmt_id)
    old["in_s"] = old.stmt_id.isin(s_ids)
    old["status"] = np.where(old.candidate, "rule candidate", np.where(old.in_s, "in S", "neither"))
    return old


def reading_lists(old, new, cand, s, u):
    unit_of = dict(zip(u.stmt_id, u.unit))
    new_ids = {}
    for name, c in (("rule candidates", cand), ("S", s)):
        for i in c[c.status == "only new"].new_id:
            new_ids.setdefault(int(i), []).append(name)
    rows = []
    for i, sets in sorted(new_ids.items()):
        n = new[new.new_id == i].iloc[0]
        call = old[old.quarter == n.quarter].reset_index(drop=True)
        b, sim = best_match(n.norm, call.norm.tolist())
        m = call.loc[b] if b is not None else None
        rows.append({
            "item_id": f"I{len(rows) + 1:03d}", "call": f"UBS {n.quarter} earnings", "section": n.section,
            "speaker": n.speaker_name, "new_in": " and ".join(sets), "metric_group": n.metric,
            "sentence": n.text, "context_before": n.before, "context_after": n["after"],
            "position_in_call": n.position_in_call, "sentence_number": n.sentence_number,
            "sentence_id": n.sentence_id, "finbert": n.finbert,
            "failed_rule_conditions": ", ".join(k for k, ok in (("quantity", n.has_quantity), ("horizon", n.has_horizon),
                                                                ("forward word", n.has_forward_word)) if not ok),
            "most_similar_old_statement": "" if m is None else m.text, "similarity": round(float(sim), 3),
            "old_statement_status": "" if m is None else m.status,
            "old_statement_unit": "" if m is None else unit_of.get(int(m.stmt_id), ""),
            "genuine": "", "duplicate_of": "", "new_target": "", "notes": ""})
    cols = ["item_id", "call", "section", "speaker", "new_in", "metric_group", "sentence", "context_before",
            "context_after", "position_in_call", "sentence_number", "sentence_id", "finbert",
            "failed_rule_conditions", "most_similar_old_statement", "similarity", "old_statement_status",
            "old_statement_unit", "genuine", "duplicate_of", "new_target", "notes"]
    reading = pd.DataFrame(rows, columns=cols)
    reading.to_csv(OUT / "only_new_for_reading.csv", index=False)

    old_ids = {}
    for name, c in (("rule candidates", cand), ("S", s)):
        for i in c[c.status == "only old"].stmt_id_old:
            old_ids.setdefault(int(i), []).append(name)
    rows = []
    for i, sets in sorted(old_ids.items()):
        o = old[old.stmt_id == i].iloc[0]
        call = new[new.quarter == o.quarter].reset_index(drop=True)
        b, sim = best_match(o.norm, call.norm.tolist())
        m = call.loc[b] if b is not None else None
        new_state = "" if m is None else ("rule candidate" if m.candidate else "in S" if m.in_s else "neither")
        rows.append({"stmt_id_old": i, "unit": unit_of.get(i, ""), "call": f"UBS {o.quarter} earnings",
                     "speaker": o.speaker_name, "old_in": " and ".join(sets), "sentence": o.text,
                     "most_similar_new_statement": "" if m is None else m.text, "similarity": round(float(sim), 3),
                     "new_statement_status": new_state, "new_finbert": "" if m is None else m.finbert})
    gone = pd.DataFrame(rows, columns=["stmt_id_old", "unit", "call", "speaker", "old_in", "sentence",
                                       "most_similar_new_statement", "similarity", "new_statement_status",
                                       "new_finbert"])
    gone.to_csv(OUT / "only_old.csv", index=False)
    return reading, gone


def label_agreement(old, new):
    """FinBERT-FLS label of statements with the same normalised text in both exports."""
    same = differ = 0
    for q in sorted(set(old.quarter) & set(new.quarter)):
        o, n = old[old.quarter == q].reset_index(drop=True), new[new.quarter == q].reset_index(drop=True)
        pairs, _, _ = pair_multiset(o.norm.tolist(), n.norm.tolist())
        for i, j in pairs:
            if o.at[i, "finbert"] == n.at[j, "finbert"]:
                same += 1
            else:
                differ += 1
    return {"paired_statements": same + differ, "same_label": same, "different_label": differ}


def write_sums():
    lines = [f"{sha256(p)}  {p.name}" for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "SHA256SUMS"]
    (OUT / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    hashes = check_exports()
    counts = call_counts()
    diff, n_same, n_old, n_new = sentence_diff()

    old, new = old_statements(), new_statements()
    u = units()
    m = match_units(u, old, new)

    model = score(new)
    old = old_status(old, pd.read_csv(DATA / "phase3g" / "scored.csv"))
    cand = compare_sets(old, new, old.candidate, new.candidate, "candidates")
    s = compare_sets(old, new, old.in_s, new.in_s, "set_s")
    reading, gone = reading_lists(old, new, cand, s, u)
    keep = ["new_id", "sentence_id"] + KEY + ["call_date", "section", "speaker_name", "joined_with_next", "text",
                                              "candidate", "metric", "type", "has_quantity", "has_horizon",
                                              "has_forward_word", "finbert", "finbert_p_specific", "specific", "in_s"]
    new[keep].to_csv(OUT / "statements_new.csv", index=False)
    new[keep].to_csv(OUT / "scored_new.csv", index=False)

    tot = counts[(counts.section == "all")]
    summary = {
        "window": f"UBS earnings calls {FIRST_Q} to {LAST_Q}",
        "exports": hashes,
        "sentences": {"old": n_old, "new": n_new, "same": n_same,
                      "by_status": diff.status.value_counts().to_dict() if len(diff) else {},
                      "by_cause": diff.proposed_cause.value_counts().to_dict() if len(diff) else {}},
        "utterances": {"old": int(tot[tot.unit == "utterances"].old.sum()),
                       "new": int(tot[tot.unit == "utterances"].new.sum())},
        "statements": {"old": len(old), "new": len(new)},
        "units": {"n": len(m), "found": int(m.found.sum()), "same_wording": int(m.same_wording.sum()),
                  "same_speaker": int(m.same_speaker.sum()), "same_figures": int(m.same_figures.sum())},
        "model": model,
        "finbert_label_agreement": label_agreement(old, new),
        "rule_candidates": {"old": int(old.candidate.sum()), "new": int(new.candidate.sum()),
                            **cand.status.value_counts().to_dict()},
        "set_s": {"old": int(old.in_s.sum()), "new": int(new.in_s.sum()), **s.status.value_counts().to_dict()},
        "only_new_for_reading": len(reading), "only_old": len(gone),
        "only_old_with_unit": sorted(x for x in gone.unit if x),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=int))
    write_sums()
    print(json.dumps(summary, indent=2, default=int))


if __name__ == "__main__":
    main()
