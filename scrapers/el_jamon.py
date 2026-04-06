import httpx, random, time
from bs4 import BeautifulSoup
from scrapers.base import ScrapeResult

HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape(url: str) -> ScrapeResult:
    time.sleep(random.uniform(1, 3))
    try:
        r = httpx.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        price_tag = soup.select_one(".price, .product-price, [class*='price']")
        price = float(price_tag.text.replace("€", "").replace(",", ".").strip())
        return ScrapeResult(price=price, available=True)
    except Exception:
        return ScrapeResult(price=None, available=False)
