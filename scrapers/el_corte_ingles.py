import random, time, re
from playwright.sync_api import sync_playwright
from scrapers.base import ScrapeResult

def scrape(url: str) -> ScrapeResult:
    """Scraper para El Corte Inglés usando Firefox headless con config especial."""
    time.sleep(random.uniform(2, 4))
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(
                headless=True,
                firefox_user_prefs={
                    'general.useragent.override': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0'
                }
            )
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='es-ES'
            )
            page = context.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(5000)

            html = page.content()
            # Buscar precio con regex (formato: X,XX €)
            prices = re.findall(r'(\d+[,\.]\d{2})\s*€', html)
            browser.close()

            if prices:
                # El primer precio es el del producto
                price = float(prices[0].replace(",", "."))
                return ScrapeResult(price=price, available=True)
            return ScrapeResult(price=None, available=False)
    except Exception:
        return ScrapeResult(price=None, available=False)
