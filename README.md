# BoE Employer Project

NLP analysis of earnings call Q&A transcripts from a G-SIB, for the Bank of
England's RegTech, Data and Innovation team. Question: does the call tell a
supervisor anything the published report does not?

## What is in here

- `src/` — shared code, one owner per file
- `notebooks/<name>/` — personal scratch folders, no shared editing
- `notebooks/final/` — the submission notebook, one owner
- `data/sample/` — tiny fixture so notebooks run without Drive
- `requirements.txt` — pinned to the Colab image, do not edit casually

Real data is not in this repo. Exports live in the shared Drive folder.

## Getting started

Colab users: see `TEAM.md`. Copy the setup cell into a new notebook and run it.

Local users:

```bash
git clone https://github.com/YOUR-ORG/boe-group.git
cd boe-group
conda create -n boe-group python=3.13
conda activate boe-group
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Two rules

Nobody parses PDFs. Analysis reads the CSV exports, never raw documents.

This repository is public. Anything you commit is visible to everyone.
