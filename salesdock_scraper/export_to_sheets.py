"""
Export scraped Salesdock transactions to Google Sheets.

Prerequisites:
  1. Create a Google Cloud project and enable the Sheets + Drive APIs.
  2. Create a Service Account, download the JSON key, and save it as:
       Desktop/salesdock_export/google_credentials.json
  3. Share your target Google Sheet with the service account e-mail address
     (found in the JSON file under "client_email") as Editor.

Run after scraper.py has finished (or at any point to sync progress).
"""

import json
import os
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

# ── Configuration ────────────────────────────────────────────────────────────
DESKTOP = Path(os.path.expanduser("~")) / "Desktop"
EXPORT_DIR = DESKTOP / "salesdock_export"
PROGRESS_FILE = EXPORT_DIR / "progress.json"
CREDENTIALS_FILE = EXPORT_DIR / "google_credentials.json"

# Paste your Google Sheet URL or just the spreadsheet ID here:
# e.g. "https://docs.google.com/spreadsheets/d/XXXXXXXX/edit"
# or just "XXXXXXXX"
SPREADSHEET_ID_OR_URL = "PASTE_YOUR_SPREADSHEET_ID_OR_URL_HERE"

WORKSHEET_NAME = "Transactions"

# Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLUMN_ORDER = [
    "Transaction ID",
    "Customer name",
    "Delivery address",
    "Correspondence address",
    "Email",
    "Phone",
    "Date of birth",
    "IBAN",
    "IBAN account name",
    "Product name",
    "Status",
    "Seller",
    "Organisation",
    "Flow",
    "Date created",
    "Date updated",
    "Contract sign date",
    "Outgoing ID",
    "Outgoing date",
    "Sale type",
    "Type",
    "Monthly price",
]

# Google Sheets max rows per batch write (stay under API limits)
BATCH_SIZE = 500


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_transactions() -> list[dict]:
    if not PROGRESS_FILE.exists():
        raise FileNotFoundError(f"Progress file not found: {PROGRESS_FILE}")
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("transactions", [])


def get_spreadsheet(client: gspread.Client):
    if SPREADSHEET_ID_OR_URL.startswith("https://"):
        return client.open_by_url(SPREADSHEET_ID_OR_URL)
    return client.open_by_key(SPREADSHEET_ID_OR_URL)


def get_or_create_worksheet(spreadsheet, name: str) -> gspread.Worksheet:
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=name, rows=30000, cols=len(COLUMN_ORDER))


def rows_to_values(transactions: list[dict]) -> list[list]:
    result = []
    for t in transactions:
        row = [t.get(col, "") for col in COLUMN_ORDER]
        result.append(row)
    return result


# ── Main export ───────────────────────────────────────────────────────────────
def export():
    if SPREADSHEET_ID_OR_URL == "PASTE_YOUR_SPREADSHEET_ID_OR_URL_HERE":
        print("ERROR: Set SPREADSHEET_ID_OR_URL in export_to_sheets.py before running.")
        return

    if not CREDENTIALS_FILE.exists():
        print(f"ERROR: Credentials file not found at {CREDENTIALS_FILE}")
        print("See the Prerequisites section at the top of this file.")
        return

    print(f"Loading transactions from {PROGRESS_FILE} …")
    transactions = load_transactions()
    print(f"  {len(transactions)} transactions loaded.")

    print("Authenticating with Google …")
    creds = Credentials.from_service_account_file(str(CREDENTIALS_FILE), scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet = get_spreadsheet(client)
    ws = get_or_create_worksheet(spreadsheet, WORKSHEET_NAME)
    print(f"  Using worksheet '{WORKSHEET_NAME}' in '{spreadsheet.title}'")

    # Clear existing data and write header
    print("Writing header row …")
    ws.clear()
    ws.append_row(COLUMN_ORDER, value_input_option="RAW")

    # Write data in batches
    all_rows = rows_to_values(transactions)
    total = len(all_rows)
    written = 0

    for i in range(0, total, BATCH_SIZE):
        batch = all_rows[i : i + BATCH_SIZE]
        # append_rows is faster than repeated append_row
        ws.append_rows(batch, value_input_option="RAW")
        written += len(batch)
        print(f"  Uploaded {written}/{total} rows …")

    print(f"\nDone! {total} rows written to Google Sheets.")
    print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit")


if __name__ == "__main__":
    export()
