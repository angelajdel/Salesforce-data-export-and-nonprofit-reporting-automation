#!/usr/bin/env python3
"""
clean_salesforce_export.py
---------------------------------
Cleans raw Salesforce CSV exports (Clients and/or Donors) by:
  1. Removing any record whose ID field contains "TEST" (case-insensitive)
     e.g. 003TEST001, 006TESTQA02, etc.
  2. Removing exact duplicate rows (same ID appearing more than once).
  3. Writing a cleaned CSV, plus a JSON "run log" documenting exactly what
     was removed and why -- so nothing is silently dropped without a trail.

USAGE
-----
    python clean_salesforce_export.py clients_export.csv \
        --id-column "Client ID" \
        --output cleaned_clients.csv \
        --log clients_clean_log.json

    python clean_salesforce_export.py donors_export.csv \
        --id-column "Donor ID" \
        --output cleaned_donors.csv \
        --log donors_clean_log.json

You can run this every time you pull a fresh export from Salesforce.
Because it's a script (not a one-off), it behaves identically every month --
that consistency is what makes the "automatic update" workflow reliable
even without a live Salesforce API connection.

TO CONNECT LIVE (future upgrade):
If/when you have Salesforce API credentials (Connected App + OAuth, or a
Simple Salesforce token), the CSV read step below can be swapped for a SOQL
query via the `simple_salesforce` library, and this script can be scheduled
(cron / Task Scheduler / a Zapier-style tool) to run automatically whenever
Salesforce data changes. The cleaning logic itself does not need to change.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd


def clean_export(input_path: str, id_column: str, test_marker: str = "TEST"):
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)

    if id_column not in df.columns:
        available = ", ".join(df.columns)
        raise SystemExit(
            f"Column '{id_column}' not found in {input_path}.\n"
            f"Available columns are: {available}\n"
            f"Pass the correct column name with --id-column."
        )

    total_rows = len(df)

    # Step 1: flag and remove test records (ID contains the test marker)
    is_test = df[id_column].str.contains(test_marker, case=False, na=False)
    test_records = df[is_test].to_dict(orient="records")
    df = df[~is_test]

    # Step 2: remove exact duplicate IDs (keep the first occurrence)
    is_dup = df.duplicated(subset=[id_column], keep="first")
    duplicate_records = df[is_dup].to_dict(orient="records")
    df = df[~is_dup]

    summary = {
        "source_file": str(input_path),
        "id_column": id_column,
        "total_rows_in_export": total_rows,
        "test_records_removed": len(test_records),
        "duplicate_records_removed": len(duplicate_records),
        "clean_rows_remaining": len(df),
        "removed_test_records": test_records,
        "removed_duplicate_records": duplicate_records,
    }

    return df, summary


def main():
    parser = argparse.ArgumentParser(description="Clean a raw Salesforce CSV export.")
    parser.add_argument("input_csv", help="Path to the raw Salesforce export CSV")
    parser.add_argument(
        "--id-column",
        required=True,
        help="Name of the unique ID column, e.g. 'Client ID' or 'Donor ID'",
    )
    parser.add_argument(
        "--test-marker",
        default="TEST",
        help="Substring that marks a record as a test record (default: TEST)",
    )
    parser.add_argument("--output", required=True, help="Path to write the cleaned CSV")
    parser.add_argument("--log", required=True, help="Path to write the JSON clean-up log")

    args = parser.parse_args()

    df_clean, summary = clean_export(args.input_csv, args.id_column, args.test_marker)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(args.output, index=False)

    Path(args.log).parent.mkdir(parents=True, exist_ok=True)
    with open(args.log, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✔ {args.input_csv}")
    print(f"  Total rows read:        {summary['total_rows_in_export']}")
    print(f"  Test records removed:   {summary['test_records_removed']}")
    print(f"  Duplicates removed:     {summary['duplicate_records_removed']}")
    print(f"  Clean rows remaining:   {summary['clean_rows_remaining']}")
    print(f"  Cleaned CSV written to: {args.output}")
    print(f"  Log written to:         {args.log}")


if __name__ == "__main__":
    main()
