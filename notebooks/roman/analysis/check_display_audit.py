"""Audit of Roman's independent checks in phases 3d to 3g: which genuine hits did the first version of check_terms.py
not show?

Run from the repository root: python notebooks/roman/analysis/check_display_audit.py
Both versions of Roman's tool are copied to a temporary directory and imported from there; the roman_check folders
are only read. "Genuine" hits are the hits of the phase 3h version (ix:header removed, short upper-case acronyms as
whole words, other terms tolerant) in the visible text. A genuine hit counts as shown if it overlaps one of the hits
that the first version displayed (the first MAX_HITS = 12 per term and file, in text including the ix:header, with
acronyms matched tolerantly). Writes notebooks/roman/data/phase3h/display_audit.csv.
"""
import hashlib
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

import lxml.html
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "notebooks" / "roman" / "data"
V1 = DATA / "phase3d" / "roman_check" / "check_terms.py"
V2 = DATA / "phase3h" / "roman_check" / "check_terms.py"
SUMS = DATA / "phase3h" / "roman_check" / "SHA256SUMS"
RUNS = {  # run: check file (None: the built-in units of version 1)
    "3d": None,
    "3e": DATA / "phase3e" / "check_units.json",
    "3f": DATA / "phase3f" / "check_units.json",
    "3f 2024-Q2": DATA / "phase3f" / "check_units_2024q2.json",
    "3g": DATA / "phase3g" / "check_units.json",
    "3g 2024-Q2": DATA / "phase3g" / "check_units_2024q2.json",
}


def load(path, name, tmp):
    copy = Path(tmp) / f"{name}.py"
    shutil.copyfile(path, copy)
    spec = importlib.util.spec_from_file_location(name, copy)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def header_span(v1, name):
    """Span of the ix:header text inside version 1's report text, (-1, -1) if the file has none."""
    tree = lxml.html.fromstring((v1.REPORTS / name).read_bytes())
    hdr = [e for e in tree.iter() if isinstance(e.tag, str) and e.tag.lower() == "ix:header"]
    if not hdr:
        return -1, -1
    ht = " ".join(" ".join(hdr[0].itertext()).split())
    full = v1.report_text(name)
    i = full.find(ht)
    assert i >= 0
    return i, i + len(ht)


def matches(mod, text, term, near):
    out = []
    for m in mod.tolerant(term).finditer(text):
        w = text[max(0, m.start() - mod.NEAR):m.end() + mod.NEAR]
        if near and not mod.tolerant(near).search(w):
            continue
        out.append((m.start(), m.end()))
    return out


def main():
    sums = {line.split()[1]: line.split()[0] for line in SUMS.read_text().splitlines() if line.strip()}
    for p in (V1, V2):
        assert hashlib.sha256(p.read_bytes()).hexdigest() == sums[str(p.relative_to(ROOT))], p
    sys.dont_write_bytecode = True
    with tempfile.TemporaryDirectory() as tmp:
        v1, v2 = load(V1, "check_terms_v1", tmp), load(V2, "check_terms_v2", tmp)
        rows = []
        for run, path in RUNS.items():
            units = v1.UNITS if path is None else v1.load_units(path)
            for unit, (files, terms) in units.items():
                for f in files:
                    old = v1.report_text(f)
                    a, b = header_span(v1, f)
                    for term, near in terms:
                        shown = matches(v1, old, term, near)[:v1.MAX_HITS]
                        genuine = [s for s in matches(v2, old, term, near) if not a <= s[0] < b]
                        # the same count on the phase 3h text (header removed) confirms the coordinates
                        assert len(genuine) == len(matches(v2, v2.report_text(f), term, near)), (run, unit, f, term)
                        overlap = lambda s, t: s[0] < t[1] and t[0] < s[1]  # noqa: E731
                        shown_genuine = sum(any(overlap(g, s) for s in shown) for g in genuine)
                        n_header = sum(a <= s[0] < b for s in shown)
                        n_false = sum(not a <= s[0] < b and not any(overlap(s, g) for g in genuine) for s in shown)
                        rows.append(dict(run=run, unit=unit, file=f, term=term, near=near or "", genuine=len(genuine),
                                         shown_genuine=shown_genuine, hidden=len(genuine) - shown_genuine,
                                         shown_header=n_header, shown_false=n_false,
                                         cap=len(genuine) > v1.MAX_HITS))
    d = pd.DataFrame(rows)
    d.to_csv(DATA / "phase3h" / "display_audit.csv", index=False)
    print(d.groupby("run")[["genuine", "shown_genuine", "hidden", "shown_header", "shown_false"]].sum().to_string())
    h = d[d.hidden > 0]
    print(h.groupby(["run", "unit", "term", "near"])[["genuine", "shown_genuine", "hidden", "shown_header",
                                                        "shown_false"]].sum().to_string())


if __name__ == "__main__":
    main()
