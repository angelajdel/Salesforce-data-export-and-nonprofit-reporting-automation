#!/usr/bin/env python3
"""
create_deadline_calendar_invites.py
---------------------------------
Reads deadlines.json, and for any deadline crossing a reminder threshold
(default: 10 days out), automatically creates a Google Calendar event on
the due date and invites the assigned staff member -- Google sends them the
calendar invite (with Accept/Decline) itself. Records that the invite went
out so it's never sent twice for the same threshold.

This is meant to run on a SCHEDULE (see .github/workflows/deadline-reminders.yml)
so it fires automatically, once a day, with no browser tab open and no one
having to click anything.

WHERE CREDENTIALS LIVE
------------------------
This script authenticates with a Google Service Account -- not anyone's
personal Google login. When run through the included GitHub Action, the
service account's key comes from an encrypted GitHub Secret (Settings ->
Secrets and variables -> Actions) -- never written in this file, never
visible in logs. If you run it locally instead, save the key file
somewhere outside this repo and point GOOGLE_SERVICE_ACCOUNT_JSON_PATH at
it (see .env pattern used by the other scripts) -- never commit the key file.

ONE-TIME GOOGLE CLOUD SETUP (done once, by whoever administers your Google
Workspace / Google Cloud):
  1. Go to console.cloud.google.com -> create (or reuse) a project.
  2. APIs & Services -> Library -> enable the "Google Calendar API."
  3. APIs & Services -> Credentials -> Create Credentials -> Service Account.
     Give it a name like "impact-hub-calendar-bot." No special roles needed.
  4. Open the new service account -> Keys -> Add Key -> Create new key ->
     JSON. This downloads a .json key file -- this is the credential. Treat
     it like a password.
  5. In Google Calendar (the web app), create or choose a calendar these
     invites should be created on (a shared team calendar works well --
     personal calendars work too). Open its Settings -> "Share with
     specific people" -> add the service account's email address (it looks
     like impact-hub-calendar-bot@your-project.iam.gserviceaccount.com,
     found in the JSON key file as "client_email") -> give it
     "Make changes to events" permission.
  6. Still in that calendar's Settings, scroll to "Integrate calendar" and
     copy the Calendar ID (often your own email address, or a long string
     ending in @group.calendar.google.com for a new shared calendar).

Required environment variables:
    GOOGLE_SERVICE_ACCOUNT_JSON   the full contents of the service account's
                                  JSON key file (paste the whole file as the
                                  secret's value)
    GOOGLE_CALENDAR_ID            the calendar ID from step 6 above

USAGE
-----
    python create_deadline_calendar_invites.py --file deadlines.json --days-before 10

Run it manually to test, or let the GitHub Action run it daily.
"""

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:
    sys.exit(
        "Missing dependencies. Install them with:\n"
        "  pip install google-api-python-client google-auth"
    )

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def get_required_env(name):
    val = os.environ.get(name)
    if not val:
        sys.exit(f"Missing required environment variable: {name}")
    return val


def days_until(date_str):
    due = datetime.strptime(date_str, "%Y-%m-%d").date()
    return (due - date.today()).days


def get_calendar_service():
    key_json = get_required_env("GOOGLE_SERVICE_ACCOUNT_JSON")
    try:
        key_info = json.loads(key_json)
    except json.JSONDecodeError:
        sys.exit(
            "GOOGLE_SERVICE_ACCOUNT_JSON doesn't look like valid JSON. "
            "Paste the *entire contents* of the downloaded key file as the secret's value."
        )
    credentials = service_account.Credentials.from_service_account_info(key_info, scopes=SCOPES)
    return build("calendar", "v3", credentials=credentials)


def create_invite(service, calendar_id, assignee_email, assignee_name, task, due_date, days_left):
    when = "today" if days_left == 0 else f"in {days_left} day{'s' if days_left != 1 else ''}"
    event = {
        "summary": f"Deadline: {task}",
        "description": (
            f"Hi {assignee_name or 'there'} -- \"{task}\" is due {when} ({due_date}).\n\n"
            f"This invite was created automatically by Impact Hub because the deadline "
            f"is coming up. Please make sure it's ready ahead of the monthly meeting."
        ),
        "start": {"date": due_date},
        "end": {"date": due_date},
        "attendees": [{"email": assignee_email}] if assignee_email else [],
        "reminders": {"useDefault": True},
    }
    service.events().insert(
        calendarId=calendar_id,
        body=event,
        sendUpdates="all",  # this is what makes Google actually email the invite to attendees
    ).execute()


def main():
    parser = argparse.ArgumentParser(description="Create automatic Google Calendar invites for upcoming deadlines.")
    parser.add_argument("--file", default="deadlines.json", help="Path to the deadlines JSON file")
    parser.add_argument("--days-before", type=int, default=10, help="How many days before the deadline to send the invite")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        sys.exit(f"{path} not found.")

    calendar_id = get_required_env("GOOGLE_CALENDAR_ID")
    service = get_calendar_service()

    deadlines = json.loads(path.read_text())
    changed = False
    sent_count = 0

    for d in deadlines:
        if d.get("status") == "done":
            continue
        if not d.get("assigneeEmail"):
            print(f"Skipping '{d['task']}' -- no assignee email on file.")
            continue

        remaining = days_until(d["dueDate"])
        already_sent = args.days_before in d.get("remindersSent", [])

        # Fires once the deadline is within the threshold, and only once per threshold --
        # so a workflow that's a day late still catches it, but never double-invites.
        if remaining <= args.days_before and not already_sent:
            print(f"Creating calendar invite for '{d['task']}' -> {d['assigneeEmail']} ({remaining} day(s) left)...")
            create_invite(
                service, calendar_id,
                d["assigneeEmail"], d.get("assigneeName", ""),
                d["task"], d["dueDate"], remaining,
            )
            d.setdefault("remindersSent", []).append(args.days_before)
            changed = True
            sent_count += 1

    if changed:
        path.write_text(json.dumps(deadlines, indent=2) + "\n")
        print(f"\n{sent_count} calendar invite(s) created. {path} updated so they won't be sent again.")
    else:
        print("No invites due today.")


if __name__ == "__main__":
    main()
