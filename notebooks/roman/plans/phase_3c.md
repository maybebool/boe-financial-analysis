# Phase 3c: forward-looking figures from the calls and their counterparts in the reports

Written 2026-09-23, before any computation of this phase; revised the same day, still before any computation (forward-looking context required for A, second main table on threads, horizon sensitivity). Descriptive: no primary test, nothing enters the register, no p-values. Release `data/results/2026-09-23/` (frozen), reports in `notebooks/roman/data/reports/` (read only).

## Question

What share of the quantified forward-looking statements that management makes in the calls has a counterpart in the banks' own reports? Where the share is low, the calls carry information that the reports do not; where it is high, the calls mostly repeat the reports.

## Unit

All 136 commitment candidates of phase 3 (`notebooks/roman/data/phase3/candidates.csv`), extracted with the phase 3 rules including the amendment of 2026-09-23: UBS 106 (earnings calls), JPMorgan 27 (earnings calls) and 3 (event call of 1 May 2023, included as a source). No candidate is added or removed in this phase. Each candidate keeps its phase 3 metric group, type (target, guidance, other), parsed value and unit.

## Which reports count as a counterpart (fixed now)

- **Primary window W0:** the quarterly report of the same bank and the same reporting quarter as the call (UBS quarterly report, JPMorgan Exhibit 99.2 supplement), published on the same day as the call as a rule. For the JPMorgan event call: the 2023-Q2 supplement, the first report after the event.
- **Wider window W1 (sensitivity):** W0 plus all earlier reports of the same bank, plus, for UBS, the annual report (Form 20-F) of the same fiscal year as the reporting quarter. W1 answers whether the figure is in the bank's written record at or before the time of the call or in the annual report that covers that year.
- **Later window W2 (sensitivity):** W1 plus the quarterly report of the following quarter, to see whether figures appear in writing only afterwards.

Reports of the other bank never count. Candidates from the last call of the window (2024-Q4) have no W2 extension and are marked as such.

## Report text

Report pages as reconstructed in phase 3b (`notebooks/roman/data/phase3b/report_pages.csv`, same code). Pages are split into sentences at a full stop, question mark or exclamation mark that is followed by whitespace and an upper-case letter. A full stop between two digits never ends a sentence, so `3.5`, `91.5` or `14.3%` stay intact. This closes the known gap of phase 3b, where search windows of the form `[^.]` stopped at decimal points. Table rows are split in the same way. Numbers in tables that have no unit or currency next to them (for example JPMorgan tables "in millions") are not parsed, so table-only figures cannot match; this is a known limitation and biases class A downwards for figures that appear only in tables.

## Quantities and tolerance (fixed now)

- **Parser:** the phase 3 quantity parser (`phase3_extract.quantities`), which handles decimals, thousands separators, currency prefixes (`$`, `USD`, `CHF`, `EUR`) and the units `%`, `bps`, `million`, `billion`, `trillion` and their abbreviations, and converts amounts to billions. It is applied to report sentences as well as to calls. Unit classes must be equal (percentage with percentage, basis points with basis points, amounts with amounts); no conversion between percentage and basis points. Currency is not compared, because UBS calls usually omit it.
- **Tolerance (primary):** two figures match if their difference is at most half a unit of the last displayed digit of the less precise figure. Examples: call `13 billion` matches report `USD 13.4bn` (tolerance 0.5) but not `USD 13.6bn`; call `1.5 billion` matches `USD 1.46bn` (tolerance 0.05); call `14%` matches `14.3%`; call `500 million` matches `USD 0.5bn`.
- **Tolerance (sensitivity):** exact equality at the displayed precision of both figures.
- **Candidate value (primary):** the phase 3 parsed value (first quantity of the candidate sentence). **Sensitivity:** any quantity in the candidate sentence.

## Classes per candidate (fixed now)

For each candidate and window, report sentences of the same bank in the window are examined:

- **A, same figure:** at least one report sentence contains a keyword of the candidate's metric group, a quantity that matches the candidate value within tolerance, and a forward-looking context under the same rules as for B (a forward-looking word or a future horizon). A reported actual value that happens to equal the target figure is not a counterpart.
- **B, same metric, no or another figure:** not A, and at least one report sentence contains a keyword of the candidate's metric group together with a forward-looking word or a future horizon (the phase 3 rules (b) and (c), resolved against the report's quarter end). Requiring the forward-looking context keeps generic mentions of the metric (for example every sentence containing "expense") out of B.
- **C, no counterpart:** neither A nor B.

Candidates of the metric group **other** have no keywords; for them the keyword condition is replaced by a cosine similarity of at least 0.6 between the candidate and the report sentence (masked text, `sentence-transformers/all-mpnet-base-v2`, revision as in phase 2). As a sensitivity for all candidates, the keyword condition is replaced by this similarity condition.

For every candidate the best report sentence is stored (for A the matching sentence, for B the forward-looking sentence with the highest similarity, for C the three most similar sentences in the window), with file and page.

## Reporting (fixed now)

- Shares of A, B and C per bank and type, always separately, in two main tables of equal rank:
  - **Candidate table:** every candidate counts once.
  - **Thread table:** only the first mention of each phase 3 thread counts (the earliest candidate of the thread, with its own call and window), with the same classes, windows and bootstrap. UBS repeats the same targets in many calls, so the candidate table weights recurring targets by their number of repetitions, while the thread table counts each commitment once.

  Cells: UBS targets, UBS guidance, UBS other, JPMorgan targets, JPMorgan guidance, JPMorgan other, with the event-call candidates shown as their own row as well as within JPMorgan. No pooled share across banks or types.
- **JPMorgan guidance:** the Exhibit 99.2 supplements contain no outlook at all (phase 3b: every hit for "guidance" refers to accounting guidance). JPMorgan guidance can therefore reach A or B only through incidental wording (for example a reported figure next to a word such as "expect" in a footnote); the cell measures the design of the supplement, not disclosure behaviour, and is reported with this note and not interpreted.
- **Uncertainty:** 95 % percentile intervals from a cluster bootstrap over calls, for both main tables: within each bank and type cell, calls are drawn with replacement (the event call is its own cluster), all candidates of a drawn call are kept, 2,000 resamples with `numpy.random.default_rng(0)`. Cells with fewer than three contributing calls get no interval, only counts. With at most nine calls per bank the intervals will be wide; they are reported next to the counts, never instead of them.
- Primary window W0 and primary tolerance in the main tables; as sensitivity tables with the same cells, for both main tables: W1, W2, exact tolerance, any quantity of the candidate, similarity instead of keyword, **A without forward-looking context** (the rule of the first draft: keyword and matching quantity suffice), and **horizon check** (if both the candidate and the report sentence state a time horizon and the two differ in calendar year, the pair does not count as A; horizons resolved with the phase 3 parser, the report sentence against its report's period end). A share that moves by more than 20 percentage points between the primary and a sensitivity setting is flagged as fragile.
- Case check: the five phase 3b cases must come out consistent with the hand-read table of phase 3b (for example the expected total of integration-related expenses in C for UBS in W0 and W1). Disagreements are listed and explained, not tuned away.

## Validation

- `notebooks/roman/data/labelling/counterparts.csv`: about 60 candidate and report-sentence pairs, blind and in random order, about 20 per class, stratified by bank as far as the cells allow. Each item shows the candidate sentence with its context and, for A and B, the best report sentence; for C the three most similar report sentences of the window. Label: `A` (the report states the same figure for the same metric), `B` (same metric, no or another figure) or `C` (none of the shown sentences is a counterpart). Guide in `counterparts_guide.md`, key with class, window, file and page in `counterparts_key.csv`.
- Reported once labelled: precision per class, confusion table, Cohen's kappa. For class C the check can only confirm that the shown sentences are not counterparts; it cannot prove that the whole report has none, so recall of A and B remains an upper bound.
- **Gate:** the shares are only treated as reliable once the extraction precision from `commitments.csv` (phase 3) is labelled as well, because a candidate that is not a real commitment has no reason to appear in a report. Until both labellings are back, all shares are provisional. If the precision of class A in `counterparts.csv` is below 0.7, the A shares are reported as not interpretable.

## Tests (pytest)

Added to `tests/`: the sentence splitter keeps `3.5`, `91.5` and `14.3%` intact and splits at `. The`; the tolerance function on the examples above; windows contain only reports of the same bank, W0 only the same quarter, W1 no later report; the event-call candidates are matched against the JPMorgan 2023-Q2 supplement in W0; the report files are unchanged after a run (hashes).

## Outputs

Computation in `analysis/phase3c_counterparts.py`, outputs in `notebooks/roman/data/phase3c/` (`matches.csv` with class, window and best sentences per candidate, `shares.csv` with counts, shares and bootstrap intervals per cell, sensitivity tables), notebook `03c_call_figures_in_reports.ipynb`.

## Status 2026-09-23 (after the results): the pre-specified rules do not measure the question

Recorded after the run, on Roman's decision; the rules are not repaired and the results stand as computed.

- **Result.** Under the rules of this plan the shares of A, B and C do not measure whether call figures have a counterpart in the reports. Three reasons: (1) many report "sentences" are whole table blocks (20 % of JPMorgan and 10 % of UBS report sentences exceed 500 characters) that contain a metric word, a forward-looking word and many numbers at once, so that all JPMorgan A matches read are artefacts; (2) the tolerance of half a unit of the less precise figure lets an integer report figure such as USD 1bn match anything from 0.5 to 1.5 billion; (3) class B needs only a metric word and a forward-looking word anywhere in the report, which almost every report satisfies, so that C stays empty in every keyword-based cell.
- **Case check against phase 3b.** Three of six cases agree (savings target in A, First Republic restructuring costs in C, integration total of 2023-Q4 in B). Three disagree: the 13 billion integration-cost statement of 2024-Q1 is classified A because the savings target is also 13 billion, the AT1 plan is classified A through a CET1 sentence with a matching amount, and the Basel III statement of 2023-Q3 is classified B through a generic note.
- **No repairs.** None of the possible repairs (splitting table blocks, tolerance by the call figure only, a similarity condition for A, a similarity condition for B) is applied.
- **Labelling sample discarded.** `counterparts.csv` is not labelled. It is moved with its key and guide to `notebooks/roman/data/labelling/discarded_phase3c/`, and the script writes any future sample there.
