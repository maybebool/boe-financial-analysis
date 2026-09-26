# Phase 3h: the call-only figures in the UBS reports of 2025 and 2026

First draft 2026-09-26; this revision of 2026-09-26 incorporates Roman's decisions of the same day. Both were written before any search or reading of this phase. Descriptive: no test, nothing enters the register. Release `data/results/2026-09-23/` (frozen); units, classes and search terms from phases 3d, 3f and 3g. The earlier phases, their folders, `notebooks/roman/data/reports/` and both `roman_check` folders are not changed; outputs only under `notebooks/roman/data/phase3h/`.

## Transparency note

When the files were obtained, the "Recent developments" sections of the 2025-Q2 and 2026-Q2 reports were briefly looked at outside this protocol. The search terms of this phase do not come from that look: the terms for (a) are the existing terms of phases 3d and 3g, and the terms for (b) are derived below from the call sentences of the units.

## Questions

- **(a)** Does the figure of one of the nine units of the main finding (T16, T25, T27, T32, T33, T68, F11, F12, F22) or of the integration-cost total T30 appear in one of the 13 UBS reports of 2025 and 2026, and in which report first?
- **(b)** What do these reports say about the outcome of each unit: achieved, missed, revised, still open or no longer mentioned, and what is the actual value where one is reported?

## Units

| unit | call | commitment (call sentence) | deadline |
|---|---|---|---|
| T16 | 2023-Q3 | NCL operational risk RWA to decrease to around 14 billion | end-2026 |
| T25 | 2023-Q4 | NCL wind-down to result in a capital release of over 6 billion | end-2026 |
| T27 | 2023-Q4 | NCL credit and market risk RWA substantially below 40 billion | end-2024 |
| T30 | 2023-Q4, 2024-Q4 | integration-related expenses to total around 13 billion, raised to around 14 billion | end-2026 |
| T32 | 2023-Q4 | going-concern capital requirement to increase by around 180 basis points to 16.7% | 2026 to 2030 |
| T33 | 2023-Q4 | issue up to 2 billion in AT1 | 2024 |
| T68 | 2024-Q4 | bring Group HoldCo down to around 90 billion | end-2025 |
| F11 | 2023-Q4 | going concern capital ratio to around 18% by building out AT1 | over time (2026 to 2030 in context) |
| F12 | 2023-Q4 | reduce LRD by over 100 billion at constant FX (Group: NCL and core divisions) | three years (end-2026) |
| F22 | 2024-Q4 | operate with an LCR below the 4Q24 level of 188% | going forward |

## Reports and manifest

- **Reports.** `notebooks/roman/data/reports_2025_2026/`, read only (13 files):
  - quarterly reports 2025-Q1 to 2026-Q2 (the 2026-Q2 report is titled "30 June 2026 Interim Report" and is treated as the 2026-Q2 quarterly report);
  - the 2025 annual report (Form 20-F);
  - the Pillar 3 reports as of the six quarter ends 2025-Q1 to 2026-Q2.

  For (b) only, and only for T27 and T33, the 2024-Q4 report and the 2024 annual report in `notebooks/roman/data/reports/` are also read (read only).
- **Publication date.** Taken from the signature "Date:" of each filing, as in phase 3e, and recorded before any search. "First" in (a) means first by publication date.
- **Manifest.** `notebooks/roman/data/phase3h/manifest.csv`, one row per report (the 13 files and the two 2024 files):
  - file name, accession and source URL (from Roman's `sources.csv`; for the two 2024 files added by Roman);
  - download date (2026-09-26 for the 13 files);
  - SHA-256 of the raw file and of the text export, number of pages, characters of the removed `ix:header`.

  **The search starts only when the manifest is complete** (no empty accession, URL or date). Raw-file hashes are checked before and after every step.

## Text

- **Module.** The text is prepared by the shared module `analysis/report_text.py` (tests in `tests/test_report_text.py`), not in the phase scripts.
- **Header.** The hidden Inline XBRL header, the block from `<ix:header>` to `</ix:header>` inclusive, is removed before any extraction. The 2025-Q2 and 2026-Q2 reports and the 2025 annual report have one; its 1.8 to 4.6 million characters of contexts and member names would otherwise match terms such as "RWA".
- **Separation rule (new, Roman's decision).** Block and table elements (`div`, `p`, `table`, `tr`, `td`, `th`, `li`, `br`) are separated by a space. Inline elements (`span`, `a`, `b`, `i`, Inline XBRL tags such as `ix:nonFraction`, `ix:nonNumeric`, `ix:continuation`) are unwrapped without a separator, so that figures split across tags stay intact. The spacer divs of the positioned layout keep producing a space.

  This differs from the phase 3b reconstruction only inside Inline XBRL text blocks. There, a whole note is nested as positioned `div` elements within one line, and phase 3b joined its sub-lines without a space (for example "settlement risk.Loan underwriting" in the 2025 annual report). The module records the number of lines whose text differs from the phase 3b rule per report in the manifest. The test that currently requires identity with phase 3b is replaced by: identical wherever a line contains no nested block element.
- **Export.** The export `notebooks/roman/data/phase3h/text/<file>.txt` (one block per page, headed `=== page N ===`) is the reference text of the pipeline. Roman's `check_terms.py` (version of `notebooks/roman/data/phase3h/roman_check/`, hashes in `SHA256SUMS`) reads the raw HTML itself; there is no shared text.
- **Hit counts for comparison.** For every term in the check files, the hit count per file on the export, with the matching rule of Roman's tool, is written into the check file (`pipeline_hits`). The count of the tool on the raw HTML is computed as well, and every difference is listed and explained before reading.
- **Matching rule, the same on both sides.** Terms are unchanged. Short upper-case acronyms (at most six characters without whitespace, e.g. AT1, LCR, LRD, TLAC, RWA) are matched as whole words, case-sensitive, with an optional plural s; all other terms as before (phrases case-insensitive, figures with word boundaries). This changes the matching of phases 3d and 3g for acronyms, which there also matched inside words (the "ELA" case in 3g), and is stated as a deviation.

## (a) Figure in the reports

- **Terms.** Unchanged: the round-1 terms of phase 3d for T16, T25, T27, T32, T33 and T68 (`data/phase3d/search_terms.csv`, round-1 hash f7e95dac…) and the phase 3g terms for F11, F12 and F22 (`data/phase3g/search_terms.csv`, hash 6fd981cc…). Both hashes are checked before searching.
- **T30.** Searched with its phase 3d terms, and in addition classified in (a) on the (b) hits, since the (b) terms include the raised figure of around 14 billion. Every class of T30 carries the note "terms from (b)" where it rests on a (b) hit.
- **Hit and reading.** Hit definition as in phases 3d and 3f: a sentence with a phrase (group 2) or a figure (group 3). Reading in two passes as in the phase 3g amendment: first every hit with a figure, then a full-text window around every term hit.
- **Classes.** As in phase 3d, with the consistency rule of 2026-09-24:
  - **A:** the same figure for the same commitment in a forward-looking sentence.
  - **B:** a forward-looking sentence on the same commitment or the same reduction, also with another scope, with another figure or without a figure.
  - **C:** neither.
  - Actual values are never A or B, even when they equal the call figure.
- **Retrospective mentions.** A sentence that names the call figure as a target in backward-looking form (for example "we met our target of around 90 billion") does not change the class. It is recorded in the column `figure_named_retrospectively` and reported next to the class.
- **Output.** One class per unit and report. Per unit: the first report by publication date with A, the first with A or B, and the first with a retrospective mention of the figure. Every quoted sentence is checked verbatim (whitespace normalised) against the exported page text.

## (b) Outcome

- **Terms.** Fixed now, derived from the call sentences (metric phrase with the report spelling variants used since phase 3d, and the call figure in report formats). They are written to `notebooks/roman/data/phase3h/outcome_terms.csv`, and the file hash goes into `run_log.json` before any search.

| unit | metric phrases | figures |
|---|---|---|
| T16 | operational risk RWA; operational risk risk-weighted assets; Non-core and Legacy | 14bn; 14 billion |
| T25 | capital release; capital released; released capital; Non-core and Legacy | 6bn; 6 billion |
| T27 | credit and market risk; market and credit risk; Non-core and Legacy | 40bn; 40 billion |
| T30 | integration-related expenses; costs to achieve | 13bn; 13 billion; 14bn; 14 billion |
| T32 | going concern capital requirement; going concern requirement; phase-in | 16.7%; 180 basis points; 180bps |
| T33 | AT1; additional tier 1 | 2bn; 2 billion |
| T68 | HoldCo; total loss-absorbing capacity; TLAC | 90bn; 90 billion |
| F11 | going concern capital ratio | 18%; 18 % |
| F12 | leverage ratio denominator; LRD | 100bn; 100 billion |
| F22 | liquidity coverage ratio; LCR | 188%; 188 % |

  Outcome words, the same for all units: achieved, reached, met, completed, exceeded, delivered, below, above, revised, updated, now expect, no longer, replaced, discontinued, remaining, cumulative.
- **Hit and reading.** A hit is a sentence or table block with a metric phrase. The hits are read in this order: first those with a figure or an outcome word, then per report the table or sentence that gives the unit's actual value as of the report date (for example the NCL RWA split, the TLAC and LCR key metrics, the cumulative integration-related expenses).
- **Status per unit and report,** one of:
  - **achieved:** the report says the commitment was met, or the reported actual meets it at or after the deadline;
  - **missed:** the deadline has passed and the reported actual does not meet it, or the report says so;
  - **revised:** a new figure, scope or deadline for the same commitment, including a changed regulatory basis (for T32 and F11, for example, new Swiss capital rules);
  - **open:** only if the deadline lies after 30 June 2026 and a report of 2026 (2026-Q1, 2026-Q2 or their Pillar 3 reports) still mentions the commitment;
  - **no longer mentioned:** otherwise, when none of the above applies.
- **Last mention.** For every unit the column `last_mentioned_in` gives the latest report that mentions the commitment (the commitment itself, not only the metric).
- **Final status and actual value.** The final status is the status in the latest report, with the sequence over the reports shown next to it. The actual value is given as reported (currency, unit, reference date, phase-in or fully applied), with the quote checked against the page. It is not converted. F12 is at constant FX in the call, and the reports give LRD at current FX, so a comparison is stated as approximate.
- **T27 and T33.** Their deadlines lie in 2024. For them the 2024-Q4 report and the 2024 annual report are also read, with the same terms and rules. If the outcome is visible in none of the reports read, the status is "not determinable from these reports".

## Check files for Roman

Written before any search, hashes in `run_log.json`, in the known format `{"unit": {"files": [...], "terms": [["term", "keyword nearby or null"], ...]}}`, with the extra key `pipeline_hits` (`[[file, term, near, hits], ...]`, counted on the export). File names are relative to `notebooks/roman/data/reports/`, so the 2025 and 2026 files are given as `../reports_2025_2026/<file>`.

- `check_units_a.json`, (a): each phrase alone and each figure with the unit's first phrase nearby, as in phase 3f; all 13 files per unit.
- `check_units_b.json`, (b): each metric phrase alone, each figure with the unit's first metric phrase nearby, and each outcome word with the unit's first metric phrase nearby; all 13 files per unit, plus the two 2024 files for T27 and T33.

## Outputs

- **Scripts:**
  - `analysis/report_text.py`, updated for the separation rule and the manifest columns;
  - `analysis/phase3h_terms.py`, outcome terms and check files with hashes and hit counts;
  - `analysis/phase3h_search.py`, (a) and (b) hits;
  - `analysis/phase3h_read.py`, classes, statuses, actual values and quote check.
- **Outputs** in `notebooks/roman/data/phase3h/`.
- **Notebook** `03h_reports_2025_2026.ipynb`.
- `FINDINGS.md` is not changed in this phase.

## Tests (pytest)

- `tests/test_report_text.py`: header removed; inline tags do not split figures; block and table elements separated; identical to phase 3b where no nested block element occurs; export roundtrip; manifest complete and hashes correct.
- `tests/test_phase3h.py`:
  - raw files unchanged;
  - the (a) terms equal the phase 3d and 3g terms (hashes);
  - the outcome terms were not changed after the recorded hash;
  - `pipeline_hits` equal a recount on the export;
  - every quote is found on its page;
  - one class per unit and report and one final status per unit;
  - "open" only where a 2026 report mentions the commitment and the deadline is later than 30 June 2026.

## Limits (stated in advance)

- **Reading and check.** One reader. C means not found with the listed terms, not proven absent. Roman's check follows with the check files.
- **Timing.** Outcomes are read at 30 June 2026, while several deadlines lie at the end of 2026 or later.
- **Scope of statements.** The reports speak for the Group or for UBS AG, and a figure of another entity or scope is not the same commitment.
- **Earlier phases.** The separation rule shows that the phase 3b text of the four Inline XBRL reports in `reports/` (2023-Q2 and 2024-Q2 reports, 2023 and 2024 annual reports) joins sub-lines of text blocks without a space. That text was read in phases 3b to 3g. This phase does not change those phases; the effect on them is reported separately.

## Amendment 2026-09-26: execution up to the search

- **Text and manifest.** `report_text.py` implements the separation rule. Lines differing from phase 3b occur only in the three Inline XBRL files (55 in the 2025-Q2 report, 206 in the 2025 annual report, 51 in the 2026-Q2 report; 231 in the 2024 annual report). Publication dates are taken from the filing signatures. The manifest is complete for the 13 files and incomplete for the 2024-Q4 report and the 2024 annual report (no accession, source URL or download date in `sources.csv`; the files themselves do not contain them). Therefore no search has been run; `phase3h_search.py` refuses while the manifest is incomplete.
- **Terms and check files.** `a_terms.csv` (81 terms, equal to the phase 3d round-1 and phase 3g terms, hashes checked), `outcome_terms.csv` (208 terms) and `check_units_a.json` / `check_units_b.json` with `pipeline_hits` were written, and their hashes recorded in `run_log.json`.
- **Deviation list.** `deviations.csv` has 71 term-file pairs where Roman's tool on the raw HTML counts differently from the pipeline on the export, each with its cause:
  - **53, table or glossary layout.** The export orders table cells row by row, so that multi-line column headers are interleaved (e.g. "Non-core and Banking Management Bank Legacy"). The raw HTML keeps them together in document order. The tool therefore counts 7 to 12 more "Non-core and Legacy" per quarterly or annual report, all in table headers. This ordering comes from the phase 3b reconstruction and applied in the earlier phases as well; it affects table headers, not running text.
  - **17, keyword window.** The same ordering changes the distance between an outcome word and its metric phrase by one or two hits.
  - **1, hyphen repair.** One line-end "phase- in" is joined as "phasein" (2025-Q3 Pillar 3 report).

## Amendment 2026-09-26: reproducible file hashes, the two 2024 files

Roman added accession and source URL of the 2024-Q4 report and the 2024 annual report to `sources.csv`; their download dates are the file time stamps, 2026-09-12 and 2026-09-23. His provenance check of the same day found both files identical to a fresh download from their EDGAR URL except for a script tag that the SEC inserts before `</body>` on delivery (`<script type="text/javascript" src="/..."></script>`, with a path that differs on every download). The 2024-Q4 file has no such tag; the annual report has one with another path. Raw-file hashes are therefore not reproducible by a new download, for the 13 new reports as well. The manifest gets two further columns: `sha256_normalized`, the SHA-256 of the raw file after removing exactly this tag (regex on bytes `<script type="text/javascript"\s+src="/[^"]*"></script>`), and `sec_script_tags_removed`, the number of tags removed. `raw_sha256` stays the check that the local files are unchanged during the phase; `sha256_normalized` is the value to compare with a new download. The tag lies outside the `PageN` containers, so the text export does not depend on it.

## Amendment 2026-09-26: search and reading (choices made while reading)

- **Search.** It ran after the manifest was complete (`hits_a.csv`, `hits_b.csv`).
- **Classes from other units' hits.** As in phase 3d (T14), a class may rest on a sentence found through another unit's terms. This applies to T16, found through T25 and T27, and to T32, found through the (b) term "phase-in" and the F12 hits.
- **Consistency rule for the NCL units.** The NCL run-down sentences make T16 and T25 B, as the rule treats the run-down with another scope as the same reduction (as Roman decided for T16 in phases 3d and 3f). These are the credit and market risk RWA ambitions of below USD 8bn and around USD 4bn, and the exit of securitization exposures in the 2025-Q2 Pillar 3 report. F12 (Group LRD) stays C, because those sentences concern RWA, not LRD. This is borderline and noted in `units_3h.csv`.
- **Status "revised" before "open".** A report that restates a changed figure for a commitment with a later deadline gets "revised", not "open" (T30, T32).
- **Final status.** It is the status of the latest quarterly or annual report that states an outcome. The Pillar 3 reports carry none of the commitments except the phase-in of T32 and one NCL sentence, so a status of "no longer mentioned" there does not override an outcome. For T33 the final status comes from the 2024 annual report (deadline 2024).
- **Actual values not reported.** Where the reports give no actual value of the metric (NCL operational risk RWA, HoldCo), the related reported quantity is named and marked as such.
- **Note on T25.** The 2024 annual report, read in this phase only for T27 and T33, states that NCL "released over USD 6 billion of capital to the Group". This is recorded as a note and does not change the status of T25, which is "no longer mentioned" in the reports of 2025 and 2026.
- **Hits only Roman's tool finds.** None of them contains a forward-looking statement on one of the units. The checked windows are glossary entries, note headings, chart labels and an outlook sentence on Group RWA model updates that the pipeline also reads.

**Result.**

- **(a)** No call figure of the ten units appears in a forward-looking sentence of the 13 reports (no A); there is no retrospective mention either. Five units are B: T16, T25 and T27 through the NCL run-down sentences, first 2025-Q1; T32 through the phase-in 2026 to 2030, first 2025-Q1; T30 with around USD 15bn, first 2025-Q4. T33, T68, F11, F12 and F22 are C.
- **(b)**
  - **Achieved:** T27 (around USD 5bn at end-2025, USD 4bn at 31 March 2026) and F22 (quarterly LCR 177.3% to 182.6%).
  - **Revised:** T30 (around USD 15bn; USD 14.2bn incurred by 30 June 2026) and T32 (USD 6bn instead of 9bn; requirement 14.99% at end-2025).
  - **Missed:** T33 (USD 3.5bn issued in 2024 against up to USD 2bn).
  - **No longer mentioned:** T16, T25, T68, F11 (ratio 19.0% at 30 June 2026) and F12 (LRD USD 1,649.8bn at 30 June 2026, current FX).
