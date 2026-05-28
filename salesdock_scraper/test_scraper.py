#!C:\Users\robin\AppData\Local\Python\pythoncore-3.11-64\python.exe
"""
TEST RUN — requests + BeautifulSoup, no browser automation.
List pages via JSON search endpoint; detail pages parsed with BeautifulSoup.
Starts at page 140, works backwards, stops after 38 transactions.
Output: Desktop/salesdock_export/test_progress.json
Run export_test.py afterwards to produce test_export.xlsx.
"""

import json
import os
import random
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ── Configuration ─────────────────────────────────────────────────────────────
DESKTOP       = Path(os.path.expanduser("~")) / "Desktop"
EXPORT_DIR    = DESKTOP / "salesdock_export"
PROGRESS_FILE = EXPORT_DIR / "test_progress.json"
FAILED_FILE   = EXPORT_DIR / "test_failed.txt"
COOKIE_FILE   = EXPORT_DIR / "cookie.txt"

BASE_URL    = "https://app.salesdock.nl/askwadraat/admin"
SEARCH_URL  = f"{BASE_URL}/transactions/search"   # JSON endpoint
DETAIL_URL  = f"{BASE_URL}/sales/{{id}}"

START_PAGE = 140
TEST_LIMIT = 38

RETRY_COUNT = 3
RETRY_WAIT  = 5
MIN_DELAY   = 3.0
MAX_DELAY   = 7.0

# Headers for HTML detail pages
HTML_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://app.salesdock.nl/",
}

# Headers for the JSON search endpoint (mimics XHR)
JSON_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"{BASE_URL}/transactions/view/all",
}


# ── Cookie helpers ────────────────────────────────────────────────────────────
def get_cookie() -> str:
    if COOKIE_FILE.exists():
        saved = COOKIE_FILE.read_text(encoding="utf-8").strip()
        if saved:
            print(f"Using saved cookie from {COOKIE_FILE}")
            return saved

    print()
    print("=" * 60)
    print("HOW TO GET YOUR COOKIE:")
    print("  1. Open Chrome and go to app.salesdock.nl (stay logged in)")
    print("  2. Press F12 to open DevTools")
    print("  3. Click the 'Network' tab")
    print("  4. Reload the page (F5)")
    print("  5. Click on any request to salesdock.nl in the list")
    print("  6. Under 'Request Headers', find the 'cookie:' line")
    print("  7. Right-click it → Copy value")
    print("=" * 60)
    print()
    cookie = input("Paste your cookie string here and press Enter:\n> ").strip()

    if not cookie:
        print("ERROR: No cookie provided. Exiting.")
        sys.exit(1)

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    COOKIE_FILE.write_text(cookie, encoding="utf-8")
    print(f"Cookie saved to {COOKIE_FILE} (won't be asked again)")
    return cookie


# ── Progress helpers ──────────────────────────────────────────────────────────
def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"transactions": [], "scraped_ids": []}


def save_progress(data: dict) -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = PROGRESS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(PROGRESS_FILE)


def log_failed(transaction_id: str) -> None:
    with open(FAILED_FILE, "a", encoding="utf-8") as f:
        f.write(f"{transaction_id}\n")


# ── HTTP helpers ──────────────────────────────────────────────────────────────
def fetch_json(session: requests.Session, page: int) -> dict | None:
    """Fetch one page from the JSON search endpoint."""
    params = {"new_filter": "true", "q": "", "page": page}
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = session.get(SEARCH_URL, params=params, headers=JSON_HEADERS, timeout=30)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except ValueError:
                    print(f"  [WARN] Response is not JSON (got HTML?) — cookie may be expired")
                    print(f"  First 200 chars: {resp.text[:200]}")
                    return None
            print(f"  [RETRY {attempt}/{RETRY_COUNT}] HTTP {resp.status_code}")
        except requests.RequestException as e:
            print(f"  [RETRY {attempt}/{RETRY_COUNT}] Request error: {e}")
        if attempt < RETRY_COUNT:
            time.sleep(RETRY_WAIT)
    return None


def fetch_html(session: requests.Session, url: str) -> BeautifulSoup | None:
    """Fetch an HTML detail page and return a BeautifulSoup object."""
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = session.get(url, headers=HTML_HEADERS, timeout=30)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "lxml")
            print(f"  [RETRY {attempt}/{RETRY_COUNT}] HTTP {resp.status_code} for {url}")
        except requests.RequestException as e:
            print(f"  [RETRY {attempt}/{RETRY_COUNT}] Request error: {e}")
        if attempt < RETRY_COUNT:
            time.sleep(RETRY_WAIT)
    return None


# ── JSON list parsing ─────────────────────────────────────────────────────────
def extract_ids_from_json(data: dict) -> list[str]:
    """
    Pull transaction IDs from the search JSON response.
    Handles common Laravel pagination shapes:
      { "data": [ {"id": 123, ...}, ... ], "last_page": N, ... }
      { "transactions": [ ... ] }
      [ {"id": 123}, ... ]   (bare array)
    """
    rows = []

    if isinstance(data, list):
        rows = data
    elif "data" in data:
        rows = data["data"]
    else:
        # Try any key whose value is a list
        for v in data.values():
            if isinstance(v, list) and v:
                rows = v
                break

    ids = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        # Try common id field names
        for key in ("id", "ID", "transaction_id", "transactie_id"):
            if key in row:
                ids.append(str(row[key]))
                break
    return ids


def get_last_page(data: dict) -> int:
    """Read the last page number from the pagination envelope."""
    for key in ("last_page", "lastPage", "total_pages", "pages"):
        if key in data and isinstance(data[key], int):
            return data[key]
    return 1


# ── Detail page parsing ───────────────────────────────────────────────────────
def find_field(soup: BeautifulSoup, labels: list[str]) -> str:
    for label in labels:
        label_lower = label.lower()

        for dt in soup.find_all("dt"):
            if label_lower in dt.get_text(strip=True).lower():
                dd = dt.find_next_sibling("dd")
                if dd:
                    val = dd.get_text(" ", strip=True)
                    if val:
                        return val

        for th in soup.find_all("th"):
            if label_lower in th.get_text(strip=True).lower():
                td = th.find_next_sibling("td")
                if td:
                    val = td.get_text(" ", strip=True)
                    if val:
                        return val

        for lbl in soup.find_all("label"):
            if label_lower in lbl.get_text(strip=True).lower():
                for sibling in lbl.next_siblings:
                    if hasattr(sibling, "get_text"):
                        val = sibling.get_text(" ", strip=True)
                        if val:
                            return val

        el = soup.find(attrs={"data-label": re.compile(re.escape(label), re.I)})
        if el:
            val = el.get_text(" ", strip=True)
            if val:
                return val

    return ""


def extract_transaction(soup: BeautifulSoup, transaction_id: str) -> dict:
    fields = {
        "Customer name":          ["Relatie", "Naam", "Klantnaam"],
        "Delivery address":       ["Leveringsadres"],
        "Correspondence address": ["Correspondentieadres"],
        "Email":                  ["E-mail", "Email"],
        "Phone":                  ["Telefoon", "Tel"],
        "Date of birth":          ["Geboortedatum"],
        "IBAN":                   ["IBAN"],
        "IBAN account name":      ["IBAN tenaamstelling", "Tenaamstelling"],
        "Product name":           ["Product", "Productnaam"],
        "Status":                 ["Status"],
        "Seller":                 ["Verkoper"],
        "Organisation":           ["Organisatie", "Aangemaakt door organisatie"],
        "Flow":                   ["Flow"],
        "Date created":           ["Datum aangemaakt", "Aangemaakt"],
        "Date updated":           ["Datum geupdate", "Geupdate"],
        "Contract sign date":     ["Contract tekendatum", "Tekendatum"],
        "Outgoing ID":            ["Uitgaand ID"],
        "Outgoing date":          ["Uitgaand datum"],
        "Sale type":              ["Sale type", "Saletype"],
        "Type":                   ["Type"],
        "Monthly price":          ["Uiteindelijk per maand", "Per maand"],
    }

    record = {"Transaction ID": transaction_id}
    for field_key, label_variants in fields.items():
        record[field_key] = find_field(soup, label_variants)
    return record


# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    cookie = get_cookie()

    progress = load_progress()
    scraped_ids: set = set(progress.get("scraped_ids", []))
    transactions: list = progress.get("transactions", [])

    if scraped_ids:
        print(f"Resuming — {len(scraped_ids)} transactions already scraped.")

    session = requests.Session()
    session.headers.update({"Cookie": cookie})

    counter = len(transactions)
    done = False

    # Probe page 1 first to get the real last page number
    print(f"\nProbing page 1 to detect total pages …")
    probe = fetch_json(session, 1)
    if probe is None:
        print("ERROR: Could not reach the search endpoint. Check your cookie.")
        print(f"Delete {COOKIE_FILE} and re-run to paste a fresh cookie.")
        sys.exit(1)

    last_page = get_last_page(probe)
    actual_start = min(START_PAGE, last_page)
    print(f"Total pages: {last_page}  |  Starting from page: {actual_start}")

    for page_num in range(actual_start, 0, -1):
        if done:
            break

        print(f"\n── Page {page_num} (counting down to 1) ──")

        data = fetch_json(session, page_num)
        if data is None:
            print(f"  [SKIP] Could not load page {page_num}")
            continue

        ids_on_page = extract_ids_from_json(data)
        print(f"  Found {len(ids_on_page)} transaction IDs on page {page_num}")

        if not ids_on_page:
            print(f"  [WARN] No IDs found — raw keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")

        for transaction_id in ids_on_page:
            if counter >= TEST_LIMIT:
                print(f"\nTest limit of {TEST_LIMIT} transactions reached. Stopping.")
                done = True
                break

            if transaction_id in scraped_ids:
                print(f"  [SKIP] ID {transaction_id} already scraped")
                continue

            time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

            detail_url = DETAIL_URL.format(id=transaction_id)
            detail_soup = fetch_html(session, detail_url)

            if detail_soup is None:
                print(f"  [FAILED] Skipping ID {transaction_id} after {RETRY_COUNT} retries")
                log_failed(transaction_id)
                continue

            record = extract_transaction(detail_soup, transaction_id)
            counter += 1
            transactions.append(record)
            scraped_ids.add(transaction_id)
            print(f"[TEST] Transactie {counter}/{TEST_LIMIT} — ID: {transaction_id} — Pagina {page_num}")

        save_progress({"transactions": transactions, "scraped_ids": list(scraped_ids)})

    save_progress({"transactions": transactions, "scraped_ids": list(scraped_ids)})
    print(f"\nTest run complete. {counter} transactions saved to {PROGRESS_FILE}")
    print("Run  python export_test.py  to produce test_export.xlsx")


if __name__ == "__main__":
    run()
