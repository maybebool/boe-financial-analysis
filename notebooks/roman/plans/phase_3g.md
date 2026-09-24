# Phase 3g: does a forward-looking-statement model find commitments that the phase 3 rules miss?

Written 2026-09-24, before any computation of this phase. Descriptive and exploratory: no test, nothing enters the register. Release `data/results/2026-09-23/` (frozen).

## Question

Do the rule-based candidates of phase 3 miss quantified forward-looking commitments that a model trained to detect forward-looking statements (FLS) finds?

## What the result can and cannot change (fixed now)

- The statement on the **six call-only figures** (T16, T25, T27, T32, T33, T68) is not affected: those units were found, read and checked; phase 3g can only add units, not remove or reclassify them.
- What can change is the **comparison basis**: the 31 genuine UBS targets set after the acquisition and their split into 16 A, 11 B and 4 C (window W1). New genuine UBS targets found here are added to the basis with their class, and the old and the new split are reported side by side.
- A new target of class C would not be added to the main finding. It would be listed as a candidate call-only figure for Roman's check, as the six were.
- New genuine guidance or other items, and new items from the JPMorgan event call, are reported separately and do not enter the 31.

## Models (pinned at run time in `notebooks/roman/data/phase3g/models.json`)

- **Primary:** `yiyanghkust/finbert-fls` (revision 443586dc31c765c0aaf1c4daaed8cf3643c92fa5), labels Not FLS, Non-specific FLS, Specific FLS; label = argmax of the softmax.
- **Second opinion:** `soleimanian/fls-roberta` (revision aebefd6b2c23a622afaafb99efdfdafd033779d5). Its configuration has three labels (FLS, "label", non_FLS); the second is an unused placeholder, so the prediction is FLS if the FLS probability exceeds the non_FLS probability, and the placeholder is ignored.
- Both run locally on the GPU, maximum length 256 tokens, seed 0. Both repositories provide weights only as `pytorch_model.bin`; they are loaded with the transformers library's standard loader. No new package is needed; if one is, it goes into `requirements-roman.txt`.

## Units

All management sentences of the UBS earnings calls from 2023-Q2 to 2024-Q4 and of the JPMorgan event call of 1 May 2023, on the phase 3 sentence basis (`notebooks/roman/data/phase3/statements.csv`, square-bracket insertions removed, sentences ending in `ex.` joined with the next sentence of the same statement): 3,177 UBS sentences and 182 event-call sentences, of which 108 are phase 3 candidates. Each sentence is classified alone, without context, as in phase 3.

## Comparison

- **Cross-tables** per bank and call type: phase 3 candidate yes/no against FinBERT-FLS Specific FLS yes/no; the same against FLS-RoBERTa FLS yes/no; and FinBERT against FLS-RoBERTa.
- **"With a number"** means that the phase 3 quantity parser (`phase3_extract.quantities`, part (a) of the candidate rule) finds a quantity in the sentence.
- **Additional set S:** sentences that FinBERT-FLS labels Specific FLS, that contain a number and that are not phase 3 candidates. For each, the table records which of the three phase 3 conditions failed (quantity, future horizon, forward-looking word) and whether FLS-RoBERTa also labels it FLS.
- **Recall check in the other direction:** phase 3 candidates that FinBERT-FLS does not label Specific FLS are counted, not read.

## Reading of S (as in phase 3d)

- **Size.** All sentences in S are read if S has at most 150 sentences; otherwise a random sample of 150 with `numpy.random.default_rng(0)`, stratified by bank and call, and the counts are extrapolated with the sampling weight. This rule is fixed before S is known.
- **Genuine commitment?** Judged against `commitments_guide.md` as in phase 3d: management's own quantified forward-looking statement about its own metric with a point or period in the future. Not genuine, with a one-line reason: reported actuals, figures attributed to others, conditional or illustrative numbers, quantity and horizon belonging to different things, statements without a future horizon even in context.
- **New or known?** A genuine sentence is a **duplicate** if it restates a commitment already covered by a phase 3 thread or a phase 3d unit (same metric, same figure or an earlier figure of the same commitment); the matching unit or thread is named. Only genuine, new commitments go further.
- **Type:** target, guidance or other, by reading, with the phase 3 definitions.

## Report search for the new genuine commitments (procedure of phase 3d)

- Search terms per new unit are written into `notebooks/roman/data/phase3g/search_terms.csv` from the call sentence alone before any report search (groups 1 to 3 as in phase 3d; hash in `run_log.json`).
- Reports: UBS quarterly reports and annual reports 2023 and 2024, JPMorgan supplements, as in phase 3d; the Pillar 3 reports are not included (phase 3f covers only the six figures). Text: the phase 3b reconstruction with the hyphen repair (`phase3b_repaired`). Windows W1 and ALL as in phase 3d.
- Classification A, B or C as in phase 3d, A with forward-looking context; quotes verified against the page by the script; for C the full list of terms.

## Outputs

`analysis/phase3g_fls.py` (models, cross-tables, set S), `analysis/phase3g_read.py` (reading, search, classes, updated basis); outputs in `notebooks/roman/data/phase3g/`; notebook `03g_fls_models.ipynb`. `FINDINGS.md` is not changed in this phase.

## Limits (stated in advance)

- FinBERT-FLS was fine-tuned on 3,500 sentences from the MD&A section of annual reports of US (Russell 3000) firms, not on earnings calls; spoken, conversational call language and a Swiss bank's terminology are outside its training data. FLS-RoBERTa was trained on a mixed corpus that includes earnings call transcripts, but only for FLS against non-FLS, without specificity.
- Neither model is validated on these data, and no labels will be collected for them; the reading of S is by one reader and serves as the only check of the model's additional finds.
- Sentences are classified without context, as in phase 3; a commitment whose figure and horizon sit in two sentences can be missed by both methods.

## Tests (pytest)

Added to `tests/`: the sentence basis matches the phase 3 statements for the selected calls; every sentence has exactly one FinBERT label; S contains only Specific FLS sentences with a quantity that are not phase 3 candidates; every quote of the new units is found on its page; the search terms were not changed after the recorded hash.

## Amendment 2026-09-24 (before any computation)

1. **Pillar 3 for new class C targets.** A new genuine UBS target of class C (W1 and ALL) is also searched in the available UBS Pillar 3 reports from the quarter of its first mention to 2024-Q4, with the same search terms and the procedure of phase 3f. Only if it is absent there as well is it listed as a candidate call-only figure next to the six.
2. **Blind spot check.** Before any reading of S, ten sentences are drawn from S at random with `numpy.random.default_rng(1)` and written to `notebooks/roman/data/labelling/phase3g_spotcheck.csv` with the columns item_id, sentence, call, quarter, context_before, context_after and the empty columns genuine (yes/no), duplicate_of and notes. The model scores and my own classification are not in the file. My classification of these ten sentences is part of the reading of S, but it is compared with Roman's only after he returns the file.

## Amendment 2026-09-24 (implementation and reading, after the results)

Everything in this phase is descriptive; the points below record choices made while reading, after S was known.

1. **Duplicates.** A genuine sentence also counts as a duplicate when it states a component of an existing unit's figure in the same passage (for example the core and NCL parts of the Group RWA walk of T35), or when it restates a phase 3 candidate that phase 3 filed under another thread (named as "T.. (candidate stmt_id)").
2. **Horizon from context.** As for T10 ("over the medium term"), a horizon given by the surrounding passage counts (the 2023-Q4 section "medium-term priorities and ambitions", "over the next 3 years", "for the foreseeable future"). Targets without any horizon, even in context, are not genuine (6621, borderline).
3. **Search terms.** The phrase "ELA" (F14) is matched case-insensitively inside words (for example "related"), as all phrases in phase 3d. The terms were not changed; only hits containing "ELA" as a word, the long form or the figure were read.
4. **Reading in two passes.** First the hits with a figure and a phrase, then every forward-looking hit. Because the first pass had shown truncated hit text, the second pass scanned the full text around every term. This moved F13, F14 and F16 from C to A before any class was recorded.
5. **Check files.** In phase 3f the check files were written before the search. Here the three new UBS targets of class C (F11, F12, F22) were only known after the search, so `check_units.json` (all UBS quarterly and annual reports plus the available Pillar 3 reports of the window) and `check_units_2024q2.json` (F11, F12) were written after it, in the phase 3f format.

Result: S has 73 sentences (UBS 68, JPM event 5), of which 53 are genuine and 22 are new (all UBS; 8 targets, 10 guidance, 4 other). The comparison basis grows from 31 to 39 UBS targets; in W1 from 16 A, 11 B, 4 C to 21 A, 11 B, 7 C. The three new C targets (going concern capital ratio around 18%, LRD reduction over 100bn, LCR below 188%) are also C in the available Pillar 3 reports and are candidates for Roman's check.

## Amendment 2026-09-24: Roman's check of F11, F12, F22 and the consistency rule

Roman checked the three new UBS targets of class C with `check_units.json` and his own search script (output in `notebooks/roman/data/phase3g/roman_check/`, `check_hits_3g.txt` unfiltered and `check_hits_3g_forward.txt` filtered on forward-looking words). The hits were pre-sorted by machine per unit; Roman read the borderline cases himself and a sample of the pre-sorting, not every hit. Result: **F11 C** (all hits are tables with actual values), **F22 C** (LCR tables and definitions), **F12 B**: the 2023 and 2024 annual reports list "Reduce RWA and LRD, freeing up capital for the UBS Group" as a key priority of Non-core and Legacy, the same reduction without the 100 billion and for the NCL part only. The consistency rule set after reviewing the borderline cases (see the amendment of the same date in `phase_3d.md`) applies to this phase as well. Updated basis of 39 UBS targets: W1 21 A, 13 B, 5 C; ALL 23 A, 11 B, 5 C. `checked_by_roman` in `new_units_read.csv` records that only the borderline cases were read by Roman.

## Amendment 2026-09-24: decisions after the check, counting rule

F12 stays B. By Roman's decision under the consistency rule, T16 becomes B in phase 3d and T27 becomes B in the Pillar 3 reports of phase 3f (amendments in `phase_3d.md` and `phase_3f.md`). Updated basis of 39 UBS targets: W1 21 A, 14 B, 4 C; ALL 23 A, 12 B, 4 C. For the main finding only C ("not mentioned") and B without any figure ("mentioned without a figure") count as "figure only in the call"; B with another figure is shown separately.
