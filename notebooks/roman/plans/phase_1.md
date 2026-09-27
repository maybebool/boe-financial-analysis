# Phase 1: evasive answers

Written 2026-09-23, before any computation of this phase. Revised the same day, still before any computation: validation sample for missed deflections, second gate, and all rules written out verbatim. Release `data/results/2026-09-13/`, earnings calls only.

## Question

Does UBS management deflect analyst questions more often than JPMorgan management, and are the UBS deflections concentrated on capital regulation, the topic that matters most to supervisors after the merger?

## Status of the evidence

The phrase list and the idea that UBS deflects on capital come from reading these same 16 calls (phase 0: 14 UBS hits against 5 JPM hits, 10 of the 14 UBS hits in 2024-Q1 to 2024-Q3). Phase 1 therefore cannot be an independent replication. It is a stricter test on the same data: the call becomes the unit of inference, a second detector (NLI) is added that was not used to form the hypothesis, and the labels are validated by hand. Every result is reported with this caveat.

## Data preparation (fixed before scoring)

1. **Sentences.** Q&A sentences of earnings calls; square-bracket insertions removed with `\[[^\]]*\]`; sentences with three words or fewer dropped for scoring (share reported per bank). Operator lines are excluded.
2. **Pairs.** As in `qa_pairs.py`: an analyst turn followed by the consecutive management or IR turns in the same call.
3. **Question segments.** Each analyst turn is split into question segments by these rules, applied in order to the turn's sentences (after bracket removal, before the short-sentence filter):
   - A new segment starts at sentence i > 1 if the previous sentence ends with `?`, or if sentence i matches, case-insensitive,
     `^\W*((and|so|then|maybe|okay|ok)\W+)*(first|firstly|second|secondly|third|the other question|my second question|a follow-up|and then|just on|on the|lastly|finally)\b`.
   - A segment that contains no sentence of four words or more, or that consists only of sentences starting with `thanks`, `thank you`, `hi`, `hello`, `hey` or `good morning/afternoon/evening`, is merged into the following segment, or into the preceding one if it is the last.
   - If this leaves no segment, the whole turn is one segment.
4. **Answer alignment.** Each management answer sentence is assigned to the question segment of its pair with the highest cosine similarity under `sentence-transformers/multi-qa-mpnet-base-dot-v1` (single-segment turns are trivial). Alignment never crosses the pair. IR sentences are not scored.

## Deflection detector

- **Phrase list.** The nine patterns of `qa_pairs.py`, applied per answer sentence, case-insensitive, unchanged. The list was fixed in `qa_pairs.py` before phase 0 and is not modified in this phase. Verbatim:
  ```
  \b(we|i)\s+(don't|do not|won't|will not|wouldn't|would not)\s+(disclose|comment|give|provide|speculate|guide|break out|get into)
  \bnot (going|gonna) to (comment|give|speculate|get into|disclose|guide)
  \b(too early|premature) to\b
  \bwe('ll| will) (update|come back|tell) you\b
  \b(at|in) (the|our) (next|upcoming|coming) (quarter|call|update|investor day)
  \bno (comment|update)\b
  \bcan't (really )?(comment|give|say|tell|disclose)
  \b(i|we) (would|'d) (rather|prefer) not\b
  \bnot in a position to\b
  ```
- **Zero-shot NLI.** `MoritzLaurer/deberta-v3-large-zeroshot-v2.0`. Premise: the answer sentence alone. Hypotheses, verbatim:
  - H_a: `The speaker declines to give the requested information.`
  - H_b: `The speaker says it is too early to say or to give details.`

  Entailment probability is the softmax over the model's two classes (entailment, not entailment). A sentence is NLI-positive when max(p(H_a), p(H_b)) ≥ 0.9.
- **Primary label.** A sentence is a deflection if the phrase list or the NLI flags it. A question segment is deflected if at least one aligned answer sentence is a deflection.

Model revisions (commit hashes) are recorded at run time in `notebooks/roman/data/phase1/models.json`; seed 0 throughout.

## Topic of the question

A question segment is **capital regulation** if its text matches at least one of these terms. Matching is case-insensitive, with a word boundary at the start of the term only, so `regulator` also matches `regulatory` and `regulators`; `*` stands for any word characters. Verbatim:

`capital requirement`, `capital regime`, `regulatory capital`, `capital rules`, `basel`, `endgame`, `too big to fail`, `tbtf`, `federal council`, `parliament`, `finma`, `swiss regime`, `parent bank`, `subsidiar* capital`, `g-sib`, `gsib`, `surcharge`, `slr`, `supplementary leverage`, `stress capital buffer`, `scb`, `at1`, `additional tier 1`, `guarantee`, `loss protection`, `regulator`, `regulation`.

Everything else is **other**. The list covers both banks: the Swiss regime debate for UBS and Basel III endgame, G-SIB surcharge and SLR for JPMorgan, so JPMorgan is a real control and not a bank without the topic.

## Primary tests

**P1-1, deflection rate UBS vs JPM.**
- Unit: call (8 UBS, 8 JPM).
- Statistic: per call, deflection sentences per 100 management answer sentences (four words or more). T = mean over UBS calls minus mean over JPM calls.
- Test: exact permutation of bank labels over the 16 calls (12,870 splits), two-sided on |T|. Two-sided because the direction was seen in phase 0 on the same data.
- Support: p < 0.05 after Holm across all primary tests of the study, with T > 0. Null: p ≥ 0.05, or T ≤ 0.

**P1-2, concentration of deflections on capital regulation, UBS relative to JPM.**
- Unit: question segment, with call as stratum.
- Statistic: for each bank, excess share E = (O − X) / D, where O is the number of deflected segments on capital regulation, X its expectation if deflections were placed at random among the segments of the same call (sum over calls of deflected segments × capital segments / segments), and D the number of deflected segments. T = E_UBS − E_JPM.
- Test: within each call, the deflection flags are permuted across that call's question segments; 10,000 random permutations with `numpy.random.default_rng(0)`, two-sided on |T|. Permuting within calls keeps every call's deflection count and topic mix fixed, so call-level differences cannot create the result.
- Support: p < 0.05 after Holm, with T > 0. Null: p ≥ 0.05, or T ≤ 0.
- Power note: with roughly 15 to 30 deflected segments per bank this test is weak; a null result is not evidence that the concentration is absent.

Both tests enter `plans/test_register.csv` with raw and Holm-adjusted p.

## Exploratory analyses (labelled as such everywhere)

**E1, timing: Swiss regulatory debate 2024 vs integration 2023.** Hypothesis: UBS deflections follow the Swiss capital regime debate (the Federal Council adopted its report on banking stability on 10 April 2024, date checked by Roman; the first UBS call afterwards is 2024-Q1 on 7 May 2024) rather than the integration year 2023.
- Statistic: difference in differences of call rates, (mean UBS 2024 − mean UBS 2023) − (mean JPM 2024 − mean JPM 2023), for all deflections and separately for deflections on capital regulation.
- Test: exact permutation of the year labels within each bank (70 × 70 = 4,900 joint splits), two-sided.
- Content check: share of UBS deflected segments that match Swiss-regime terms (`federal council`, `parliament`, `swiss regime`, `too big to fail`, `parent bank`, `finma`) against integration terms (`credit suisse`, `integration`, `non-core`, `migration`, `combined`, `cost save`), per year.
- Why exploratory: phase 0 already showed 10 of 14 UBS phrase hits in 2024-Q1 to 2024-Q3, so the hypothesis is formed on the data it would be tested on, and a third primary test would exceed the limit of two per phase. Robustness: move the start of the debate period to 2023-Q4 (6 February 2024), when the parliamentary inquiry was already running.

**E2, answer relevance.** Per question segment, relevance of its aligned answer with `cross-encoder/ms-marco-MiniLM-L-6-v2` and with `multi-qa-mpnet-base-dot-v1`. Relevance lift = score of the true answer minus the mean score of the other answers of the same call (within-call null). Answer length is controlled by scoring the first 128 tokens of each answer and, as an alternative, by the residual of lift on log answer words. Compared by bank, topic and year at call level; descriptive only.

**E3, detector agreement.** Overlap of phrase list and NLI per bank; share of deflections found by one method only.

## Robustness for the primary tests

Each primary test is rerun with: phrase list only; NLI only; NLI thresholds 0.8 and 0.95; short sentences kept; rate per 10,000 answer words instead of per 100 sentences; topic by embedding similarity to a fixed prototype sentence ("The question is about regulatory capital requirements for the bank.", cosine ≥ 0.5 with `multi-qa-mpnet-base-dot-v1`) instead of keywords. A result that changes sign or crosses 0.05 in any variant is reported as fragile.

## Validation

Two samples under `notebooks/roman/data/labelling/`, each with a guide `<task>_guide.md`. Model scores are kept in a separate key file so that labelling is blind.

- `deflection.csv`: answer sentences with their question segment and one sentence of context on each side, in random order (seed 0), without bank-independent hints such as scores or strata. Label: deflection yes/no. Per bank:
  - flagged part, up to 50 sentences, drawn from the strata both methods positive, phrase list only, NLI only (all items if a stratum is smaller than its share), plus up to 10 unflagged sentences with NLI 0.5 to 0.9;
  - unflagged part, about 50 further sentences not flagged by the primary detector and outside the 0.5 to 0.9 band, at least half of them from answers aligned to capital-regulation segments.
- `question_topic.csv`: about 100 question segments stratified by bank and keyword outcome (about 25 per cell). Label: capital regulation yes/no.

Estimation. Each sampled sentence carries the weight N_stratum / n_stratum of its stratum (strata: flagged by method combination; unflagged NLI 0.5 to 0.9; unflagged aligned to capital; unflagged other). Precision is the weighted share of true deflections among flagged sentences. The miss share is the weighted estimate of true deflections among unflagged sentences divided by the weighted estimate of all true deflections (one minus recall). Cohen's kappa is computed between the primary detector and Roman's labels on the sample.

Gate. P1-1 and P1-2 are reported as not interpretable if any of these holds: precision of the primary detector below 0.7 in either bank; precision differs between banks by more than 0.2; the estimated miss share differs between banks by more than 0.2. A bank difference could otherwise come from the detector alone. Until the labels are back all phase 1 results are provisional.

## Tests (pytest)

Added to `tests/`: question segments partition each analyst turn without loss; every answer sentence is aligned to a segment of its own pair; no alignment crosses a call; the deflection rate uses management answer sentences only.

## Outputs

Computation in `analysis/phase1_*.py`, outputs in `notebooks/roman/data/phase1/`, notebook `01_evasive_answers.ipynb`.

## Amendment 2026-09-23 (after scoring, before any test statistic was computed)

While inspecting flagged sentences it became clear that the release contains no `n't` at all: every negative contraction appears as one word (`donot`, `wonot`, `canot`, `havenot`), in both banks and all calls. The alternatives `don't`, `won't` and `can't` of the pre-registered phrase list therefore never match. The primary analysis keeps the phrase list unchanged. One exploratory variant is added (E4): the same nine patterns applied to text in which `(\w+)not\b` forms of the affected auxiliaries (do, does, did, wo, ca, would, could, should, is, are, was, were, have, has, had) are restored to `n't` (`canot` becomes `can't`). E4 is reported for P1-1 and P1-2 as exploratory and not entered in the register. The contraction problem is reported to Roman as a release issue.

## Amendment 2026-09-23 (after the first results): E5, topic per whole analyst turn

Reading the deflected UBS segments showed that the splitting rule often separates the regulatory context of a question from its final question sentence, so the segment topic misses regime questions. E5 repeats the concentration analysis with the topic assigned to the whole analyst turn. It is exploratory, formed after seeing the results, and not entered in the register.

- Unit: question/answer pair, with call as stratum.
- Topic: the pair is capital regulation if the whole analyst turn matches the keyword list of this plan (same terms, same matching rule).
- Deflection: the pair is deflected if at least one management answer sentence of four words or more is a deflection under the primary detector.
- Statistic and test as P1-2 at pair level: excess share E = (O − X) / D per bank, T = E_UBS − E_JPM, deflection flags permuted within calls, 10,000 permutations with `numpy.random.default_rng(0)`, two-sided, p = (k + 1) / (N + 1).
- Timing as E1 with the pair topic: difference in differences of the call rate of deflection sentences in capital-regulation pairs per 100 management answer sentences, 2024 against 2023 (and from 2023-Q4 as robustness), exact within-bank permutation of the year labels.

## Amendment 2026-09-23 (before the corrected release): primary tests on the corrected release

The release `2026-09-13` has lost every `n't` in the sentence segmentation of the pipeline. The pipeline is being fixed and a corrected release will follow. Fixed now, before the corrected release exists:

1. P1-1 and P1-2 are recomputed on the corrected release without any change: the same pairing, splitting rule, alignment model, phrase list, NLI model, hypotheses and threshold 0.9, keyword list, statistics, permutation schemes and seeds, and the same robustness variants. Only the release folder changes.
2. The values on the corrected release are the primary results and replace the current rows of P1-1 and P1-2 in `plans/test_register.csv`, with Holm recomputed. The values on `2026-09-13` are reported next to them as a run on faulty data, whatever the new values turn out to be.
3. There are no further changes to the detector or the splitting for the primary tests. E4 (restored contractions) becomes redundant on the corrected release and is dropped there; E1, E2, E3 and E5 are rerun unchanged as exploratory analyses.
4. The labelling samples are drawn again from the corrected release with the same procedure and seed. The samples drawn from `2026-09-13` are superseded and are not labelled.

## Amendment 2026-09-24: validation results and labelling decisions

**Labelling decisions (Roman).** `deflection.csv` (180 sentences) is labelled. `question_topic.csv` will not be labelled; the capital-regulation topic label of phase 1 is therefore **not validated**.

**Evaluation** as specified in the validation section of this plan (`analysis/phase1_validation.py`, outputs `data/phase1/validation_*.csv`; stratum weights N/n; kappa unweighted on the sample; bootstrap intervals added as a supplement):

| | Precision | Miss share (1 − recall) | Kappa |
|---|---|---|---|
| UBS, primary detector | 0.45 (0.32 to 0.61) | 0.75 (0.00 to 0.91) | 0.46 |
| JPM, primary detector | 0.59 (0.36 to 0.77) | 0.93 (0.62 to 0.97) | 0.51 |
| UBS, phrase list only | 0.47 | 0.88 | 0.32 |
| JPM, phrase list only | 0.57 | 0.98 | 0.21 |
| UBS, NLI only | 0.47 | 0.78 | 0.46 |
| JPM, NLI only | 0.60 | 0.93 | 0.50 |

**Gate.** Precision is below 0.7 in both banks, so the pre-registered gate fails. The differences between the banks stay within 0.2 (precision 0.14, miss share 0.17), but the miss shares rest on three labelled deflections in the stratum "unflagged other" with weights of 45 and 62 and are very uncertain. By this plan, **P1-1 and P1-2 are reported as not interpretable**. Their values and the register are not changed.

**Notes.** Roman's notes contain one "alignment wrong" (item D059, labelled 0, detector agrees) and no "uncertain" or "borderline"; a comparison of agreement for these cases is therefore not possible.

**Exploratory, formed after the labels.** Weighted by strata, the labels estimate that 5.1 % of UBS and 9.3 % of JPMorgan management answer sentences are deflections (bootstrap 1.0 to 12.5 % and 1.8 to 19.5 %), against detector flag rates of 2.8 % and 1.2 %. The detector's higher rate for UBS may thus come from what the detector finds rather than from how often management deflects. This estimate is pooled by bank, not by call, and is not a test.
