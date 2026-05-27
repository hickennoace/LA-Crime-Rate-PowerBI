# L.A. Crime Rate

A Power BI report I built on LAPD crime data, 2020 through late 2023. The dataset has around 852,950 reported incidents and 28 columns. It's a real-world open dataset, so a chunk of the work is just cleaning before any of it can be charted.

## The data

It comes from the LAPD open data portal (Crime Data from 2020 to Present). The CSV is in the repo as `data.zip` (~42 MB compressed) so the report opens without any download step.

If you'd rather pull it fresh:

- LAPD portal: https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8
- Or run `py download_data.py` which fetches the same file (no third-party libraries, just `urllib`).

Date coverage runs 2020-01-01 to 2023-12-04, so 2023 is a partial year. I flag that on any chart where it matters with a `Year Label` measure that appends "(partial)".

## The 7 pages

I split things out so no single page tried to do everything. Each page has its own focus and slicers.

**Page 1 - Executive overview.** The "what's the headline" page.
- Cards: Total Crimes, Crimes YoY %, Avg Crimes/Day, Top Weapon.
- Charts: crimes per year, crimes per month.
- Donut: Part 1 vs Part 2 share.
- Slicers: year, quarter.

**Page 2 - Geographic and operational.** Where and when crimes happen.
- Bar: crimes by LAPD division (21 divisions).
- Bar: crimes by premise (street, residence, parking lot, etc).
- Heatmap: hour-of-day x weekday with conditional formatting. This is the page that surfaces the most obvious patterns. Friday/Saturday late evenings are dark red and Sunday mornings are mostly empty.
- Slicer: year.

**Page 3 - Deep dive.** The page I use the most when poking around.
- Bar: top weapons, with unknowns and "verbal threat" filtered out so the chart isn't dominated by them.
- Area chart: Part 1 vs Part 2 severity over time.
- Donut: victim descent breakdown.
- Column: victim age bands.
- Cards: avg reporting lag, crimes reported late (>30 days).

**Page 4 - Victim demographics.**
- Cards: total crimes, avg victim age, victims with known age.
- Bar: crimes by victim sex (M, F - I null out the "X" sentinel during cleanup).
- Column: crimes by victim age band (Under 18, 18-25, 26-35, 36-50, 51+, Unknown).
- Bar: crimes by victim descent (the dataset uses single-letter codes; I label them in Power Query).
- Slicer: year.

**Page 5 - Time patterns.**
- Cards: avg crimes per day, avg crimes per month.
- Column: crimes by hour of day (0-23).
- Bar: crimes by day of week.
- Column: crimes by month.
- Slicer: year.

**Page 6 - Crime type breakdown.**
- Cards: total crimes, Part 1 crimes, Part 1 share.
- Bar: top crime types by incident count.
- Donut: Part 1 vs Part 2 severity split.
- Slicers: year, LAPD division.

**Page 7 - Status and investigation.**
- Cards: total crimes, still under investigation, arrest rate, avg reporting lag.
- Bar: crimes by case status.
- Column: avg reporting lag by year.
- Donut: case status distribution.
- Slicer: year.

Case status codes used on page 7: IC = Investigation Continuing, AA = Adult Arrest, JA = Juvenile Arrest, AO = Adult Other, JO = Juvenile Other.

## DAX measures

Full source is in `02_DAX_Measures.dax`. The important ones:

| Measure | What it does |
|---|---|
| `Total Crimes` | `COUNTROWS(crime)` |
| `Crimes YoY` / `Crimes YoY %` | Year-over-year via `SAMEPERIODLASTYEAR` against the DimDate table |
| `Avg Crimes per Day` | Total divided by distinct days in the current filter context |
| `Avg Crimes per Month` | `AVERAGEX` over the YearMonth column |
| `Crimes 12M Rolling Avg` | 12-month rolling average via `DATESINPERIOD` |
| `Top Weapon Name` | Most frequent weapon after the "unknowns" exclusion list |
| `Avg Reporting Lag (days)` | Average of `reporting_lag_days` |
| `Crimes Reported Late (>30d)` | Count where lag > 30 (some crimes get reported years late) |
| `Arrest Rate` | Share of crimes with status AA or JA |
| `Crimes Under Investigation` | Count where status = IC |
| `Part 1 Crimes` / `Part 1 Share` | FBI index (serious) crime count and share |
| `Peak Hour of Day` | Most common hour, formatted on a 12h clock |
| `Busiest Weekday` | Weekday with the most crimes |
| `Top Crime Description` | Most frequent crime description in current context |
| `Year Label` | Adds "(partial)" to the 2023 label on charts |

A few of these came out of asking the data a question. `Crimes Reported Late (>30d)` exists because I noticed during validation that the reporting-lag distribution has a long tail. Some crimes show a `date_reported` that's more than a year after the `date_occurred`, which I didn't expect.

## Power Query cleaning

The cleaning lives in `01_PowerQuery_M_Script.pq`. The dataset has some real quirks:

1. The CSV loads with UTF-8 encoding.
2. One header is literally corrupted: column 16 comes in as `FOLDING KNIFE` instead of `weapon_description`. The script renames it.
3. `date_occurred` arrives as a string with a time component. I split it into date and time and parse the date as `DD/MM/YYYY` with en-GB locale. The default parse picks the wrong format and silently produces nulls.
4. Cast every column to its proper type.
5. Clean misspelled "UNKONW" (typo from the source) to null, proper-case weapon descriptions.
6. Null out sentinel values: weapon_code = 0, victim_age = 0, victim_sex = "X".
7. Add the columns I want for charts: `year_occurred`, `month_name`, `quarter_occurred`, `weekday_name`, `weekday_number`, `hour_occurred`, `is_part_1`, `reporting_lag_days`, `victim_age_band`, `victim_descent_label`.
8. Drop columns that are mostly null (`crime_code_2`, `crime_code_3`, `crime_code_4`, `cross_street`).

`validate_dataset.py` is a separate script that runs these assumptions on the raw CSV before Power Query touches it, just so I know the header corruption, date format, and sentinel values are still there in any future refresh.

## How to open

1. Get the CSV - either extract `data.zip` or run `py download_data.py`.
2. Put the CSV in the same folder as `L.A_Crime_Rate.pbip`.
3. Open the pbip in Power BI Desktop.

If you keep the CSV somewhere else, the path is hardcoded in the `crime` query's `Source` step. Update it there.

`validate_pbir.py` is a sanity check on the generated PBIR project - it parses every visual.json and confirms that every column and measure referenced actually exists in the semantic model. I added this because PBIR is text-based and easy to break by hand-editing.

## Files

```
L.A_Crime_Rate.pbip                   Power BI project entry point
Crime_Data_from_2020_to_Present.csv   Source data (LAPD)
01_PowerQuery_M_Script.pq             Power Query M
02_DAX_Measures.dax                   DAX measures (reference)
download_data.py                      Fetches the CSV from LAPD
validate_dataset.py                   Sanity checks on the raw CSV
validate_pbir.py                      Checks the PBIR structure
L.A_Crime_Rate.Report/                Report definition (PBIR format)
  definition/pages/                   One folder per page
L.A_Crime_Rate.SemanticModel/         Semantic model (TMDL format)
  definition/tables/                  crime, DimDate, _Measures
```
