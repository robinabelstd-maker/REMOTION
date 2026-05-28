"""
Salesdock CRM Transaction Scraper
- Uses existing Chrome profile (no login required)
- Resumes from progress.json if interrupted
- Saves progress every 50 transactions
- Retries failed pages up to 3 times
"""

import asyncio
import json
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ── Configuration ────────────────────────────────────────────────────────────
CHROME_PROFILE_PATH = r"C:\Users\robin\AppData\Local\Google\Chrome\User Data"
CHROME_EXE_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DESKTOP = Path(os.path.expanduser("~")) / "Desktop"
EXPORT_DIR = DESKTOP / "salesdock_export"
PROGRESS_FILE = EXPORT_DIR / "progress.json"
FAILED_FILE = EXPORT_DIR / "failed_transactions.txt"

BASE_URL = "https://app.salesdock.nl/askwadraat/admin"
LIST_URL = f"{BASE_URL}/transactions/view/all"
DETAIL_URL = f"{BASE_URL}/sales/{{id}}"

TOTAL_APPROX = 28_000
SAVE_INTERVAL = 50
RETRY_COUNT = 3
RETRY_WAIT = 5          # seconds between retries
MIN_DELAY = 3.0         # minimum delay between detail pages
MAX_DELAY = 7.0         # maximum delay between detail pages
PAGE_TIMEOUT = 30_000   # ms


# ── Progress helpers ─────────────────────────────────────────────────────────
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


# ── Extraction helpers ────────────────────────────────────────────────────────
def text_or_empty(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


async def get_field(page, label: str) -> str:
    """
    Try multiple selector strategies for label→value pairs.
    Salesdock typically renders detail rows as:
      <dt>Label</dt><dd>Value</dd>
    or table rows with th/td pairs.
    """
    try:
        # Strategy 1: dt/dd pairs
        locator = page.locator(f"dt:has-text('{label}') + dd").first
        if await locator.count() > 0:
            return text_or_empty(await locator.inner_text(timeout=3000))

        # Strategy 2: th/td pairs
        locator = page.locator(f"th:has-text('{label}') + td").first
        if await locator.count() > 0:
            return text_or_empty(await locator.inner_text(timeout=3000))

        # Strategy 3: label/span pairs
        locator = page.locator(f"label:has-text('{label}') ~ span").first
        if await locator.count() > 0:
            return text_or_empty(await locator.inner_text(timeout=3000))

        # Strategy 4: any element with data-label attribute
        locator = page.locator(f"[data-label='{label}']").first
        if await locator.count() > 0:
            return text_or_empty(await locator.inner_text(timeout=3000))

    except Exception:
        pass
    return ""


async def extract_transaction(page, transaction_id: str) -> dict:
    """Extract all fields from an open transaction detail page."""
    record = {"Transaction ID": transaction_id}

    fields = {
        "Customer name":        ["Relatie", "Naam", "Klantnaam"],
        "Delivery address":     ["Leveringsadres"],
        "Correspondence address": ["Correspondentieadres"],
        "Email":                ["E-mail", "Email"],
        "Phone":                ["Telefoon", "Tel"],
        "Date of birth":        ["Geboortedatum"],
        "IBAN":                 ["IBAN"],
        "IBAN account name":    ["IBAN tenaamstelling", "Tenaamstelling"],
        "Product name":         ["Product", "Productnaam"],
        "Status":               ["Status"],
        "Seller":               ["Verkoper"],
        "Organisation":         ["Organisatie", "Aangemaakt door organisatie"],
        "Flow":                 ["Flow"],
        "Date created":         ["Datum aangemaakt", "Aangemaakt"],
        "Date updated":         ["Datum geupdate", "Geupdate"],
        "Contract sign date":   ["Contract tekendatum", "Tekendatum"],
        "Outgoing ID":          ["Uitgaand ID"],
        "Outgoing date":        ["Uitgaand datum"],
        "Sale type":            ["Sale type", "Saletype"],
        "Type":                 ["Type"],
        "Monthly price":        ["Uiteindelijk per maand", "Per maand"],
    }

    for field_key, label_variants in fields.items():
        value = ""
        for label in label_variants:
            value = await get_field(page, label)
            if value:
                break
        record[field_key] = value

    return record


# ── Pagination ────────────────────────────────────────────────────────────────
async def get_total_pages(page) -> int:
    """Detect total pages from pagination controls."""
    try:
        # Common pattern: last page link text is a number
        pagination = page.locator("ul.pagination li a, nav[aria-label='pagination'] a")
        count = await pagination.count()
        pages = []
        for i in range(count):
            txt = await pagination.nth(i).inner_text()
            txt = txt.strip()
            if txt.isdigit():
                pages.append(int(txt))
        if pages:
            return max(pages)

        # Fallback: look for "Pagina X van Y" text
        text_match = page.locator("text=/pagina.*van.*/i").first
        if await text_match.count() > 0:
            raw = await text_match.inner_text()
            numbers = re.findall(r"\d+", raw)
            if len(numbers) >= 2:
                return int(numbers[1])

    except Exception as e:
        print(f"  [WARN] Could not detect total pages: {e}")

    return 1


async def get_transaction_ids_on_page(page) -> list[str]:
    """Collect all transaction IDs visible in the table on the current page."""
    ids = []
    try:
        # Strategy 1: links matching /sales/{id}
        links = page.locator("a[href*='/admin/sales/']")
        count = await links.count()
        for i in range(count):
            href = await links.nth(i).get_attribute("href") or ""
            match = re.search(r"/sales/(\d+)", href)
            if match:
                tid = match.group(1)
                if tid not in ids:
                    ids.append(tid)

        if ids:
            return ids

        # Strategy 2: first column of each data row is the ID
        rows = page.locator("table tbody tr")
        row_count = await rows.count()
        for i in range(row_count):
            cell = rows.nth(i).locator("td").first
            txt = (await cell.inner_text()).strip()
            if txt.isdigit():
                ids.append(txt)

    except Exception as e:
        print(f"  [WARN] Could not collect IDs on page: {e}")

    return ids


# ── Core scraper ──────────────────────────────────────────────────────────────
async def scrape_detail(page, transaction_id: str, page_num: int, counter: int) -> dict | None:
    url = DETAIL_URL.format(id=transaction_id)

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            await page.goto(url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle", timeout=PAGE_TIMEOUT)
            record = await extract_transaction(page, transaction_id)
            print(f"Transactie {counter} van ~{TOTAL_APPROX} — ID: {transaction_id} — Pagina {page_num}")
            return record

        except PlaywrightTimeoutError:
            print(f"  [RETRY {attempt}/{RETRY_COUNT}] Timeout on ID {transaction_id}")
            if attempt < RETRY_COUNT:
                await asyncio.sleep(RETRY_WAIT)
        except Exception as e:
            print(f"  [RETRY {attempt}/{RETRY_COUNT}] Error on ID {transaction_id}: {e}")
            if attempt < RETRY_COUNT:
                await asyncio.sleep(RETRY_WAIT)

    print(f"  [FAILED] Skipping ID {transaction_id} after {RETRY_COUNT} retries")
    log_failed(transaction_id)
    return None


async def run():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    if not Path(CHROME_EXE_PATH).exists():
        print(f"ERROR: Chrome not found at {CHROME_EXE_PATH}")
        print("Update CHROME_EXE_PATH in this script to match your Chrome installation.")
        return

    # Load previous progress
    progress = load_progress()
    scraped_ids: set = set(progress.get("scraped_ids", []))
    transactions: list = progress.get("transactions", [])

    print(f"Resuming — {len(scraped_ids)} transactions already scraped.")

    async with async_playwright() as pw:
        # Use the existing Chrome profile — launch as persistent context
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE_PATH,
            channel="chrome",           # uses system Chrome at CHROME_EXE_PATH, no Playwright install needed
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
            ignore_default_args=["--enable-automation"],
            viewport=None,
        )

        page = await context.new_page()

        # ── Discover total pages ──────────────────────────────────────────────
        print("Navigating to transactions list page 1 …")
        await page.goto(f"{LIST_URL}?page=1", timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
        await page.wait_for_load_state("networkidle", timeout=PAGE_TIMEOUT)

        total_pages = await get_total_pages(page)
        print(f"Total pages detected: {total_pages}")

        counter = len(scraped_ids)

        # ── Page loop ─────────────────────────────────────────────────────────
        for page_num in range(1, total_pages + 1):
            print(f"\n── Page {page_num}/{total_pages} ──")

            if page_num > 1:
                try:
                    await page.goto(
                        f"{LIST_URL}?page={page_num}",
                        timeout=PAGE_TIMEOUT,
                        wait_until="domcontentloaded",
                    )
                    await page.wait_for_load_state("networkidle", timeout=PAGE_TIMEOUT)
                except Exception as e:
                    print(f"  [WARN] Could not load list page {page_num}: {e}")
                    continue

            ids_on_page = await get_transaction_ids_on_page(page)
            print(f"  Found {len(ids_on_page)} transaction IDs on page {page_num}")

            for transaction_id in ids_on_page:
                if transaction_id in scraped_ids:
                    print(f"  [SKIP] ID {transaction_id} already scraped")
                    continue

                # Random polite delay
                await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

                record = await scrape_detail(page, transaction_id, page_num, counter + 1)

                if record:
                    counter += 1
                    transactions.append(record)
                    scraped_ids.add(transaction_id)

                    # Periodic save
                    if counter % SAVE_INTERVAL == 0:
                        save_progress({"transactions": transactions, "scraped_ids": list(scraped_ids)})
                        print(f"  [SAVED] Progress saved ({counter} transactions)")

            # Save at end of every page too
            save_progress({"transactions": transactions, "scraped_ids": list(scraped_ids)})

        await context.close()

    # Final save
    save_progress({"transactions": transactions, "scraped_ids": list(scraped_ids)})
    print(f"\nDone! {counter} transactions scraped. Data saved to {PROGRESS_FILE}")


if __name__ == "__main__":
    asyncio.run(run())
