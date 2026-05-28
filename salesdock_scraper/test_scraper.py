#!C:\Users\robin\AppData\Local\Programs\Python\Python314\python.exe
"""
TEST RUN — requests + BeautifulSoup, no browser automation.
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
DESKTOP     = Path(os.path.expanduser("~")) / "Desktop"
EXPORT_DIR  = DESKTOP / "salesdock_export"
PROGRESS_FILE = EXPORT_DIR / "test_progress.json"
FAILED_FILE   = EXPORT_DIR / "test_failed.txt"
COOKIE_FILE   = EXPORT_DIR / "cookie.txt"          # saved so you only paste once

BASE_URL   = "https://app.salesdock.nl/askwadraat/admin"
LIST_URL   = f"{BASE_URL}/transactions/view/all"
DETAIL_URL = f"{BASE_URL}/sales/{{id}}"

START_PAGE = 140
TEST_LIMIT = 38

RETRY_COUNT = 3
RETRY_WAIT  = 5    # seconds between retries
MIN_DELAY   = 3.0  # seconds between requests
MAX_DELAY   = 7.0

HEADERS = {
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


# ── HTTP helper ───────────────────────────────────────────────────────────────
def fetch(session: requests.Session, url: str) -> BeautifulSoup | None:
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "lxml")
            print(f"  [RETRY {attempt}/{RETRY_COUNT}] HTTP {resp.status_code} for {url}")
        except requests.RequestException as e:
            print(f"  [RETRY {attempt}/{RETRY_COUNT}] Request error: {e}")
        if attempt < RETRY_COUNT:
            time.sleep(RETRY_WAIT)
    return None


# ── Parsing: transaction list ─────────────────────────────────────────────────
def get_transaction_ids(soup: BeautifulSoup) -> list[str]:
    ids = []
    seen = set()

    # Strategy 1: anchor tags linking to /admin/sales/{id}
    for a in soup.find_all("a", href=re.compile(r"/admin/sales/\d+")):
        m = re.search(r"/sales/(\d+)", a["href"])
        if m and m.group(1) not in seen:
            ids.append(m.group(1))
            seen.add(m.group(1))

    if ids:
        return ids

    # Strategy 2: first <td> of each table row contains a bare number
    for row in soup.select("table tbody tr"):
        cells = row.find_all("td")
        if cells:
            txt = cells[0].get_text(strip=True)
            if txt.isdigit() and txt not in seen:
                ids.append(txt)
                seen.add(txt)

    return ids


def get_total_pages(soup: BeautifulSoup) -> int:
    """Read the highest page number from the pagination block."""
    nums = []
    for a in soup.select("ul.pagination a, nav a[href*='page=']"):
        txt = a.get_text(strip=True)
        if txt.isdigit():
            nums.append(int(txt))
        # also check href ?page=N
        href = a.get("href", "")
        m = re.search(r"page=(\d+)", href)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) if nums else 1


# ── Parsing: transaction detail ───────────────────────────────────────────────
def find_field(soup: BeautifulSoup, labels: list[str]) -> str:
    """
    Try several HTML patterns to locate a labelled value.
    Returns the first non-empty match, or "".
    """
    for label in labels:
        label_lower = label.lower()

        # Pattern 1: <dt>Label</dt><dd>Value</dd>
        for dt in soup.find_all("dt"):
            if label_lower in dt.get_text(strip=True).lower():
                dd = dt.find_next_sibling("dd")
                if dd:
                    val = dd.get_text(" ", strip=True)
                    if val:
                        return val

        # Pattern 2: <th>Label</th><td>Value</td>
        for th in soup.find_all("th"):
            if label_lower in th.get_text(strip=True).lower():
                td = th.find_next_sibling("td")
                if td:
                    val = td.get_text(" ", strip=True)
                    if val:
                        return val

        # Pattern 3: <label>Label</label> … sibling text node or <span>/<p>
        for lbl in soup.find_all("label"):
            if label_lower in lbl.get_text(strip=True).lower():
                for sibling in lbl.next_siblings:
                    if hasattr(sibling, "get_text"):
                        val = sibling.get_text(" ", strip=True)
                        if val:
                            return val

        # Pattern 4: element with data-label attribute
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

    for page_num in range(START_PAGE, 0, -1):
        if done:
            break

        print(f"\n── Page {page_num} (counting down from {START_PAGE}) ──")

        url = f"{LIST_URL}?page={page_num}"
        soup = fetch(session, url)
        if soup is None:
            print(f"  [SKIP] Could not load list page {page_num}")
            continue

        # Check if we've been redirected to a login page
        if "login" in (soup.title.string or "").lower() if soup.title else False:
            print("\nERROR: Session expired or cookie is invalid.")
            print(f"Delete {COOKIE_FILE} and re-run the script to paste a fresh cookie.")
            sys.exit(1)

        ids_on_page = get_transaction_ids(soup)
        print(f"  Found {len(ids_on_page)} transaction IDs on page {page_num}")

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
            detail_soup = fetch(session, detail_url)

            if detail_soup is None:
                print(f"  [FAILED] Could not load ID {transaction_id} after {RETRY_COUNT} retries")
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
