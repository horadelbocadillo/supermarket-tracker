import httpx, random, time
from scrapers.base import ScrapeResult

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; price-tracker/1.0)"}

def scrape(url: str) -> ScrapeResult:
    """url debe ser la URL del producto en tienda.mercadona.es"""
    # Extraer product_id de la URL
    product_id = url.rstrip("/").split("/")[-1]
    api_url = f"https://tienda.mercadona.es/api/products/{product_id}/"
    time.sleep(random.uniform(1, 3))
    try:
        r = httpx.get(api_url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        data = r.json()
        price = float(data["price_instructions"]["unit_price"])
        return ScrapeResult(price=price, available=True)
    except Exception:
        return ScrapeResult(price=None, available=False)
