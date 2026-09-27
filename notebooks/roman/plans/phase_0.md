# Phase 0: reproduce the starting point

Written 2026-09-23, before any computation of this phase.

**Question.** Do `contrast.py` and `qa_pairs.py` reproduce the numbers recorded in the working brief on release `data/results/2026-09-13/`, and is the environment able to run the local models needed in later phases?

**Hypothesis.** Both scripts are deterministic, so every recorded number is reproduced exactly (AUC and p to three decimals, counts exactly, rates to one decimal).

**Unit of analysis.** As in the original scripts: sentences (contrast), question/answer pairs and answer words (non-answers).

**Statistics checked.**

- `contrast.py`: n, leave-one-call-out AUC 2023 vs 2024 and exact permutation p over 70 call splits, for analyst Q&A and constant speaker, per bank.
- `qa_pairs.py`: number of pairs per bank, number of non-answer phrase hits, hits per 10,000 answer words per bank, binomial test of UBS hits against the UBS share of answer words.
- Drift: Spearman rho between call similarity and time lag for the constant speaker. No script for this exists, so a reconstruction is attempted with the masking of `contrast.py`.

**Tests.** None. Phase 0 has no primary test and adds nothing to the test register.

**Support.** All numbers match. **Null result.** Any mismatch is reported with the reproduced value and the likely cause; the recorded value is not used later unless it is reproduced.

**Known deviation.** `qa_pairs.py` wrote its output to `data/qa_pairs.csv`, outside the permitted folder. The output path is changed to `data/roman/qa_pairs.csv`; nothing else in the script is changed.

**Amendment 2026-09-23.** On request, all outputs are stored under `notebooks/roman/data/` instead of `data/roman/`; the top-level `data/` folder is not written to. This changes storage locations only, not the analysis.

**Amendment 2026-09-23.** The method behind the recorded drift numbers was supplied after the first run and is implemented in `analysis/drift_reference.py` (views and masking of `contrast.py`, one document per quarter, TF-IDF with min_df = 2, Spearman rho between lag and cosine similarity, one-sided p from 5000 permutations of the quarter order with seed 0). This is a reproduction of recorded numbers, not a new test.

**Amendment 2026-09-23 (corrected release).** Release `2026-09-13` had lost every `n't` in its sentence segmentation; the corrected release is `2026-09-23` (same sentences and keys, 359 sentences with restored contractions). `analysis/phase0_reproduce.py` and `analysis/drift_reference.py` are rerun unchanged on `2026-09-23`. The values on `2026-09-13` are kept in `notebooks/roman/data/phase0_release_2026-09-13/` and reported next to the new ones. The numbers recorded in the working brief were computed on the faulty release, so small deviations on the corrected release are expected and are reported, not adjusted.
