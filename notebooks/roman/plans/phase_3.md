# Phase 3: commitment tracking

Written 2026-09-23, before any computation of this phase; revised the same day before the first run (event call decided, sentence joining fixed, implementation details below). Release `data/results/2026-09-23/` (via `RELEASE_DIR`), frozen for all phases. Phase 3 is descriptive: there is no primary test, nothing enters the test register, and no p-values are computed.

## Question

Which quantified forward-looking statements does management make in the calls, and what happens to each of them in later calls: restated, revised up or down, horizon moved, reported as achieved, or never mentioned again? How does that picture differ between UBS and JPMorgan over the window?

## Why this is relevant

A supervisor can check a bank's own targets against later calls without a model of the business. A target that is quietly no longer mentioned, or one whose horizon keeps moving, is a signal that the reported figures alone do not show. The comparison with JPMorgan shows how much of this is ordinary guidance practice.

## Definitions

- **Commitment candidate.** A management statement that contains (a) a quantity (a number with a unit, percentage, basis points, or a currency amount), (b) a time horizon in the future relative to the call date (a year, "end of", "by", "exit rate", "run-rate", "full year", "next year", "medium term", a quarter), and (c) a forward-looking verb or noun (`target`, `aim`, `ambition`, `expect`, `plan`, `commit`, `deliver`, `achieve`, `reach`, `guidance`, `guide`, `intend`, `on track`, `remain`). The exact regular expressions are written into `analysis/phase3_extract.py` before the first run and quoted in the notebook.
- **Type.** Each candidate is tagged as **target** (a goal under management's control: cost saves, headcount, non-core run-down, capital ratio targets, buybacks, integration milestones, return targets) or **guidance** (a forecast of a market-dependent figure: NII, expenses, loan growth, charge-offs). The tag comes from a fixed metric dictionary (below); items that match neither are tagged **other**. Targets and guidance are always reported separately, because JPMorgan gives annual guidance every quarter while UBS set out a multi-year integration plan, and pooled counts would compare different practices.
- **Metric dictionary.** Fixed keyword groups, for example cost saves (`cost save`, `gross cost`, `run-rate saves`), capital (`CET1`, `capital ratio`, `leverage ratio`), non-core (`non-core`, `NCL`, `run-down`, `wind-down`), distributions (`buyback`, `repurchase`, `dividend`), returns (`return on CET1`, `RoCET1`, `RoTCE`, `ROTCE`, `through the cycle`), net new assets (`net new assets`, `net new money`, `NNA`), NII (`net interest income`, `NII`), expenses (`expense`, `adjusted expense`), integration (`integration`, `migration`, `legal entity`, `merger` of entities), headcount (`headcount`, `FTE`, `employees`). The full list is written into the script before the first run.
- **Value and horizon.** Parsed from the candidate text by rules: the numeric value with unit, and the horizon resolved to a calendar date against the call date ("next year" in the 2023-Q4 call held in February 2024 means 2025; "full year" in a January call means the new year). Unparsed values or horizons are left empty, not guessed.

## Data preparation

1. Management sentences of the earnings calls, prepared remarks and Q&A. Square-bracket insertions removed.
2. **Event call.** The JPMorgan event call of 1 May 2023 contains the only merger-specific JPMorgan commitments (for example incremental net income from First Republic, integration costs, a CET1 target). Decided by Roman: the event call is included **as an origin only** and flagged as such in every table; it is never used as a follow-up call.
3. **Split sentences.** The release splits some sentences at the abbreviation `ex.` (37 sentences, mostly JPMorgan "NII ex. Markets" guidance). A sentence ending in `ex.` is joined with the next sentence of the same statement before extraction. Sentences ending in `No.` are not joined, because they are genuine answers such as "Yeah, no.". No other abbreviation is joined. The fix is in the pipeline for the next release, but this analysis stays frozen on `2026-09-23`.
4. **Context window.** Value and horizon may sit in the neighbouring sentence ("We expect 2025 NII ex. Markets to be about 90 billion."). Each candidate is parsed together with the previous and next sentence of the same statement; the candidate sentence itself must still meet (a) to (c).

## Tracking

1. **Threads.** Candidates of the same bank are grouped into threads in chronological order: a candidate joins the earliest existing thread of the same bank and metric group whose first mention has a cosine similarity of at least 0.6 with it (masked texts, `sentence-transformers/all-mpnet-base-v2`, revision as in phase 2); otherwise it opens a new thread. Because masking removes years, guidance for different years would merge: for type **guidance** a candidate joins a thread only if its parsed horizon year equals the thread's (or one of them is unparsed). For type **target** the horizon is not used for grouping, so that a moved horizon shows up as `horizon_moved`.
2. **Follow-ups.** For each thread and each earnings call of the same bank after the call of the first mention, the management sentence of the same metric group most similar to the first mention is taken as the follow-up if its similarity is at least 0.6; otherwise the call has no follow-up. For guidance threads, sentences with a different parsed horizon year are skipped.
3. **Proposed status per follow-up** (rules on the parsed values and horizons): `restated` (same value and horizon), `revised_up` / `revised_down` (value changed; the direction is numeric only, whether it is more or less ambitious is left to Roman), `horizon_moved`, `achieved` (an achievement verb such as "achieved", "reached", "completed", "delivered", "exceeded" together with the target value or more, and no progress wording such as "towards", "on track" or "progress"), `mentioned_no_value` (same metric, no comparable value).
4. **Proposed final status per thread:** the last proposed follow-up status, or `no_follow_up_found` if no later call has a follow-up. `no_follow_up_found` is split into `due_within_window` (horizon on or before the last call of the bank) and `not_due_in_window`. The label "silently dropped" is not assigned by the rules; it is Roman's judgement in the review.
5. **Sensitivity.** Thread counts and final statuses are also reported for similarity thresholds 0.5 and 0.7. Descriptive only.

## Outputs

- `notebooks/roman/data/phase3/candidates.csv`: every candidate with bank, call, speaker, section, text, context, metric group, type, parsed value, unit and horizon.
- `notebooks/roman/data/phase3/threads.csv`: one row per thread with the first mention, the follow-up per later call (text, similarity, proposed status), the proposed final status, and empty columns `status_reviewed` and `notes` for Roman. This table is the main deliverable.
- Summary tables: threads per bank and type; proposed final statuses per bank and type; share of threads with `no_follow_up_found` and `due_within_window`; number of revisions per thread; time from first mention to first revision. Counts are also shown per 1,000 management sentences, and always UBS next to JPMorgan.
- Notebook `03_commitments.ipynb` with the tables, a timeline chart of threads (one row per thread, marks per call coloured by proposed status), and three to five case studies chosen for their supervisory relevance and read in full.

## Validation

- `notebooks/roman/data/labelling/commitments.csv`: about 100 candidates, stratified by bank and type, plus about 50 management sentences per bank that contain a quantity but are not candidates (half of them with a future horizon). Label: `1` if the sentence states a quantified forward-looking commitment or guidance with a horizon, else `0`. Blind, random order, guide in `commitments_guide.md`, strata in `commitments_key.csv`. Reported: precision of the extraction, estimated recall (weighted by strata), Cohen's kappa, per bank.
- `threads.csv` is reviewed by Roman in full. Reported afterwards: agreement between proposed and reviewed final status (Cohen's kappa, confusion table), per bank.
- Optional recall check: if Roman lists the commitments he knows from the banks' own presentations, the share of them found by the extraction is reported.

## Tests (pytest)

Added to `tests/`: candidates come only from management sentences; follow-ups only from later earnings calls of the same bank; the event call is never a follow-up; horizon parsing relative to the call date on fixed examples ("next year" in a February 2024 call gives 2025); value parsing on fixed examples (`13 billion`, `14%`, `$88 billion`, `50 basis points`); sentences ending in `ex.` are joined with the next sentence of the same statement only.

## What would count as a finding

Phase 3 makes no statistical claims. A finding is a pattern that holds up in Roman's review, for example UBS targets whose horizon moved repeatedly, or a group of targets that disappear from the calls, stated as counts next to the JPMorgan counts and illustrated by the case studies.

## Amendment 2026-09-23 (after inspecting the first extraction, before tracking)

Two parsing errors were found by reading a sample of candidates and are corrected; the candidate definition (a) to (c) is unchanged. (1) A year preceded by "from", "since", "starting" or "beginning in" is a starting point, not a horizon, and is ignored when resolving the horizon ("From 2026, our aim is to build to around 200 billion ... by 2028" now resolves to 2028, not 2026). (2) "end of the year" and "end of this year" are added to the expressions that resolve to the end of the call year. Known limitation left as it is: the metric dictionary classifies some cost-reduction targets phrased as "take out ... gross expenses" as expense guidance; Roman's review of `threads.csv` catches these.
