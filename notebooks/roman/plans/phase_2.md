# Phase 2: novelty and drift

Written 2026-09-23, before any computation of this phase. Revised the same day, still before any computation: one primary test only (decay), the level becomes exploratory, event call and CFO change stated explicitly, effect sizes with their range reported next to p. Release `data/results/2026-09-23/` (via `RELEASE_DIR`), earnings calls only.

## Question

After the merger was completed, does UBS management say more that is new relative to its own earlier calls than JPMorgan management does, and does that novelty fade more slowly?

## Hypothesis

Integrating Credit Suisse forces UBS to talk about new subjects (non-core run-down, legal entity mergers, client migration, the Swiss capital debate) for longer than the small First Republic acquisition forces JPMorgan. UBS management novelty is therefore higher than JPMorgan's from the first call after completion onwards, and it decays more slowly.

## Status of the evidence

Phase 0 already showed on these data that call similarity falls with time lag for both banks and more steeply for JPMorgan (constant speaker rho −0.61 for UBS, −0.85 for JPMorgan). That result points against a slower decline of UBS vocabulary, so the direction of the decay hypothesis is not taken for granted, and all tests are two-sided.

## Data preparation

1. **Sentences.** All sentences of the eight earnings calls per bank, operator lines excluded, square-bracket insertions removed, sentences with three words or fewer dropped (share reported per bank and role).
2. **Masking.** Text is masked with `contrast.clean` from `contrast.py` (names, numbers, quarters, years and months replaced by placeholder tokens, lower case), so that recurring template sentences with new figures ("revenues were USD X bn") do not count as new.
3. **Calls.** Only earnings calls are used. The JPMorgan event call of 1 May 2023 is neither a target call nor part of any reference set. The first call after completion is 2023-Q2 for both banks (UBS 31 August 2023, completion 12 June 2023; JPMorgan 14 July 2023, First Republic acquired 1 May 2023). The 2023-Q1 calls serve only as reference. Target calls are 2023-Q2 to 2024-Q4, seven per bank.

## Novelty measure

- **Embedding model.** `sentence-transformers/all-mpnet-base-v2`, revision pinned at run time in `notebooks/roman/data/phase2/models.json`; embeddings L2-normalised; seed 0.
- **Reference set.** For a target call t of bank b, the reference pool is all eligible sentences of all roles (management, analyst, IR) from the earnings calls of bank b before t. Because the pool grows with t, and a maximum over more sentences is mechanically higher, the reference is a random sample of fixed size R from the pool. R = 415, the smallest number of eligible sentences in any 2023-Q1 call (JPMorgan). Novelty is averaged over D = 20 independent draws with `numpy.random.default_rng(0)`.
- **Sentence novelty.** 1 − max cosine similarity between the sentence and the R reference sentences.
- **Call novelty.** Mean sentence novelty over the management sentences of the call (prepared remarks and Q&A together).

## Primary test

Phase 2 has one primary test, the decay of novelty (P2-2). The level of novelty is analysed with the same test and the same robustness variants, but only as exploratory analysis E1. Reason: the decay answers how long a merger echoes in a bank's communication, which is the supervisory question, while a difference in level can simply be house style (UBS presents by slide, JPMorgan in a few long statements; different speakers, different templates) and would be present without any merger.

The register already holds P1-1 (p_raw 0.040) and P1-2 (p_raw 0.155). P2-2 enters `plans/test_register.csv`, and Holm is recomputed across all three primary tests of the study. With three tests the smallest p must be below 0.0167 to count, which means P1-1 can no longer reach significance. This is the intended study-wide control and is reported as such.

**P2-2, decay of novelty, UBS vs JPMorgan.**
- Unit: call, the 14 target calls (7 per bank).
- Statistic: slope of call novelty on the quarter index (2023-Q2 = 0, …, 2024-Q4 = 6) by ordinary least squares, per bank. T = slope_UBS − slope_JPM. A positive T means UBS novelty falls more slowly (or rises more).
- Test: exact permutation of bank labels over the 14 target calls (3,432 splits), two-sided on |T|; for each split the slope is fitted on the calls assigned to each group with their own quarter index. The two banks share the same quarters, so a common time trend makes this permutation conservative, not anticonservative.
- Support: Holm-adjusted p < 0.05 with T > 0. Null: otherwise. A significant negative T (UBS novelty fades faster) is reported as evidence against the hypothesis.
- Power note: a slope on seven calls per bank is noisy; a null result is not evidence of equal decay.

**Speaker change.** The UBS CFO changed after 2023-Q2 (Sarah Youngwood until 2023-Q2, Todd Tuckner from 2023-Q3). A new speaker brings new phrasing, so UBS management novelty can rise in 2023-Q3 for reasons unrelated to content, which would flatten or raise the UBS slope. At JPMorgan, Jamie Dimon is absent in 2024-Q2 and leaves the 2024-Q1 Q&A midway. The constant-speaker variant (Ermotti, Barnum) exists for exactly this reason; if it disagrees with the main result in sign or crosses 0.05, the result is reported as fragile.

**Reporting.** For P2-2 and E1 the effect size (T, and the two slopes or levels) is reported with equal prominence next to the p-value, together with its range (minimum and maximum of T) over all robustness variants.

## Robustness

P2-2 and E1 are each rerun with:
- **constant speakers** only (Ermotti, Barnum) as the control for speaker change (the UBS CFO changed after 2023-Q2; Dimon is absent in 2024-Q2); Ermotti has only 73 eligible sentences in 2024-Q2, so this variant is noisy;
- a second embedding model, `sentence-transformers/all-MiniLM-L6-v2`;
- lexical novelty with TF-IDF (unigrams and bigrams, min_df = 2, sublinear tf, English stop words, fitted per bank on all its calls) instead of embeddings;
- reference = the immediately preceding call only (lag-1 novelty, no sampling);
- reference = management sentences only;
- call novelty as the share of management sentences with max similarity below 0.5 instead of the mean;
- short sentences kept;
- the paired alternative to the permutation: within-quarter swaps of the bank labels (2^7 = 128 sign flips). With 128 flips the smallest two-sided p is 0.016, so this variant can confirm direction but cannot pass Holm on its own.

A result that changes sign or crosses 0.05 (raw) in any variant is reported as fragile; the constant-speaker variant matters most.

## Exploratory analyses (labelled as such everywhere)

- **E1, novelty level after completion, UBS vs JPMorgan.** T = mean call novelty of the UBS target calls minus that of the JPMorgan target calls; exact permutation of bank labels over the 14 target calls (3,432 splits), two-sided; same robustness variants as P2-2. Not entered in the register.
- **E2, novelty curves by role and section:** management prepared, management Q&A, analysts, per bank and call.
- **E3, what is new:** the ten most novel management sentences per call with their nearest earlier sentence, for qualitative reading, and the share of novel sentences (max similarity below 0.5) that match the phase 1 capital-regulation keyword list, by bank and year.
- **E4, analyst novelty:** the P2-2 and E1 statistics for analyst sentences, as an outside view of what the market found new.
- **E5, consistency with phase 0:** call-by-call similarity matrix on the same embeddings and Spearman rho between lag and similarity, next to the TF-IDF values of phase 0.

## Validation

`notebooks/roman/data/labelling/novelty.csv`: about 100 management sentences, stratified by bank and novelty quartile (about 12 or 13 per cell), each shown with its most similar earlier sentence (from the full pool, not the sample) and that sentence's call. Label: `1` if the sentence says something substantially different from its nearest earlier sentence, `0` if it restates it. Guide in `novelty_guide.md`, scores and strata in `novelty_key.csv`, blind and in random order. Reported: AUC and Spearman correlation between novelty and the label, per bank. If the AUC is below 0.7 in either bank, or differs between banks by more than 0.1, P2-2 and E1 are reported as not interpretable, because the novelty score would not measure the same thing in both banks.

## Tests (pytest)

Added to `tests/`: the reference pool of a call contains only sentences of the same bank from strictly earlier calls; every reference sample has exactly R sentences; operator lines and sentences under four words are excluded; masking is applied before embedding; the target set is 2023-Q2 to 2024-Q4.

## Outputs

Computation in `analysis/phase2_novelty.py` (embeddings and novelty) and `analysis/phase2_inference.py` (tests, robustness, exploratory analyses, register), outputs in `notebooks/roman/data/phase2/`, notebook `02_novelty_drift.ipynb`.

## Amendment 2026-09-23 (after seeing the results): E6, sections weighted equally

Fixed after the results of P2-2 and E2 were seen, and therefore exploratory. P2-2 is not changed.

E2 showed that management novelty is much lower in prepared remarks than in the Q&A for both banks (JPMorgan about 0.25 against 0.48), and that the share of Q&A sentences in the management total varies strongly between JPMorgan calls. The call mean of P2-2 therefore mixes content with the mix of sections. E6 recomputes the call value as the unweighted mean of two numbers, the mean novelty of management prepared-remark sentences and the mean novelty of management Q&A sentences, with the primary embeddings, reference and sampling. The slope difference (as P2-2) and the level difference (as E1) are tested with the same exact permutation over the 14 target calls (3,432 splits), two-sided, and reported with their effect sizes. E6 is not entered in the register.
