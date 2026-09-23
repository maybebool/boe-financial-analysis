"""Phase 3b: reconstruct report text page by page and retrieve passages for the five phase 3 cases.

Run from the repository root: python notebooks/roman/analysis/phase3b_reports.py
Reads notebooks/roman/data/reports/ (never modified) and phase 3 statements; writes report_pages.csv,
checks.csv, hits_reports.csv and hits_calls.csv to notebooks/roman/data/phase3b/.
"""
import hashlib
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup, NavigableString

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / "notebooks" / "roman" / "data" / "reports"
PHASE3 = ROOT / "notebooks" / "roman" / "data" / "phase3"
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3b"

CASES = {
    "C1": ("UBS", [r"gross cost sav", r"gross sav", r"cost reduction", r"(run-rate|exit rate)[^.]{0,80}sav"]),
    "C2": ("UBS", [r"integration-related expenses", r"integration expenses", r"costs to achieve"]),
    "C3": ("UBS", [r"\bFRTB\b", r"fundamental review of the trading book", r"Basel III final", r"final Basel III",
                   r"Basel 3 final", r"final Basel 3", r"Basel III reform"]),
    "C4": ("UBS", [r"\bAT1\b[^.]{0,120}issu", r"issu[^.]{0,120}\bAT1\b", r"additional tier 1[^.]{0,120}issu",
                   r"issu[^.]{0,120}additional tier 1"]),
    "C5": ("JPM", [r"First Republic", r"bargain purchase", r"\boutlook\b", r"\bguidance\b"]),
}
CHECK_TERMS = ["FRTB", "Basel III", "integration-related", "First Republic"]
SPACE_RE = re.compile(r"\s+")
LEFT_RE = re.compile(r"left:\s*(-?[\d.]+)px")
TOP_RE = re.compile(r"top:\s*(-?[\d.]+)px")
WIDTH_RE = re.compile(r"width:\s*([\d.]+)px")


def file_hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(REPORTS.glob("*.htm"))}


def line_text(div):
    """Text of one positioned line: spacer divs and non-breaking spaces become one space, nothing else is added."""
    parts = []
    for node in div.descendants:
        if isinstance(node, NavigableString):
            if node.parent.name == "div" and "inline-block" in node.parent.get("style", ""):
                parts.append(" ")
            else:
                parts.append(str(node))
    return SPACE_RE.sub(" ", "".join(parts).replace("\xa0", " ")).strip()


def join_lines(lines):
    out = ""
    for ln in lines:
        if not ln:
            continue
        if out.endswith("-") and ln[:1].islower():
            out = out[:-1] + ln
        else:
            out = (out + " " + ln).strip()
    return out


def pages_positioned(html):
    """UBS PDF conversions: one text per PageN container, lines in column, top, left order."""
    b = html.find("</ix:header>")
    soup = BeautifulSoup(html[b:] if b >= 0 else html, "html.parser")
    pages = []
    for page in soup.find_all("div", id=re.compile(r"^Page\d+$")):
        width = float(WIDTH_RE.search(page.get("style", "")).group(1)) if WIDTH_RE.search(page.get("style", "")) else 794
        rows = []
        for d in page.find_all("div", style=re.compile(r"position:absolute")):
            st = d.get("style", "")
            lm, tm = LEFT_RE.search(st), TOP_RE.search(st)
            if not (lm and tm):
                continue
            if d.find_parent("div", style=re.compile(r"position:absolute")) is not None:
                continue  # nested line, already contained in its parent's text
            left, top = float(lm.group(1)), float(tm.group(1))
            rows.append((0 if left < width / 2 else 1, top, left, line_text(d)))
        rows.sort()
        pages.append((int(page["id"][4:]), join_lines([r[3] for r in rows])))
    return pages


def pages_split(html, pattern):
    """Flowing HTML: split at page markers, text per chunk with get_text."""
    chunks = re.split(pattern, html)
    out = []
    for i, ch in enumerate(chunks, start=1):
        txt = SPACE_RE.sub(" ", BeautifulSoup(ch, "html.parser").get_text(" ").replace("\xa0", " ")).strip()
        if txt:
            out.append((i, txt))
    return out


def reconstruct(path):
    html = path.read_text(encoding="utf-8", errors="replace")
    if 'id="Page' in html:
        return pages_positioned(html), "positioned"
    if path.name.startswith("UBS"):
        return pages_split(html, r'<a name="page_\d+"></a>'), "flow_page_anchor"
    return pages_split(html, r'<hr style="page-break-after:always">'), "flow_page_break"


def heading_before(text, pos):
    """Nearest preceding short title-case run, as a rough section label."""
    window = text[max(0, pos - 1500):pos]
    cands = re.findall(r"(?:^|\. )([A-Z][A-Za-z&,\- ]{3,60})(?= [A-Z][a-z])", window)
    return cands[-1].strip() if cands else ""


def retrieve(df, text_col, meta_cols, bank_filter):
    rows = []
    for case, (bank, pats) in CASES.items():
        rx = re.compile("|".join(f"(?:{p})" for p in pats), re.I)
        sub = df[df.bank == bank] if bank_filter else df
        for _, r in sub.iterrows():
            t = r[text_col]
            for m in rx.finditer(t):
                rows.append(dict(case=case, **{c: r[c] for c in meta_cols}, match=m.group(0),
                                 context=t[max(0, m.start() - 300):m.end() + 300]))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    before = file_hashes()
    pages, checks = [], []
    for p in sorted(REPORTS.glob("*.htm")):
        bank, quarter = p.stem.split("_")[:2]
        if "annual" in p.stem:
            quarter = f"{quarter} annual report"
        pg, layout = reconstruct(p)
        raw = p.read_text(encoding="utf-8", errors="replace")
        full = " ".join(t for _, t in pg)
        checks.append(dict(file=p.name, layout=layout, pages=len(pg), empty_pages=sum(1 for _, t in pg if not t),
                           characters=len(full),
                           **{f"raw_{w}": len(re.findall(re.escape(w), raw)) for w in CHECK_TERMS},
                           **{f"text_{w}": len(re.findall(re.escape(w), full)) for w in CHECK_TERMS}))
        pages += [dict(bank=bank, quarter=quarter, file=p.name, page=n, text=t) for n, t in pg]
    pages = pd.DataFrame(pages)
    pages.to_csv(OUT / "report_pages.csv", index=False)
    pd.DataFrame(checks).to_csv(OUT / "checks.csv", index=False)

    hr = retrieve(pages, "text", ["bank", "quarter", "file", "page"], True)
    hr.to_csv(OUT / "hits_reports.csv", index=False)
    st = pd.read_csv(PHASE3 / "statements.csv")
    st["text"] = st.text.fillna("")
    hc = retrieve(st, "text", ["bank", "quarter", "call_type", "stmt_id", "speaker_name", "section"], True)
    hc.to_csv(OUT / "hits_calls.csv", index=False)
    assert file_hashes() == before, "report files changed"
    print(pd.DataFrame(checks).to_string(index=False))
    print(hr.groupby(["case", "quarter"]).size().unstack(0).fillna(0).astype(int))
    print(hc.groupby(["case", "quarter"]).size().unstack(0).fillna(0).astype(int))


if __name__ == "__main__":
    main()
