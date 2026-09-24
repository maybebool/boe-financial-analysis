# Findings: earnings calls against reports, UBS and JPMorgan 2023–2024

Status 2026-09-24. Descriptive unless a test is named; sources in brackets.

## 1. Main finding

Of the 31 genuine UBS targets set in the calls after the Credit Suisse acquisition, 16 have the same figure in a forward-looking sentence of a report available at the time of the call, 11 the same commitment without or with another figure, and 4 no counterpart; a standalone savings programme of 1.1bn, announced before the acquisition, is counted separately (`03d_counterparts_read.ipynb`, `data/phase3d/counts.csv`). Six forward-looking capital, funding and run-down figures appear only in the call materials, the transcript and the presentation slides filed alongside, and in no quarterly or annual report (the slides were not checked separately): the Non-core and Legacy (NCL) operational risk RWA of around 14bn, the NCL credit and market risk RWA below 40bn, the AT1 issuance of up to 2bn in 2024 and the HoldCo reduction to around 90bn are in no UBS report up to the end of 2024, and the NCL capital release of over 6bn and the going-concern requirement rising to 16.7% are mentioned in the 2023 annual report without a figure (`data/phase3d/counterparts_read.csv`). Roman checked these six and the pre-acquisition programme in the same-quarter and same-year annual reports; the script searched all reports to the end of 2024, with a broader follow-up search (`plans/phase_3d.md`, `data/phase3d/roman_check/`). For the NCL RWA target, one forward-looking sentence on the NCL run-down (2023-Q4 report, 2023 annual report) concerns Group RWA and is kept as a borderline case (`plans/phase_3d.md`). The expected total of integration-related expenses (around 13bn, raised to around 14bn in 2024-Q4) is stated explicitly only in the calls; the reports give quarterly amounts, next-quarter expectations and, in 2023-Q2, an indirect order of magnitude (`03b_call_vs_report.ipynb`, `data/phase3b/comparison.csv`).

## 2. Pattern

In the three cases where the reports address these topics, they say that something is planned or expected, while the calls say how much: capital "released from the unwinding" of NCL against "over 6 billion", a phase-in of higher requirements from 2025 to 2030 against "around 180 basis points to 16.7%", a revised estimate of integration costs against "around 13 billion" (`03d_counterparts_read.ipynb`, `03b_call_vs_report.ipynb`).

## 3. Side findings

- **Disclosure channel.** All six figures come from the prepared remarks, not the Q&A, as do 29 of the 31 targets; for two targets the figure came in the call about three and five months before it appeared in a report (CET1 around 14 %, tax rate around 40 %; checked by Roman) (`03e_disclosure_channel.ipynb`).
- **Novelty.** UBS novelty fades faster than JPMorgan's, but the result is fragile and reflects format and speaker change rather than content (`02_novelty_drift.ipynb`).
- **Drift.** Call similarity falls over time in wording (TF-IDF) but not in meaning (sentence embeddings) (`02_novelty_drift.ipynb`).
- **First Republic.** JPMorgan's event-call figures for restructuring costs and incremental net income are never restated as numbers, separate disclosure ends after 2024-Q1, and the calls keep the preliminary 2.7bn gain after the supplements revised it to 2.8bn (`03b_call_vs_report.ipynb`).
- **Automation.** Neither pre-specified rules nor a language model without training reliably identify which figures appear only in the calls or where management evades; the deflection detector fails the pre-registered validation gate (precision 0.45 at UBS, 0.59 at JPMorgan), so P1-1 and P1-2 are not interpretable and the labels show no reliable difference between the banks (`01_evasive_answers.ipynb`, `03c_call_figures_in_reports.ipynb`, `plans/phase_1.md`).

## 4. Limits

- Eight earnings calls per bank, so every test rests on very few units (`plans/phase_1.md`, `plans/phase_2.md`).
- The main finding concerns one bank: the JPMorgan supplements (Exhibit 99.2) contain no forward-looking statements and offer no comparable written record (`03b_call_vs_report.ipynb`, `03d_counterparts_read.ipynb`).
- Classifications in phases 3b and 3d were made by one reader; Roman checked the seven UBS targets that were classified without counterpart before his check, in the narrower window of section 1; the other units are unchecked (`data/phase3d/counterparts_read.csv`, column `checked_by_roman`). Class C means not found with the pre-specified search terms listed per unit, not proven absent (`plans/phase_3d.md`).
- On the report side only the quarterly reports, the JPMorgan supplements and the UBS annual reports 2023 and 2024 were searched; the Pillar 3 reports are missing and could weaken the main finding if they state these figures (`plans/phase_3b.md`). The investor presentations belong to the call side, as the transcripts refer to the slides, and were not checked separately.
- Only the deflection sample was labelled; the question topic, novelty and commitment samples will not be labelled, so the topic label, the novelty measure and the commitment extraction are not validated (`plans/phase_1.md`, `plans/phase_2.md`, `plans/phase_3.md`).
- All values rest on the frozen release `data/results/2026-09-23`; the control run of all phases on the final release of the pipeline is still outstanding (`analysis/config.py`, `plans/phase_3.md`).
