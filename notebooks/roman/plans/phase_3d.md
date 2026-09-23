# Phase 3d: counterparts in the reports, by targeted search and reading

Written 2026-09-23, before any search of this phase. Descriptive and exploratory: no test, nothing enters the register, no p-values and no intervals. Release `data/results/2026-09-23/` (frozen), reports in `notebooks/roman/data/reports/` (read only). Phase 3d replaces the automatic classification of phase 3c, whose pre-specified rules did not measure the question (see the status note in `plans/phase_3c.md`).

## Question

For each commitment made in the calls, does the bank's written record (window W1) contain the same figure, the same metric without or with another figure, or nothing? The answer is given by targeted search and reading, one commitment at a time.

## Units (fixed now)

- **Threads of phase 3**, each represented by its first mention (the earliest candidate of the thread, with its call and quarter): 69 threads, UBS 48 (36 targets, 7 guidance, 5 other) and JPMorgan 21 (15 guidance, 1 target and 2 other from the earnings calls; 1 target and 2 other from the event call).
- **Event-call additions.** The event call of 1 May 2023 contains five management statements with a quantity and a forward-looking word; three are already phase 3 candidates (stmt_id 767, 774, 850). The other two are added as units because they fail only the horizon rule of phase 3: the one-time gain of about 2.6 billion (766) and more than 500 million of incremental net income per year (771). Where an addition restates the same commitment as an existing thread (771 and 850 both concern the 500 million), the two are read as one unit and the merge is noted in the table.

## Window (fixed now)

W1 as defined in phase 3c: the quarterly report of the same bank and quarter as the first mention, all earlier reports of the same bank, and for UBS the annual report (Form 20-F) of the same fiscal year. For the event call: the JPMorgan supplements of 2023-Q1 and 2023-Q2. Report text as reconstructed in phase 3b; sentences split as in phase 3c, so decimals stay intact. Table blocks longer than 500 characters are not treated as sentences: a hit inside a table block is shown as a window of 300 characters around the hit.

## Search (fixed per unit before looking at the reports)

For every unit, a set of search terms is written into `notebooks/roman/data/phase3d/search_terms.csv` from the call sentence alone, before any search in the reports is run; the file's hash is recorded in `run_log.json` at the start of the search. Each set contains:

1. the keywords of the unit's phase 3 metric group;
2. two to four phrases from the call sentence that name the commitment (for example `gross cost sav`, `exit rate`, `integration-related expenses`, `costs to achieve`, `AT1`, `Card net charge-off rate`);
3. the figure in the formats in which reports write it: with and without currency (`USD`, `$`), abbreviated and written out (`13bn`, `13 billion`), with and without one decimal (`13.0bn`), percentages with and without a space (`14%`, `14 %`), and basis points (`30 basis points`, `30bps`).

If a unit yields no hit at all, one further round of terms may be added after reading the call context (for example a synonym used by the bank elsewhere); every added term is appended to the file with a `round = 2` flag, never replacing the first round.

## Reading and classification

All hits of a unit are read in their context. Classes as defined in phase 3c:

- **A, same figure:** a report sentence states the same figure for the same metric in a forward-looking context (a target, expectation, plan or guidance, not a reported actual value), allowing for rounding in the sense of the call figure's precision (call `13 billion` against report `USD 13bn` or `USD 13.0bn`; call `around 14%` against `around 14%`).
- **B, same metric, no or another figure:** a report sentence is forward-looking about the same metric but gives no figure or a different one (for example quarterly integration expenses without the expected total).
- **C, no counterpart:** no such sentence among the hits of all search terms.

A same number for a different metric (the 13 billion savings target against 13 billion of integration costs) is never A. For A and B the table carries a verbatim quote, file and page; the script checks every quote against the reconstructed page text, as in phase 3b, and refuses to write the table if a quote is not found. For C the table carries the complete list of search terms used, both rounds.

## Is it a genuine commitment? (fixed now)

Before classifying, each unit's first mention is judged against the phase 3 labelling guide (`commitments_guide.md`): a genuine commitment or guidance is management's own quantified forward-looking statement about its own metric with a point or period in the future. Units are marked `not_genuine` with a one-line reason if the first mention is, for example, a reported actual value, a figure attributed to others (consensus, forward curves), a conditional or illustrative number, a statement whose quantity and horizon belong to different things, or a sentence filed under the wrong metric so that the thread does not describe one commitment. Units marked `not_genuine` are listed with their reason and excluded from the counts. This judgement overlaps with Roman's labelling of `commitments.csv`; where both exist, disagreements are listed.

## Output

- `notebooks/roman/data/phase3d/counterparts_read.csv`, one row per unit: `unit, bank, type, metric, origin (quarter and call type), stmt_id, call_sentence, genuine (yes/no), reason_not_genuine, class (A/B/C or empty if not genuine), figure_call, figure_report, quote_report, file, page, search_terms, merged_with, comment, checked_by_roman` (the last column empty).
- Counts per bank and type (targets, guidance, other; the event call also as its own row): units, not genuine, and A, B, C among the genuine units. No shares with intervals; shares may be shown next to the counts only where a cell has at least ten genuine units.
- JPMorgan guidance is reported with the note that the Exhibit 99.2 supplements contain no outlook, so the cell reflects the design of the supplement.
- Consistency with phase 3b: the units that correspond to the five hand-read cases are listed with their 3b reading; disagreements are explained.
- Notebook `03d_counterparts_read.ipynb`.

## Limits

The reading is done once, by the analyst who also wrote the search terms; there is no second reader, and `checked_by_roman` is the only check. C means "not found with the listed terms", not "proven absent". W1 includes documents published up to the same day as the call and the annual report of the same fiscal year, which is published after the fourth-quarter call.

## Tests (pytest)

Added to `tests/`: every quote in the output is found verbatim (whitespace normalised) on the stated page; every C row lists at least one search term per group 1 to 3; `search_terms.csv` was not changed after the recorded hash, except for appended `round = 2` rows; report files are unchanged after a run.

## Amendment 2026-09-23 (before any search): second window over all reports, sort order

- **Window ALL.** In addition to W1, every unit is searched in all reports of the same bank up to the end of 2024: all quarterly reports 2023-Q1 to 2024-Q4 and, for UBS, both annual reports (2023 and 2024). Same search terms, same reading rules, same quote check. The table gets its own columns `class_all`, `first_report_all` (the earliest report, by reporting period, that contains an A counterpart, or if there is none a B counterpart), `quote_all`, `file_all`, `page_all`. This separates "the call is earlier than the reports" (C or B in W1, A in ALL in a later report) from "only the call states it" (C or B in both). Counts for ALL are reported as their own table, next to the W1 counts.
- **Sort order.** `counterparts_read.csv` is sorted with all genuine UBS target units of class C in W1 first (for Roman's complete check), then the remaining UBS targets, then UBS guidance and other, then JPMorgan, each block by origin quarter.
