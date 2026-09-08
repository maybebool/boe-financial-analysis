# How we work

## One-time setup

1. Create a GitHub account if you do not have one, and accept Roman's invitation.
2. On GitHub go to Settings, Developer settings, Personal access tokens, and
   create a token with scope `repo` and an expiry date.
3. In Colab click the key icon on the left, add a secret named `GH_TOKEN` and
   paste the token. Add a second secret `HF_TOKEN` with a read token from
   huggingface.co if you plan to load models.
4. Accept access to the shared Drive folder `boe-data`.

## Setup cell — copy this to the top of every new notebook

```python
# project setup — run first, do not edit except NAME
NAME = "inessa" # <<< your name

import sys, subprocess, pathlib
IN_COLAB = "google.colab" in sys.modules

if IN_COLAB:
    from google.colab import drive, userdata
    drive.mount("/content/drive", force_remount=False)
    if not pathlib.Path("/content/boe-group").exists():
        _t = userdata.get("GH_TOKEN")
        subprocess.run(["git", "clone", "-q",
                        f"https://{_t}@github.com/YOUR-ORG/boe-group.git",
                        "/content/boe-group"], check=True)
    ROOT = pathlib.Path("/content/boe-group")
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
    print("\n>>> Runtime -> Restart session, then run this cell again.")
    raise

import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from src import loading

import torch
print(f"ok  python {sys.version.split()[0]}  pandas {pd.__version__}  "
      f"cuda {torch.cuda.is_available()}  data {DATA}")
```

## Loading data

```python
df = loading.load_topics(DATA)        # one row per topic, quarter and speaker role
st = loading.load_statements(DATA)    # one row per statement
mt = loading.load_metrics(DATA)       # the reported figures
```

These functions always pick the newest dated export. Roman announces in Discord
which export is current.

## Saving your work

In Colab use the menu: File, Save a copy in GitHub. Repository
`YOUR-ORG/boe-group`, branch your own name, path
`notebooks/<name>/<file>.ipynb`, type a commit message, save.

Then open a pull request against `main` on GitHub if the work should go into the
submission. Only Roman and John can merge.

## Rules

Work only in your own folder and only on your own branch.

Nobody parses PDFs. Analysis reads the CSV exports, never the source documents.

Never run `git push --force`.

This repository is public. Everything you commit is visible to everyone. No
passwords, no tokens, no private notes.
