"""
Downloads Crime_Data_from_2020_to_Present.csv from the LAPD Open Data portal
and saves it to the same folder as this script.

Usage:
    python download_data.py

No external libraries required — uses Python's built-in urllib.
"""

import os
import urllib.request

URL = "https://data.lacity.org/api/views/2nrs-mtv8/rows.csv?accessType=DOWNLOAD"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Crime_Data_from_2020_to_Present.csv")


def progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(downloaded / total_size * 100, 100)
        mb_done = downloaded / 1_000_000
        mb_total = total_size / 1_000_000
        print(f"\r  {pct:.1f}%  ({mb_done:.1f} MB / {mb_total:.1f} MB)", end="", flush=True)
    else:
        print(f"\r  {downloaded / 1_000_000:.1f} MB downloaded...", end="", flush=True)


def download():
    if os.path.exists(OUTPUT_FILE):
        print(f"File already exists: {OUTPUT_FILE}")
        print("Delete it first if you want to re-download.")
        return

    print("Downloading from LAPD Open Data portal...")
    print("This file is ~190 MB — may take a few minutes.\n")

    urllib.request.urlretrieve(URL, OUTPUT_FILE, reporthook=progress)

    print(f"\n\nDone. Saved to:\n  {OUTPUT_FILE}")
    print("\nYou can now open L.A_Crime_Rate.pbip in Power BI Desktop.")


if __name__ == "__main__":
    download()
