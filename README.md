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

## Automatic Google Calendar invites (10 days before a deadline)

The Deadlines tab inside Impact Hub can email a reminder with one click, but
a browser tab can't act on a timer with nobody watching — that needs
something that runs on a schedule independent of anyone having the tool
open. This repo includes exactly that, using GitHub Actions (free for
public and most private repos), and instead of an email, it creates a real
**Google Calendar invite** — the assigned staff member gets it on their
calendar with Accept/Decline, the same as any meeting invite.

**How it works:** `deadlines.json` in this repo is the shared source of
truth. Once a day, a GitHub Action runs
`scripts/create_deadline_calendar_invites.py`, which checks every deadline
and creates a calendar event — dated on the due date, with the assigned
staff member added as an attendee — once it's within 10 days out. Google
sends the invite itself; no one has to open anything.

**One-time setup (Google Cloud side):**
1. Go to [console.cloud.google.com](https://console.cloud.google.com) →
   create (or reuse) a project.
2. **APIs & Services → Library** → enable the **Google Calendar API**.
3. **APIs & Services → Credentials → Create Credentials → Service Account.**
   Name it something like `impact-hub-calendar-bot`. No special roles needed.
4. Open the new service account → **Keys → Add Key → Create new key → JSON.**
   This downloads a `.json` key file — treat it like a password.
5. In Google Calendar (the web app), pick or create the calendar these
   invites should be created on (a shared team calendar works well).
   Open its **Settings → Share with specific people** → add the service
   account's email (looks like `impact-hub-calendar-bot@your-project.iam.gserviceaccount.com`,
   found in the key file as `"client_email"`) → give it **"Make changes to
   events"** permission.
6. Still in that calendar's Settings, scroll to **"Integrate calendar"**
   and copy the **Calendar ID**.

**One-time setup (GitHub side):**
1. Push this repo to GitHub if you haven't already.
2. **Settings → Secrets and variables → Actions → New repository secret.**
   Add two secrets:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` — paste the **entire contents** of the
     downloaded key file
   - `GOOGLE_CALENDAR_ID` — the Calendar ID from step 6 above
3. That's it. `.github/workflows/deadline-reminders.yml` runs automatically
   every day at 8am UTC. You can also trigger it manually anytime from the
   repo's **Actions** tab, to test it without waiting for the schedule.

**Keeping `deadlines.json` current:** whenever you update deadlines inside
Impact Hub, click **"Download deadlines.json"** on the Export & Present step,
then commit that file to the repo (drag-and-drop upload works fine, same as
any other file). The automation only knows about what's in that file — it
doesn't read the browser tool's storage directly, since that storage only
exists while the Impact Hub page itself is open.

**Change the invite window:** edit `--days-before 10` in
`.github/workflows/deadline-reminders.yml` to whatever number of days you'd
rather be warned. Each deadline tracks which thresholds it's already
triggered (`remindersSent` in the JSON), so nothing gets double-invited for
the same deadline.

## Exporting into the Ignite FY26 Outcomes Template

If your organization already tracks outcomes in the real Ignite-style FY26
template (monthly/quarterly columns across Domains of Care, Reasons for
Homelessness, Program Counts, Utilization, and per-program detail),
Impact Hub can export directly into it without you retyping anything.

**In Impact Hub:** on the Export & Present step, under "Export for the
Ignite FY26 Outcomes Template," pick which month this data represents and
click **"Download outcomes_export.json."** This is a small data file, not
the spreadsheet itself.

**Then run:**
```bash
python scripts/fill_ignite_template.py \
    --template "Ignite_FY26_Outcomes_-_Template.xlsx" \
    --data outcomes_export.json \
    --month Aug \
    --output "Ignite_FY26_Outcomes_-_Filled.xlsx"
```

This opens your **actual template file** and writes values only into the
cells Impact Hub can compute:
- Education and Employment (30+) domain
- Reasons for Homelessness (matched by keyword to your configured Reason categories)
- Total youth served, and active-youth counts per program
- Utilization % (overall, and per program)

Everything else in your template — New Enrollments, per-program exit
detail, Street Outreach, Residential Therapy, quarterly/FY26 rollup columns,
goals, and prior-year actuals — is left exactly as it already is. The
script tells you exactly which rows it filled and which it skipped (and
why), so nothing is silently missed.

Run it again each month with that month's export, pointing `--template` at
last month's filled copy if you want to build up the full year in one file.

## Automated Salesforce sync (no manual export, ever)

`scripts/fetch_salesforce_data.py` and `scripts/clean_salesforce_export.py`
already existed for running by hand. This turns that into something that
runs itself: a GitHub Action pulls fresh Client and Donor data straight from
Salesforce, cleans it, and commits the result back to this repo automatically
— every weekday morning, with nobody running anything.

**How it works:** `.github/workflows/salesforce-sync.yml` runs on a
schedule, authenticates to Salesforce using credentials stored as encrypted
GitHub Secrets, runs the same SOQL queries and cleaning logic as the manual
scripts, and commits the cleaned files to `data/cleaned_clients.csv` and
`data/cleaned_donors.csv` in this repo.

**One-time setup:**
1. Set up a Salesforce Connected App (or username/password/security token)
   — see the setup instructions at the top of `scripts/fetch_salesforce_data.py`
   for exactly how, either auth method works here too.
2. In your GitHub repo: **Settings → Secrets and variables → Actions → New
   repository secret.** Add whichever set matches your auth method:
   - Username/password flow: `SF_AUTH_METHOD` (`password`), `SF_USERNAME`,
     `SF_PASSWORD`, `SF_SECURITY_TOKEN`, `SF_DOMAIN`
   - Client credentials flow: `SF_AUTH_METHOD` (`client_credentials`),
     `SF_CLIENT_ID`, `SF_CLIENT_SECRET`, `SF_DOMAIN`
   - Optional, either way: `SF_CLIENT_SOQL` / `SF_DONOR_SOQL` to override the
     default queries with your org's actual object/field names
3. That's it. The workflow runs automatically every weekday at 12:00 UTC.
   Trigger it manually anytime from the repo's **Actions** tab to test it
   without waiting for the schedule.

**What this does NOT do yet:** it keeps the data in this GitHub repo current
automatically, but Impact Hub itself (the browser tool) still needs that
data brought in via the Import step — it doesn't reach out and fetch
anything on its own, since it's a static page with no server behind it.
Bridging that last step (an in-page "Sync from GitHub" button that loads
`data/cleaned_clients.csv` directly from this repo) is a natural next
addition once this pipeline is confirmed working.
