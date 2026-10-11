# Findings: earnings calls against reports, UBS and JPMorgan 2023 to 2024

Status 2026-10-09. Descriptive; sources in brackets.

## 1. Main finding

Of the 39 genuine UBS targets set in the calls after the Credit Suisse acquisition, 8 have a figure that no UBS quarterly, annual or Pillar 3 report up to the end of 2024 states as a target (`01_call_targets.ipynb`, `02_reports_to_2024.ipynb`, `exports/call_only_8.csv`). Four are not mentioned at all: AT1 issuance of up to 2bn in 2024 (T33), HoldCo at around 90bn (T68), a going concern capital ratio of around 18% (F11) and an LCR below 188% (F22). Four are mentioned without a figure: Non-core and Legacy (NCL) operational risk RWA of around 14bn (T16), an NCL capital release of over 6bn (T25), NCL credit and market risk RWA below 40bn (T27) and a Group LRD reduction of over 100bn (F12). For T25 and F12 the 2024 annual report states a result of the size of the call figure after the fact, without naming it as a target. Of the other 31 targets, 23 have the same figure in a report and 7 another figure. One of these is the higher going concern requirement (T32): around 180 basis points in the call, around USD 10bn of tier 1 capital in the reports from 2024-Q1, the same increase in another unit. The total of integration-related expenses (T30, around 13bn, later 14bn) is counted separately: the reports give quarterly amounts and, before the call figure, an indirect order of magnitude of approximately USD 12bn in the 2023-Q2 report (`02_reports_to_2024.ipynb`).

## 2. Method

The targets come from a rule-based extraction (31) and from sentences that FinBERT-FLS found and the rules missed (8). Search terms were fixed before each search, and every quote is verified against the report page (`report_checks.py`, `exports/quote_check_to_2024.csv`, `exports/quote_check_2025_2026.csv`). The rule that a forward-looking report sentence without a figure counts as a mention was fixed after the results were known. An independent manual check of the call-only units, repeated in full with a corrected check tool, changed no classification (column `checked_manually` in `data/call_only_targets/`). The reclassification of T32 came later, from re-reading the reports for the outcome (`data/call_only_targets/outcome_corrections.csv`). A further search covered the equivalent forms of the call figures in two passes, by figure and by keyword. All 768 distinct passages were read in full; no further target appears in another unit (`data/call_only_targets/equivalent_forms_judgments.csv`). The finding is confirmed on the export of 2026-09-30: the seven UBS calls are identical in text and the search yields no new candidate (`01_call_targets.ipynb`).

## 3. Pattern and outcome

Where the reports address these topics, they say that something is planned, while the calls say how much. The reports set targets of their own instead of taking up the call figures: NCL RWA of around USD 29bn by the end of 2025 and around USD 22bn by the end of 2026 (2024-Q4 report). None of the call figures appears as a target in the 13 reports of 2025 and 2026 (`04_reports_2025_2026.ipynb`, `exports/outcomes_2025_2026.csv`). Their outcomes:

- **Achieved:** T25 (USD 8bn by the end of 2025), T27 (USD 14.3bn at the end of 2024, calculated) and F22 (LCR between 177% and 183%).
- **Revised:** T32 (about 108 basis points, calculated) and T30 (USD 14.2bn spent by mid-2026).
- **Missed:** T33 (USD 3.5bn of AT1 issued in 2024).
- **Open:** T16 (USD 24.0bn at mid-2026) and F12. The F12 reduction reached USD 102.3bn at the end of 2024 and USD 138.4bn at the end of 2025 and stood at USD 92.2bn at mid-2026, excluding currency effects and the separately reported Basel III change.
- **No longer mentioned:** T68 and F11.

## 4. Side findings

- **Channel.** All eight figures come from the prepared remarks, not the Q&A (`03_channel_and_timing.ipynb`).
- **Novelty.** UBS novelty fades faster than JPMorgan's, but the result is fragile (`02_novelty_drift.ipynb` in the analysis folder of the project repository).
- **Automation.** The deflection detector fails the pre-registered validation gate (precision 0.45 at UBS, 0.59 at JPMorgan), so the two tests on deflection are not interpretable (`01_evasive_answers.ipynb` in the analysis folder of the project repository).

## 5. Limits

- The main finding concerns one bank: the JPMorgan supplements contain no forward-looking statements.
- One reader; only the call-only units were checked independently. "Not mentioned" means not found with the listed terms.
- T32 was missed at first because the terms followed the unit of the call; the later search depends on the forms and keywords fixed for it.
- The search for equivalent forms covers the reports up to the end of 2024. For the reports of 2025 and 2026, the statement that no call figure appears as a target rests on the search in the units of the call.
- Topic labels, the novelty measure and the commitment extraction are not validated.
- In the export of 2026-09-30 the JPMorgan earnings calls have 3 to 8 sentences fewer each than in the earlier export; this affects only the analyses of deflection and novelty, which were not rerun.
- The investor presentations were not searched.

## 6. Pre-specified rules

The rules below were written down before the corresponding search or computation. For the last two steps the plan was committed to the project repository before any computation; the commit is given. The plans of the earlier steps were written before the search but committed together with the results, so their commits give only an upper bound for the date.

- **Classes (commits c213189, a9eefa0).** A report sentence counts only when it states the quantity as a target, plan, expectation or guidance, not as a reported value. Class A: the same figure, allowing for rounding at the precision of the call figure. Class B: forward-looking on the same metric with another or no figure. Class C: not found with the terms fixed from the call sentence.
- **Search terms.** For each unit the terms were fixed from the call sentence before the search: the metric, two to four naming phrases and the figure in its spellings. Every counterpart quote is verified verbatim against its page.
- **Reports of 2025 and 2026 (commit ec6f1e3).** Terms unchanged from the earlier search; outcome per unit as achieved, missed, revised, open or no longer mentioned, with the actual value where one is reported.
- **Control run on the export of 2026-09-30 (commit b1686e7).** The finding holds if all source sentences of the 39 targets are present with the same call, speaker, figure and wording, and the candidate search in the window yields no new quantified target.
- **Equivalent forms (commit ce2fa50).** Every form of a call figure in another unit is listed with its calculation and conversion base. A converted report figure counts as the same when it lies within 10% of the call figure; a hit counts only in a forward-looking context. Two passes: figure forms near a keyword, and keywords alone with a forward-looking word and a quantity in the context.

## 7. Files

| File | Content |
|---|---|
| `00_get_reports.ipynb` | fetches the report files with a recorded source from EDGAR and compares their hashes; optional |
| `01_call_targets.ipynb` | the 39 targets and their source sentences in the export of 2026-09-30 |
| `02_reports_to_2024.ipynb` | classes, the eight call-only figures, T30, T32, Pillar 3, equivalent forms |
| `03_channel_and_timing.ipynb` | section of the call and lead of the call over the reports |
| `04_reports_2025_2026.ipynb` | outcome of the commitments, with the recalculated key values |
| `report_checks.py` | page text of the reports, verification of quotes, table values |
| `exports/` | the tables of the notebooks as CSV, with `SHA256SUMS` |

The files under `data/call_only_targets/` were generated from the working files of the analysis by the script `analysis/build_final_inputs.py` in the analysis folder of the project repository (commit 1326a8c). `build_log.csv` in that folder lists every file with its source and target SHA-256 and the changes made.

The notebooks run in the order of their numbers; `03` reads an export written by `01`. Without the report files under `data/reports/` they show the delivered results and skip the verification of quotes; the checks on counts and key values run in both cases.
