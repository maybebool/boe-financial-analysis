# Libraries used in `angelo_a3.ipynb`

Versions are those installed in the project's `.venv` (Python 3.13.15, the notebook's kernel), read on 2026-10-07.

## Third-party libraries

| Library | Version | Used for |
|---|---|---|
| numpy | 2.1.3 | arrays and numerics |
| pandas | 2.2.3 | data frames |
| matplotlib | 3.10.0 | charts (`pyplot`, `colors.LinearSegmentedColormap`) |
| scipy | 1.18.1 | `scipy.sparse` |
| scikit-learn | 1.6.1 | `CountVectorizer`, `ENGLISH_STOP_WORDS`, `adjusted_rand_score`, `adjusted_mutual_info_score`, `cohen_kappa_score`, `f1_score`, `StratifiedKFold` |
| torch | 2.14.0+cu126 | GPU/CPU check, model training |
| transformers | 5.16.1 | `get_linear_schedule_with_warmup` |
| sentence-transformers | 5.7.0 | `SentenceTransformer`, `losses`, `util.batch_to_device` |
| bertopic | 0.17.4 | `BERTopic`, `BaseDimensionalityReduction` |
| umap-learn | 0.5.12 | `UMAP` |
| hdbscan | 0.8.44 | `HDBSCAN` |

`tqdm` 4.70.1 is not imported directly. It shows up in the notebook output through a `notebook_tqdm` warning from sentence-transformers.

## Standard library (no version)

`gc`, `hashlib`, `itertools`, `pathlib`, `re`, `subprocess`, `sys`, `textwrap`, `time`

## Project modules

- `src.loading` (`src/loading.py`): uses pandas and pathlib.
- `notebooks.env_cell` (`notebooks/env_cell.py`): checks the installed versions against `requirements.txt`.

## Colab only

`google.colab` (`drive`) is imported only in the Colab branch of the setup cell. It is not installed locally.

## Compared with `requirements.txt`

- The pinned versions match what is installed.
- `torch` and `scipy` are not pinned. `torch` is left unpinned on purpose, and `scipy` comes in as a dependency of scikit-learn, UMAP and BERTopic. Their versions above come from the venv, not from `requirements.txt`.
- `requirements.txt` also pins `pyarrow` 18.1.0, `seaborn` 0.13.2, `spacy` 3.8.16 and `nltk` 3.9.1. The notebook does not import any of them. They are installed in the venv, probably for other notebooks in the repo.
