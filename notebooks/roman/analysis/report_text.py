"""Shared text preparation for UBS report files (phase 3h onwards): hidden iXBRL header, page texts, text export,
manifest.

The page text is the phase 3b reconstruction (`phase3b_reports.pages_positioned`, positioned layout, hyphen repair of
2026-09-23), so that text read in later phases is built exactly as in phases 3b to 3g. Before that, the hidden Inline
XBRL header is removed explicitly: the block from `<ix:header` to `</ix:header>` inclusive. Inline XBRL tags inside
the pages are unwrapped without a separator, as in phase 3b.

Command line (from the repository root):
    python notebooks/roman/analysis/report_text.py SRC_DIR OUT_DIR
writes OUT_DIR/text/<file>.txt (one block per page, headed "=== page N ===") and OUT_DIR/manifest.csv with file name,
accession, source URL, SHA-256 of the raw file and of the text export. Accession and source URL are not contained in
the files; they are read from OUT_DIR/sources.csv (columns file, accession, source_url) and stay empty where missing.
The source files are never modified; their hashes are checked before and after.
"""
import hashlib
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase3b_reports import pages_positioned  # noqa: E402

IX_HEADER_RE = re.compile(r"<ix:header\b.*?</ix:header\s*>", re.I | re.S)
HIDDEN_RE = re.compile(r"<(\w+)[^>]*style=\"[^\"]*display:\s*none[^\"]*\"[^>]*>(.*?)</\1>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
PAGE_MARK = "=== page {} ==="


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


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


def report_pages(path, repair=True):
    """Page texts [(page number, text)] of one report, ix:header removed, positioned layout only."""
    html, _ = strip_ix_header(read_html(path))
    assert 'id="Page' in html, f"{Path(path).name}: not in the positioned layout"
    return pages_positioned(html, repair=repair)


def export_text(pages):
    return "\n".join(f"{PAGE_MARK.format(n)}\n{t}" for n, t in pages) + "\n"


def parse_export(text):
    """Inverse of export_text: [(page number, text)]."""
    parts = re.split(r"^=== page (\d+) ===\n", text, flags=re.M)
    return [(int(n), t.rstrip("\n")) for n, t in zip(parts[1::2], parts[2::2])]


def build(src_dir, out_dir):
    src_dir, out_dir = Path(src_dir), Path(out_dir)
    files = sorted(src_dir.glob("*.htm"))
    before = {p.name: sha256_bytes(p.read_bytes()) for p in files}
    src = out_dir / "sources.csv"
    sources = pd.read_csv(src, keep_default_na=False).set_index("file") if src.exists() else pd.DataFrame()
    (out_dir / "text").mkdir(parents=True, exist_ok=True)
    rows = []
    for p in files:
        html = read_html(p)
        stripped, removed = strip_ix_header(html)
        assert all(t == "" for t in hidden_texts(stripped)), f"{p.name}: hidden element with text outside ix:header"
        pages = report_pages(p)
        txt = export_text(pages).encode("utf-8")
        (out_dir / "text" / f"{p.stem}.txt").write_bytes(txt)
        get = lambda col: str(sources.loc[p.name, col]) if p.name in sources.index else ""  # noqa: E731
        rows.append(dict(file=p.name, accession=get("accession"), source_url=get("source_url"),
                         raw_sha256=before[p.name], text_sha256=sha256_bytes(txt), pages=len(pages),
                         ix_header_removed=removed > 0, ix_header_chars=removed))
    after = {p.name: sha256_bytes(p.read_bytes()) for p in files}
    assert after == before, "source files changed"
    manifest = pd.DataFrame(rows)
    manifest.to_csv(out_dir / "manifest.csv", index=False)
    return manifest


if __name__ == "__main__":
    print(build(sys.argv[1], sys.argv[2]).drop(columns=["raw_sha256", "text_sha256"]).to_string(index=False))
