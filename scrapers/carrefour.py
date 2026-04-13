import random, time, re
from playwright.sync_api import sync_playwright
from scrapers.base import ScrapeResult

def scrape(url: str) -> ScrapeResult:
    """Scraper para Carrefour usando Firefox headless (Chromium bloqueado por Cloudflare)."""
    time.sleep(random.uniform(2, 4))
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(4000)

            # Buscar precio en el selector específico del buybox
            try:
                price_el = page.locator('.buybox__price').first
                price_text = price_el.inner_text()
            except:
                # Fallback a regex en todo el HTML
                html = page.content()
                prices = re.findall(r'(\d+[,\.]\d{2})\s*€', html)
                price_text = prices[0] if prices else None

            browser.close()

            if price_text:
                price = float(re.search(r'(\d+[,\.]\d{2})', price_text).group(1).replace(",", "."))
                return ScrapeResult(price=price, available=True)
            return ScrapeResult(price=None, available=False)
    except Exception:
        return ScrapeResult(price=None, available=False)
