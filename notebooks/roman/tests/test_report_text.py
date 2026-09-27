import re
from functools import lru_cache

import pytest

import report_text as rt

DATA = rt.Path(rt.__file__).resolve().parents[1] / "data"
NEW = DATA / "reports_2025_2026"
OLD = DATA / "reports"
HEADER_TOKENS = re.compile(r"0001610520|ifrs-full:|xbrli:|dei:")


def positioned(lines):
    return ('<div id="Page1" style="width:794px;">' + "".join(
        f'<div style="position:absolute; left:10px; top:{10 * i}px;">{ln}</div>' for i, ln in enumerate(lines, 1))
        + "</div>")


def test_strip_removes_whole_header_block():
    html = ('<html><body><div style="display:none"><ix:header><ix:hidden>RWA 0001610520</ix:hidden>'
            "<ix:resources>ubs:NonCoreMember</ix:resources></ix:header></div>" + positioned(["Visible RWA text"]))
    stripped, removed = rt.strip_ix_header(html)
    assert removed > 0 and "ix:header" not in stripped and "0001610520" not in stripped
    assert rt.hidden_texts(stripped) == [""]
    assert rt.strip_ix_header(stripped) == (stripped, 0)


def test_inline_tags_do_not_split_figures(tmp_path):
    f = tmp_path / "x.htm"
    f.write_text(positioned(['USD 1.<ix:nonFraction name="a">5</ix:nonFraction>bn of <ix:nonNumeric>RWA</ix:nonNumeric>']))
    assert rt.report_pages(f) == [(1, "USD 1.5bn of RWA")]


def test_export_roundtrip():
    pages = [(1, "first page"), (2, "second\nwith a line"), (7, "")]
    assert rt.parse_export(rt.export_text(pages)) == pages


def test_block_elements_separated_inline_joined(tmp_path):
    f = tmp_path / "x.htm"
    f.write_text(positioned(['<div style="position:relative;"><div style="position:absolute;left:1px;top:1px;">'
                             'settlement risk.</div><div style="position:absolute;left:1px;top:9px;">Loan '
                             '<span>under</span>writing</div></div>']))
    assert rt.report_pages(f) == [(1, "settlement risk. Loan underwriting")]


@lru_cache(maxsize=None)
def lines_of(path):
    html, _ = rt.strip_ix_header(rt.read_html(path))
    soup = rt.BeautifulSoup(html, "html.parser")
    return [d for d in soup.find_all("div", style=rt.POS_RE) if d.find_parent("div", style=rt.POS_RE) is None]


FILES = sorted(p for d in (OLD, NEW) if d.exists() for p in d.glob("UBS_*.htm"))
IX_FILES = [p for p in FILES if "<ix:header" in rt.read_html(p)]


@pytest.mark.skipif(not IX_FILES, reason="no iXBRL reports available")
@pytest.mark.parametrize("path", IX_FILES, ids=lambda p: p.name)
def test_ixbrl_pages_have_no_header_text(path):
    pages = rt.report_pages(path)
    assert pages and not any(HEADER_TOKENS.search(t) for _, t in pages)


@pytest.mark.skipif(not IX_FILES, reason="no iXBRL reports available")
@pytest.mark.parametrize("path", IX_FILES, ids=lambda p: p.name)
def test_identical_to_phase3b_without_nested_blocks(path):
    """The separation rule changes only lines with nested block elements (Inline XBRL text blocks)."""
    for d in lines_of(path):
        if not rt.has_nested_block(d):
            assert rt.line_text(d) == rt.line_text_3b(d)


@pytest.mark.skipif(not NEW.exists(), reason="reports_2025_2026 not available")
def test_no_hidden_text_outside_header_in_new_reports():
    for p in sorted(NEW.glob("*.htm")):
        stripped, _ = rt.strip_ix_header(rt.read_html(p))
        assert all(t == "" for t in rt.hidden_texts(stripped)), p.name


def test_build_writes_manifest_and_keeps_sources(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    f = src / "UBS_x_report.htm"
    body = '<ix:header>0001610520</ix:header>' + positioned(["Page text"]) + "<p>Date: March 17, 2025</p>"
    f.write_text(body + '<script type="text/javascript" src="/abc/x.js"></script></body>')
    out = tmp_path / "out"
    sources = rt.pd.DataFrame({"accession": ["0000000000-00-000000"], "source_url": ["https://example.org/x"]},
                              index=["UBS_x_report.htm"])
    raw = f.read_bytes()
    m = rt.build([f], out, sources, {"UBS_x_report.htm": "2026-09-26"})
    assert f.read_bytes() == raw
    row = m.iloc[0]
    assert list(m.columns) == rt.MANIFEST_COLUMNS
    assert row.accession == "0000000000-00-000000" and row.source_url == "https://example.org/x"
    assert row.download_date == "2026-09-26" and row.publication_date == "2025-03-17"
    assert row.raw_sha256 == rt.sha256_bytes(raw) and row.ix_header_chars > 0
    assert row.sec_script_tags_removed == 1
    assert row.sha256_normalized == rt.sha256_bytes((body + "</body>").encode())
    txt = (out / "text" / "UBS_x_report.txt").read_bytes()
    assert row.text_sha256 == rt.sha256_bytes(txt) and b"0001610520" not in txt
    assert rt.incomplete(m).empty
    m2 = rt.build([f], out, sources.iloc[0:0], {})
    assert len(rt.incomplete(m2)) == 1
