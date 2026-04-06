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
