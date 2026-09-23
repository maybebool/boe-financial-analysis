import pytest

import phase3b_reports as p3b

FRAGMENT = """<div id="Page1" style="position:relative;width:794px;height:1123px;">
<div style="position:absolute;left:57px;top:110px;">The<div style="display:inline-block;width:8px">&#160;</div>impact of <span>FR</span><span>TB</span> is<div style="display:inline-block;width:2px">&#160;</div>expec-</div>
<div style="position:absolute;left:57px;top:128px;">ted to rise.</div>
<div style="position:absolute;left:420px;top:100px;">Right column.</div>
</div>"""


def test_positioned_reconstruction():
    pages = p3b.pages_positioned(FRAGMENT)
    assert pages == [(1, "The impact of FRTB is expected to rise. Right column.")]


@pytest.mark.skipif(not p3b.REPORTS.exists(), reason="reports not available")
def test_every_report_has_text_and_is_unchanged():
    before = p3b.file_hashes()
    assert len(before) == 18  # 16 quarterly reports and 2 UBS annual reports
    for name in ["UBS_2023-Q1_report.htm", "UBS_2024-Q4_report.htm", "JPM_2023-Q2_report.htm"]:
        pages, _ = p3b.reconstruct(p3b.REPORTS / name)
        assert pages and all(t for _, t in pages)
    assert p3b.file_hashes() == before
