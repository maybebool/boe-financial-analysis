"""Report text, quote verification and table values for the notebooks of 05_call_only_targets.

The UBS filings are PDF conversions with one container per page (`PageN`) and absolutely positioned lines. The
page text is rebuilt line by line (column, top, left), with a repair of line-end hyphens. Two rules for the text
of one line are kept, because the quotes were verified under both in the course of the work:

- "current": block and table elements inside a line are separated by a space, inline elements are joined;
- "legacy": all text nodes of a line are joined, only spacer elements become a space.

A quote counts as verified when it occurs verbatim, after whitespace normalisation, in the text of its page under
one of the two rules. The report files are never modified.
"""
import hashlib
import html as htmlmod
import json
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup, NavigableString, Tag

SPACE_RE = re.compile(r"\s+")
LEFT_RE = re.compile(r"left:\s*(-?[\d.]+)px")
TOP_RE = re.compile(r"top:\s*(-?[\d.]+)px")
WIDTH_RE = re.compile(r"width:\s*([\d.]+)px")
POS_RE = re.compile(r"position:absolute")
IX_HEADER_RE = re.compile(r"<ix:header\b.*?</ix:header\s*>", re.I | re.S)
HYPHENATED_RE = re.compile(r"\b[A-Za-z]+(?:-[A-Za-z]+)+\b")
SEC_SCRIPT_RE = re.compile(rb'<script type="text/javascript"\s+src="/[^"]*"></script>')  # added by EDGAR on delivery
BLOCK = {"div", "p", "table", "thead", "tbody", "tfoot", "tr", "td", "th", "li", "ul", "ol", "br", "section",
         "h1", "h2", "h3", "h4", "h5", "h6"}
RULES = ("current", "legacy")
CACHE_DIR = "_page_text"
NCL_TABLE = "Composition of Non-core and Legacy"


def ws(text):
    """Whitespace normalised to single spaces."""
    return SPACE_RE.sub(" ", str(text)).strip()


def sha256_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized_sha256(raw):
    """SHA-256 of the file after removing the script tag that EDGAR inserts on delivery; its path differs per
    download, so this hash is the one to compare between two downloads of the same filing."""
    return sha256_bytes(SEC_SCRIPT_RE.sub(b"", raw))


def read_html(path):
    return Path(path).read_bytes().decode("utf-8", errors="replace")


def _line_current(div):
    parts = []

    def walk(node):
        for child in node.children:
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif isinstance(child, Tag):
                sep = child.name in BLOCK
                if sep:
                    parts.append(" ")
                walk(child)
                if sep:
                    parts.append(" ")

    walk(div)
    return SPACE_RE.sub(" ", "".join(parts).replace("\xa0", " ")).strip()


def _line_legacy(div):
    parts = []
    for node in div.descendants:
        if isinstance(node, NavigableString):
            if node.parent.name == "div" and "inline-block" in node.parent.get("style", ""):
                parts.append(" ")
            else:
                parts.append(str(node))
    return SPACE_RE.sub(" ", "".join(parts).replace("\xa0", " ")).strip()


def _join_lines(lines, keep_hyphen):
    """Join printed lines. A line-end hyphen before a lower-case word is a soft break and is removed, unless the
    hyphenated form occurs elsewhere in the same report (for example 'Non-' + 'core')."""
    out = ""
    for line in lines:
        if not line:
            continue
        if out.endswith("-") and line[:1].islower():
            head = re.search(r"([A-Za-z-]+)-$", out)
            tail = re.match(r"[A-Za-z-]+", line)
            if head and tail and f"{head.group(1)}-{tail.group(0)}".lower() in keep_hyphen:
                out = out + line
            else:
                out = out[:-1] + line
        else:
            out = (out + " " + line).strip()
    return out


def build_page_texts(path):
    """Page texts of one report under both rules: {"current": {page: text}, "legacy": {page: text}}."""
    html = IX_HEADER_RE.sub("", read_html(path))
    if 'id="Page' not in html:
        raise ValueError(f"{Path(path).name}: not in the positioned page layout")
    soup = BeautifulSoup(html, "html.parser")
    pages = {rule: [] for rule in RULES}
    for page in soup.find_all("div", id=re.compile(r"^Page\d+$")):
        wm = WIDTH_RE.search(page.get("style", ""))
        width = float(wm.group(1)) if wm else 794
        rows = []
        for div in page.find_all("div", style=POS_RE):
            style = div.get("style", "")
            left, top = LEFT_RE.search(style), TOP_RE.search(style)
            if not (left and top) or div.find_parent("div", style=POS_RE) is not None:
                continue
            rows.append((0 if float(left.group(1)) < width / 2 else 1, float(top.group(1)), float(left.group(1)),
                         _line_current(div), _line_legacy(div)))
        rows.sort(key=lambda r: r[:3])
        number = int(page["id"][4:])
        pages["current"].append((number, [r[3] for r in rows]))
        pages["legacy"].append((number, [r[4] for r in rows]))
    out = {}
    for rule in RULES:
        keep = {w.lower() for _, lines in pages[rule] for ln in lines for w in HYPHENATED_RE.findall(ln)}
        out[rule] = {number: _join_lines(lines, keep) for number, lines in pages[rule]}
    return out


def page_texts(path):
    """Page texts of one report, read from the local cache next to the reports when the file hash matches."""
    path = Path(path)
    digest = sha256_bytes(path.read_bytes())
    cache = path.parent / CACHE_DIR / f"{path.stem}.json"
    if cache.exists():
        stored = json.loads(cache.read_text(encoding="utf-8"))
        if stored.get("sha256") == digest:
            return {rule: {int(k): v for k, v in stored[rule].items()} for rule in RULES}
    texts = build_page_texts(path)
    cache.parent.mkdir(exist_ok=True)
    cache.write_text(json.dumps({"sha256": digest, **texts}, ensure_ascii=False), encoding="utf-8")
    return texts


def report_status(reports_dir, manifest):
    """One row per report of the manifest: present locally, and whether its hash equals the manifest."""
    rows = []
    for r in manifest.itertuples():
        path = Path(reports_dir) / r.file
        present = path.exists()
        raw = path.read_bytes() if present else b""
        rows.append({"file": r.file, "present": present,
                     "sha256_matches": bool(present and r.sha256 in (sha256_bytes(raw), normalized_sha256(raw)))})
    return pd.DataFrame(rows)


def verify_quotes(quotes, reports_dir):
    """Check every quote verbatim against the text of its page.

    quotes: DataFrame with the columns file, page, quote. Returns the same rows with the columns `checked` (the
    report is present), `verified` (the quote is on the stated page) and `rule` (the line rule under which it
    was found). Quotes of reports that are not present are returned unchecked."""
    reports_dir = Path(reports_dir)
    texts, rows = {}, []
    for r in quotes.itertuples(index=False):
        row = r._asdict()
        path = reports_dir / r.file
        if not path.exists():
            rows.append({**row, "checked": False, "verified": False, "rule": ""})
            continue
        if r.file not in texts:
            texts[r.file] = page_texts(path)
        found = [rule for rule in RULES if ws(r.quote) in ws(texts[r.file][rule].get(int(r.page), ""))]
        rows.append({**row, "checked": True, "verified": bool(found), "rule": found[0] if found else ""})
    return pd.DataFrame(rows)


def ncl_table(path):
    """Operational risk RWA and total RWA of the table 'Composition of Non-core and Legacy', for the two
    reporting dates of the table. The values are read from the positioned cells and the column is checked."""
    html = read_html(path)
    segment = html[html.index(">" + NCL_TABLE):][:60000]
    items = []
    for m in re.finditer(r'<div id="[^"]*" style="position:absolute;([^"]*)">', segment):
        left, top = LEFT_RE.search(m.group(1)), TOP_RE.search(m.group(1))
        end = segment.find('<div id="', m.end())
        text = htmlmod.unescape(re.sub(r"<[^>]+>", "", segment[m.end():end if end > 0 else m.end() + 300]))
        text = text.replace("\xa0", " ").strip()
        if left and top and text:
            items.append((float(top.group(1)), float(left.group(1)), text))
    top0 = items[0][0]
    rows = {}
    for top, left, text in items:
        if top < top0:
            break
        if top <= top0 + 260:
            rows.setdefault(round(top), []).append((left, text))
    rows = [sorted(r) for _, r in sorted(rows.items())]
    head = [(left, text) for top, left, text in items if top0 <= top <= top0 + 60
            and text in ("RWA", "LRD", "Total assets")]
    if sorted(t for _, t in head) != ["LRD", "RWA", "Total assets"]:
        raise ValueError(f"{Path(path).name}: column headers of the table not found")
    is_date = re.compile(r"\d\d?\.\d\d?\.\d\d")
    dates = next(r for r in rows if sum(bool(is_date.fullmatch(t)) for _, t in r) == 6)
    dates = [t for _, t in dates if is_date.fullmatch(t)]
    oprisk = next(r for r in rows if r[0][1] == "Operational risk")[1:]
    total = next(r for r in rows if r[0][1] == "Total")[1:]
    i = [t for _, t in sorted(head)].index("RWA")
    rwa_total = total[2 * i:2 * i + 2]
    if len(oprisk) != 2 or len(total) != 6 or any(abs(a[0] - b[0]) > 3 for a, b in zip(oprisk, rwa_total)):
        raise ValueError(f"{Path(path).name}: operational risk values are not in the RWA columns")
    return {"dates": dates[2 * i:2 * i + 2], "operational_risk": [float(t) for _, t in oprisk],
            "total_rwa": [float(t) for _, t in rwa_total]}


def mode_message(status):
    """One line that states the mode of the run."""
    n, present = len(status), int(status.present.sum())
    if present == 0:
        return (f"REPORTS NOT PRESENT: quote verification skipped ({n} reports expected under data/reports/). "
                "The results below come from the delivered files; counts and key values are still asserted.")
    if present < n:
        return (f"REPORTS PARTLY PRESENT ({present} of {n}): quotes of the missing reports are not verified; "
                "counts and key values are asserted.")
    return f"REPORTS PRESENT ({n} of {n}): every quote is verified against the text of its page."
