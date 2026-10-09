# Phase 3i: control run of the main finding on the export of 2026-09-30

Written 2026-10-09, before any computation of this phase. Descriptive: no test, nothing enters the register. The phases 3 to 3h, their folders, `notebooks/roman/data/reports/`, `notebooks/roman/data/reports_2025_2026/` and both `roman_check` folders are not changed; `RELEASE_DIR` in `analysis/config.py` stays at `data/results/2026-09-23/`.

## Transparency note

Before this plan was written, the export of 2026-09-30 was handled outside this protocol for the submission package: its files were hashed, its row counts and columns were read (19,092 sentences, 2,570 utterances, 2022-Q1 to 2025-Q4), and it was compared with the structured files derived from it. No text of the export of 2026-09-30 was compared with the export of 2026-09-23, and none of the phase 3 or phase 3g rules or models was run on it.

## Question

Does the main finding, which rests on the export of 2026-09-23, hold on the export of 2026-09-30? The main finding: of the 39 genuine UBS targets set in the calls after the Credit Suisse acquisition, 9 have a figure that appears in no UBS report up to the end of 2024, with the integration-cost total (T30) counted separately (`FINDINGS.md`, `data/phase3g/basis.csv`).

The reports are independent of the export. They are not searched again in this phase unless the decision rule below requires it for a changed or added target.

## Exports

- **Old.** `data/results/2026-09-23/` in the repository root, the basis of all earlier phases.
- **New.** `~/projects/earnings-call-nlp-pipeline/exports/2026-09-30/`. Before any other step, the SHA-256 of its `all_sentences.csv` and `all_utterances.csv` is compared with the files in `notebooks/final/data/results/2026-09-30/`; the phase stops if they differ. The hashes of the four files used are written to `data/phase3i/export_hashes.json`.
- **Window.** UBS earnings calls 2023-Q2 to 2024-Q4 (seven calls). The new export also holds 2022 and 2025; these calls lie outside the window and are not used. The JPMorgan event call belongs to the phase 3g sentence basis but not to the main finding; it is not part of this phase.

## Units

The 39 targets are the 31 UBS units of `data/phase3d/counterparts_read.csv` with `genuine == "yes"`, `type == "target"` and `pre_acquisition != "yes"`, and the 8 units of `data/phase3g/new_units_read.csv` with `type == "target"`. Each unit has one source statement, identified by its `stmt_id` in `data/phase3/statements.csv`. The script stops if the two selections do not give 31 and 8 units.

## Step 1: comparison of the two exports (CPU)

- **Counts.** Per call in the window and per export: number of sentences and of utterances, in total and by section and speaker role.
- **Sentence comparison.** Per call, the sentences of both exports are compared on the normalised text. Normalisation: curly quotation marks and apostrophes mapped to straight ones, runs of whitespace reduced to one space, leading and trailing whitespace removed. Nothing else is changed (case, punctuation and hyphens stay). Each sentence falls into one class:
  - *same*: the normalised text occurs in both exports in the same call (matched as multisets, so repeated sentences such as "Thank you." are paired one to one);
  - *same text, other attribute*: paired as above, but speaker name, speaker role or section differs;
  - *only old* and *only new*: no partner with the same normalised text in the call.
- **Cause.** For the sentences that are only old or only new, each is aligned with its nearest neighbours in the other export (position in the call, `difflib` similarity of the normalised text) and the cause is described in words from that alignment: sentence splitting (one sentence against two), changed wording, added or removed sentence, changed speaker assignment. The description is made by reading the aligned pairs; the script only supplies the alignment and a proposed cause label.
- **Output.** `call_counts.csv`, `sentence_diff.csv` (every sentence that is not *same*, with both keys, texts, similarity and the proposed cause).

## Step 1: the source statements of the 39 units

The phase 3 statements are built from the export by `load_statements()` in `analysis/phase3_extract.py` (management sentences, square-bracket insertions removed, sentences ending in "ex." joined with the next one). The same function is applied to the new export, without change, by pointing it to the new folder at run time.

For each unit, the source statement is searched among the new statements of the same call:

- **found, same wording**: a new statement of the same call (bank, quarter, call type) and the same speaker name has the same normalised text. By definition the figures are then the same; as a check, `quantities()` of both texts is compared as well.
- **found, other wording**: no such statement, but the most similar new statement of the same call has a `difflib` similarity of at least 0.8. Reported with both texts, the similarity, and whether speaker and figures (`quantities()`) agree.
- **not found**: neither.

Output `units_match.csv`: unit, call, found, same wording, same speaker, same figures, old and new `sentence_id`, old and new key (`position_in_call`, `sentence_number`), old and new text where they differ.

## Step 2: candidate search on the new export

Same settings as in phases 3 and 3g; no rule, pattern, model, revision or threshold is changed.

- **Rules (phase 3).** `is_candidate()` of `analysis/phase3_extract.py` on the new statements in the window.
- **FinBERT-FLS (phase 3g).** `yiyanghkust/finbert-fls` at revision `443586dc31c765c0aaf1c4daaed8cf3643c92fa5`, maximum length 256 tokens, batch size 64, seed 0, on the GPU, on the new statements in the window. As in phase 3g, the additional set S is: labelled Specific FLS, contains a number, not a rule candidate. FLS-RoBERTa is not rerun: in phase 3g it labelled all 73 sentences of S as FLS and narrowed nothing.
- **Reproducibility check.** For statements with the same normalised text in both exports, the new FinBERT-FLS label is compared with the label in `data/phase3g/scored.csv`. Differences are reported; they would mean that the model run itself is not reproduced.
- **Comparison.** Rule candidates and S, old against new, matched within the call on the normalised text: *same*, *only old*, *only new*. Old sets: `data/phase3/candidates.csv` and `data/phase3g/set_s.csv`, restricted to the window.
- **List for Roman.** Every statement that is *only new* in the rule candidates or in S is written to `only_new_for_reading.csv` with its text, the sentence before and after, call, speaker, section, which set it is new in, the phase 3 metric group, and, where it exists, the most similar old statement of the same call with its similarity (so that a reworded old candidate can be recognised). The columns `genuine`, `duplicate_of`, `new_target` and `notes` are empty and are filled by Roman. I do not classify these statements.
- **Only old.** Statements that are *only old* are listed in `only_old.csv` with the unit they belong to, if any. A unit whose source statement is only old is already covered by step 1.

## Decision rule (fixed before computation)

- The finding **holds** if
  - (a) all source statements of the 39 targets are present in the new export with the same content: same call, same speaker, same figure and same wording after normalisation of whitespace and quotation marks, and
  - (b) the candidate search in the window 2023-Q2 to 2024-Q4 yields no new quantified targets on capital, costs, funding or NCL, or the new candidates do not belong in the basis after Roman's reading.
- If a source statement differs or a target is added, it is classified by the rules of `plans/phase_3d.md` and `plans/phase_3g.md` and checked against the reports before any statement of the finding is changed.

Reported outcome, one of three: *holds*; *holds with adjustment* (a source statement differs or a target is added, and the classification and the report check are done); *open until Roman's reading* (there are *only new* candidates that Roman has not read yet). The report also states whether the count of 9, with T30 separate, is unchanged.

A source statement that is *found, other wording* does not by itself change the finding; it fails condition (a) as worded and is reported for Roman's decision together with both texts.

## Implementation and outputs

- `analysis/phase3i_check.py` (steps 1 and 2; imports the unchanged functions of `phase3_extract.py`), tests in `tests/test_phase3i.py`.
- Outputs in `notebooks/roman/data/phase3i/`: `export_hashes.json`, `call_counts.csv`, `sentence_diff.csv`, `statements_new.csv`, `units_match.csv`, `scored_new.csv`, `candidates_compare.csv`, `set_s_compare.csv`, `only_new_for_reading.csv`, `only_old.csv`, `summary.json`, `SHA256SUMS`.
- Notebook `03i_export_check.ipynb`, with saved outputs.
- `FINDINGS.md` is not changed in this phase.

## Limits known in advance

- The comparison is on wording. A sentence whose wording is unchanged but whose position, `sentence_id` or neighbours changed counts as the same; the old and new keys are recorded.
- Splitting changes can move a figure and its horizon into different sentences. Such a statement can drop out of the rule candidates or enter them without any change in what was said; the alignment in `only_new_for_reading.csv` and `only_old.csv` is meant to make this visible.
- The classes A, B and C of the 39 targets rest on the reports and on one reader. This phase does not re-read them.
