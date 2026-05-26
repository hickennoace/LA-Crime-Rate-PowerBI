"""
Downloads Crime_Data_from_2020_to_Present.csv from the LAPD Open Data portal
and saves it to the same folder as this script.

Usage:
    python download_data.py

Requirements:
    pip install requests
"""

import os
import requests

URL = "https://data.lacity.org/api/views/2nrs-mtv8/rows.csv?accessType=DOWNLOAD"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Crime_Data_from_2020_to_Present.csv")


def download():
    if os.path.exists(OUTPUT_FILE):
        print(f"File already exists: {OUTPUT_FILE}")
        print("Delete it first if you want to re-download.")
        return

    print("Downloading from LAPD Open Data portal...")
    print("This file is ~190 MB — may take a few minutes depending on your connection.\n")

    with requests.get(URL, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0

        with open(OUTPUT_FILE, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded / total * 100
                    print(f"\r  {pct:.1f}%  ({downloaded / 1_000_000:.1f} MB / {total / 1_000_000:.1f} MB)", end="")

    print(f"\n\nDone. Saved to:\n  {OUTPUT_FILE}")
    print("\nYou can now open L.A_Crime_Rate.pbip in Power BI Desktop.")


if __name__ == "__main__":
    download()
