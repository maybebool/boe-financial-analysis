# How we work

Two ways to work: in Colab, where nothing has to be installed, or locally with
your own Python. Colab is the default. Both read the same exports and produce
the same numbers.

## One-time setup

1. Create a GitHub account if you do not have one, and accept Roman's invitation
   to the repository.
2. Accept the invitation to the shared Drive folder `boe-data`.
3. In Drive, open **Shared with me**, right click `boe-data`, choose
   **Organise**, **Add shortcut**, and put the shortcut in **My Drive**.
   Without that shortcut Colab cannot see the folder and every notebook stops
   with a `[CONTRACT] folder not found` error.

That is all for Colab. For local work see the section further down.

## Starting a notebook

Open [Google Colab](https://colab.research.google.com), create a new notebook,
and copy the setup cell below to the very top. Change `NAME` to your own name
and run it. It clones the project, installs what is missing and checks that
everyone is on the same versions.

```python
# project setup — run first, do not edit except NAME
NAME = "inessa"  # <<< your name

import sys, subprocess, pathlib
IN_COLAB = "google.colab" in sys.modules
REPO = "boe-financial-analysis"

if IN_COLAB:
    from google.colab import drive
    drive.mount("/content/drive", force_remount=False)
    if not pathlib.Path(f"/content/{REPO}").exists():
        subprocess.run(["git", "clone", "-q",
                        f"https://github.com/maybebool/{REPO}.git",
                        f"/content/{REPO}"], check=True)
    ROOT = pathlib.Path(f"/content/{REPO}")
    DATA = pathlib.Path("/content/drive/MyDrive/boe-data")
else:
    ROOT = pathlib.Path.cwd()
    while not (ROOT / "requirements.txt").exists() and ROOT != ROOT.parent:
        ROOT = ROOT.parent
    DATA = ROOT / "data"

sys.path.insert(0, str(ROOT))
if IN_COLAB:
    subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin"], check=False)
    subprocess.run(["git", "-C", str(ROOT), "merge", "-q", "origin/main", "-m", "sync"],
                   check=False)
else:
    behind = subprocess.run(
        ["git", "-C", str(ROOT), "rev-list", "--count", "HEAD..origin/main"],
        capture_output=True, text=True).stdout.strip()
    if behind not in ("", "0"):
        print(f"note: your branch is {behind} commits behind origin/main. "
              f"Run 'git merge origin/main' when you are ready.")
        
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                str(ROOT / "requirements.txt")], check=True)

from notebooks.env_cell import verify, check_python
check_python()
try:
    verify(ROOT)
except RuntimeError as e:
    print(e)
    print("\n Runtime -> Restart session, then run this cell again.")
    raise

import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from src import loading

print(f"ok  python {sys.version.split()[0]}  pandas {pd.__version__}  data {DATA}")
```

If the cell stops with a version mismatch, use Runtime, Restart session, then run
the same cell again. That is normal and only happens once.

## Working locally

If you run the notebooks on your own machine instead of Colab, copy the export
folder from Drive into the repository, into `data/results/`. Nothing else
changes: the setup cell already points `DATA` at `<repo>/data` when it is not
running in Colab, and `loading` finds the export there.

Download `boe-data/results/2026-09-13` from Drive and put it here, so that the
paths read:

    <repo>/data/results/2026-09-13/all_utterances.csv
    <repo>/data/results/2026-09-13/all_sentences.csv
    <repo>/data/results/2026-09-13/all_metrics.csv
    <repo>/data/results/2026-09-13/UBS/...
    <repo>/data/results/2026-09-13/JPM/...

Check it with `print(loading.exports(DATA))`, which should list the date.

`data/` is in `.gitignore` and has to stay there. The CSV files contain the
transcripts word for word, this repository is public, and the transcripts are
copyrighted by the banks. Never commit anything out of `data/`, and never
remove the `.gitignore` entry.

When a new export is announced, download it as well. Old ones can stay, the
notebooks pin the date they were written against.

## Loading data

```python
EXPORT = "2026-09-13"  # pin the export this notebook was written against

utt = loading.load(DATA, "all_utterances.csv", EXPORT)
sent = loading.load(DATA, "all_sentences.csv", EXPORT)
met = loading.load(DATA, "all_metrics.csv", EXPORT)
```

These three files hold every bank. The column is called `bank`, so filter with
`utt[utt["bank"] == "UBS"]`.

The export covers UBS and JPMorgan, eight quarters each, 2023-Q1 to 2024-Q4.
JPMorgan has one extra call in 2023-Q2, on the First Republic acquisition. It is
included in the combined files and marked in the `call_type` column, which is
`earnings` for the quarterly calls and `event` for that one. Filter it out with
`utt[utt["call_type"] == "earnings"]` when a comparison needs one call per
quarter.

Single documents live in a folder per bank inside the same export:

```python
print(loading.firms(DATA, EXPORT))              # banks in this export
print(loading.files(DATA, EXPORT, "UBS"))       # file names for that bank

q1 = loading.load(DATA, "UBS_2023-Q1_call_utterances.csv", EXPORT, firm="UBS")
```

Run `print(loading.exports(DATA))` to see which export dates exist. Keep
`EXPORT` pinned to a date so the notebook gives the same numbers when you rerun
it later. Roman announces in Discord when a new export is there.

Read the `README.md` inside the export folder before you start comparing the two
banks. It lists what is not comparable between them, and there is more of that
than you would expect.

## Saving your work

Use the menu: **File, Save a copy in GitHub**. The first time, GitHub asks for
permission once — allow it.

In the dialog set four things:

- Repository: `maybebool/boe-financial-analysis`
- Branch: your own name
- File path: `notebooks/<yourname>/<filename>.ipynb` — type the full path.
  Colab suggests only the filename, which would drop your notebook in the wrong
  place.
- Commit message: one line on what you did

To reopen your work later: **File, Open notebook, GitHub tab**, enter
`maybebool/boe-financial-analysis`, pick your branch, pick your notebook.

When your work should go into the final report, open a pull request against
`main` on GitHub. Only Roman and John can merge.

## Rules

Work only in your own folder and on your own branch.

Analysis reads the CSV exports, never the source documents. Nobody in the team
opens a PDF or an HTML filing; the pipeline does that and hands over the result.

Never commit anything out of `data/`, and never commit a notebook with the source
text visible in its output. Before you commit, clear the outputs: in Colab under
Edit, Clear all outputs, locally in the notebook menu under Clear All Outputs.

Never run `git push --force`.

This repository is public. Everything you commit is visible to everyone. No
passwords, no private notes.

## Commit messages

One line, lower case, in the form `type(scope): description`.

- `feat(topics): add sentiment trend chart`
- `fix(loading): handle empty export`
- `docs(readme): clarify setup step`
- `refactor(plots): move helper into src`

Types we use: `feat`, `fix`, `docs`, `refactor`. Scope is the area you touched,
usually a folder or module name.