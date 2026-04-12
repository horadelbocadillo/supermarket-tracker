import httpx, random, time
from scrapers.base import ScrapeResult

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; price-tracker/1.0)"}

def scrape(url: str) -> ScrapeResult:
    """url debe ser la URL del producto en tienda.mercadona.es"""
    # Extraer product_id de la URL (formato: /product/ID/slug)
    parts = url.rstrip("/").split("/")
    product_id = parts[-2] if parts[-1].isalpha() or "-" in parts[-1] else parts[-1]
    # Buscar el ID numérico
    for part in parts:
        if part.isdigit():
            product_id = part
            break
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
