# Nonprofit Monthly Reporting Toolkit

A repeatable workflow for turning a raw Salesforce export into a clean
dataset, a formatted Excel dashboard, an eye-catching presentation, and
meeting-ready talking points — every month, with the same steps.

## What's included

| File | Purpose |
|---|---|
| `scripts/clean_salesforce_export.py` | Removes test records (ID contains "TEST") and duplicate rows from a raw export |
| `scripts/build_excel_report.py` | Builds the formatted, multi-tab Excel dashboard from the cleaned data |
| `scripts/build_presentation.js` | Builds the monthly PowerPoint deck |
| `Monthly_Meeting_Prompt.md` | A copy-paste AI prompt for turning the numbers into talking points |
| `sample_data/` | Example raw exports (with intentional test records & duplicates) used to build the demo outputs |
| `outputs/` | The generated cleaned CSVs, Excel workbook, and presentation |

## The monthly workflow

**1. Export from Salesforce.**
In Salesforce, run/export your Client report and your Donor (Opportunity)
report as CSV. Keep the ID column in the export — it's what the cleaning
script checks for "TEST" in the ID (e.g. `003TEST001`).

**2. Clean each export:**
```bash
python scripts/clean_salesforce_export.py clients_export.csv \
    --id-column "Client ID" \
    --output outputs/cleaned_clients.csv \
    --log outputs/clients_clean_log.json

python scripts/clean_salesforce_export.py donors_export.csv \
    --id-column "Donor ID" \
    --output outputs/cleaned_donors.csv \
    --log outputs/donors_clean_log.json
```
This strips any row whose ID contains "TEST" (case-insensitive) and drops
exact duplicate IDs, keeping the first occurrence of each. It also writes a
JSON log of exactly what was removed, so nothing disappears without a trail.

**3. Build the Excel dashboard:**
```bash
python scripts/build_excel_report.py \
    --clients outputs/cleaned_clients.csv \
    --donors outputs/cleaned_donors.csv \
    --clients-log outputs/clients_clean_log.json \
    --donors-log outputs/donors_clean_log.json \
    --output outputs/Monthly_Report.xlsx
```
This produces a workbook with:
- **Dashboard** — KPI tiles (active clients, total raised, donor count) with
  live formulas, plus a bar chart of clients by program and a pie chart of
  donations by campaign
- **Clients** and **Donors** — full cleaned lists, formatted as tables
- **Data Cleanup Log** — an audit trail of what was excluded and why

**4. Build the presentation.**
Open `scripts/build_presentation.js`, update the `STATS` object at the top
with this month's numbers (client counts by program, campaign totals, top
donors, upcoming deadlines), then run:
```bash
node scripts/build_presentation.js
```
This produces `outputs/Monthly_Impact_Presentation.pptx` — a 5-slide deck
(title, KPI overview, program breakdown, fundraising breakdown, and
deadlines/next steps) ready to present as-is or drop into a larger deck.

**5. Prep your talking points.**
Open `Monthly_Meeting_Prompt.md`, fill in the brackets, and paste it into a
Claude conversation along with the new `Monthly_Report.xlsx`. You'll get a
short summary, talking points with numbers attached, anomalies worth
flagging, an opening narrative, and a clean action list of deadlines.

## About "automatic" updates

True real-time syncing (the dashboard updating itself the moment Salesforce
changes) requires a live connection — Salesforce API credentials via a
Connected App, used with a library like `simple_salesforce`. See
**"Connecting real Salesforce access"** below for exactly how to set this up
on your own machine, with your credentials never leaving it.

## Connecting real Salesforce access

`scripts/fetch_salesforce_data.py` pulls Client and Donor records straight
from Salesforce and writes them as CSVs, ready for
`clean_salesforce_export.py`. It runs entirely on your own computer — your
Salesforce credentials live in a local `.env` file that never gets pasted
into a chat, uploaded, or seen by anyone else, including Claude.

**One-time setup:**
```bash
pip install -r requirements.txt
cp .env.example .env
```
Open `.env` and fill in your real values. Ask your Salesforce admin for
either:
- **Username + password + security token** (simplest for a personal script), or
- **A Connected App with Client Credentials flow** (better if more than one
  person will run this)

Both options are explained step-by-step inside `.env.example` and at the top
of `fetch_salesforce_data.py`.

**Every month, instead of manually exporting from Salesforce:**
```bash
python scripts/fetch_salesforce_data.py --output-dir raw_exports/
```
This replaces Step 1 of the manual workflow above — everything after it
(cleaning, the Excel dashboard, the presentation, Impact Hub) works exactly
the same, because it's still just working from CSVs.

**The one part specific to your org:** the two SOQL queries near the top of
`fetch_salesforce_data.py` (`DEFAULT_CLIENT_SOQL`, `DEFAULT_DONOR_SOQL`)
assume plain `Contact` and `Opportunity` objects. Every Salesforce org names
its fields and client/donor objects a little differently, so you'll want to
point these at your actual objects — either edit the script directly, or set
`SF_CLIENT_SOQL` / `SF_DONOR_SOQL` in `.env` to override them without
touching the code. If you tell me your org's actual object and field API
names, I can write the exact queries for you.

**Keeping credentials safe:** `.gitignore` is already set up to exclude
`.env` and every generated output file. Never commit `.env`, never paste its
contents into a support ticket or chat, and rotate your security
token/client secret if you ever suspect it's been exposed.

## Adjusting for your real data

The scripts assume these column names, matching the sample data:
- Clients: `Client ID, First Name, Last Name, Email, Phone, Program, Enrollment Date, Status`
- Donors: `Donor ID, Donor Name, Email, Amount, Close Date, Campaign, Donation Type`

If your Salesforce export uses different column names, either rename the
columns in the exported CSV before running the scripts, or tell me your
actual export's column names and I'll adjust the scripts to match exactly.
