import re
from functools import lru_cache

import pytest

import report_text as rt
from phase3b_reports import pages_positioned

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


@lru_cache(maxsize=None)
def pages_of(path):
    return tuple(rt.report_pages(path))


IX_FILES = sorted(p for d in (OLD, NEW) if d.exists() for p in d.glob("UBS_*.htm") if "<ix:header" in rt.read_html(p))


@pytest.mark.skipif(not IX_FILES, reason="no iXBRL reports available")
@pytest.mark.parametrize("path", IX_FILES, ids=lambda p: p.name)
def test_ixbrl_pages_have_no_header_text_and_match_phase3b(path):
    pages = pages_of(path)
    assert pages and not any(HEADER_TOKENS.search(t) for _, t in pages)
    # identical to the reconstruction used in phases 3b to 3g, which cut the file at </ix:header>
    assert list(pages) == pages_positioned(rt.read_html(path), repair=True)


@pytest.mark.skipif(not NEW.exists(), reason="reports_2025_2026 not available")
def test_no_hidden_text_outside_header_in_new_reports():
    for p in sorted(NEW.glob("*.htm")):
        stripped, _ = rt.strip_ix_header(rt.read_html(p))
        assert all(t == "" for t in rt.hidden_texts(stripped)), p.name


def test_build_writes_manifest_and_keeps_sources(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "UBS_x_report.htm").write_text('<ix:header>0001610520</ix:header>' + positioned(["Page text"]))
    out = tmp_path / "out"
    out.mkdir()
    (out / "sources.csv").write_text("file,accession,source_url\nUBS_x_report.htm,0000000000-00-000000,https://example.org/x\n")
    raw = (src / "UBS_x_report.htm").read_bytes()
    m = rt.build(src, out)
    assert (src / "UBS_x_report.htm").read_bytes() == raw
    row = m.iloc[0]
    assert row.accession == "0000000000-00-000000" and row.source_url == "https://example.org/x"
    assert row.raw_sha256 == rt.sha256_bytes(raw)
    txt = (out / "text" / "UBS_x_report.txt").read_bytes()
    assert row.text_sha256 == rt.sha256_bytes(txt) and b"0001610520" not in txt and bool(row.ix_header_removed)
