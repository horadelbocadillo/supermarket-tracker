from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime
from db import get_all_products, get_price_history, get_last_price
from pricing import is_offer

app = FastAPI()
templates = Jinja2Templates(directory="dashboard/templates")

def days_since(iso_date: str) -> int:
    dt = datetime.fromisoformat(iso_date)
    return (datetime.utcnow() - dt).days

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    products = get_all_products()
    items = []
    for p in products:
        history = get_price_history(p["id"])
        last_price = get_last_price(p["id"])
        last_date = history[-1]["scraped_at"] if history else None
        stale = days_since(last_date) > 3 if last_date else False
        offer = is_offer(last_price, history) if last_price else False
        items.append({**p, "price": last_price, "offer": offer,
                      "stale": stale, "last_date": last_date})
    from itertools import groupby
    items.sort(key=lambda x: x["supermarket"])
    grouped = {k: list(v) for k, v in groupby(items, key=lambda x: x["supermarket"])}
    return templates.TemplateResponse("index.html", {"request": request, "grouped": grouped})

@app.get("/debug/scrape-test")
def debug_scrape_test():
    """Endpoint temporal para debuggear scrapers en Railway."""
    import httpx
    results = {}

    # Test 1: Mercadona API
    try:
        url = "https://tienda.mercadona.es/api/products/34262/"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        r = httpx.get(url, headers=headers, timeout=10)
        results["mercadona"] = {"status": r.status_code, "body": r.text[:200]}
    except Exception as e:
        results["mercadona"] = {"error": str(e)}

    # Test 2: Carrefour con scraper real
    try:
        from scrapers.carrefour import scrape as carrefour_scrape
        result = carrefour_scrape("https://www.carrefour.es/supermercado/canonigo-carrefour-el-mercado-200-g/R-521032349/p")
        results["carrefour"] = {"price": result.price, "available": result.available}
    except Exception as e:
        import traceback
        results["carrefour"] = {"error": str(e), "traceback": traceback.format_exc()}

    # Test 3: El Corte Inglés con Playwright
    try:
        from scrapers.el_corte_ingles import scrape as eci_scrape
        url = "https://www.elcorteingles.es/supermercado/B001018915300109-verleal-corazones-de-alcachofas-baby-bolsa-300-g/"
        result = eci_scrape(url)
        results["el_corte_ingles"] = {"price": result.price, "available": result.available}
    except Exception as e:
        results["el_corte_ingles"] = {"error": str(e)}

    return results


@app.get("/product/{product_id}", response_class=HTMLResponse)
def detail(request: Request, product_id: int):
    products = get_all_products()
    product = next((p for p in products if p["id"] == product_id), None)
    history = get_price_history(product_id)
    from pricing import compute_median
    prices = [h["price"] for h in history if h["price"]]
    median_val = compute_median(prices) if prices else None
    return templates.TemplateResponse("detail.html", {
        "request": request, "product": product,
        "history": history, "median": median_val
    })
