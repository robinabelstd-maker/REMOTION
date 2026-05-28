# Salesdock CRM Scraper

Scrapes all transactions from Salesdock and exports to Google Sheets or Excel.

---

## Prerequisites

- Python 3.10+
- Google Chrome installed
- Must already be logged into Salesdock in Chrome

---

## Setup (run once)

**Close Chrome completely before setup and before every scraper run.**

Double-click `setup_windows.bat`, or run manually:

```bat
pip install playwright gspread google-auth openpyxl
playwright install chrome
mkdir %USERPROFILE%\Desktop\salesdock_export
```

---

## Run the scraper

```bat
python scraper.py
```

- Opens Chrome using your existing profile (no login needed)
- Scrapes every transaction detail page
- Saves progress to `Desktop\salesdock_export\progress.json` every 50 transactions
- If interrupted, re-run the same command — it resumes automatically
- Failed transaction IDs are logged to `Desktop\salesdock_export\failed_transactions.txt`

---

## Export to Google Sheets

### 1. Create Google Cloud credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project → Enable **Google Sheets API** and **Google Drive API**
3. Go to **IAM & Admin → Service Accounts** → Create service account
4. Download the JSON key → save as `Desktop\salesdock_export\google_credentials.json`
5. Create a new Google Sheet and share it (Editor) with the `client_email` from the JSON

### 2. Configure and run

Open `export_to_sheets.py` and set:

```python
SPREADSHEET_ID_OR_URL = "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"
```

Then run:

```bat
python export_to_sheets.py
```

---

## Export to Excel (no Google account needed)

```bat
python export_to_excel.py
```

Output: `Desktop\salesdock_export\transactions.xlsx`

---

## File overview

| File | Purpose |
|------|---------|
| `scraper.py` | Main scraper — collects all transaction data |
| `export_to_sheets.py` | Upload results to Google Sheets |
| `export_to_excel.py` | Save results as Excel file |
| `setup_windows.bat` | One-time setup script |
| `requirements.txt` | Python dependencies |

---

## Troubleshooting

**"Chrome is already running"** — Close Chrome completely (check system tray too), then re-run.

**Login page appears** — Chrome profile path may be wrong. Verify:
`C:\Users\robin\AppData\Local\Google\Chrome\User Data`

**Fields are empty** — Salesdock may have updated their HTML. Open a transaction manually,
right-click the missing field → Inspect, and update the label strings in `scraper.py`'s
`fields` dictionary inside `extract_transaction()`.

**Rate limited / captcha** — Increase `MIN_DELAY` and `MAX_DELAY` in `scraper.py`.
