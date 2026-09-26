"""Shared text preparation for UBS report files (phase 3h onwards): hidden iXBRL header, page texts, text export,
manifest.

Rules (plans/phase_3h.md, revision of 2026-09-26):
- The hidden Inline XBRL header, the block from `<ix:header` to `</ix:header>` inclusive, is removed before any
  extraction.
- Pages are the `PageN` containers of the positioned layout; lines are ordered by column, top and left and joined with
  the hyphen repair of 2026-09-23, as in phase 3b (`phase3b_reports`).
- Within a line, block and table elements (div, p, table, tr, td, th, li, br, ...) are separated by a space; inline
  elements (span, a, b, i, font, Inline XBRL tags) are unwrapped without a separator, so that figures split across
  tags stay intact. This differs from phase 3b only where a line contains nested block elements (Inline XBRL text
  blocks), which phase 3b joined without a space; the number of such lines is recorded per report.

Used by analysis/phase3h_text.py, which writes the text export and the manifest. The source files are never modified;
their hashes are checked before and after.
"""
import hashlib
import html as htmlmod
import re
import sys
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup, NavigableString, Tag

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase3b_reports import LEFT_RE, SPACE_RE, TOP_RE, WIDTH_RE, hyphenated_words, join_lines  # noqa: E402
from phase3b_reports import line_text as line_text_3b  # noqa: E402

IX_HEADER_RE = re.compile(r"<ix:header\b.*?</ix:header\s*>", re.I | re.S)
HIDDEN_RE = re.compile(r"<(\w+)[^>]*style=\"[^\"]*display:\s*none[^\"]*\"[^>]*>(.*?)</\1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
DATE_RE = re.compile(r"Date:\s*([A-Z][a-z]+ \d{1,2}, \d{4})")
POS_RE = re.compile(r"position:absolute")
BLOCK = {"div", "p", "table", "thead", "tbody", "tfoot", "tr", "td", "th", "li", "ul", "ol", "br", "section",
         "h1", "h2", "h3", "h4", "h5", "h6"}
SEC_SCRIPT_RE = re.compile(rb'<script type="text/javascript"\s+src="/[^"]*"></script>')  # inserted by EDGAR on delivery
PAGE_MARK = "=== page {} ==="
MANIFEST_COLUMNS = ["file", "accession", "source_url", "download_date", "publication_date", "raw_sha256",
                    "sha256_normalized", "sec_script_tags_removed", "text_sha256", "pages", "ix_header_chars", "lines", "lines_nested_block",
                    "lines_differing_from_phase3b"]


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def normalized_sha256(raw):
    """SHA-256 of the raw bytes after removing the script tag that EDGAR inserts before </body> on delivery (its path
    differs on every download), and the number of tags removed (amendment of 2026-09-26)."""
    tags = SEC_SCRIPT_RE.findall(raw)
    return sha256_bytes(SEC_SCRIPT_RE.sub(b"", raw)), len(tags)


def read_html(path):
    return Path(path).read_bytes().decode("utf-8", errors="replace")


def strip_ix_header(html):
    """Remove the hidden Inline XBRL header block. Returns (html without the block, number of characters removed)."""
    blocks = IX_HEADER_RE.findall(html)
    assert len(blocks) <= 1, "more than one ix:header block"
    return IX_HEADER_RE.sub("", html), sum(len(b) for b in blocks)


def hidden_texts(html):
    """Visible-text content of elements styled display:none (outside the ix:header, which is removed first)."""
    return [" ".join(TAG_RE.sub(" ", inner).split()) for _, inner in HIDDEN_RE.findall(html)]


def publication_date(html):
    """Signature date of the filing ('Date: Month D, YYYY'), the last one in the file, as in phase 3e."""
    text = htmlmod.unescape(re.sub(r"\s+", " ", TAG_RE.sub(" ", html)))
    found = DATE_RE.findall(text)
    return pd.Timestamp(found[-1]).date().isoformat() if found else ""


def line_text(div):
    """Text of one positioned line: block and table elements separated by a space, inline elements joined."""
    parts = []

    def walk(node):
        for c in node.children:
            if isinstance(c, NavigableString):
                parts.append(str(c))
            elif isinstance(c, Tag):
                sep = c.name in BLOCK
                if sep:
                    parts.append(" ")
                walk(c)
                if sep:
                    parts.append(" ")

    walk(div)
    return SPACE_RE.sub(" ", "".join(parts).replace("\xa0", " ")).strip()


def has_nested_block(div):
    return any(e.name in BLOCK and not (e.name == "div" and "inline-block" in e.get("style", ""))
               for e in div.find_all(True))


def pages_and_stats(html, repair=True):
    """Page texts [(page number, text)] of html without ix:header, and line statistics against phase 3b."""
    soup = BeautifulSoup(html, "html.parser")
    pages, n_lines, n_nested, n_diff = [], 0, 0, 0
    for page in soup.find_all("div", id=re.compile(r"^Page\d+$")):
        wm = WIDTH_RE.search(page.get("style", ""))
        width = float(wm.group(1)) if wm else 794
        rows = []
        for d in page.find_all("div", style=POS_RE):
            st = d.get("style", "")
            lm, tm = LEFT_RE.search(st), TOP_RE.search(st)
            if not (lm and tm) or d.find_parent("div", style=POS_RE) is not None:
                continue
            left, top = float(lm.group(1)), float(tm.group(1))
            text = line_text(d)
            n_lines += 1
            n_nested += has_nested_block(d)
            n_diff += text != line_text_3b(d)
            rows.append((0 if left < width / 2 else 1, top, left, text))
        rows.sort()
        pages.append((int(page["id"][4:]), [r[3] for r in rows]))
    keep = hyphenated_words(ln for _, rows in pages for ln in rows) if repair else frozenset()
    stats = dict(lines=n_lines, lines_nested_block=n_nested, lines_differing_from_phase3b=n_diff)
    return [(n, join_lines(rows, keep)) for n, rows in pages], stats


def report_pages(path, repair=True):
    """Page texts [(page number, text)] of one report, ix:header removed, positioned layout only."""
    html, _ = strip_ix_header(read_html(path))
    assert 'id="Page' in html, f"{Path(path).name}: not in the positioned layout"
    return pages_and_stats(html, repair)[0]


def export_text(pages):
    return "\n".join(f"{PAGE_MARK.format(n)}\n{t}" for n, t in pages) + "\n"


def parse_export(text):
    """Inverse of export_text: [(page number, text)]."""
    parts = re.split(r"^=== page (\d+) ===\n", text, flags=re.M)
    return [(int(n), t.rstrip("\n")) for n, t in zip(parts[1::2], parts[2::2])]


def build(files, out_dir, sources, download_dates):
    """Text export to out_dir/text/ and manifest rows for the given report files.

    sources: DataFrame indexed by file with columns accession, source_url; download_dates: {file: date}.
    Missing values stay empty; completeness is checked by the caller."""
    files = [Path(f) for f in files]
    out_dir = Path(out_dir)
    before = {p: sha256_bytes(p.read_bytes()) for p in files}
    (out_dir / "text").mkdir(parents=True, exist_ok=True)
    rows = []
    for p in files:
        raw = read_html(p)
        stripped, removed = strip_ix_header(raw)
        assert 'id="Page' in stripped, f"{p.name}: not in the positioned layout"
        assert all(t == "" for t in hidden_texts(stripped)), f"{p.name}: hidden element with text outside ix:header"
        pages, stats = pages_and_stats(stripped)
        txt = export_text(pages).encode("utf-8")
        (out_dir / "text" / f"{p.stem}.txt").write_bytes(txt)
        get = lambda col: str(sources.loc[p.name, col]) if p.name in sources.index else ""  # noqa: E731
        norm, n_tags = normalized_sha256(p.read_bytes())
        rows.append(dict(file=p.name, accession=get("accession"), source_url=get("source_url"),
                         download_date=download_dates.get(p.name, ""), publication_date=publication_date(stripped),
                         raw_sha256=before[p], sha256_normalized=norm, sec_script_tags_removed=n_tags,
                         text_sha256=sha256_bytes(txt), pages=len(pages),
                         ix_header_chars=removed, **stats))
    assert {p: sha256_bytes(p.read_bytes()) for p in files} == before, "source files changed"
    return pd.DataFrame(rows, columns=MANIFEST_COLUMNS)


def incomplete(manifest):
    """Rows of the manifest with an empty accession, source URL, download or publication date."""
    cols = ["accession", "source_url", "download_date", "publication_date"]
    return manifest[(manifest[cols].astype(str) == "").any(axis=1)]
