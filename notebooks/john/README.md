## Module Reference


All Stage 2 structuring logic lives in `utils` as a set of pure functions: each takes a DataFrame in and returns a new one, so any step can be re-run, tested, or imported independently.


| Function                                                           | Input --> Output                                     | Purpose                                                                                                                                                  |
| ------------------------------------------------------------------ | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `load_raw_data()`                                                  | -> `(raw_sentences, raw_utterances, raw_metrics)` | Reads the three raw Stage 1 CSVs via `loading.load()`                                                                                                    |
| `build_structured_utterances(raw_utterances)`                      | raw -> structured                                   | Adds a stable per-call `utterance_id`; tags `is_routine_earnings` (flags non-routine calls like the JPM 2023-Q2 event call, without dropping them)       |
| `_fix_contractions(text)`                                          | text -> text                                        | Repairs the `all_sentences.csv` tokenisation bug (`"do not"` -> `"donot"`) via `CONTRACTION_FIX_MAP`                                                      |
| `build_structured_sentences(raw_sentences, structured_utterances)` | raw + structured -> structured                      | Links sentences to their parent utterance; applies `_fix_contractions`                                                                                   |
| `build_qa_exchanges(structured_utterances)`                        | structured -> Q&A-only subset                       | Groups consecutive analyst turns into exchanges (handles back-to-back different analysts correctly); flags `is_filler`                                   |
| `clean_boilerplate(text)`                                          | text -> text                                        | Strips operator/call-mechanics phrases (`BOILERPLATE_PHRASES`) from text used for topic modelling, without affecting the underlying `is_filler` decision |
| `run_pipeline()`                                                   | — -> dict of all 3 DataFrames                     | Orchestrates the full Stage 2 pass end-to-end                                                                                                            |



Also exported: CALL_KEY (the ["bank", "quarter", "call_type", "call_date"] key every groupby/ merge in this project uses to stay within a single call), CONTRACTION_FIX_MAP, FILLER_PHRASES / BOILERPLATE_PHRASES.

#### Running utils.py

Every notebook needs the project root on sys.path before importing src, since Jupyter sets the working directory to wherever the notebook file lives, not the project root. Put this in the first Setup cell of every notebook:

```
import sys
import pathlib


def find_project_root(marker: str = "src") -> pathlib.Path:
    path = pathlib.Path.cwd()
    for parent in [path, *path.parents]:
        if (parent / marker).is_dir():
            return parent
    raise RuntimeError(f"Could not find project root (looking for '{marker}') above {path}")


project_root = find_project_root()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

```

In the next cell, then you can import `util` from `src`

```
from src import utils

data = utils.run_pipeline()

```

### From the command line

`python -m src.utils`

#### Notebooks

`00_upload_and_clean_csv.ipynb`

This Notebook, contains Stage 2 + Stage 3. It loads the raw CSVs, checks the upload worked, runs diagnostic EDA on the raw data (coverage, document structure, volume, text quality, including the sentence/utterance reconstruction diff that surfaced the contraction bug), builds the Stage 2 structuring pipeline, then runs a confirmatory Stage 3 pass on the clean structured output. Produces structured_utterances.csv, structured_sentences.csv, qa_exchanges_utterance_level.csv.

### Design decisions and fixes along the way

- `is_routine_earnings` flag, not deletion, the JPM 2023-Q2 event call (First Republic acquisition) is genuine coverage; it's tagged so it can be excluded from quarter-over-quarter comparisons rather than silently pooled in or dropped.
- Contraction bug found by reconstruction diff, sentences reconstructed from structured_sentences were diffed word-by-word against structured_utterances' own text field, which is what surfaced the systematic "do not" -> "donot" pattern.
- Q&A exchange grouping handles back-to-back different analysts, a naive "new exchange when speaker_role becomes analyst" rule merges two unrelated questions when one analyst's closing remark is immediately followed by a different analyst; the fix also checks speaker_name.
- `is_filler` combines two independent checks: no management reply + short text, or mostly-scripted language (greetings, operator hand-offs, sign-offs) detected via FILLER_PHRASES, since greetings usually do get a short reply and so evade the first check alone.
- `clean_boilerplate` is separate from `is_filler`: filler decides whether to drop a whole exchange; boilerplate-cleaning strips scripted language out of otherwise-substantive exchanges before the performing topic modelling.