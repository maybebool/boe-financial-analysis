# Findings: earnings calls against reports, UBS and JPMorgan 2023–2024

Status 2026-09-23. Descriptive unless a test is named; sources in brackets.

## 1. Main finding

Of the 31 genuine UBS targets set in the calls after the Credit Suisse acquisition, 16 have the same figure in a forward-looking sentence of a report available at the time of the call, 11 the same commitment without or with another figure, and 4 no counterpart; a standalone savings programme of 1.1bn, announced before the acquisition, is counted separately (`03d_counterparts_read.ipynb`, `data/phase3d/counts.csv`). Six forward-looking capital, funding and run-down figures appear only in the calls: the Non-core and Legacy (NCL) operational risk RWA of around 14bn, the NCL credit and market risk RWA below 40bn, the AT1 issuance of up to 2bn in 2024 and the HoldCo reduction to around 90bn are in no UBS report up to the end of 2024, and the NCL capital release of over 6bn and the going-concern requirement rising to 16.7% are mentioned in the 2023 annual report without a figure (`data/phase3d/counterparts_read.csv`). Roman checked these units and the pre-acquisition programme in the same-quarter report and the annual report of the same year; the search across all reports up to the end of 2024, including a broader follow-up search, was done by script (`plans/phase_3d.md`, `data/phase3d/roman_check/`). For the NCL RWA target, one forward-looking sentence on the NCL run-down (2023-Q4 report, 2023 annual report) concerns Group RWA and is kept as a borderline case (`plans/phase_3d.md`). The expected total of integration-related expenses (around 13bn, raised to around 14bn in 2024-Q4) is stated explicitly only in the calls; the reports give quarterly amounts, next-quarter expectations and, in 2023-Q2, an indirect order of magnitude (`03b_call_vs_report.ipynb`, `data/phase3b/comparison.csv`).

## 2. Pattern

In the three cases where the reports address these topics, they say that something is planned or expected, while the calls say how much: capital "released from the unwinding" of NCL against "over 6 billion", a phase-in of higher requirements from 2025 to 2030 against "around 180 basis points to 16.7%", a revised estimate of integration costs against "around 13 billion" (`03d_counterparts_read.ipynb`, `03b_call_vs_report.ipynb`).

## 3. Side findings

- **Evasive answers.** UBS deflects in 2.95 of 100 answer sentences against 1.14 at JPMorgan (difference 1.81, range 0.90 to 2.00 over robustness variants, exact p 0.040, Holm-adjusted p 0.080 across three primary tests), so the hypothesis is not supported, nor is a concentration of UBS deflections on capital regulation (Holm p 0.155) (`01_evasive_answers.ipynb`, `plans/test_register.csv`).
- **Novelty.** UBS management novelty fades faster, not slower, than JPMorgan's (Holm p 0.040); the result is fragile and largely disappears when prepared remarks and Q&A are weighted equally, pointing to format and speaker change (`02_novelty_drift.ipynb`).
- **Drift.** The strong TF-IDF decline of call similarity over time is weak and non-significant with sentence embeddings: the drift concerns wording, not meaning (`02_novelty_drift.ipynb`, E5).
- **First Republic.** The event-call figures for restructuring costs (about 2bn post-tax) and incremental net income (more than 500m a year) are not restated as numbers in any later call or supplement; the supplements show First Republic separately only until 2024-Q1 and revise the bargain purchase gain to 2.8bn, while the calls still cite 2.7bn in 2024-Q2 (`03b_call_vs_report.ipynb`, `03d_counterparts_read.ipynb`).
- **Relevance models.** Cross-encoder and embedding relevance do not detect evasion, because deflections repeat the topic of the question (`01_evasive_answers.ipynb`, E2).
- **Automatic matching.** Pre-specified rules matching call figures to report sentences agree with the hand-read cases in three of six and were discarded (`03c_call_figures_in_reports.ipynb`, `plans/phase_3c.md`).

## 4. Limits

- Eight earnings calls per bank, so every test rests on very few units (`plans/phase_1.md`, `plans/phase_2.md`).
- The main finding concerns one bank: the JPMorgan supplements (Exhibit 99.2) contain no forward-looking statements and offer no comparable written record (`03b_call_vs_report.ipynb`, `03d_counterparts_read.ipynb`).
- Classifications in phases 3b and 3d were made by one reader; Roman checked the seven UBS targets that were classified without counterpart before his check, in the narrower window of section 1; the other units are unchecked (`data/phase3d/counterparts_read.csv`, column `checked_by_roman`). Class C means not found with the pre-specified search terms listed per unit, not proven absent (`plans/phase_3d.md`).
- On the report side only the quarterly reports, the JPMorgan supplements and the UBS annual reports 2023 and 2024 were searched; the Pillar 3 reports are missing and could weaken the main finding if they state these figures (`plans/phase_3b.md`). The investor presentations belong to the call side, as the transcripts refer to the slides, and were not checked separately.
- The labelling samples for phases 1 and 2 (deflection, question topic, novelty) and for phase 3 (commitments) are not yet labelled; all detector-based results are provisional (`data/labelling/`).
- All values rest on the frozen release `data/results/2026-09-23`; the control run of all phases on the final release of the pipeline is still outstanding (`analysis/config.py`, `plans/phase_3.md`).
