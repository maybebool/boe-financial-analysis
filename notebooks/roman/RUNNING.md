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
    python notebooks/roman/analysis/phase1_validation.py  # after labelling: precision, miss share, kappa, gate
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

## Phase 3b, call against quarterly report (descriptive)

Reads the report files in `notebooks/roman/data/reports/` (16 quarterly reports and the UBS annual reports 2023 and 2024; never modified) and the phase 3 statements.

    python notebooks/roman/analysis/phase3b_reports.py   # text reconstruction, checks, retrieval
    python notebooks/roman/analysis/phase3b_compare.py   # comparison table, every quote verified against its source
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03b_call_vs_report.ipynb

Plan: `notebooks/roman/plans/phase_3b.md`.

## Phase 3c, call figures in the reports (descriptive)

    python notebooks/roman/analysis/phase3c_counterparts.py   # classes A/B/C, bootstrap, sensitivities, labelling sample (GPU)
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03c_call_figures_in_reports.ipynb

Plan: `notebooks/roman/plans/phase_3c.md`.

## Phase 3d, counterparts by targeted search and reading (descriptive, exploratory)

    python notebooks/roman/analysis/phase3d_terms.py    # units and round-1 search terms (only before the first search)
    python notebooks/roman/analysis/phase3d_search.py   # search all reports up to end-2024, hash log in run_log.json
    python notebooks/roman/analysis/phase3d_read.py     # reading result, quotes verified, counts
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03d_counterparts_read.ipynb

`phase3d_terms.py` must not be rerun after the first search: it would overwrite the appended round-2 terms. Plan: `notebooks/roman/plans/phase_3d.md`. Table for review: `notebooks/roman/data/phase3d/counterparts_read.csv`.

### Repaired text reconstruction (hyphen fix of 2026-09-23)

    python notebooks/roman/analysis/phase3b_reports.py --repaired   # writes notebooks/roman/data/phase3b_repaired/
    python notebooks/roman/analysis/phase3d_search.py --repaired    # same terms, writes notebooks/roman/data/phase3d/repaired/

The read tables (`phase3b/comparison.csv`, `phase3d/counterparts_read.csv`) are based on the original reconstruction and are not regenerated by these runs.

## Phase 3e, disclosure channel (descriptive)

    python notebooks/roman/analysis/phase3e_terms.py     # check terms for the independent check, written before any search
    python notebooks/roman/analysis/phase3e_channel.py   # mentions, first mentions, call-first units
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03e_disclosure_channel.ipynb

Plan: `notebooks/roman/plans/phase_3e.md`.

## Phase 3f, Pillar 3 reports (descriptive)

    python notebooks/roman/analysis/phase3f_pillar3.py   # check files first, then reconstruction and search with phase 3d terms
    python notebooks/roman/analysis/phase3f_read.py      # reading result, quotes verified
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03f_pillar3.ipynb

Plan: `notebooks/roman/plans/phase_3f.md`. The 2024-Q2 Pillar 3 report is added later with the same terms.

## Phase 3g, FLS models against the phase 3 rules (descriptive)

    python notebooks/roman/analysis/phase3g_fls.py                  # FinBERT-FLS and FLS-RoBERTa (GPU), cross-tables, set S, blind spot check
    python notebooks/roman/analysis/phase3g_read.py terms           # reading of S, new units, search terms and their hash
    python notebooks/roman/analysis/phase3g_read.py search          # UBS quarterly and annual reports, windows W1 and ALL
    python notebooks/roman/analysis/phase3g_read.py pillar3 F11 F12 F22   # new UBS targets of class C in the Pillar 3 reports
    python notebooks/roman/analysis/phase3g_read.py classify        # classes with verified quotes, updated basis
    python notebooks/roman/analysis/phase3g_read.py checkfiles      # check files for the independent check
    python notebooks/roman/analysis/phase3g_read.py spotcheck       # after the blind labels: comparison with the reading of S
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03g_fls_models.ipynb

Plan: `notebooks/roman/plans/phase_3g.md`. Rerunning `terms` rewrites the hash in `run_log.json`; the search terms are then those in `phase3g_read.py`. The blind spot check is in `data/labelling/phase3g_spotcheck.csv` (key in `data/phase3g/spotcheck_key.csv`).

## Amendment to 3f and 3g, Pillar 3 report as of 30 June 2024

    python notebooks/roman/analysis/pillar3_2024q2.py   # T16, T25, T27, T32, T33, F11, F12 in UBS_2024-Q2_pillar3.htm; output in data/phase3f/pillar3_2024q2/ and data/phase3g/pillar3_2024q2/

## Audit of the independent checks and recheck files (2026-09-26)

    python notebooks/roman/analysis/check_display_audit.py   # genuine hits not shown by the first check tool; data/phase3h/display_audit.csv
    python notebooks/roman/analysis/recheck_units.py         # data/phase3g/check_units_recheck.json, data/phase3e/check_units_recheck.json

## Phase 3h, reports of 2025 and 2026 (descriptive)

    python notebooks/roman/analysis/phase3h_text.py     # text export (shared module report_text.py) and manifest.csv
    python notebooks/roman/analysis/phase3h_terms.py    # a_terms.csv, outcome_terms.csv, check_units_a/b.json with pipeline_hits, deviations.csv
    python notebooks/roman/analysis/phase3h_search.py   # hits_a.csv, hits_b.csv; refuses while the manifest is incomplete
    python -m pytest -q notebooks/roman/tests

Plan: `notebooks/roman/plans/phase_3h.md`. Accession and source URL come from `data/phase3h/sources.csv` (entered manually).
    python notebooks/roman/analysis/phase3h_read.py     # classes_a.csv, outcomes_b.csv, units_3h.csv, quotes.csv (quotes verified)
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03h_reports_2025_2026.ipynb

## Phase 3i, control run on the export of 2026-09-30 (descriptive)

Reads the old release `data/results/2026-09-23/` and the new export in `~/projects/earnings-call-nlp-pipeline/exports/2026-09-30/` (checked against `notebooks/final/data/results/2026-09-30/`); `RELEASE_DIR` is not changed.

    python notebooks/roman/analysis/phase3i_check.py   # export comparison, 39 source statements, rules and FinBERT-FLS on the new export (GPU)
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03i_export_check.ipynb

Plan: `notebooks/roman/plans/phase_3i.md`. Outputs in `notebooks/roman/data/phase3i/` with `SHA256SUMS`.

## Phase 3j, equivalent forms of the call-only figures (descriptive)

    python notebooks/roman/analysis/phase3j_terms.py                 # forms.csv, check_units_3j.json (before the search)
    cd notebooks/roman/data/phase3j && CHECK_MAX_HITS=100000 python -u ../phase3h/roman_check/check_terms.py --units check_units_3j.json > check_hits_3j.txt   # about 11 minutes
    python notebooks/roman/analysis/phase3j_read.py hits             # hits.csv, passages.csv; checks the counts against the tool output (about 11 minutes)
    python notebooks/roman/analysis/phase3j_reading.py               # reading_3j.csv: the reading result per passage
    python notebooks/roman/analysis/phase3j_read.py classify         # read.csv, summary.csv, SHA256SUMS (quotes verified, pages added)
    python -m pytest -q notebooks/roman/tests
    jupyter nbconvert --to notebook --execute --inplace notebooks/roman/03j_equivalent_forms.ipynb

Plan: `notebooks/roman/plans/phase_3j.md`. `phase3j_terms.py` must not be rerun after the search without rerunning the tool.
