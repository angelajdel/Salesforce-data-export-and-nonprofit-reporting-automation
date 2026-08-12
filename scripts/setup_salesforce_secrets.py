#!/usr/bin/env python3
"""
setup_salesforce_secrets.py
---------------------------------
A friendly, one-time setup wizard that asks a few plain questions and
handles the technical part of getting your Salesforce credentials into
GitHub Secrets -- no need to find your way around GitHub's Settings pages.

WHAT THIS DOES
---------------
GitHub Secrets have to be encrypted before they're sent to GitHub -- that's
just how GitHub's API works, for anyone setting a secret, not just here.
This script:
  1. Asks you a few questions (which Salesforce login method you're using,
     and the actual values)
  2. Fetches your repository's public encryption key from GitHub
  3. Encrypts each value correctly using PyNaCl (a well-tested, correct
     implementation of the exact encryption GitHub requires)
  4. Sends each encrypted value to GitHub as a secret

Nothing is ever printed back to the screen after you type it, nothing is
saved to a file, and nothing goes anywhere except directly to GitHub's own
API. The plaintext values only ever exist in memory while this script runs.

WHAT YOU'LL NEED BEFORE RUNNING THIS
--------------------------------------
1. Your Salesforce login info (see the setup instructions at the top of
   fetch_salesforce_data.py if you haven't set up a Salesforce connection
   before -- you need EITHER a username/password/security token OR a
   Connected App's Client ID/Secret).

2. A GitHub Personal Access Token with permission to manage this repo's
   secrets:
     - Classic token (github.com/settings/tokens/new): check the "repo" scope
     - Fine-grained token: under this repo's permissions, set
       "Secrets: Read and write"
   This token is only used by this script, right now, to set things up --
   revoke it afterward the same as you would any setup token.

USAGE
-----
    pip install requests pynacl
    python setup_salesforce_secrets.py
"""

import base64
import getpass
import sys

import requests
from nacl import encoding, public


def prompt(question, default=None, secret=False):
    suffix = f" [{default}]" if default else ""
    reader = getpass.getpass if secret else input
    val = reader(f"{question}{suffix}: ").strip()
    return val or default


def get_public_key(repo, token):
    resp = requests.get(
        f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    if resp.status_code != 200:
        sys.exit(
            f"Couldn't reach that repo's secrets settings (HTTP {resp.status_code}).\n"
            f"Double check the repo name and that your token has 'repo' scope "
            f"(classic) or 'Secrets: Read and write' (fine-grained).\n{resp.text}"
        )
    return resp.json()


def encrypt_secret(public_key_b64, secret_value):
    public_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def set_secret(repo, token, key_id, public_key_b64, name, value):
    if not value:
        print(f"  (skipping {name} -- no value given)")
        return
    encrypted_value = encrypt_secret(public_key_b64, value)
    resp = requests.put(
        f"https://api.github.com/repos/{repo}/actions/secrets/{name}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        json={"encrypted_value": encrypted_value, "key_id": key_id},
    )
    if resp.status_code in (201, 204):
        print(f"  \u2713 {name} set")
    else:
        print(f"  \u2717 {name} failed (HTTP {resp.status_code}): {resp.text}")


def main():
    print("Impact Hub -- Salesforce secrets setup")
    print("---------------------------------------")
    print("This sets up the GitHub Actions automation that pulls fresh data from")
    print("Salesforce on a schedule. Nothing you type here is saved to a file.\n")

    repo = prompt("GitHub repo (e.g. angelajdel/your-repo-name)")
    token = prompt("GitHub Personal Access Token", secret=True)

    print("\nFetching this repo's encryption key from GitHub...")
    key_info = get_public_key(repo, token)
    key_id = key_info["key_id"]
    public_key_b64 = key_info["key"]
    print("Got it.\n")

    print("Which way do you log into Salesforce?")
    print("  1) Username, password, and security token")
    print("  2) A Connected App (Client ID / Client Secret)")
    choice = prompt("Enter 1 or 2", default="1")

    secrets_to_set = {}

    if choice == "2":
        secrets_to_set["SF_AUTH_METHOD"] = "client_credentials"
        secrets_to_set["SF_CLIENT_ID"] = prompt("Salesforce Connected App Client ID", secret=True)
        secrets_to_set["SF_CLIENT_SECRET"] = prompt("Salesforce Connected App Client Secret", secret=True)
    else:
        secrets_to_set["SF_AUTH_METHOD"] = "password"
        secrets_to_set["SF_USERNAME"] = prompt("Salesforce username (your login email)")
        secrets_to_set["SF_PASSWORD"] = prompt("Salesforce password", secret=True)
        secrets_to_set["SF_SECURITY_TOKEN"] = prompt("Salesforce security token (emailed to you by Salesforce)", secret=True)

    domain = prompt("Is this a Sandbox org? (yes/no)", default="no")
    secrets_to_set["SF_DOMAIN"] = "test" if domain.lower().startswith("y") else "login"

    customize = prompt("\nDo you want to customize the Salesforce queries now? (yes/no)", default="no")
    if customize.lower().startswith("y"):
        secrets_to_set["SF_CLIENT_SOQL"] = prompt("Client SOQL query (leave blank to use the default)")
        secrets_to_set["SF_DONOR_SOQL"] = prompt("Donor SOQL query (leave blank to use the default)")

    print("\nSending everything to GitHub...")
    for name, value in secrets_to_set.items():
        set_secret(repo, token, key_id, public_key_b64, name, value)

    print("\nDone. Go to your repo's Actions tab and run 'Salesforce Sync' manually")
    print("to test it -- no need to wait for tomorrow's scheduled run.")
    print("\nOne last thing: go revoke the GitHub token you just used, the same way")
    print("you would after any one-time setup task.")


if __name__ == "__main__":
    main()
