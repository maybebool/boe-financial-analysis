# Phase 3f: the six call-only figures in the Pillar 3 reports

Written 2026-09-24, before any search of this phase. Descriptive: no test, nothing enters the register. Release `data/results/2026-09-23/` (frozen); units, search terms and classes from phase 3d.

## Question

Do the six figures of the main finding, which appear in no UBS quarterly or annual report, appear in a UBS Pillar 3 report? The Pillar 3 reports are the regulatory disclosure most likely to carry capital and RWA figures, so they are the strongest test of the main finding on the report side.

## Units

T16 (NCL operational risk RWA around 14bn by end-2026), T25 (NCL capital release over 6bn by end-2026), T27 (NCL credit and market risk RWA substantially below 40bn by end-2024), T32 (going-concern requirement rising by around 180bp to 16.7% between 2026 and 2030), T33 (AT1 issuance up to 2bn in 2024), T68 (HoldCo around 90bn by end-2025). Classes after Roman's check in phase 3d: T16, T27, T33, T68 are C; T25 and T32 are B (2023 annual report, no figure).

## Reports

`notebooks/roman/data/reports/`, read only: `UBS_2023-Q3_pillar3.htm`, `UBS_2023-Q4_pillar3.htm`, `UBS_2024-Q1_pillar3.htm`, `UBS_2024-Q3_pillar3.htm`, `UBS_2024-Q4_pillar3.htm`, filed on 7 November 2023, 28 March 2024, 7 May 2024, 8 November 2024 and 17 March 2025 (dates given by Roman). The report as of 30 June 2024 (filed 23 August 2024) is not yet available; when Roman adds it as `UBS_2024-Q2_pillar3.htm`, it is searched with the same terms and read by the same rules, and the result is added as a dated amendment.

**Window per unit:** the Pillar 3 reports from the quarter of the unit's first mention in a call up to 2024-Q4 (T16 from 2023-Q3; T25, T27, T32, T33 from 2023-Q4; T68 only 2024-Q4).

## Text and search

- Reconstruction with the phase 3b code for the positioned layout, with the hyphen repair of 2026-09-23 (a line-end hyphen is kept when the hyphenated word occurs elsewhere in the same report). Pages are split into sentences as in phase 3c; table blocks longer than 500 characters are shown as a window of 300 characters around the hit.
- **Search terms:** the round-1 terms of the six units in `notebooks/roman/data/phase3d/search_terms.csv`, unchanged, no new terms; the file's round-1 hash is checked against the phase 3d log before searching. Hit definition as in phase 3d: a sentence with a phrase (group 2) or a figure (group 3); metric keywords (group 1) only rank the hits.

## Reading and classification

Classes as in phase 3d: **A** the same figure for the same commitment in a forward-looking sentence; **B** the same commitment forward-looking, without or with another figure; **C** neither among the hits. Reported actual values (current NCL RWA, current going-concern requirements or ratios, issued AT1 amounts, TLAC balances) are never A or B, even when they are the same metric. For A and B the table gives a verbatim quote, file and page, checked against the page text by the script. The Pillar 3 classes are reported next to the phase 3d classes; they do not overwrite them.

## Check files for Roman

`notebooks/roman/data/phase3f/check_units.json` (only the five available files) and `check_units_2024q2.json` (only `UBS_2024-Q2_pillar3.htm`, for all six units), in the known format `{"T16": {"files": [...], "terms": [["term", "keyword nearby or null"], ...]}}`. The terms are the phase 3d round-1 terms: each phrase (group 2) alone, and each figure (group 3) with the unit's first phrase as the keyword nearby. The group 1 keywords are regular expressions and are not included. Both files are written before any search of this phase.

## Outputs

`analysis/phase3f_pillar3.py` (reconstruction, search, check files) and `analysis/phase3f_read.py` (reading result, quote check); outputs in `notebooks/roman/data/phase3f/`; notebook `03f_pillar3.ipynb`. `FINDINGS.md` is not changed in this phase.

## Tests (pytest)

Added: the check files list only existing Pillar 3 files within each unit's window (and only the 2024-Q2 file in the second file); every quote is found on its page; the round-1 terms are unchanged. The existing hash tests of phases 3b and 3d are narrowed to the files they logged, because new report files in the folder are expected.

## Amendment 2026-09-24 (implementation, before reading)

Instead of narrowing the phase 3b and 3d hash tests, `phase3b_reports.py` now lists only the report files of phase 3b (`report_files()`, all `*.htm` except `*pillar3*`), so a rerun of phase 3b would not take the Pillar 3 reports for quarterly reports, and the existing tests stay unchanged. Result of the reading: all six units are C in the five available Pillar 3 reports; two borderline sentences (2023-Q4 report, pages 7 and 70) are quoted in `pillar3_read.csv`.

## Amendment 2026-09-24: Roman's check

Roman checked all six units in the five available Pillar 3 reports with `check_units.json` and his own search script. He filtered the output on forward-looking words (expect, plan to, we plan, aim, target, by the end of, intend, will be, ambition) and read all remaining passages; a counterpart phrased without these words would not have reached his reading. Output in `notebooks/roman/data/phase3f/roman_check/` (`check_hits_3f.txt`, unfiltered, and `check_hits_3f_forward.txt`, filtered). Result: all six units C confirmed. The Basel III estimate of USD 25bn (of which 10bn in NCL, 2023-Q4) and the "low single-digit percentage increases" (2024-Q4) concern T17, not the six units; the Group-RWA sentence (2023-Q4, p. 7) is the same borderline case as T27 in phase 3d; the sentence on exiting NCL exposures (2023-Q4, p. 70) concerns securitizations only; the USD 1.6bn of AT1 issued in the second half of 2024 is an actual value. Entered in `pillar3_read.csv`, column `checked_by_roman`.

## Amendment 2026-09-24 (after the results): consistency rule, T27 from C to B

Roman set a consistency rule after reviewing the borderline cases of phases 3d and 3g and applied it to all phases: if a report speaks in forward-looking form about the same reduction, also with another scope or without a figure, the unit is B. **T27** therefore becomes B in the Pillar 3 reports, with the sentence on p. 7 of the 2023-Q4 Pillar 3 report ("The core business-led reductions in RWA, coupled with the run-down of positions in Non-core and Legacy during 2024 and 2025, are expected to more than offset the effects of revised Basel III standards"), the same sentence that makes T27 B in phase 3d. `pillar3_read.csv` gets the columns `quote_pillar3` and `quote_location` for B quotes; the sentence on p. 70 stays a borderline case for T25. The other five units are unchanged: T16, T25, T32, T33, T68 are C in the five available Pillar 3 reports.

## Amendment 2026-09-24 (after the results): T16 and T25 from C to B

Roman's decision: the consistency rule applies fully to the Pillar 3 reports. **T16** becomes B with the sentence on p. 7 of the 2023-Q4 Pillar 3 report (the NCL run-down in 2024 and 2025, the same sentence as for T27), and **T25** becomes B with the sentence on p. 70 of the same report ("We plan to exit the exposures in Non-core and Legacy in near-to-mid term", securitization exposures of NCL); both without a figure. The sentence on p. 70 is therefore no longer a borderline case. Result in the five available Pillar 3 reports: T16, T25 and T27 B (mentioned without a figure), T32, T33 and T68 C; none of the six figures appears.

## Amendment 2026-09-26: the Pillar 3 report as of 30 June 2024

Roman added `UBS_2024-Q2_pillar3.htm` (filed 23 August 2024). It was searched with the units and terms of `check_units_2024q2.json` (T16, T25, T27, T32, T33; phase 3d round-1 terms, hash checked; T68 starts in 2024-Q4), the same reconstruction and hit definition, and read with the consistency rule; script `analysis/pillar3_2024q2.py`, output in `notebooks/roman/data/phase3f/pillar3_2024q2/`. Result: all five units are C in this report; none of the figures appears and there is no forward-looking sentence on the same reduction (the only forward-looking RWA sentence is the Basel III estimate of T17). The primary results in `pillar3_read.csv` are not changed; Roman's check with the same check file is pending.

## Amendment 2026-09-26: Roman's independent check was incomplete, recheck

The first version of Roman's `check_terms.py` showed at most 12 hits per term and file, searched the hidden Inline XBRL header and matched short acronyms tolerantly. The Pillar 3 reports have no Inline XBRL header, but the display limit affected all six units: in the check of the five Pillar 3 reports 866 of 1,194 genuine hits were not shown (T16 16, T25 4, T27 274, T32 155, T33 297, T68 120), and in the check of the 2024-Q2 report 210 of 284 (T25 7, T27 81, T32 36, T33 86). The largest gaps are broad phrases ("risk-weighted assets", "additional tier 1", "going concern capital"); the tolerant acronym matching added 7 false hits among those shown ("AT1" 6, "TLAC" 1). Since Roman filtered only the displayed output on forward-looking words, hits beyond the limit did not reach his reading. Audit: `analysis/check_display_audit.py`, `notebooks/roman/data/phase3h/display_audit.csv`. Recheck with the phase 3h version of the tool (`notebooks/roman/data/phase3h/roman_check/`) and CHECK_MAX_HITS set, using the existing `check_units.json` and `check_units_2024q2.json`. The primary values (`pillar3_read.csv`) are unchanged.

## Amendment 2026-09-26: recheck completed

Roman repeated the check of the six units in the five Pillar 3 reports, and of five units in the 2024-Q2 report, with the phase 3h version of `check_terms.py` and all hits shown, filtered the output on forward-looking words, had the hits pre-sorted by machine and read the borderline cases himself (raw output with hashes in `notebooks/roman/data/phase3h/roman_check/recheck_2026-09-26/`). Result: no figure of the six units appears in any Pillar 3 report. The only forward-looking sentences without a figure are the NCL sentences in the 2023-Q4 report (p. 7, run-down in 2024 and 2025; p. 70, exit from the NCL securitization exposures) and in the 2024-Q4 report (p. 69, "in Non-core and Legacy, where we continue to exit our remaining exposures"). The 2024-Q4 sentence was a hit for T25 and T27 in `hits.csv` but was not recorded in `pillar3_read.csv`; each 2023-Q4 sentence is recorded for one unit only (p. 7 for T16 and T27, p. 70 for T25). The classes (T16, T25, T27 B; T32, T33, T68 C; all C in the 2024-Q2 report) are unchanged. `checked_by_roman` is completed in `pillar3_read.csv` and `pillar3_2024q2/read.csv`; the primary values are unchanged.
