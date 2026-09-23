# Phase 3b: call against quarterly report for the five phase 3 cases

Written 2026-09-23, before any search in the reports. Descriptive: no test, nothing enters the register.

## Question

For the five case studies of phase 3, does the same information appear in the bank's quarterly report of the same quarter, and which document shows a change first or more precisely? Where the call carries information that the report does not, the call adds something for a supervisor; where the report is earlier or more exact, the call adds little.

## Sources

- **Calls:** management statements of the earnings calls from `notebooks/roman/data/phase3/statements.csv` (release `data/results/2026-09-23`, with the `ex.` joins of phase 3). The JPMorgan event call of 1 May 2023 is used only as the origin of case 5.
- **Reports:** `notebooks/roman/data/reports/`, read only, 16 files: UBS quarterly reports ("Our key figures" reports, filed as 6-K) and JPMorgan Earnings Release Financial Supplements (Exhibit 99.2), 2023-Q1 to 2024-Q4. The files are never modified; extracted text is written to `notebooks/roman/data/phase3b/`.

## Text reconstruction (fixed before searching)

Three layouts occur:

1. **UBS 2023-Q2 to 2024-Q4** (PDF conversions, Inline XBRL for the half-year reports): each page is a container `div id="PageN"`; each printed line is an absolutely positioned `div` with `left` and `top` in pixels, and word spaces are separate inline-block `div`s. Reconstruction: parse the body after `</ix:header>` (if present) with BeautifulSoup (`html.parser`); for every line `div` take the concatenated text of its descendants, with every spacer `div` and `&#160;` turned into one space, and no space inserted between adjacent text nodes (words split across XBRL tags such as `FR` + `TB` are rejoined). Lines are assigned to their page container (nearest ancestor with `id="Page…"`) and sorted by column (left edge below or above half the page width), then `top`, then `left`. Lines are joined with a space; a line ending in a hyphen followed by a line starting with a lower-case letter is joined without the hyphen.
2. **UBS 2023-Q1** (flowing HTML): pages split at `<a name="page_N">`; text via BeautifulSoup `get_text(" ")`.
3. **JPMorgan supplements** (flowing HTML, Workiva): pages split at `<hr style="page-break-after:always">`; text via `get_text(" ")`, so that table cells stay separated.

In all layouts whitespace is collapsed. Checks before searching: every file yields text for every page; the words `FRTB`, `Basel III`, `integration-related` and `First Republic` are counted in the raw file (where fragmented) and in the reconstructed text, and the reconstructed count must be at least the raw count. The page number used as location ("Fundstelle") is the page index in the file (container `PageN`, anchor `page_N`, or the running count of page breaks for JPMorgan), plus the nearest preceding heading-like line where one can be identified.

## Cases and search terms (fixed before searching)

| Case | Bank | Information | Search terms (case-insensitive) |
|---|---|---|---|
| C1 | UBS | Gross cost saves: target and cumulative achieved | `gross cost sav`, `gross sav`, `cost reduction`, `run-rate`, `exit rate` together with `sav` |
| C2 | UBS | Integration-related expenses: expected total and incurred | `integration-related expenses`, `integration expenses`, `costs to achieve` |
| C3 | UBS | Basel III final / FRTB: expected RWA effect | `FRTB`, `fundamental review of the trading book`, `Basel III final`, `final Basel III`, `Basel 3 final`, `final Basel 3`, `Basel III reform` |
| C4 | UBS | AT1 issuance: plan and amount issued | `AT1`, `additional tier 1` together with `issu` |
| C5 | JPM | First Republic: event-call figures (bargain purchase gain, restructuring costs, incremental net income) and the quarterly contribution; JPMorgan guidance (NII, expense) as a check whether supplements carry outlook at all | `First Republic`, `bargain purchase`, `outlook`, `guidance` |

For every case, bank and quarter, all passages with a hit are retrieved with about 300 characters of context and written to `notebooks/roman/data/phase3b/hits_reports.csv` and `hits_calls.csv`, with document, page and position.

## Comparison table

One row per case and quarter (C1 to C4: UBS 2023-Q1 to 2024-Q4; C5: JPMorgan event call and 2023-Q1 to 2024-Q4), with the columns:

`case, bank, quarter, in_call (yes/no), in_report (yes/no), figure_call, figure_report, first_or_more_precise (call / report / same / neither), quote_call, location_call, quote_report, location_report, comment, checked_by_roman`.

`in_call` and `in_report` are set from the retrieval (a hit counts only if the passage concerns the case, not a mere word match). The figures, the judgement of which document shows the change first or more precisely, and the quotes are filled by reading the retrieved passages; every entry carries its quote and location so that it can be checked, and `checked_by_roman` is left empty. Calls and reports of the same quarter are published on the same day for both banks as a rule, but the filing dates are not in the files, so "first" compares quarters, and within a quarter the more precise document is named.

Output: `notebooks/roman/data/phase3b/comparison.csv` and notebook `03b_call_vs_report.ipynb` with the table per case, a one-line reading per case, and the retrieval counts.

## What would count as a finding

A case where the call states a figure or a change that the report of the same or an earlier quarter does not contain (or the reverse), stated with quote and location. No statistical claims.

## Tests (pytest)

Added to `tests/`: the reconstruction of a UBS page rejoins a word split across tags and turns spacer elements into single spaces (on a small synthetic fragment); every report file yields at least one page of text; the search never writes into `notebooks/roman/data/reports/` (file hashes before and after a run are equal).

## Amendment 2026-09-23: UBS annual reports (Form 20-F) for C1 and C2

Written before any search in the annual reports. Two further files are read, never modified: `UBS_2023_annual_report.htm` and `UBS_2024_annual_report.htm` (Form 20-F, Inline XBRL, same positioned page layout as the quarterly reports from 2023-Q2; reconstructed with layout 1 unchanged). Question: do the annual reports state the expected total integration-related expenses, their increase from around 13 to around 14 billion, or the gross cost saves target with progress?

- Search: the C1 and C2 terms of this plan, unchanged, plus one search for total figures, which was also used when reading the quarterly reports for C2: sentences that contain `integration` or `cost` together with `USD 13bn`, `USD 14bn`, `USD 13 billion` or `USD 14 billion` (decimals allowed).
- Table: four rows added to `comparison.csv`, labelled `2023 annual report` and `2024 annual report` for C1 and C2. The call columns refer to the fourth-quarter call of the same year (2023-Q4 on 6 February 2024, 2024-Q4 on 4 February 2025), which precedes the annual report; the filing date is not in the files. `first_or_more_precise` compares the annual report with that call.
- Checks as for the quarterly reports: text on every page, check-word counts in reconstructed text at least as high as in the raw file, file hashes unchanged.
