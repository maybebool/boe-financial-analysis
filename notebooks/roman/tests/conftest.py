import os, sys, warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
os.chdir(ROOT)  # the scripts read the release with a path relative to the repository root
sys.path.insert(0, str(ROOT / "notebooks" / "roman"))
sys.path.insert(0, str(ROOT / "notebooks" / "roman" / "analysis"))
warnings.filterwarnings("ignore", message="Unknown solver options")
