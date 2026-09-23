# Running the analysis

All commands run from the repository root in the conda environment `boe-group`. Extra packages are listed in `notebooks/roman/requirements-roman.txt`:

    pip install -r notebooks/roman/requirements-roman.txt

Input is the release set by `RELEASE_DIR` in `notebooks/roman/analysis/config.py`, currently `data/results/2026-09-23/` (read only). All outputs go to `notebooks/roman/data/`; the top-level `data/` folder is not written to.

## Phase 0, reproduce

    python notebooks/roman/contrast.py                     # year contrast, about 40 s
    python notebooks/roman/qa_pairs.py                     # writes notebooks/roman/data/qa_pairs.csv
    python notebooks/roman/analysis/phase0_reproduce.py    # writes notebooks/roman/data/phase0/
    python notebooks/roman/analysis/drift_reference.py     # drift reference, writes notebooks/roman/data/phase0/
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/00_reproduce.ipynb

Plan: `notebooks/roman/plans/phase_0.md`. The first run on the faulty release `2026-09-13` is kept in `notebooks/roman/data/phase0_release_2026-09-13/`. Test register: `notebooks/roman/plans/test_register.csv`.

## Phase 1, evasive answers

Needs a GPU for reasonable speed (about one minute on an RTX 4080). Models are loaded at the pinned revisions in `analysis/phase1_common.py`.

    python notebooks/roman/analysis/phase1_score.py       # segments, alignment, phrase list, NLI, relevance
    python notebooks/roman/analysis/phase1_inference.py   # P1-1, P1-2, robustness, E1 to E5, updates the register
    python notebooks/roman/analysis/phase1_labelling.py   # blind samples in notebooks/roman/data/labelling/
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/01_evasive_answers.ipynb

Plan: `notebooks/roman/plans/phase_1.md`. The run on the faulty release `2026-09-13` is kept in `notebooks/roman/data/phase1_faulty_release_2026-09-13/`, its superseded labelling samples in `notebooks/roman/data/labelling/superseded_release_2026-09-13/`.

## Phase 2, novelty and drift

    python notebooks/roman/analysis/phase2_novelty.py     # embeddings and sentence novelty (GPU, about 15 s)
    python notebooks/roman/analysis/phase2_inference.py   # P2-2, E1 to E6, robustness, updates the register
    python notebooks/roman/analysis/phase2_labelling.py   # blind novelty sample in notebooks/roman/data/labelling/
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/02_novelty_drift.ipynb

Plan: `notebooks/roman/plans/phase_2.md`.

## Phase 3, commitment tracking (descriptive)

    python notebooks/roman/analysis/phase3_extract.py   # candidates, metric groups, values, horizons
    python notebooks/roman/analysis/phase3_track.py     # threads, follow-ups, proposed statuses, labelling sample (GPU)
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03_commitments.ipynb

Plan: `notebooks/roman/plans/phase_3.md`. The table for review is `notebooks/roman/data/phase3/threads.csv`.
