```python
def build_exchange_texts(qa_exchanges: pd.DataFrame) -> pd.DataFrame:
    """
    Input:  qa_exchanges (from build_qa_exchanges)
    Output: a NEW DataFrame, one row per substantive exchange, with the
    analyst's question text concatenated into a single `question_text` field.
    Filler exchanges are dropped.
    """
    df = qa_exchanges[~qa_exchanges["is_filler"]].copy()
    df = df[df["speaker_role"] == "analyst"]

    exchange_texts = (
        df.sort_values(CALL_KEY + ["utterance_id"])
        .groupby(CALL_KEY + ["qa_exchange_id"])["text"]
        .apply(lambda texts: " ".join(texts))
        .rename("question_text")
        .reset_index()
    )
    return exchange_texts
```



```python
def _speaker_name_stopwords(structured_utterances: pd.DataFrame) -> list:
    """
    Analysts and management constantly address each other by first name
    ("Thanks, Jeremy", "Hey, Betsy") — found by inspecting the first topic
    model fit, where several "topics" turned out to just be a first name.
    """
    first_names = structured_utterances["speaker_name"].dropna().str.split().str[0].str.lower()
    return sorted(first_names.unique())
```

A NEW DataFrame, one row per substantive exchange, with the

analyst's question text concatenated into a single `question_text` field.

Filler exchanges are dropped here:



```python
exchange_texts = build_exchange_texts(qa_exchanges)
```

feed this  to your Topic model and do whatever else you need to do;  the speaker name already filtered out
