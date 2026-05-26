"""
Pre-import validation for the L.A. Crime dataset.
Confirms every data-quality assumption before we commit to Power Query transforms.
"""

import pandas as pd
import numpy as np
from pathlib import Path

CSV = Path(__file__).parent / "Crime_Data_from_2020_to_Present.csv"

# Read with all columns as string so we can inspect raw values
print(f"Loading {CSV.name}...")
df = pd.read_csv(CSV, dtype=str, low_memory=False, keep_default_na=False)
print(f"  Rows: {len(df):,}    Columns: {len(df.columns)}\n")

# 1. Confirm the corrupted header
print("=" * 70)
print("1. HEADER CHECK (column index 16 should be 'weapon_description')")
print("=" * 70)
for i, c in enumerate(df.columns):
    flag = "  <-- corrupted? expected weapon_description" if c == "FOLDING KNIFE" else ""
    print(f"  [{i:2}] {c}{flag}")

# Rename the bad column for the rest of this script
if "FOLDING KNIFE" in df.columns:
    df = df.rename(columns={"FOLDING KNIFE": "weapon_description"})

# 2. Date format confirmation
print("\n" + "=" * 70)
print("2. DATE FORMAT CHECK (expecting DD/MM/YYYY)")
print("=" * 70)
# Parse both ways and see which yields valid dates with sensible distribution
for col in ["date_reported", "date_occurred"]:
    sample = df[col].str.split(" ").str[0]   # drop time portion if any
    dmy = pd.to_datetime(sample, format="%d/%m/%Y", errors="coerce")
    mdy = pd.to_datetime(sample, format="%m/%d/%Y", errors="coerce")
    print(f"  {col}:")
    print(f"     parsed as DD/MM/YYYY -> {dmy.notna().sum():,} valid, "
          f"range {dmy.min()} -> {dmy.max()}")
    print(f"     parsed as MM/DD/YYYY -> {mdy.notna().sum():,} valid, "
          f"range {mdy.min()} -> {mdy.max()}")

# Use DD/MM/YYYY going forward
df["date_occurred_dt"] = pd.to_datetime(
    df["date_occurred"].str.split(" ").str[0], format="%d/%m/%Y", errors="coerce")
df["date_reported_dt"] = pd.to_datetime(
    df["date_reported"], format="%d/%m/%Y", errors="coerce")

print(f"\n  Final date_occurred range: "
      f"{df['date_occurred_dt'].min().date()} -> {df['date_occurred_dt'].max().date()}")

# 3. Weapon column profile
print("\n" + "=" * 70)
print("3. WEAPON COLUMN PROFILE")
print("=" * 70)
print(f"  Distinct weapon_description values: {df['weapon_description'].nunique()}")
print(f"  Null weapon_description:           {df['weapon_description'].eq('').sum():,}")
print("\n  Top 15 RAW weapon descriptions:")
print(df["weapon_description"].value_counts().head(15).to_string())

# 4. Apply exclusions and recompute top weapons
print("\n" + "=" * 70)
print("4. TOP WEAPONS AFTER EXCLUSIONS")
print("=" * 70)
exclude_text = {"UNKONW", "UNKNOWN", "UNKNOWN WEAPON/OTHER WEAPON", "", "NONE", "VERBAL THREAT"}
exclude_code = {"0", "500"}
clean = df[
    (~df["weapon_description"].str.upper().isin(exclude_text))
    & (~df["weapon_code"].isin(exclude_code))
]
print(f"  Rows after exclusion: {len(clean):,} ({len(clean)/len(df):.1%} of total)")
print("\n  Top 10 weapons (clean):")
print(clean["weapon_description"].value_counts().head(10).to_string())

# 5. Unknown sentinels in demographic columns
print("\n" + "=" * 70)
print("5. UNKNOWN-VALUE SENTINELS")
print("=" * 70)
print(f"  victim_age == 0:        {(df['victim_age'] == '0').sum():,}")
print(f"  victim_sex == 'X':      {(df['victim_sex'] == 'X').sum():,}")
print(f"  victim_sex empty:       {(df['victim_sex'] == '').sum():,}")
print(f"  victim_descent == 'X':  {(df['victim_descent'] == 'X').sum():,}")
print(f"  weapon_code == 0:       {(df['weapon_code'] == '0').sum():,}")

# 6. Area distribution preview
print("\n" + "=" * 70)
print("6. CRIMES BY AREA (top 10)")
print("=" * 70)
print(df["area_name"].value_counts().head(10).to_string())

# 7. Yearly distribution preview
print("\n" + "=" * 70)
print("7. CRIMES BY YEAR")
print("=" * 70)
yearly = df["date_occurred_dt"].dt.year.value_counts().sort_index()
print(yearly.to_string())

# 8. Reporting-lag preview (Advanced Insight #1)
print("\n" + "=" * 70)
print("8. REPORTING-LAG PREVIEW (date_reported - date_occurred)")
print("=" * 70)
lag = (df["date_reported_dt"] - df["date_occurred_dt"]).dt.days
print(f"  mean: {lag.mean():.1f} days   median: {lag.median():.0f} days")
print(f"  >30 days:  {(lag > 30).sum():,}")
print(f"  >365 days: {(lag > 365).sum():,}")
print(f"  negative (data error): {(lag < 0).sum():,}")

# 9. Daily/monthly average preview (Metric C)
print("\n" + "=" * 70)
print("9. AVERAGE-RATE BASELINES")
print("=" * 70)
distinct_days = df["date_occurred_dt"].dt.date.nunique()
distinct_months = df["date_occurred_dt"].dt.to_period("M").nunique()
print(f"  Avg crimes per day:   {len(df)/distinct_days:.1f}  "
      f"(over {distinct_days} distinct days)")
print(f"  Avg crimes per month: {len(df)/distinct_months:.1f}  "
      f"(over {distinct_months} distinct months)")

print("\n[DONE]")
