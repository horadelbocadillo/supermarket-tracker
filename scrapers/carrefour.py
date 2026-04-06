import httpx, random, time
from scrapers.base import ScrapeResult

HEADERS = {"User-Agent": "Mozilla/5.0"}

def scrape(url: str) -> ScrapeResult:
    time.sleep(random.uniform(1, 3))
    try:
        r = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        r.raise_for_status()
        data = r.json()
        price = float(data["product"]["price"]["value"])
        return ScrapeResult(price=price, available=True)
    except Exception:
        return ScrapeResult(price=None, available=False)
