import re
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "analysis"))
from config import RELEASE_DIR

s = pd.read_csv(RELEASE_DIR / "all_sentences.csv")
s = s[(s.call_type == "earnings") & (s.section == "qa")]
u = (s.sort_values(["bank", "quarter", "position_in_call", "sentence_number"])
       .groupby(["bank", "quarter", "position_in_call", "speaker_role", "speaker_name"], sort=False)
       .sentence.apply(" ".join).reset_index().rename(columns={"sentence": "text"}))

def build_pairs(u):
    rows = []
    for (bank, q), call in u.groupby(["bank", "quarter"], sort=False):
        call = call.sort_values("position_in_call").to_dict("records")
        i = 0
        while i < len(call):
            if call[i]["speaker_role"] != "analyst":
                i += 1; continue
            qu = call[i]; ans = []; j = i + 1
            while j < len(call) and call[j]["speaker_role"] in ("management", "ir"):
                ans.append(call[j]); j += 1
            if ans:
                rows.append({"bank": bank, "quarter": q, "position_in_call": qu["position_in_call"],
                             "analyst": qu["speaker_name"], "question": qu["text"],
                             "answerers": ", ".join(dict.fromkeys(a["speaker_name"] for a in ans)),
                             "answer": " ".join(a["text"] for a in ans)})
            i = j
    return pd.DataFrame(rows)

NON_ANSWER = [
    r"\b(we|i)\s+(don't|do not|won't|will not|wouldn't|would not)\s+(disclose|comment|give|provide|speculate|guide|break out|get into)",
    r"\bnot (going|gonna) to (comment|give|speculate|get into|disclose|guide)",
    r"\b(too early|premature) to\b",
    r"\bwe('ll| will) (update|come back|tell) you\b",
    r"\b(at|in) (the|our) (next|upcoming|coming) (quarter|call|update|investor day)",
    r"\bno (comment|update)\b",
    r"\bcan't (really )?(comment|give|say|tell|disclose)",
    r"\b(i|we) (would|'d) (rather|prefer) not\b",
    r"\bnot in a position to\b",
]
NA_RE = re.compile("|".join(NON_ANSWER), re.I)

if __name__ == "__main__":
    p = build_pairs(u)
    p["non_answer_hits"] = p.answer.map(lambda t: len(NA_RE.findall(t)))
    vec = TfidfVectorizer(stop_words="english", sublinear_tf=True, min_df=2).fit(pd.concat([p.question, p.answer]))
    Q, A = vec.transform(p.question), vec.transform(p.answer)
    p["rel"] = np.asarray(Q.multiply(A).sum(1)).ravel()
    rng = np.random.default_rng(0); null = []
    for (b, q), idx in p.groupby(["bank", "quarter"]).groups.items():
        idx = np.array(idx)
        for k in idx:
            others = idx[idx != k]
            null.append((k, cosine_similarity(Q[k], A[others]).mean()))
    p.loc[[k for k, _ in null], "rel_null"] = [v for _, v in null]
    p["rel_lift"] = p.rel - p.rel_null
    print(p.groupby("bank").size())
    t = p.groupby(["quarter", "bank"]).agg(pairs=("rel", "size"), rel_lift=("rel_lift", "mean"),
                                           non_answer_share=("non_answer_hits", lambda x: (x > 0).mean())).unstack("bank").round(3)
    print(t)
    p.to_csv(Path("notebooks/roman/data") / "qa_pairs.csv", index=False)  # data/ is git-ignored
