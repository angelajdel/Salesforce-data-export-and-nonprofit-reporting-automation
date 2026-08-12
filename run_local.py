#!/usr/bin/env python3
"""
run_local.py
---------------------------------
Runs Impact Hub entirely on your own computer -- no GitHub, no online
account, no repository needed for anyone using this. This is the
alternative to the GitHub Actions automation: instead of a scheduled cloud
job keeping a shared website current, you run this whenever you want fresh
numbers, on your own machine, using your own Salesforce credentials.

WHAT THIS DOES
---------------
1. Pulls fresh Client and Donor data from Salesforce (same script the
   GitHub automation uses -- scripts/fetch_salesforce_data.py)
2. Cleans it -- removes test records and duplicates
   (scripts/clean_salesforce_export.py)
3. Opens the folder containing the two cleaned CSVs
4. Opens impact_hub.html in your default browser

WHY YOU STILL DRAG TWO FILES IN
----------------------------------
This is the one unavoidable step: browsers are deliberately not allowed to
read files off your computer's disk without you choosing them yourself --
that's a security boundary, not a limitation of this tool. So after this
script opens both the folder and the browser tab, drag the two CSV files
from that folder onto the matching cards in Impact Hub (or click "Choose
file"). Takes a few seconds.

ONE-TIME SETUP
---------------
    pip install -r requirements.txt
    cp .env.example .env
    (fill in your real Salesforce credentials in .env -- see the setup
    instructions at the top of scripts/fetch_salesforce_data.py)

EVERY TIME YOU WANT FRESH DATA
---------------------------------
    python run_local.py

WANT THIS TO RUN AUTOMATICALLY ON A SCHEDULE, WITHOUT GITHUB?
------------------------------------------------------------------
This script itself can be scheduled locally instead of via GitHub Actions:
  - Mac/Linux: add a line to your crontab (`crontab -e`) such as
      0 8 * * 1-5 cd /path/to/this/folder && /usr/bin/python3 run_local.py
  - Windows: use Task Scheduler to run this script on whatever schedule
    you'd like, with the "Start in" folder set to this project's folder.
This still needs the computer to be on at the scheduled time -- unlike the
GitHub version, which runs in the cloud regardless of anyone's computer.
"""

import subprocess
import sys
import webbrowser
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "local_data"


def run(cmd, description):
    print(f"\n{description}...")
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    if result.returncode != 0:
        sys.exit(f"\n'{description}' failed. Fix the error above and try again.")


def open_folder(path):
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)])
    elif sys.platform.startswith("win"):
        subprocess.run(["explorer", str(path)])
    else:
        subprocess.run(["xdg-open", str(path)])


def main():
    print("Impact Hub -- local run (no GitHub involved)")
    print("-----------------------------------------------")

    raw_dir = SCRIPT_DIR / "raw_exports"
    OUTPUT_DIR.mkdir(exist_ok=True)

    run(
        [sys.executable, "scripts/fetch_salesforce_data.py", "--output-dir", str(raw_dir)],
        "Pulling fresh data from Salesforce",
    )

    run(
        [
            sys.executable, "scripts/clean_salesforce_export.py",
            str(raw_dir / "clients_export.csv"),
            "--id-column", "Id",
            "--output", str(OUTPUT_DIR / "cleaned_clients.csv"),
            "--log", str(OUTPUT_DIR / "clients_clean_log.json"),
        ],
        "Cleaning client data",
    )

    run(
        [
            sys.executable, "scripts/clean_salesforce_export.py",
            str(raw_dir / "donors_export.csv"),
            "--id-column", "Id",
            "--output", str(OUTPUT_DIR / "cleaned_donors.csv"),
            "--log", str(OUTPUT_DIR / "donors_clean_log.json"),
        ],
        "Cleaning donor data",
    )

    print(f"\nOpening {OUTPUT_DIR} so you can grab the two files...")
    open_folder(OUTPUT_DIR)

    impact_hub_path = SCRIPT_DIR / "impact_hub.html"
    print(f"Opening Impact Hub in your browser...")
    webbrowser.open(f"file://{impact_hub_path}")

    print(
        "\nAlmost done -- drag cleaned_clients.csv and cleaned_donors.csv from the "
        "folder that just opened onto the matching cards in Impact Hub, then click "
        "'Clean this data.'"
    )


if __name__ == "__main__":
    main()
