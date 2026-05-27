# L.A. Crime Rate

A Power BI report I put together on LAPD crime data from 2020 through late 2023. The dataset has around 852,950 reported incidents.

## The data

It comes from the LAPD open data portal (Crime Data from 2020 to Present). The CSV is included in this repo as `data.zip` (~42 MB compressed) so you don't need to download it separately.

If you'd rather pull it fresh:

- LAPD portal: https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8
- Or run `py download_data.py` which fetches the same file.

Rows run from 2020-01-01 to 2023-12-04, so 2023 is a partial year. The charts flag this where it matters.

## What's in the report

7 pages, each focused on one angle so no single page tries to do everything:

1. Executive overview - headline KPIs and yearly trends.
2. Geographic and operational - crimes by LAPD division, premise, and an hour-by-weekday heatmap.
3. Deep dive - weapons (with unknowns cleaned out), severity, victim descent, age bands, reporting lag.
4. Victim demographics - sex, age band, descent.
5. Time patterns - hour of day, day of week, monthly seasonality.
6. Crime type breakdown - top crime types and the Part 1 vs Part 2 split.
7. Status and investigation - case outcomes and arrest rates.

Case status codes on page 7: IC = Investigation Continuing, AA = Adult Arrest, JA = Juvenile Arrest, AO = Adult Other, JO = Juvenile Other.

## DAX measures

Full source is in `02_DAX_Measures.dax`. The ones I lean on most:

- `Total Crimes` - row count.
- `Crimes YoY` / `Crimes YoY %` - year-over-year via SAMEPERIODLASTYEAR.
- `Avg Crimes per Day` and `per Month`.
- `Crimes 12M Rolling Avg`.
- `Avg Reporting Lag (days)` and `Crimes Reported Late (>30d)` - I wanted to see how often crimes get reported well after they happen. Some of them lag by years.
- `Arrest Rate` - share of crimes with status AA or JA.
- `Part 1 Crimes` / `Part 1 Share` - serious (FBI index) crime count and share.

## Power Query

The cleaning is in `01_PowerQuery_M_Script.pq`. The dataset has a few quirks worth flagging:

- One header is corrupted (`FOLDING KNIFE` instead of `weapon_description`).
- Dates are DD/MM/YYYY, which Power Query doesn't pick up by default.
- "Unknown" shows up as `UNKONW` (typo from the source), `0`, or `X` depending on the column. I null those out.
- A few columns are almost entirely empty (`crime_code_2`-`crime_code_4`, `cross_street`) so I drop them.
- I add the columns I actually want for charts: year, month name, quarter, weekday, hour, `is_part_1`, `reporting_lag_days`, age bands, and descent labels.

## How to open

1. Get the CSV - either extract `data.zip` or run `py download_data.py`.
2. Put the CSV in the same folder as `L.A_Crime_Rate.pbip`.
3. Open the pbip in Power BI Desktop.

If you keep the CSV somewhere else, the path is hardcoded in the `crime` query's `Source` step. Update it there.

## Files

```
L.A_Crime_Rate.pbip                   Power BI project entry point
Crime_Data_from_2020_to_Present.csv   Source data (LAPD)
01_PowerQuery_M_Script.pq             Power Query M
02_DAX_Measures.dax                   DAX measures
download_data.py                      Fetches the CSV from LAPD
validate_dataset.py                   Sanity checks on the raw CSV
validate_pbir.py                      Checks the PBIR structure
L.A_Crime_Rate.Report/                Report definition (PBIR)
L.A_Crime_Rate.SemanticModel/         Semantic model (TMDL)
```
