import re, itertools
import numpy as np, pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / "analysis"))
from config import RELEASE_DIR

s = pd.read_csv(RELEASE_DIR / "all_sentences.csv")
s = s[s.call_type == 'earnings'].copy()

NAMES = set()
for n in s.speaker_name.dropna().unique():
    NAMES.update(t for t in re.split(r"[ .]+", n) if len(t) > 2)
NAMES.update(["Sergio", "Ermotti", "Todd", "Tuckner", "Sarah", "Youngwood", "Jamie", "Jeremy"])
MASKS = [
    (r"\b[1-4]Q\s?'?\d{2}\b|\bQ[1-4]\b", " QTR "),
    (r"\b(first|second|third|fourth)[- ]quarter\b", " QTR "),
    (r"\b(19|20)\d{2}\b", " YEAR "),
    (r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b", " MONTH "),
    (r"[$€£]?\d[\d,.]*\s?(%|percent|bps|basis points|billion|million|bn|trillion)?", " NUM "),
]
NAME_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, NAMES), key=len, reverse=True)) + r")\b", re.I)

def clean(t):
    t = t.lower()
    t = re.sub(r"\[[^\]]*\]", " ", t)
    t = NAME_RE.sub(" PERSON ", t)
    for p, r in MASKS:
        t = re.sub(p, r, t)
    return t

s["text"] = s.sentence.map(clean)
s["n_words"] = s.sentence.str.split().str.len()
s = s[s.n_words >= 4]
s["period"] = (s.quarter >= "2024-Q1").astype(int)  # 0 = 2023, 1 = 2024

VIEWS = {
    "analyst_qa": lambda d: d[(d.section == "qa") & (d.speaker_role == "analyst")],
    "constant_mgmt": lambda d: d[d.speaker_name.isin(["Sergio P. Ermotti", "Jeremy Barnum"])],
}

def cv_auc(d, labels_by_call):
    y = d.quarter.map(labels_by_call).values
    calls = sorted(d.quarter.unique())
    scores = np.zeros(len(d))
    for c in calls:
        tr, te = (d.quarter != c).values, (d.quarter == c).values
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=3, sublinear_tf=True, stop_words="english")
        Xtr = vec.fit_transform(d.text[tr]); Xte = vec.transform(d.text[te])
        clf = LogisticRegression(C=1.0, max_iter=2000, class_weight="balanced").fit(Xtr, y[tr])
        scores[te] = clf.predict_proba(Xte)[:, 1]
    return roc_auc_score(y, scores)

def permutation_test(d):
    calls = sorted(d.quarter.unique())
    true = {c: int(c >= "2024-Q1") for c in calls}
    obs = cv_auc(d, true)
    null = []
    for combo in itertools.combinations(calls, len(calls) // 2):
        lab = {c: int(c in combo) for c in calls}
        a = cv_auc(d, lab)
        null.append(max(a, 1 - a))  # label direction is arbitrary
    null = np.array(null)
    return obs, np.mean(null >= obs), np.percentile(null, 95)

def fightin_words(d, top=15):
    vec = CountVectorizer(ngram_range=(1, 2), min_df=3, stop_words="english")
    X = vec.fit_transform(d.text)
    vocab = np.array(vec.get_feature_names_out())
    y = d.period.values
    a = np.asarray(X.sum(0)).ravel() * 0.01 + 0.01  # informative prior, scaled corpus counts
    a0 = a.sum()
    y_i = np.asarray(X[y == 1].sum(0)).ravel(); n_i = y_i.sum()
    y_j = np.asarray(X[y == 0].sum(0)).ravel(); n_j = y_j.sum()
    delta = (np.log((y_i + a) / (n_i + a0 - y_i - a)) - np.log((y_j + a) / (n_j + a0 - y_j - a)))
    var = 1 / (y_i + a) + 1 / (y_j + a)
    z = delta / np.sqrt(var)
    order = np.argsort(z)
    return list(zip(vocab[order[::-1][:top]], z[order[::-1][:top]].round(1))), list(zip(vocab[order[:top]], z[order[:top]].round(1)))

if __name__ == "__main__":
    for view, f in VIEWS.items():
        for bank in ["UBS", "JPM"]:
            d = f(s[s.bank == bank]).reset_index(drop=True)
            obs, p, q95 = permutation_test(d)
            print(f"{view:14s} {bank}  n={len(d):5d}  AUC 2023 vs 2024 = {obs:.3f}  null95 = {q95:.3f}  p = {p:.3f}")
