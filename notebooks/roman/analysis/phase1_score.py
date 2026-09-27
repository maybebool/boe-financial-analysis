"""Phase 1 scoring: question segments, answer alignment, phrase list, NLI and relevance models.

Run from the repository root: python notebooks/roman/analysis/phase1_score.py
Writes segments.csv, answer_sentences.csv, question_sentences.csv, relevance.csv and models.json to
notebooks/roman/data/phase1/.
"""
import json

import numpy as np
import pandas as pd
import torch
from sentence_transformers import CrossEncoder, SentenceTransformer
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from phase1_common import (CE_MODEL, EMB_MODEL, NLI_HYPOTHESES, NLI_MODEL, OUT, REVISIONS, SEED, TOPIC_PROTOTYPE,
                           build_segments, build_sentence_pairs, load_qa_sentences, phrase_flag)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
KEY = ["bank", "quarter", "call_type", "position_in_call", "sentence_number"]
TRUNC_TOKENS = 128


def align(answers, seg, emb):
    """Assign every answer sentence to the most similar question segment of its own pair (cosine)."""
    seg_vec = emb.encode(seg.text.tolist(), batch_size=64, normalize_embeddings=True, convert_to_numpy=True)
    ans_vec = emb.encode(answers.text.tolist(), batch_size=128, normalize_embeddings=True, convert_to_numpy=True)
    seg_pos = {sid: i for i, sid in enumerate(seg.segment_id)}
    segs_of_pair = seg.groupby("pair_id").segment_id.apply(list).to_dict()
    aligned, sim = [], []
    for k, pid in enumerate(answers.pair_id):
        cands = segs_of_pair[pid]
        sims = [float(ans_vec[k] @ seg_vec[seg_pos[c]]) for c in cands]
        j = int(np.argmax(sims))
        aligned.append(cands[j]); sim.append(sims[j])
    proto = emb.encode([TOPIC_PROTOTYPE], normalize_embeddings=True, convert_to_numpy=True)[0]
    return aligned, sim, seg_vec @ proto


@torch.no_grad()
def nli_scores(texts):
    tok = AutoTokenizer.from_pretrained(NLI_MODEL, revision=REVISIONS[NLI_MODEL])
    model = AutoModelForSequenceClassification.from_pretrained(
        NLI_MODEL, revision=REVISIONS[NLI_MODEL], dtype=torch.float16).to(DEVICE).eval()
    ent = model.config.label2id["entailment"]
    out = {}
    for name, hyp in NLI_HYPOTHESES.items():
        probs = []
        for i in range(0, len(texts), 64):
            batch = texts[i:i + 64]
            enc = tok(batch, [hyp] * len(batch), truncation=True, max_length=256, padding=True,
                      return_tensors="pt").to(DEVICE)
            probs.append(torch.softmax(model(**enc).logits.float(), -1)[:, ent].cpu().numpy())
        out[name] = np.concatenate(probs)
    return out


def truncate(texts, tokenizer, n=TRUNC_TOKENS):
    return [tokenizer.convert_tokens_to_string(tokenizer.tokenize(t)[:n]) for t in texts]


def relevance(seg, answers, emb):
    """Relevance of each segment's aligned answer against the other answers of the same call."""
    a = answers[answers.speaker_role == "management"].sort_values(KEY)
    ans_text = a.groupby("segment_id").text.apply(" ".join)
    ans_words = a.groupby("segment_id").n_words.sum()
    ce = CrossEncoder(CE_MODEL, max_length=512, device=DEVICE, revision=REVISIONS[CE_MODEL])
    s = seg[seg.segment_id.isin(ans_text.index)].reset_index(drop=True)
    s["answer"] = s.segment_id.map(ans_text)
    s["answer_words"] = s.segment_id.map(ans_words)
    s["answer_128"] = truncate(s.answer.tolist(), ce.tokenizer)
    rows = []
    for (bank, q), call in s.groupby(["bank", "quarter"]):
        call = call.reset_index(drop=True)
        n = len(call)
        for variant, col in [("first128", "answer_128"), ("full", "answer")]:
            qi, ai = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
            qi, ai = qi.ravel(), ai.ravel()
            ce_s = ce.predict(list(zip(call.text.values[qi], call[col].values[ai])), batch_size=128,
                              show_progress_bar=False).reshape(n, n)
            qv = emb.encode(call.text.tolist(), convert_to_numpy=True)
            av = emb.encode(call[col].tolist(), convert_to_numpy=True)
            bi_s = qv @ av.T  # dot product, the similarity the model was trained for
            for name, M in [("cross_encoder", ce_s), ("bi_encoder", bi_s)]:
                true = np.diag(M)
                null = (M.sum(1) - true) / max(n - 1, 1)
                for i in range(n):
                    rows.append(dict(segment_id=call.segment_id[i], bank=bank, quarter=q, model=name,
                                     answer_variant=variant, score=true[i], null=null[i], lift=true[i] - null[i],
                                     answer_words=call.answer_words[i]))
    return pd.DataFrame(rows)


def main():
    torch.manual_seed(SEED); np.random.seed(SEED)
    OUT.mkdir(parents=True, exist_ok=True)
    s = load_qa_sentences()
    questions, answers = build_sentence_pairs(s)
    questions, seg = build_segments(questions)
    emb = SentenceTransformer(EMB_MODEL, device=DEVICE, revision=REVISIONS[EMB_MODEL])
    answers = answers.reset_index(drop=True)
    answers["segment_id"], answers["align_sim"], proto_sim = align(answers, seg, emb)
    seg["prototype_sim"] = proto_sim
    seg["capital_proto"] = seg.prototype_sim >= 0.5
    answers["phrase"] = answers.text.map(phrase_flag)
    for name, p in nli_scores(answers.text.tolist()).items():
        answers[name] = p
    answers["nli_max"] = answers[["nli_a", "nli_b"]].max(1)
    rel = relevance(seg, answers, emb)
    cols = KEY + ["sentence_id", "pair_id", "segment_id", "speaker_role", "speaker_name", "text", "n_words"]
    questions[cols].to_csv(OUT / "question_sentences.csv", index=False)
    answers[cols + ["align_sim", "phrase", "nli_a", "nli_b", "nli_max"]].to_csv(OUT / "answer_sentences.csv", index=False)
    seg.to_csv(OUT / "segments.csv", index=False)
    rel.to_csv(OUT / "relevance.csv", index=False)
    meta = dict(revisions=REVISIONS, nli_hypotheses=NLI_HYPOTHESES, device=DEVICE,
                gpu=torch.cuda.get_device_name(0) if DEVICE == "cuda" else None, nli_dtype="float16",
                truncation_tokens=TRUNC_TOKENS, seed=SEED)
    (OUT / "models.json").write_text(json.dumps(meta, indent=2))
    print(seg.groupby("bank").size(), answers.groupby("bank").agg(phrase=("phrase", "sum"),
          nli=("nli_max", lambda x: (x >= 0.9).sum())))


if __name__ == "__main__":
    main()
