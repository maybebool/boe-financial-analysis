"""Phase 3j: the reading result, one row per unit and distinct passage.

Run from the repository root, after `phase3j_read.py hits`: python notebooks/roman/analysis/phase3j_reading.py
Writes reading_3j.csv to notebooks/roman/data/phase3j/, the input of `phase3j_read.py classify`.

The passages were read sentence by sentence (every sentence with a search term or a forward-looking word). The
forward-looking sentences on the quantity of a unit are listed in NOTED with their class. No other passage states
a target or plan for the quantity of its unit; those passages get one of the three classes that do not count,
assigned by the wording rule in `fallback()`, which only sorts them for the tables.
"""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "notebooks" / "roman" / "data" / "phase3j"

# (units, text that identifies the sentence, class, quote, conversion, comment)
NOTED = [
    (("T30",), "expected to be broadly offset by accretion-to-par effects of approximately USD 12bn",
     "same target, another unit",
     "Cumulative integration-related expenses are expected to be broadly offset by accretion-to-par effects of "
     "approximately USD 12bn",
     "12 / 13 = 0.92, inside the tolerance of 10%; indirect form: the total is equated with the accretion effects",
     "Known since phase 3b as the indirect order of magnitude in the 2023-Q2 report; published before the call "
     "figure of around 13bn (2023-Q4) and outside the tolerance for the raised figure of around 14bn (12 / 14 = 0.86)."),
    (("T30",), "of integration-related expenses", "other", "", "",
     "Forward-looking, but the amount of the next quarter, not the total (as in phase 3b)."),
    (("T30",), "Integration-related expenses are expected to be around", "other", "", "",
     "Forward-looking, but the amount of the next quarter, not the total (as in phase 3b)."),
    (("T30",), "integration-related expenses are expected to be around", "other", "", "",
     "Forward-looking, but the amount of the next quarter, not the total (as in phase 3b)."),
    (("T27", "T16"), "About half of these RWA are expected to run-off by the end of 2026", "other",
     "About half of these RWA are expected to run-off by the end of 2026", "",
     "Forward-looking on NCL RWA excluding operational risk (about half of USD 55bn), but for the end of 2026, "
     "not for the deadline of T27 (end of 2024), and not on operational risk RWA (T16)."),
    (("T27", "T25"), "representing around 5% of Group RWA at the end of 2026", "other",
     "with the remaining portfolio there representing around 5% of Group RWA at the end of 2026", "",
     "Forward-looking on total NCL RWA at the end of 2026 (the call target T26), another period than T27."),
    (("T27", "T25"), "share of around 5% of Group RWA", "other", "", "",
     "Target for total NCL RWA at the end of 2026, another period than T27 and no figure for the capital release."),
    (("T27", "T25"), "share of below 5% of Group RWA", "other", "", "",
     "Target for total NCL RWA at the end of 2026, another period than T27 and no figure for the capital release."),
    (("T27",), "around USD 29bn by the end of 2025 and around USD 22bn by the end of 2026", "other",
     "aim to reduce Non-core and Legacy RWA to around USD 29bn by the end of 2025 and around USD 22bn by the end of "
     "2026", "",
     "New ambition for total NCL RWA after the deadline of T27; published with the 2024-Q4 results."),
    (("T25", "T16", "F12"), "freeing up capital for the UBS Group", "other",
     "freeing up capital for the UBS Group", "",
     "The NCL key priority, forward-looking without a figure: the class B counterpart already recorded in phase 3d."),
    (("T25",), "capital released from the unwinding of the Non", "other", "", "",
     "Forward-looking without a figure: the class B counterpart of T25 already recorded in phase 3d."),
    (("T16",), "decrease in operation al risk RWA to USD 138bn from USD 145bn", "other", "", "",
     "Forward-looking on the operational risk RWA of the Group under the final Basel III standards, not of NCL."),
    (("F12",), "low single-digit percentage increase", "other", "", "",
     "Forward-looking on the effect of the final Basel III standards on the LRD, not on the reduction of the call."),
    (("F12",), "leverage ratio denominator by around USD 1.7bn", "other", "", "",
     "Effect of one transaction on the LRD, not the reduction of the call."),
]
RESULT = re.compile(r"\b(increased|decreased|remained|unchanged|was|were|amounted|totaled|reflecting|driven by|"
                    r"compared with|as of \d|issued on|redeem(ed)?|achieved|reduced)\b", re.I)
REQUIREMENT = re.compile(r"\b(requirements?|add-ons?|eligible|defined as|consists of|methodology|approach|"
                         r"Terms and Conditions|floored|phase-in|sensitivit|depreciation|appreciation)\b", re.I)


def fallback(text):
    """Sort a passage without a target for its unit into one of the classes that do not count."""
    n_req, n_res = len(REQUIREMENT.findall(text)), len(RESULT.findall(text))
    if n_req > n_res:
        return "definition or requirement"
    return "result" if n_res else "other"


def main():
    p = pd.read_csv(OUT / "passages.csv", keep_default_na=False).drop_duplicates(["unit", "text_id"])
    rows, used = [], set()
    for r in p.itertuples():
        row = {"unit": r.unit, "text_id": r.text_id, "class": fallback(r.text), "forward_looking": "no", "quote": "",
               "conversion": "", "comment": ""}
        for i, (units, marker, cls, quote, conv, comment) in enumerate(NOTED):
            if r.unit in units and marker in r.text:
                keep_quote = quote if quote and quote in r.text else ""
                row.update({"class": cls, "forward_looking": "yes", "quote": keep_quote, "conversion": conv,
                            "comment": comment})
                used.add(i)
                break
        rows.append(row)
    unused = [NOTED[i][1] for i in range(len(NOTED)) if i not in used]
    if unused:
        raise SystemExit(f"noted sentences not found in any passage: {unused}")
    d = pd.DataFrame(rows)
    counted = d[d["class"].str.startswith("same target")]
    if (counted.quote == "").any():
        raise SystemExit("a counted passage has no verbatim quote")
    d.to_csv(OUT / "reading_3j.csv", index=False)
    print(d.groupby(["unit", "class"]).size().unstack(fill_value=0).to_string())
    print(d[d.forward_looking == "yes"].groupby(["unit", "class"]).size())


if __name__ == "__main__":
    main()
