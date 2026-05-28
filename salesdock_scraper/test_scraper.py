#!C:\Users\robin\AppData\Local\Programs\Python\Python314\python.exe
"""
TEST RUN — scrapes 38 transactions starting from page 140, going backwards.
Saves to Desktop/salesdock_export/test_progress.json (separate from main run).
Run export_test.py afterwards to produce test_export.xlsx.
"""

import asyncio
import json
import os
import random
import re
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# ── Configuration ────────────────────────────────────────────────────────────
CHROME_PROFILE_PATH = r"C:\Users\robin\AppData\Local\Google\Chrome\User Data"
DESKTOP = Path(os.path.expanduser("~")) / "Desktop"
EXPORT_DIR = DESKTOP / "salesdock_export"
PROGRESS_FILE = EXPORT_DIR / "test_progress.json"   # separate from main run
FAILED_FILE = EXPORT_DIR / "test_failed.txt"

BASE_URL = "https://app.salesdock.nl/askwadraat/admin"
LIST_URL = f"{BASE_URL}/transactions/view/all"
DETAIL_URL = f"{BASE_URL}/sales/{{id}}"

START_PAGE = 140        # begin here, count down to page 1
TEST_LIMIT = 38         # stop after this many transactions

RETRY_COUNT = 3
RETRY_WAIT = 5
MIN_DELAY = 3.0
MAX_DELAY = 7.0
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
    try:
        locator = page.locator(f"dt:has-text('{label}') + dd").first
        if await locator.count() > 0:
            return text_or_empty(await locator.inner_text(timeout=3000))

        locator = page.locator(f"th:has-text('{label}') + td").first
        if await locator.count() > 0:
            return text_or_empty(await locator.inner_text(timeout=3000))

        locator = page.locator(f"label:has-text('{label}') ~ span").first
        if await locator.count() > 0:
            return text_or_empty(await locator.inner_text(timeout=3000))

        locator = page.locator(f"[data-label='{label}']").first
        if await locator.count() > 0:
            return text_or_empty(await locator.inner_text(timeout=3000))

    except Exception:
        pass
    return ""


async def extract_transaction(page, transaction_id: str) -> dict:
    record = {"Transaction ID": transaction_id}

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

    for field_key, label_variants in fields.items():
        value = ""
        for label in label_variants:
            value = await get_field(page, label)
            if value:
                break
        record[field_key] = value

    return record


async def get_transaction_ids_on_page(page) -> list[str]:
    ids = []
    try:
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


async def scrape_detail(page, transaction_id: str, page_num: int, counter: int) -> dict | None:
    url = DETAIL_URL.format(id=transaction_id)

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            await page.goto(url, timeout=PAGE_TIMEOUT, wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle", timeout=PAGE_TIMEOUT)
            record = await extract_transaction(page, transaction_id)
            print(f"[TEST] Transactie {counter}/{TEST_LIMIT} — ID: {transaction_id} — Pagina {page_num}")
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

    progress = load_progress()
    scraped_ids: set = set(progress.get("scraped_ids", []))
    transactions: list = progress.get("transactions", [])

    if scraped_ids:
        print(f"Resuming test run — {len(scraped_ids)} transactions already scraped.")

    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=CHROME_PROFILE_PATH,
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
            ignore_default_args=["--enable-automation"],
            viewport=None,
        )

        page = await context.new_page()

        counter = len(transactions)
        done = False

        # Iterate pages from START_PAGE down to 1
        for page_num in range(START_PAGE, 0, -1):
            if done:
                break

            print(f"\n── Page {page_num} (counting down from {START_PAGE}) ──")

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
                if counter >= TEST_LIMIT:
                    print(f"\nTest limit of {TEST_LIMIT} transactions reached. Stopping.")
                    done = True
                    break

                if transaction_id in scraped_ids:
                    print(f"  [SKIP] ID {transaction_id} already scraped")
                    continue

                await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

                record = await scrape_detail(page, transaction_id, page_num, counter + 1)

                if record:
                    counter += 1
                    transactions.append(record)
                    scraped_ids.add(transaction_id)

            save_progress({"transactions": transactions, "scraped_ids": list(scraped_ids)})

        await context.close()

    save_progress({"transactions": transactions, "scraped_ids": list(scraped_ids)})
    print(f"\nTest run complete. {counter} transactions saved to {PROGRESS_FILE}")
    print("Run  python export_test.py  to produce test_export.xlsx")


if __name__ == "__main__":
    asyncio.run(run())
