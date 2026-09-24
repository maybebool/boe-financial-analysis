# Phase 3e: disclosure channel of the call-only figures

Written 2026-09-24, before any computation of this phase. Descriptive: no test, nothing enters the register, no shares with intervals. Release `data/results/2026-09-23/` (frozen); units, classes and quotes from phase 3d (`notebooks/roman/data/phase3d/counterparts_read.csv`, after Roman's check); report text as reconstructed in phase 3b (original reconstruction, as used in phase 3d).

## Part 1: who brings up the figure

**Question.** When UBS management states a figure that appears in no report, does it do so in the prepared remarks, or in the Q&A, and there because an analyst asked or on its own initiative?

**Units.** The six call-only figures of phase 3d (T16 NCL operational risk RWA ~14bn, T25 NCL capital release >6bn, T27 NCL credit and market risk RWA <40bn, T32 going-concern requirement +~180bp to 16.7%, T33 AT1 issuance up to 2bn in 2024, T68 HoldCo ~90bn) and the expected total of integration-related expenses of case C2 (~13bn from 2023-Q4, raised to ~14bn in 2024-Q4).

**Mentions.** Every management statement in the UBS earnings calls (phase 3 statements, `ex.` joins included) that states the figure of the unit. Candidates are retrieved with these patterns (case-insensitive, decimals and thousands separators allowed, figure and topic word in the same statement), then read; a candidate counts only if the figure refers to the same commitment:

| Unit | Figure pattern | Topic pattern |
|---|---|---|
| T16 | `14 billion`, `14bn` | `operational risk` |
| T25 | `6 billion`, `6bn` | `capital release`, `releas`, `free up`, `freeing` |
| T27 | `40 billion`, `40bn` | `risk-weighted`, `RWA`, `credit and market risk` |
| T32 | `16.7`, `180 basis points`, `180 bps` | `going concern`, `going-concern`, `capital requirement` |
| T33 | `2 billion`, `2bn` | `AT1`, `additional tier 1` |
| T68 | `90 billion`, `90bn` | `HoldCo`, `holding company` |
| C2 | `13 billion`, `14 billion`, `13bn`, `14bn` | `integration-related`, `integration related`, `costs to achieve`, `cost to achieve` |

For C2 the savings target of 13 billion is excluded by reading (it shares the number). Analyst sentences with the figure are listed separately as context and do not count as mentions.

**Classification of each mention.**
- `prepared`: the statement is in the prepared remarks.
- `qa, asked`: the statement is in the Q&A, and the analyst question of its question/answer pair (phase 1 pairing: the analyst turn followed by consecutive management turns) explicitly asks about the topic of the unit (the NCL run-down or its RWA and capital, going-concern or other capital requirements, AT1 or capital-instrument issuance, HoldCo or funding volumes, integration costs or costs to achieve).
- `qa, unprompted`: in the Q&A, but the question is about something else.
- `qa, outside a pair`: in the Q&A section but not part of a question/answer pair.

The judgement between asked and unprompted is made by reading; for every Q&A mention the full analyst turn is given verbatim so that Roman can check it.

**Comparison.** The same classification for the first mention (the phase 3d unit's `stmt_id`) of all 31 genuine UBS targets set after the acquisition, counted separately for W1 classes A, B and C. Only counts are reported.

## Part 2: the call is earlier

**Units.** All genuine UBS units of phase 3d whose class in window ALL is A and whose first report with the A counterpart (`first_report_all`) comes after the quarter of the first mention in the call. The reporting order is 2023-Q1, 2023-Q2, 2023-Q3, 2023-Q4, 2023 annual report, 2024-Q1, 2024-Q2, 2024-Q3, 2024-Q4, 2024 annual report; the gap is the number of steps in this order. An annual report that follows the fourth-quarter call of the same year counts as later, and this is noted.

**Table.** Unit, call quarter, first report, gap, call quote with location (statement and speaker), report quote with file and page (from phase 3d, verified again against the page text).

**Check file for Roman.** `notebooks/roman/data/phase3e/check_units.json`, one entry per unit in the format `{"T17": {"files": [...], "terms": [["term", "keyword nearby or null"], ...]}}`, keyed by the phase 3d unit id. `files` are the report files from the call quarter up to and including the first report quarter, as named in `notebooks/roman/data/reports/`. The terms are taken from the call sentence only: the figure in the spellings reports use (`14%`, `1bn`, `1 billion`) and the words of the commitment, each with an optional keyword that must occur nearby. They are written into the file by the script before any search of this phase is run. Phase 3d had already read these reports, so the terms are not blind to the reports' existence, only to any new search.

**Checklist.** In the terminal: for each unit, the statement that must be found in the later report and what must be absent from the earlier ones.

## Outputs

`analysis/phase3e_channel.py`; outputs in `notebooks/roman/data/phase3e/` (`mentions.csv`, `first_mentions.csv`, `counts.csv`, `call_first.csv`, `check_units.json`); notebook `03e_disclosure_channel.ipynb`. `FINDINGS.md` is not changed in this phase.

## Tests (pytest)

Added to `tests/`: every mention is a management statement of a UBS earnings call; every `qa` mention has an analyst question from the same call; `check_units.json` lists only existing report files, starting with the call quarter and ending with the first report quarter; every report quote in `call_first.csv` is found on its page.

## Amendment 2026-09-24 (after the results): Roman's check of part 2, lead in months

- **Roman's check** with `check_units.json` and his own search script (hits copied to `notebooks/roman/data/phase3e/roman_check/check_hits_3e.txt`): T10 and T36 confirmed. T17, T34 and T55 were not checked and are rated weak: T17 because the 2023-Q4 report already gives the Basel III effect as USD 25bn, an equivalent quantity in another unit; T34 because the first report is the annual report, which follows the fourth-quarter call by construction; T55 because "around 5%" is in the reports from 2023-Q4 and only the wording "below 5%" appears later.
- **Lead in months instead of quarters.** Publication dates are taken from the signature date of each filing ("Date: Month D, YYYY" in the file). For all eight UBS quarterly reports this date equals the call date of the same quarter, which the script checks; the annual reports are signed on 28 March 2024 and 17 March 2025. The lead is the number of days between the call and the report's signature date, divided by 30.44. This corrects the statement in phase 3b that the filing dates are not in the files.
