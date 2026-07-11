import json, random, re, time
import httpx
from scrapers.base import ScrapeResult

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

def scrape(url: str) -> ScrapeResult:
    """url debe ser la URL del producto en www.dia.es (formato /categoria/subcategoria/p/ID).

    La página incluye un bloque JSON-LD (schema.org/Product) con precio y
    disponibilidad, renderizado en servidor — no requiere Playwright.
    """
    time.sleep(random.uniform(1, 3))
    try:
        r = httpx.get(url, headers=HEADERS, timeout=20, follow_redirects=True)
        r.raise_for_status()
        m = re.search(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', r.text, re.S)
        data = json.loads(m.group(1))
        offer = data["offers"]
        price = float(offer["price"])
        available = offer.get("availability", "").endswith("InStock")
        return ScrapeResult(price=price, available=available)
    except Exception:
        return ScrapeResult(price=None, available=False)
