# L.A. Crime Rate -> Power BI Report

An interactive Power BI report analysing **852,950 LAPD reported incidents** from 2020-01-01 through 2023-12-04 (2023 is a partial year).

## Data Source

| Field | Detail |
|---|---|
| Source | LAPD Open Data -> *Crime Data from 2020 to Present* |
| File | `Crime_Data_from_2020_to_Present.csv` |
| Rows | ~852,950 |
| Date range | 2020-01-01 → 2023-12-04 |

## Report Pages

### Page 1 -> Executive Overview
High-level KPIs and crime trends across the full dataset.
- **Cards:** Total Crimes · Crimes YoY · Avg Crimes/Day · Top Weapon
- **Charts:** Crimes per Year · Crimes per Month
- **Slicers:** Year · Quarter
- **Donut:** Part 1 vs Part 2 severity split

### Page 2 -> Geographic & Operational
Where crimes happen across LAPD divisions.
- **Bar:** Crimes by LAPD Division
- **Bar:** Crimes by Premise
- **Heatmap:** Hour × Weekday matrix (conditional formatting)
- **Slicer:** Year

### Page 3 -> Deep Dive
Weapons, severity, victim descent, and reporting quality.
- **Bar:** Top Weapons (cleaned -> excludes unknowns)
- **Area:** Severity over time (Part 1 vs Part 2)
- **Donut:** Victim Descent
- **Column:** Victim Age Bands
- **Cards:** Avg Reporting Lag · Crimes Reported Late (>30 days)

### Page 4 -> Victim Demographics
Who the victims are.
- **Cards:** Total Crimes · Avg Victim Age · Victims with Known Age
- **Bar:** Crimes by Victim Sex (M = Male, F = Female)
- **Column:** Crimes by Victim Age Band
- **Bar:** Crimes by Victim Descent
- **Slicer:** Year

### Page 5 -> Time Patterns
When crimes happen.
- **Cards:** Avg Crimes per Day · Avg Crimes per Month
- **Column:** Crimes by Hour of Day (0–23)
- **Bar:** Crimes by Day of Week
- **Column:** Crimes by Month
- **Slicer:** Year

### Page 6 -> Crime Type Breakdown
What types of crimes are being committed.
- **Cards:** Total Crimes · Part 1 Crimes · Part 1 Share
- **Bar:** Top Crime Types by Incident Count
- **Donut:** Part 1 vs Part 2 Severity Split
- **Slicers:** Year · LAPD Division

### Page 7 -> Status & Investigation
Case outcomes and reporting quality.
- **Cards:** Total Crimes · Still Under Investigation · Arrest Rate · Avg Reporting Lag
- **Bar:** Crimes by Case Status (IC / AA / JA / AO / JO)
- **Column:** Avg Reporting Lag by Year
- **Donut:** Case Status Distribution
- **Slicer:** Year

> **Status codes:** IC = Investigation Continuing · AA = Adult Arrest · JA = Juvenile Arrest · AO = Adult Other · JO = Juvenile Other

## DAX Measures

| Measure | Description |
|---|---|
| `Total Crimes` | COUNTROWS of the crime table |
| `Crimes YoY` / `Crimes YoY %` | Year-over-year delta using SAMEPERIODLASTYEAR |
| `Avg Crimes per Day` | Total ÷ distinct days in context |
| `Avg Crimes per Month` | AVERAGEX over YearMonth values |
| `Top Weapon Name` | Most common weapon (unknowns excluded) |
| `Crimes 12M Rolling Avg` | 12-month rolling average via DATESINPERIOD |
| `Avg Reporting Lag (days)` | Average days between occurrence and report |
| `Crimes Reported Late (>30d)` | Crimes with reporting lag > 30 days |
| `Arrest Rate` | % of crimes resulting in adult or juvenile arrest |
| `Crimes Under Investigation` | Crimes with status = IC |
| `Part 1 Crimes` / `Part 1 Share` | Serious (FBI index) crime count and share |
| `Peak Hour of Day` | Most common hour formatted as 12-hr clock |
| `Busiest Weekday` | Weekday with the most crimes |
| `Top Crime Description` | Most frequent crime description in context |
| `Year Label` | Flags partial year on charts |

Full DAX source: [`02_DAX_Measures.dax`](02_DAX_Measures.dax)

## Power Query Transformations

The `crime` table is loaded from the CSV via a multi-step M script ([`01_PowerQuery_M_Script.pq`](01_PowerQuery_M_Script.pq)) that:

1. Loads the CSV with UTF-8 encoding
2. Fixes a corrupted column header (`FOLDING KNIFE` → `weapon_description`)
3. Splits `date_occurred` into date + time with en-GB locale (DD/MM/YYYY)
4. Casts all columns to correct types
5. Cleans misspelled `UNKONW` → null and proper-cases weapon descriptions
6. Nulls out sentinel values (weapon_code = 0, victim_age = 0, victim_sex = "X")
7. Adds derived columns: `year_occurred`, `month_name`, `quarter_occurred`, `weekday_name`, `weekday_number`, `hour_occurred`, `is_part_1`, `reporting_lag_days`, `victim_age_band`, `victim_descent_label`
8. Removes mostly-null columns (crime_code_2–4, cross_street)

## How to Open

### Step 1 -> Get the data file

The source CSV (`Crime_Data_from_2020_to_Present.csv`) is **not included in this repo** because it is 192 MB. Download it using the provided script:

```bash
py download_data.py
```

This will download the file directly from the LAPD Open Data portal and save it to the correct location automatically. Requires Python 3 -> no additional libraries needed.

> **Prefer not to run a script?** Download the file manually from the LAPD Open Data portal:
> [https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8](https://data.lacity.org/Public-Safety/Crime-Data-from-2020-to-Present/2nrs-mtv8)
> Place the downloaded file in the root of this folder as `Crime_Data_from_2020_to_Present.csv`. The Python script above does exactly this automatically.

### Step 2 -> Open the report

1. Install [Power BI Desktop](https://powerbi.microsoft.com/desktop/)
2. Open `L.A_Crime_Rate.pbip`
3. Power BI will load the semantic model and all 7 report pages automatically

> **Note:** The CSV path is hardcoded in Power Query. If you place the file somewhere other than the repo root, update it in Power Query Editor → `crime` query → step `Source`.

## Project Structure

```
L.A Crime Rate/
├── L.A_Crime_Rate.pbip                   # Power BI project entry point
├── Crime_Data_from_2020_to_Present.csv   # Source data (LAPD open data)
├── 01_PowerQuery_M_Script.pq             # Full Power Query M script
├── 02_DAX_Measures.dax                   # All DAX measures (reference)
├── validate_dataset.py                   # Python data validation script
├── validate_pbir.py                      # Python PBIR structure validator
├── L.A_Crime_Rate.Report/                # Report definition (PBIR format)
│   └── definition/pages/                 # One folder per page
└── L.A_Crime_Rate.SemanticModel/         # Semantic model (TMDL format)
    └── definition/tables/                # crime, DimDate, _Measures
```
