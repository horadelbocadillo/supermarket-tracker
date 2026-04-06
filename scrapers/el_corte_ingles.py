import random, time
from playwright.sync_api import sync_playwright
from scrapers.base import ScrapeResult

def scrape(url: str) -> ScrapeResult:
    time.sleep(random.uniform(2, 4))
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)
            page.wait_for_selector(".price__amount", timeout=8000)
            price_text = page.locator(".price__amount").first.inner_text()
            price = float(price_text.replace("€", "").replace(",", ".").strip())
            browser.close()
            return ScrapeResult(price=price, available=True)
    except Exception:
        return ScrapeResult(price=None, available=False)
