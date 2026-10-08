# Using the Output Files: Practical Guide
## What this pipeline is and isn't


This document explains what the pipeline does and what each output files give you. 


## How to run it

Everything is in utils.py. The three source CSVs (all_sentences.csv, all_utterances.csv, all_metrics.csv) are read from disk in exactly one place: load_raw_data(). Every other function takes a DataFrame in and returns a new one; the raw data is never modified in place.

### Usage from notebook ( this assumes you've setup up your notebook environment as instructed by Roman)

```
from src import utils
data = utils.run_pipeline()
data["structured_sentence"].head()
```

OR from command line

```
python -m src.utils
```

This prints a short data-quality summary and writes every output file listed below to the current directory.


OR if you don't want be to be bothered by all of that:

pick up from the shared folder: `https://drive.google.com/drive/folders/17wErUoAVfs1LiVZcXVVR6s_DDhEkZ3iv?usp=drive_link`


## First: the three files

| File | One row is... | Use it when you want to... |
| --- | --- | --- |
| **structured_sentences.csv** | One sentence someone said | Read exact wording of individual statements |
| **structured_utterances.csv**| One person's full turn speaking (could be several sentences) | Get a steadier, less noisy tone reading, one sentence alone can be misleading |
| **exchanges_utterance_level.csv** | One analyst's question plus management's full reply | See what subject was being discussed, and read a question-and-answer in full |

A simple rule of thumb: go to the sentence file to find something specific and quote it; go to the exchange file to understand what the conversation was about.

## A short glossary (so the column names make sense)

- **`bank` / `quarter`** : which bank and which quarter's results call this row is from.
- **`speaker_role`** : analyst` (asking questions), `management` (answering), or `operator` (the call host saying things like "next question is from...").
- **`is_filler` / `is_filler_sentence`** : `True` means this row is just small talk
  ("Thank you.", "Good morning.") with no real content. **Always filter these out first** , otherwise your counts will include greetings and "thank yous" as if they were real
  questions or answers.


### Outputs & sample Usage

Every file shares a common set of "location" columns: bank, quarter, call_type, call_date, so any two files can be joined on those plus whatever unit they share (utterance_id or qa_exchange_id).


 #### structured_utterances.csv: one row per speaker turn

The cleaned version of the source utterance data, with a per-call `utterance_id` added, and `is_routine_earnings` flagging the one non-routine call in the dataset (JPM's 2023-Q2 First Republic acquisition call), so it can be excluded from routine quarter-over-quarter comparisons without deleting it.

**Usage Example**

Wants to know how call length or Q&A volume trends over time, without touching sentence-level detail:
```
u = data["structured_utterances"]
u[u.section == "qa"].groupby(["bank", "quarter"]).size()   # Q&A turns per call

```


#### structured_sentences.csv: one row per sentence

The finest-grained text unit. sentence is the cleaned text; sentence_raw keeps whatever the source data originally said, for audit. As of the current source data, these two columns are identical for every row, the contraction-mangling bug they used to differ on has been fixed upstream (verified: 0 of 19,092 sentences differ). The fix function is kept in the pipeline as a no-op safety net in case the bug ever resurfaces in a future data drop (if ever there i sone), so it's safe to keep reading from sentence either way. `is_filler_sentence` flags courtesy/operator phrases ("Thank you.", "Please go ahead.") that carry no analytical content.


**Usage Example**

Wants every real sentence management said in Q&A, with filler stripped out:
```
s = data["structured_sentences"]
real_mgmt_qa = s.query("speaker_role == 'management' and not is_filler_sentence")

```
  
#### qa_exchanges_utterance_level.csv — Q&A turns grouped into one analyst "ask"

Adds qa_exchange_id (one id per analyst question + the management reply that follows) and is_filler (flags exchanges that are pure small talk or operator handoff, with no real question in them, kept for audit, not deleted).

**Usage Example**

anyone building a question-and-answer viewer for a specific call:

```
qa = data["qa_exchanges"]
one_call = qa.query("bank == 'JPM' and quarter == '2024-Q1' and not is_filler")
for exchange_id, exchange in one_call.groupby("qa_exchange_id"):
    print(exchange[["speaker_role", "speaker_name", "text"]])
```


## Known Limitations
- sentence_raw vs sentence: identical for every row in the current source data; the contraction-mangling bug ("don't" --> "donot") that used to make them differ has been fixed upstream. The fix function stays in the pipeline as a defensive no-op; if a future data drop reintroduces the bug, sentence_raw will start differing again and the fix will silently kick back in.
-  JPM has far more analyst coverage than UBS (avg. ~39 Q&A exchanges per call vs. ~25), any cross-bank comparison should normalise by volume, not use raw counts.



### One rule worth repeating

Always check is_filler / is_filler_sentence is excluded before counting anything. Every example above either already filters it out or works with text directly, but if you're building your own count or pivot table from scratch, forgetting this is the single most common way to get a misleading number: "Thank you." and "Good morning." will get counted as if they were real questions or answers otherwise.