# Phase 3j: equivalent forms of the call-only figures in the reports up to the end of 2024

Written 2026-10-09, before any search of this phase; revised the same day, still before any search, to add Roman's second reading of T68. Descriptive: no test, nothing enters the register. Release `data/results/2026-09-23/` (frozen); the phases 3 to 3i, their folders, `notebooks/roman/data/reports/`, `notebooks/roman/data/reports_2025_2026/` and both `roman_check` folders are not changed.

## Why this phase

Phase 3d searched each call figure in the unit of the call. T32 (going concern requirement up by around 180 basis points to 16.7%) was classed "mentioned without a figure", although the reports from 2024-Q1 give the same increase as "around USD 10bn" of tier 1 capital (`data/phase3h/corrections_v2.csv`). The terms were too narrow. This phase repeats the search for the remaining units with every equivalent form of the call figure.

## Transparency note

Before this plan was written, the following was already known from phases 3d to 3h and from the correction of phase 3h:

- the values of the table "Composition of Non-core and Legacy" (NCL operational risk RWA and total RWA per reporting date), which bear on T16 and T27;
- the sentences on the NCL capital release in the annual reports 2024 and 2025 (T25);
- the passages on the phase-in of the higher capital requirements, read for T32, which stand next to passages on AT1 and going concern capital (T33, F11).
- the going and gone concern table of the 2024-Q4 report (p. 41), from which the bases for the two readings of T68 are taken.

The conversion bases below were looked up for this plan in the key figures of the 2024 annual report (p. 32, p. 390) and in the call statements. No search with the terms of this phase has been run.

## Question

For each of the eight remaining call-only units (T33, T68, F11, F22, T16, T25, T27, F12) and for the integration-cost total (T30): does any UBS quarterly, annual or Pillar 3 report up to the end of 2024 state the target of the call in another unit or form?

## Reports

The 16 UBS files in `notebooks/roman/data/reports/`: the quarterly reports 2023-Q1 to 2024-Q4, the annual reports 2023 and 2024, and the Pillar 3 reports 2023-Q3 to 2024-Q4. All units are searched in all 16 files, also in reports published before the call.

## Conversion bases

| base | value | source |
|---|---|---|
| Group RWA, 31.12.2023 | USD 546.5bn | 2024 annual report, p. 32 (546,505) |
| Group RWA, 31.12.2024 | USD 498.5bn | 2024 annual report, p. 32 (498,538) |
| Group LRD, 31.12.2023 | USD 1,695.4bn | 2024 annual report, p. 32 (1,695,403) |
| Group LRD, 31.12.2024 | USD 1,519.5bn | 2024 annual report, p. 32 (1,519,477) |
| CET1 capital ratio assumed by management | around 14% | call 2023-Q4, statement 4697 |
| going concern ratio, 31.12.2023 | 17.0%, of which CET1 14.5% and AT1 2.5% | call 2023-Q4, statement 4791 |
| gone concern capital, 31.12.2024 | USD 98bn | call 2024-Q4, statement 6559 |
| eligible gone concern capital, 31.12.2024 | USD 97.7bn | 2024-Q4 report, p. 41 (97,655) |
| AT1 capital, 31.12.2024 | USD 16.4bn | 2024-Q4 report, p. 41 (16,372; CET1 71,367 and total going concern capital 87,739) |
| AT1 capital expected to stay at its current level through 2025 | | call 2024-Q4, statement 6558 |
| NCL operational risk RWA, 30.9.2023 | USD 30bn | call 2023-Q3, statement 4301 |
| Group operational risk RWA | USD 145bn | call 2023-Q3, statement 4299 |
| integration-related expenses to end-2023 | USD 4.5bn | call 2023-Q4, statement 4762 |
| USD per CHF, 31.12.2023 | 1.19 | 2024 annual report, p. 390 |

The bases are those at the date of the call. A report of another date may use another base. When a hit is read, the figure is converted back with the base at the reporting date of that report, and that base is recorded with its source.

## Units and equivalent forms

Each line gives a form, the calculation and the central value that is searched.

**T33**, call 2023-Q4: "we expect to issue up to 2 billion in AT1 in 2024."

- amount: USD 2bn;
- in Swiss francs: 2 / 1.19 = CHF 1.7bn;
- share of RWA: 2 / 546.5 = 0.37%, 37 basis points;
- share of LRD: 2 / 1,695.4 = 0.12%, 12 basis points;
- resulting stock: AT1 of 2.5% x 546.5 = 13.7bn at end-2023, plus 2 = 15.7bn;
- resulting AT1 ratio: 2.5% + 0.37% = 2.9%.

**T68**, call 2024-Q4: "we're targeting to bring down Group HoldCo to around 90 billion by the end of 2025." The call does not define "Group HoldCo". Two readings are searched, each with its own forms; a hit in either reading counts.

*Reading 1: the gone concern capital of UBS Group AG*, which the preceding statement gives as 98 billion (97.7 in the report).

- amount: USD 90bn;
- reduction: 98 - 90 = USD 8bn, or 8%;
- share of RWA: 90 / 498.5 = 18.1%;
- share of LRD: 90 / 1,519.5 = 5.9%.

*Reading 2: all funding raised through the holding company*, that is the gone concern capital plus the AT1 instruments issued by UBS Group AG: 97.7 + 16.4 = USD 114.0bn at 31.12.2024.

- amount: USD 90bn (as in reading 1);
- reduction: 114.0 - 90 = USD 24bn, or 21%;
- gone concern part, with AT1 held at its current level as the call states (statement 6558): 90 - 16.4 = USD 73.6bn, a reduction of 97.7 - 73.6 = USD 24bn;
- that gone concern part as a share of RWA: 73.6 / 498.5 = 14.8%; as a share of LRD: 73.6 / 1,519.5 = 4.8%.

Reading 2 leaves out holding company debt that counts neither as gone concern capital nor as AT1 (for example senior debt with less than one year to maturity); the reports up to the end of 2024 were not searched for such a total before this plan. If a report states the funding of UBS Group AG in another delimitation, the figure is converted with the corresponding total of that report and the delimitation is recorded with the hit.

**F11**, call 2023-Q4: "bringing the going concern capital ratio to around 18% while broadly maintaining our CET1 capital ratio at around 14%."

- ratio: 18%;
- increase: 18.0 - 17.0 = 1.0 percentage point, 100 basis points;
- AT1 ratio: 18 - 14 = 4% of RWA, an increase of 1.5 percentage points from 2.5%;
- amounts on RWA of 546.5: going concern capital 98.4bn, AT1 21.9bn, AT1 increase 8.2bn;
- leverage form: 98.4 / 1,695.4 = 5.8% of LRD.

**F22**, call 2024-Q4: "we expect to operate with an LCR below our 4Q24 level of 188%."

- ratio: 188% (188.4% in the key figures);
- any forward-looking statement that gives a level, a range or a target for the LCR or for high-quality liquid assets. No conversion base is fixed in advance, because the call gives only a direction; a figure on high-quality liquid assets is converted with the net cash outflows of the same report.

**T16**, call 2023-Q3: "we expect operational risk RWA in NCL to decrease to around 14 billion by the end of 2026."

- amount: USD 14bn;
- reduction: 30 - 14 = USD 16bn, or 53% ("by around half");
- share of Group operational risk RWA: 14 / 145 = 9.7%;
- share of Group RWA: 14 / 546.5 = 2.6%;
- CET1 capital equivalent of the reduction at 14%: 16 x 0.14 = USD 2.2bn.

**T25**, call 2023-Q4: "we expect our wind-down efforts to result in a capital release of over 6 billion by the end of 2026."

- amount: USD 6bn;
- RWA equivalent at a CET1 ratio of 14%: 6 / 0.14 = USD 43bn;
- effect on the Group CET1 ratio: 6 / 546.5 = 1.1 percentage points, 110 basis points;
- any forward-looking figure on the equity or capital attributed to NCL.

**T27**, call 2023-Q4: "By the end of 2024, we expect [...] credit and market risk risk-weighted assets to be substantially below 40 billion."

- amount: USD 40bn;
- total NCL RWA: 40 + 30 of operational risk = USD 70bn;
- share of Group RWA: 40 / 546.5 = 7.3%; total NCL 70 / 546.5 = 12.8%;
- reduction from the level of 31.12.2023 (74.0 - 30.0 = 44.0, table "Composition of Non-core and Legacy"): USD 4bn, or 9%.

**F12**, call 2023-Q4: "we expect to reduce LRD by over 100 billion at constant FX [...]" over the next three years.

- amount: USD 100bn;
- share: 100 / 1,695.4 = 5.9%;
- resulting level: 1,695.4 - 100 = USD 1,595bn ("below 1.6 trillion");
- capital equivalent at a leverage ratio requirement of 5.0%: USD 5bn; at the CET1 leverage requirement of 3.5%: USD 3.5bn (requirements as in the going concern table of the 2024 annual report, p. 163).

**T30**, call 2023-Q4: integration-related expenses "to total to around 13 billion by the end of 2026, including the 4 and a half billion incurred to date"; call 2024-Q4: "around 14 billion".

- amount: USD 13bn, USD 14bn;
- remaining at end-2023: 13 - 4.5 = USD 8.5bn; remaining at a later date: total less the cumulative expenses reported at that date;
- ratio to the gross cost saves of around USD 13bn: around 100% ("costs to achieve" of one dollar per dollar saved).

## Tolerance

- **Same unit as the call.** As in `plans/phase_3d.md`: the same figure allowing for rounding at the precision of the call figure.
- **Another unit.** The report figure, converted back with the base at the reporting date of that report, lies within 10% of the call figure. For orientation: the T32 case is within 2% (180 basis points on 546.5 are 9.8, against 10 in the reports).
- Words such as "over", "below", "up to" and "around" do not enter the comparison; they are recorded with the hit.
- A figure outside the tolerance, in a forward-looking sentence on the same quantity, is recorded as "another figure", as in phase 3d.

## What counts

A hit counts only if it states the quantity as a target or plan: a forward-looking context in the sense of `plans/phase_3d.md` (a target, expectation, plan or guidance, not a reported actual value). Results, definitions and regulatory requirements do not count; they are classified and listed.

## Search

- **Tool.** `data/phase3h/roman_check/check_terms.py` (SHA-256 c27228e8…, checked before the run), unchanged, with `CHECK_MAX_HITS=100000`, on the raw HTML of the 16 files.
- **Terms.** Written by `analysis/phase3j_terms.py` to `data/phase3j/check_units_3j.json` before the search; the SHA-256 of that file is recorded in `run_log.json`. Two kinds of terms per unit:
  - *Pass A, figure forms.* Every central value above, with all values inside the tolerance of 10%, each required near a keyword of the unit. Amounts in billions: all integers in the band, as "Nbn" and "N billion" (for amounts below 10 in steps of 0.5); percentages: all values in the band to one decimal, and integers where they lie in the band; basis points: multiples of 5 in the band, as "N basis points", "Nbps" and "Nbp".
  - *Pass B, keywords.* The keywords alone. This pass is meant for forms that the list above did not anticipate.
- **Keywords.**
  - T33: AT1, additional tier 1.
  - T68, reading 1: HoldCo, TLAC, total loss-absorbing, gone concern, senior unsecured.
  - T68, reading 2: holding company, UBS Group AG (required near: issuance, issued, funding, debt), funding plan, AT1, additional tier 1.
  - F11: going concern, AT1, additional tier 1.
  - F22: LCR, liquidity coverage ratio, HQLA, high-quality liquid assets.
  - T16: operational risk.
  - T25: capital release, capital released, released capital, freeing up capital, free up, attributed equity.
  - T27: Non-core and Legacy, credit and market risk.
  - F12: LRD, leverage ratio denominator.
  - T30: integration-related expenses, costs to achieve, integration costs.
- **Hits read.**
  - Pass A: every hit.
  - Pass B: every hit whose shown context (250 characters on each side) contains a forward-looking word and a quantity. Forward-looking word: `FORWARD_RE` of `analysis/phase3_extract.py`, extended by will, would, aim, intend, anticipate, estimate, ambition, objective, goal and outlook. Quantity: `quantities()` of the same module. The other pass B hits are counted per unit and file and not read.
  - Identical contexts that recur in several reports are read once and counted for each report.
  - If the hits to read for one unit exceed 600 distinct contexts, I report this to Roman before reading that unit and do not sample on my own.
- **Page.** The tool gives no page. For every hit that is quoted, the page is taken from the page text of phase 3b (repaired reconstruction) or of phase 3f, and the quote is verified verbatim against that page; the script refuses to write otherwise.

## Classification of the hits read

One reader. Each hit read gets one class:

- **same target, same unit**: forward-looking, the call figure in the unit of the call (a class A counterpart that phase 3d missed);
- **same target, another unit**: forward-looking, an equivalent form inside the tolerance;
- **same target, another figure**: forward-looking on the same quantity, a figure outside the tolerance;
- **result**: a reported actual value;
- **definition or requirement**: a definition, a regulatory requirement or a description of method;
- **other**: another quantity, another entity or another period.

## Consequence for the count

A unit with at least one hit of the first or second class leaves the call-only figures, as T32 did. A unit with hits of the third class moves from "not mentioned" or "mentioned without a figure" to "mentioned with another figure", which also removes it from the call-only figures under the counting rule of `03g_fls_models.ipynb`. I report the resulting count; the decision on each unit is Roman's. `FINDINGS.md`, `data/phase3d/` and `data/phase3g/` are not changed in this phase.

## Implementation and outputs

- `analysis/phase3j_terms.py` (terms), `analysis/phase3j_read.py` (parsing of the tool output, pass B filter, classes with verified quotes), tests in `tests/test_phase3j.py`.
- Outputs in `notebooks/roman/data/phase3j/`: `check_units_3j.json`, `forms.csv` (unit, form, calculation, central value, terms), `check_hits_3j.txt` (raw tool output), `hits.csv` (every hit with pass, term, file and context), `read.csv` (every hit read, with class, quote, page and conversion), `summary.csv` (per unit: forms, hits, hits read, hits per class, resulting status), `run_log.json`, `SHA256SUMS`.
- Notebook `03j_equivalent_forms.ipynb`, with saved outputs.

## Limits known in advance

- The equivalent forms are those I could think of. Pass B is the safeguard against forms I did not anticipate, but it depends on the keywords and on a forward-looking word within 250 characters.
- The conversions use the bases at the call date, and several assume a ratio (CET1 of 14%, leverage requirement of 5.0%). A report may reason with another base.
- One reader. "Not found" means not found with these terms.
- The investor presentations belong to the call side and are not searched.
