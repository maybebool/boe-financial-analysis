# BoE Employer Project: submission package

NLP analysis of bank earnings calls (UBS and JPMorgan, 2022-Q1 to 2025-Q4) for the
Bank of England's RegTech, Data and Innovation team. This package holds the
notebooks, the shared code and the data they read, so that everything runs on a
local machine without Google Drive.

## Contents

| Path | What it is |
|---|---|
| `requirements.txt` | pinned packages |
| `src/` | shared loading code and the data preparation pipeline |
| `notebooks/env_cell.py` | environment check used by the setup cell of every notebook |
| `notebooks/00_data_preparation/00_upload_and_clean_csv.ipynb` | data preparation: exploration of the export, structuring pipeline and comparison of its output with the supplied structured files |
| `notebooks/01_sentiment_classification/sentiment_classification.ipynb` | sentiment and emotion classification, topics of the classified sentences |
| `notebooks/02_topic_modelling/topic_modelling.ipynb` | topic models, themes and semantic drift |
| `notebooks/03_analyst_question_topics/analyst_question_topics.ipynb` | analyst question topics and deal attention |
| `notebooks/04_llm_risk_signals/llm_risk_signals.ipynb` | LLM analysis of merger-related Q&A |
| `notebooks/05_call_only_targets/` | figures stated only in the calls: five notebooks, `README.md` with the findings, helper module and exports |
| `data/results/2026-09-30/` | data export of 30 September 2026 and the structured files derived from it |
| `data/call_only_targets/` | result files read by the notebooks of section 05 |
| `data/reports/` | UBS reports used for the verification of quotes in section 05 |
| `data/sentiment_classification_output_UBS.csv`, `data/sentiment_classification_output_JPM.csv` | sentence labels written by the sentiment notebook |

## Setup

1. Python 3.13.
2. Create a fresh environment and install the pinned packages:
   `pip install -r requirements.txt`
3. Open the notebooks from this folder in Jupyter, VS Code or PyCharm and run them
   locally; for Google Colab see the section below. The setup cell of every
   notebook finds this folder by looking for `src/loading.py` and
   `requirements.txt` and reads all data from `data/`.

## Order

0. `00_upload_and_clean_csv.ipynb` (optional): rebuilds the structured files and
   checks them against the supplied files. The other notebooks read the supplied
   files, so this step can be skipped.
1. `sentiment_classification.ipynb`, once with `bank_name = 'UBS'` and once with
   `bank_name = 'JPM'` (the cell under "Choose Bank"). Each run writes
   `data/sentiment_classification_output_<bank>.csv`. Both files are already
   included, so this step can be skipped.
2. `topic_modelling.ipynb`, which reads the two label files in section 6, and
   `analyst_question_topics.ipynb`.
3. `llm_risk_signals.ipynb` does not depend on the other notebooks and
   can run at any time.
4. `notebooks/05_call_only_targets/`: `00_get_reports.ipynb` (optional), then
   `01_call_targets.ipynb` to `04_reports_2025_2026.ipynb` in the order of their
   numbers.

## Requirements at run time

- Internet access on the first run: the models are downloaded from the Hugging
  Face Hub and the sentiment notebook downloads NLTK resources.
- An NVIDIA GPU with CUDA for the model part of `llm_risk_signals.ipynb`
  (from the cell "SWITCH TO GPU" onwards). The cells before it run on a CPU. All
  other notebooks run on a CPU; a GPU only makes them faster.

## Running in Google Colab

- Upload the unzipped folder `final` to the top level of My Drive (path
  `My Drive/final`) and open a notebook from there with Google Colaboratory.
- The notebooks use only this folder: code, pinned packages and data are read
  from `My Drive/final`, and no GitHub access is needed.
- The setup cell installs the pinned packages. If it reports that packages
  changed, use Runtime, Restart session once and run the notebook again from the
  setup cell.
- `llm_risk_signals.ipynb` (notebook 04) runs its first part on a CPU runtime and
  switches to a GPU runtime at the cell marked SWITCH TO GPU; the setup is
  repeated in the cell after each runtime switch.

In a local run the setup cell mounts nothing and installs nothing.

## Section 00: data preparation

`notebooks/00_data_preparation/00_upload_and_clean_csv.ipynb` documents how the
structured files were built. It loads the team export in `data/results/2026-09-30/`
(`all_sentences.csv`, `all_utterances.csv`, `all_metrics.csv`), explores it and runs
the structuring pipeline in `src/utils.py`; `using-output-file.md` next to it
describes the output files.

- The notebook rebuilds `structured_sentences.csv`, `structured_utterances.csv` and
  `qa_exchanges_utterance_level.csv` and writes them to `data/derived/2026-09-30/`.
  Its last cell compares them by SHA-256 with the supplied files of the same name
  in `data/results/2026-09-30/` and fails if one differs.
- The other notebooks read the supplied files in `data/results/2026-09-30/`, not
  the rebuilt ones. Section 00 is therefore optional and can run at any time.
- No internet access and no GPU are needed; the notebook runs in a few seconds.

## Section 05: figures stated only in the calls

`notebooks/05_call_only_targets/` compares the quantified targets of the UBS calls
with the UBS reports. Start with its `README.md`, which states the findings and
the rules fixed in advance.

- Order: `00_get_reports.ipynb` (optional), then `01_call_targets.ipynb` to
  `04_reports_2025_2026.ipynb` in the order of their numbers. The section does not
  depend on sections 01 to 04.
- Data: `data/results/2026-09-30/`, `data/call_only_targets/` and the report files
  under `data/reports/`. With the reports present, every quote is verified
  against its page; without them the notebooks show the delivered results and
  state that this verification was skipped.
- Internet access is needed only for `00_get_reports.ipynb`, and only when report
  files are missing: it fetches them from EDGAR and requires the environment
  variable `SEC_USER_AGENT`.
- No GPU is needed; the five notebooks run in under a minute.

## Note on section 6 of `topic_modelling.ipynb`

The label files in `data/` are the output of version 3 of the sentiment notebook.
The saved outputs of section 6 in `topic_modelling.ipynb` were produced with the labels
of an earlier version and are being updated to the version 3 labels. Until then,
a fresh run of section 6 gives values that differ from the saved outputs.

## Data

The files under `data/` contain transcript text of the banks' earnings calls. The
text is the banks' copyright. It is included for the assessment of this project
only and must not be shared or published.

The folder `data/reports/` contains UBS quarterly, annual and Pillar 3 reports as
filed with the SEC (EDGAR). They are publicly available, remain the property of UBS
and are included only for the assessment, so that every quote can be checked
offline.
