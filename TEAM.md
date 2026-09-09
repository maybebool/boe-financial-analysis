# How we work

You do not need to install anything. No Git, no Python, no tokens. Everything
runs in the browser.

## One-time setup

1. Create a GitHub account if you do not have one, and accept Roman's invitation
   to the repository.
2. Accept the invitation to the shared Drive folder `boe-data`.

That is all.

## Starting a notebook

Open [Google Colab](https://colab.research.google.com), create a new notebook,
and copy the setup cell below to the very top. Change `NAME` to your own name
and run it. It clones the project, installs what is missing and checks that
everyone is on the same versions.

```python
# project setup — run first, do not edit except NAME 
NAME = "inessa" # <<< your name

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
subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "origin"], check=False)
subprocess.run(["git", "-C", str(ROOT), "merge", "-q", "origin/main", "-m", "sync"],
               check=False)
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

## Loading data

```python
df = loading.load_topics(DATA)        # one row per topic, quarter and speaker role
st = loading.load_statements(DATA)    # one row per statement
mt = loading.load_metrics(DATA)       # the reported figures
```

These always pick the newest dated export from the Drive folder. Roman announces
in Discord which export is current.

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

Nobody parses PDFs. Analysis reads the CSV exports, never the source documents.

Never run `git push --force`.

This repository is public. Everything you commit is visible to everyone. No
passwords, no private notes.