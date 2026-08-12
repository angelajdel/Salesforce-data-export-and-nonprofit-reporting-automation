#!/usr/bin/env python3
"""
fetch_salesforce_data.py
---------------------------------
Pulls Client and Donor records directly from Salesforce and writes them to
CSV, in the same shape clean_salesforce_export.py / build_excel_report.py /
Impact_Hub.html already expect.

WHERE YOUR CREDENTIALS LIVE
----------------------------
This script reads credentials ONLY from a local `.env` file (or real
environment variables) on your own machine. They are never printed, never
logged, and never sent anywhere except directly to Salesforce's own login
endpoint. Nothing about your credentials is visible to, or needed by, any
AI assistant, chat, or the browser-based Impact Hub tool -- this script
runs entirely on your computer, standalone.

  1. Copy `.env.example` to `.env`
  2. Fill in your real values in `.env`
  3. Make sure `.env` is in your `.gitignore` (a starter one is included)
  4. Never paste the contents of `.env` into a chat, ticket, or Slack message

SETUP (one-time, done by whoever administers your Salesforce org)
-------------------------------------------------------------------
You need ONE of the following. Ask your Salesforce admin for whichever your
org prefers -- either works with this script.

Option A -- Username/Password/Security Token (simplest for a personal script)
  1. In Salesforce: Setup -> Users -> your user -> "Reset My Security Token"
     (emailed to you)
  2. Set in .env:
       SF_AUTH_METHOD=password
       SF_USERNAME=you@yourorg.org
       SF_PASSWORD=your_salesforce_password
       SF_SECURITY_TOKEN=the_token_emailed_to_you
       SF_DOMAIN=login        (use "test" if this is a Sandbox org)

Option B -- Connected App / Client Credentials (better for a shared/team tool)
  1. In Salesforce: Setup -> App Manager -> New Connected App
  2. Enable OAuth, select "Client Credentials Flow", assign a run-as user
  3. Set in .env:
       SF_AUTH_METHOD=client_credentials
       SF_CLIENT_ID=the_connected_apps_consumer_key
       SF_CLIENT_SECRET=the_connected_apps_consumer_secret
       SF_DOMAIN=login        (use "test" if this is a Sandbox org,
                                or your "My Domain" name, e.g. yourorg)

WHAT DATA IT PULLS
-------------------
The two SOQL queries below are the part most specific to your org -- every
Salesforce setup names its client/donor objects and fields differently.
Edit CLIENT_SOQL and DONOR_SOQL to match your org before running, or set
SF_CLIENT_SOQL / SF_DONOR_SOQL in .env to override them without touching
this file. Defaults below assume plain Contact records and Opportunities
(a common Nonprofit Success Pack setup) -- adjust the object and field API
names to match what your org actually uses.

USAGE
-----
    pip install -r requirements.txt
    python fetch_salesforce_data.py --output-dir raw_exports/

This writes raw_exports/clients_export.csv and raw_exports/donors_export.csv,
ready to feed straight into clean_salesforce_export.py.
"""

import argparse
import csv
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# --- Default SOQL -- EDIT THESE to match your org's actual objects/fields ---
DEFAULT_CLIENT_SOQL = """
    SELECT Id, FirstName, LastName, Email, Phone, Program__c,
           CreatedDate, npsp__Status__c
    FROM Contact
    WHERE RecordType.Name = 'Client'
"""

DEFAULT_DONOR_SOQL = """
    SELECT Id, Account.Name, Contact.Email, Amount, CloseDate,
           Campaign.Name, Type
    FROM Opportunity
    WHERE IsWon = true
"""


def get_credential(name, required=True):
    val = os.environ.get(name)
    if required and not val:
        sys.exit(
            f"Missing required setting: {name}\n"
            f"Set it in your .env file (see .env.example) before running this script."
        )
    return val


def connect():
    """Builds an authenticated Salesforce session from local env vars only."""
    from simple_salesforce import Salesforce

    auth_method = get_credential("SF_AUTH_METHOD")
    domain = os.environ.get("SF_DOMAIN", "login")

    if auth_method == "password":
        return Salesforce(
            username=get_credential("SF_USERNAME"),
            password=get_credential("SF_PASSWORD"),
            security_token=get_credential("SF_SECURITY_TOKEN"),
            domain=domain,
        )

    elif auth_method == "client_credentials":
        import requests

        client_id = get_credential("SF_CLIENT_ID")
        client_secret = get_credential("SF_CLIENT_SECRET")
        token_url = f"https://{domain}.salesforce.com/services/oauth2/token"

        resp = requests.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            sys.exit(
                f"Salesforce login failed ({resp.status_code}). "
                f"Check SF_CLIENT_ID / SF_CLIENT_SECRET / SF_DOMAIN in .env.\n"
                f"(Response body withheld -- it may echo back request details.)"
            )
        payload = resp.json()
        return Salesforce(
            instance_url=payload["instance_url"],
            session_id=payload["access_token"],
        )

    else:
        sys.exit(
            "SF_AUTH_METHOD must be 'password' or 'client_credentials'. "
            "See the setup instructions at the top of this script."
        )


def flatten(record):
    """Flattens Salesforce's nested relationship fields (Account.Name, etc.)
    into simple flat column names, and drops the 'attributes' metadata block."""
    flat = {}
    for key, val in record.items():
        if key == "attributes":
            continue
        if isinstance(val, dict):
            for subkey, subval in val.items():
                if subkey == "attributes":
                    continue
                flat[f"{key}.{subkey}"] = subval
        else:
            flat[key] = val
    return flat


def run_query(sf, soql, label):
    print(f"Querying {label}...")
    result = sf.query_all(soql)
    records = [flatten(r) for r in result["records"]]
    print(f"  {len(records)} {label} records returned")
    return records


def write_csv(records, path):
    if not records:
        print(f"  (no records -- skipping {path})")
        return
    fieldnames = list(records[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"  written to {path}")


def main():
    if load_dotenv:
        load_dotenv()  # loads .env from the current directory, if present

    parser = argparse.ArgumentParser(description="Pull Client and Donor data from Salesforce.")
    parser.add_argument("--output-dir", default="raw_exports", help="Where to write the CSVs")
    args = parser.parse_args()

    sf = connect()

    client_soql = os.environ.get("SF_CLIENT_SOQL", DEFAULT_CLIENT_SOQL)
    donor_soql = os.environ.get("SF_DONOR_SOQL", DEFAULT_DONOR_SOQL)

    clients = run_query(sf, client_soql, "client")
    donors = run_query(sf, donor_soql, "donor")

    out_dir = Path(args.output_dir)
    write_csv(clients, out_dir / "clients_export.csv")
    write_csv(donors, out_dir / "donors_export.csv")

    print("\nDone. Next step:")
    print(f"  python clean_salesforce_export.py {out_dir}/clients_export.csv --id-column \"Id\" "
          f"--output outputs/cleaned_clients.csv --log outputs/clients_clean_log.json")
    print(f"  python clean_salesforce_export.py {out_dir}/donors_export.csv --id-column \"Id\" "
          f"--output outputs/cleaned_donors.csv --log outputs/donors_clean_log.json")


if __name__ == "__main__":
    main()
