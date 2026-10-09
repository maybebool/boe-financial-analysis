# Findings: earnings calls against reports, UBS and JPMorgan 2023 to 2024

Status 2026-10-09. Descriptive; sources in brackets.

## 1. Main finding

Of the 39 genuine UBS targets set in the calls after the Credit Suisse acquisition, 8 have a figure that no UBS quarterly, annual or Pillar 3 report up to the end of 2024 states as a target (`03g_fls_models.ipynb`, `03f_pillar3.ipynb`, `data/phase3h/corrections_v2.csv`). Four are not mentioned at all: AT1 issuance of up to 2bn in 2024 (T33), HoldCo at around 90bn (T68), a going concern capital ratio of around 18% (F11) and an LCR below 188% (F22). Four are mentioned without a figure: Non-core and Legacy (NCL) operational risk RWA of around 14bn (T16), an NCL capital release of over 6bn (T25), NCL credit and market risk RWA below 40bn (T27) and a Group LRD reduction of over 100bn (F12). For T25 and F12 the 2024 annual report states a result of the size of the call figure after the fact, without naming it as a target. Of the other 31 targets, 23 have the same figure in a report and 7 another figure. One of these is the higher going concern requirement (T32): around 180 basis points in the call, around USD 10bn of tier 1 capital in the reports from 2024-Q1, the same increase in another unit. The total of integration-related expenses (T30, around 13bn, later 14bn) is counted separately: the reports give quarterly amounts and, before the call figure, an indirect order of magnitude of approximately USD 12bn in the 2023-Q2 report (`03b_call_vs_report.ipynb`, `03j_equivalent_forms.ipynb`).

## 2. Method

The targets come from a rule-based extraction (31) and from sentences that FinBERT-FLS found and the rules missed (8). Search terms were fixed before each search, and every quote is verified against the report page (`plans/phase_3d.md`, `plans/phase_3g.md`). A commit made before the computation documents this only for phases 3i and 3j; the plans of phases 3d to 3h were committed together with their results. The rule that a forward-looking report sentence without a figure counts as a mention was fixed after the results were known. An independent manual check of the call-only units, repeated in full with a corrected check tool, changed no classification (`plans/phase_3f.md`). The reclassification of T32 came later, from re-reading the reports in phase 3h (`data/phase3h/corrections_v2.csv`). A further search covered the equivalent forms of the call figures in two passes, by figure and by keyword. All 768 distinct passages were read in full; no further target appears in another unit (`plans/phase_3j.md`). The finding is confirmed on the export of 2026-09-30: the seven UBS calls are identical in text and the search yields no new candidate (`03i_export_check.ipynb`).

## 3. Pattern and outcome

Where the reports address these topics, they say that something is planned, while the calls say how much. The reports set targets of their own instead of taking up the call figures: NCL RWA of around USD 29bn by the end of 2025 and around USD 22bn by the end of 2026 (2024-Q4 report). None of the call figures appears as a target in the 13 reports of 2025 and 2026 (`03h_reports_2025_2026.ipynb`, `data/phase3h/units_3h_v2.csv`). Their outcomes:

- **Achieved:** T25 (USD 8bn by the end of 2025), T27 (USD 14.3bn at the end of 2024, calculated) and F22 (LCR between 177% and 183%).
- **Revised:** T32 (about 108 basis points, calculated) and T30 (USD 14.2bn spent by mid-2026).
- **Missed:** T33 (USD 3.5bn of AT1 issued in 2024).
- **Open:** T16 (USD 24.0bn at mid-2026) and F12. The F12 reduction reached USD 102.3bn at the end of 2024 and USD 138.4bn at the end of 2025 and stood at USD 92.2bn at mid-2026, excluding currency effects and the separately reported Basel III change.
- **No longer mentioned:** T68 and F11.

## 4. Side findings

- **Channel.** All eight figures come from the prepared remarks, not the Q&A (`03e_disclosure_channel.ipynb`).
- **Novelty.** UBS novelty fades faster than JPMorgan's, but the result is fragile (`02_novelty_drift.ipynb`).
- **Automation.** The deflection detector fails the pre-registered validation gate (precision 0.45 at UBS, 0.59 at JPMorgan), so P1-1 and P1-2 are not interpretable (`01_evasive_answers.ipynb`).

## 5. Limits

- The main finding concerns one bank: the JPMorgan supplements contain no forward-looking statements.
- One reader; only the call-only units were checked independently. "Not mentioned" means not found with the listed terms.
- T32 was missed at first because the terms followed the unit of the call; the later search depends on the forms and keywords of its plan.
- The search for equivalent forms (phase 3j) covers the reports up to the end of 2024. For the reports of 2025 and 2026, the statement that no call figure appears as a target rests on the search in the units of the call (phase 3h).
- Topic labels, the novelty measure and the commitment extraction are not validated.
- In the export of 2026-09-30 the JPMorgan earnings calls have 3 to 8 sentences fewer each; this affects only phases 1 and 2, which rest on the release of 2026-09-23 and were not rerun.
- The investor presentations were not searched.
