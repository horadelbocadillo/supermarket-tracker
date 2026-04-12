# Supermarket Tracker — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Web personal que scrapea precios de 5 supermercados, guarda histórico en SQLite, muestra un dashboard con precios actuales e indicador de oferta, y avisa por Telegram una vez al día.

**Architecture:** FastAPI sirve el dashboard y expone los datos; APScheduler lanza el scraping diario; cada supermercado tiene su propio scraper con interfaz común; el bot de Telegram lee los resultados de SQLite y envía un mensaje agrupado si hay ofertas.

**Tech Stack:** Python 3.11+, Playwright, BeautifulSoup4, FastAPI, Jinja2, SQLite (sqlite3 stdlib), APScheduler, python-telegram-bot, Chart.js (CDN), Tailwind CSS (CDN), Railway (deploy).

---

## Task 1: Setup del proyecto

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`

**Step 1: Crear pyproject.toml**

```toml
[project]
name = "supermarket-tracker"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111",
    "uvicorn>=0.29",
    "jinja2>=3.1",
    "playwright>=1.44",
    "beautifulsoup4>=4.12",
    "httpx>=0.27",
    "apscheduler>=3.10",
    "python-telegram-bot>=21.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "httpx>=0.27"]
```

**Step 2: Crear .gitignore**

```
.env
*.db
__pycache__/
.venv/
.playwright/
```

**Step 3: Crear .env.example**

```
TELEGRAM_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**Step 4: Instalar dependencias**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

**Step 5: Commit**

```bash
git add .
git commit -m "chore: project setup"
```

---

## Task 2: Base de datos

**Files:**
- Create: `db.py`
- Create: `tests/test_db.py`

**Step 1: Escribir el test**

```python
# tests/test_db.py
import os, pytest
from db import init_db, add_product, save_price, get_last_price, get_price_history

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))

def test_save_and_retrieve_price():
    init_db()
    add_product("mercadona", "Leche", "https://example.com")
    save_price(1, 0.65)
    price = get_last_price(1)
    assert price == 0.65

def test_price_history():
    init_db()
    add_product("lidl", "Aceite", "https://example.com")
    save_price(1, 4.99)
    save_price(1, 4.49)
    history = get_price_history(1)
    assert len(history) == 2
    assert history[0]["price"] == 4.99
```

**Step 2: Verificar que falla**

```bash
pytest tests/test_db.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'db'`

**Step 3: Implementar db.py**

```python
import os, sqlite3
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "tracker.db")

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supermarket TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            price REAL,
            scraped_at TEXT NOT NULL
        );
        """)

def add_product(supermarket, name, url):
    with _conn() as c:
        c.execute(
            "INSERT INTO products (supermarket, name, url) VALUES (?,?,?)",
            (supermarket, name, url)
        )

def save_price(product_id, price):
    with _conn() as c:
        c.execute(
            "INSERT INTO price_history (product_id, price, scraped_at) VALUES (?,?,?)",
            (product_id, price, datetime.utcnow().isoformat())
        )

def get_last_price(product_id):
    with _conn() as c:
        row = c.execute(
            "SELECT price FROM price_history WHERE product_id=? ORDER BY scraped_at DESC LIMIT 1",
            (product_id,)
        ).fetchone()
    return row[0] if row else None

def get_price_history(product_id):
    with _conn() as c:
        rows = c.execute(
            "SELECT price, scraped_at FROM price_history WHERE product_id=? ORDER BY scraped_at ASC",
            (product_id,)
        ).fetchall()
    return [{"price": r[0], "scraped_at": r[1]} for r in rows]

def get_all_products():
    with _conn() as c:
        rows = c.execute(
            "SELECT id, supermarket, name, url FROM products WHERE active=1"
        ).fetchall()
    return [{"id": r[0], "supermarket": r[1], "name": r[2], "url": r[3]} for r in rows]
```

**Step 4: Verificar que pasa**

```bash
pytest tests/test_db.py -v
```
Expected: PASS

**Step 5: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "feat: sqlite database layer"
```

---

## Task 3: Lógica de oferta

**Files:**
- Create: `pricing.py`
- Create: `tests/test_pricing.py`

**Step 1: Escribir el test**

```python
# tests/test_pricing.py
from pricing import is_offer, compute_median

def test_no_offer_insufficient_history():
    # Menos de 7 registros → nunca oferta
    history = [{"price": p} for p in [1.0, 0.9, 0.8]]
    assert is_offer(0.8, history) is False

def test_offer_when_below_median_and_min_30d():
    history = [{"price": p} for p in [1.0]*10 + [0.5]]  # 11 registros
    # precio actual 0.5 == mínimo 30d y < mediana (1.0)
    assert is_offer(0.5, history) is True

def test_no_offer_when_above_median():
    history = [{"price": p} for p in [1.0]*10 + [1.2]]
    assert is_offer(1.2, history) is False

def test_median_calculation():
    assert compute_median([1, 2, 3, 4, 5]) == 3
    assert compute_median([1, 2, 3, 4]) == 2.5
```

**Step 2: Verificar que falla**

```bash
pytest tests/test_pricing.py -v
```

**Step 3: Implementar pricing.py**

```python
from statistics import median

MIN_HISTORY = 7
DAYS_30 = 30

def compute_median(prices: list[float]) -> float:
    return median(prices)

def is_offer(current_price: float, history: list[dict]) -> bool:
    """
    Devuelve True si:
    1. Hay al menos MIN_HISTORY registros
    2. current_price < mediana histórica
    3. current_price == mínimo de los últimos DAYS_30 registros
    """
    prices = [h["price"] for h in history if h["price"] is not None]
    if len(prices) < MIN_HISTORY:
        return False
    med = compute_median(prices)
    recent = prices[-DAYS_30:]
    return current_price < med and current_price <= min(recent)
```

**Step 4: Verificar que pasa**

```bash
pytest tests/test_pricing.py -v
```

**Step 5: Commit**

```bash
git add pricing.py tests/test_pricing.py
git commit -m "feat: offer detection logic"
```

---

## Task 4: Scrapers — interfaz común + Mercadona

**Files:**
- Create: `scrapers/__init__.py`
- Create: `scrapers/base.py`
- Create: `scrapers/mercadona.py`
- Create: `tests/test_scrapers.py`

**Step 1: Crear base.py**

```python
# scrapers/base.py
from dataclasses import dataclass

@dataclass
class ScrapeResult:
    price: float | None
    available: bool
```

**Step 2: Implementar scrapers/mercadona.py**

Mercadona tiene una API JSON no oficial: `https://tienda.mercadona.es/api/products/<id>/`

```python
# scrapers/mercadona.py
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
```

**Step 3: Test de integración (marcado para saltar en CI)**

```python
# tests/test_scrapers.py
import pytest
from scrapers.base import ScrapeResult

def test_scrape_result_structure():
    r = ScrapeResult(price=1.29, available=True)
    assert r.price == 1.29
    assert r.available is True

def test_scrape_result_failed():
    r = ScrapeResult(price=None, available=False)
    assert r.price is None
```

**Step 4: Verificar**

```bash
pytest tests/test_scrapers.py -v
```

**Step 5: Commit**

```bash
git add scrapers/ tests/test_scrapers.py
git commit -m "feat: scraper base + mercadona"
```

---

## Task 5: Scrapers — Carrefour, Lidl, El Corte Inglés, El Jamón

**Files:**
- Create: `scrapers/carrefour.py`
- Create: `scrapers/lidl.py`
- Create: `scrapers/el_corte_ingles.py`
- Create: `scrapers/el_jamon.py`
- Create: `scrapers/router.py`

**scrapers/carrefour.py** — API JSON por EAN:

```python
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
```

**scrapers/lidl.py** — Playwright:

```python
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
            page.wait_for_selector("[class*='price']", timeout=8000)
            price_text = page.locator("[class*='price']").first.inner_text()
            price = float(price_text.replace("€", "").replace(",", ".").strip())
            browser.close()
            return ScrapeResult(price=price, available=True)
    except Exception:
        return ScrapeResult(price=None, available=False)
```

**scrapers/el_corte_ingles.py** — Playwright:

```python
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
```

**scrapers/el_jamon.py** — BeautifulSoup:

```python
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
```

**scrapers/router.py** — despacha al scraper correcto según supermercado:

```python
from scrapers import mercadona, carrefour, lidl, el_corte_ingles, el_jamon
from scrapers.base import ScrapeResult

_SCRAPERS = {
    "mercadona": mercadona.scrape,
    "carrefour": carrefour.scrape,
    "lidl": lidl.scrape,
    "el_corte_ingles": el_corte_ingles.scrape,
    "el_jamon": el_jamon.scrape,
}

def scrape(supermarket: str, url: str) -> ScrapeResult:
    fn = _SCRAPERS.get(supermarket)
    if not fn:
        return ScrapeResult(price=None, available=False)
    return fn(url)
```

**Step: Commit**

```bash
git add scrapers/
git commit -m "feat: all scrapers + router"
```

---

## Task 6: products.json + seed de la base de datos

**Files:**
- Create: `products.json`
- Create: `seed.py`

**products.json** — rellena con tus productos reales:

```json
[
  {"supermarket": "mercadona", "name": "Leche Hacendado 1L", "url": "https://tienda.mercadona.es/product/..."},
  {"supermarket": "carrefour",  "name": "Producto X",         "url": "https://www.carrefour.es/..."},
  {"supermarket": "lidl",       "name": "Producto Y",         "url": "https://www.lidl.es/..."},
  {"supermarket": "el_corte_ingles", "name": "Producto Z",   "url": "https://www.elcorteingles.es/..."},
  {"supermarket": "el_jamon",   "name": "Producto W",         "url": "https://www.eljamon.com/..."}
]
```

**seed.py**:

```python
import json
from db import init_db, add_product

if __name__ == "__main__":
    init_db()
    with open("products.json") as f:
        products = json.load(f)
    for p in products:
        add_product(p["supermarket"], p["name"], p["url"])
    print(f"Seeded {len(products)} products.")
```

**Step: Ejecutar seed**

```bash
python seed.py
```

**Step: Commit**

```bash
git add products.json seed.py
git commit -m "feat: product seed"
```

---

## Task 7: Scheduler — scraping diario

**Files:**
- Create: `scheduler.py`

```python
import logging
from datetime import datetime
from db import init_db, get_all_products, save_price
from scrapers.router import scrape as do_scrape
from pricing import is_offer, get_price_history_for
from bot.telegram import send_offers

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def run_daily_scrape():
    log.info("Starting daily scrape %s", datetime.utcnow())
    products = get_all_products()
    offers = []

    for product in products:
        result = do_scrape(product["supermarket"], product["url"])
        if result.price is not None:
            save_price(product["id"], result.price)
            log.info("✓ %s → %.2f€", product["name"], result.price)
        else:
            log.warning("✗ %s → scrape failed", product["name"])

        # Comprobar oferta con el histórico actualizado
        from db import get_price_history
        history = get_price_history(product["id"])
        current = result.price or (history[-1]["price"] if history else None)
        if current and is_offer(current, history):
            offers.append({**product, "price": current})

    if offers:
        send_offers(offers)
        log.info("Telegram alert sent for %d offers", len(offers))


if __name__ == "__main__":
    from apscheduler.schedulers.blocking import BlockingScheduler
    init_db()
    scheduler = BlockingScheduler()
    scheduler.add_job(run_daily_scrape, "cron", hour=8, minute=0)
    log.info("Scheduler started — runs every day at 08:00 UTC")
    scheduler.start()
```

**Step: Commit**

```bash
git add scheduler.py
git commit -m "feat: daily scrape scheduler"
```

---

## Task 8: Bot de Telegram

**Files:**
- Create: `bot/__init__.py`
- Create: `bot/telegram.py`

```python
# bot/telegram.py
import os
from collections import defaultdict
from datetime import date
import telegram  # python-telegram-bot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_offers(offers: list[dict]):
    """Envía un mensaje agrupado por supermercado con los productos en oferta."""
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("TELEGRAM_TOKEN y TELEGRAM_CHAT_ID son obligatorios")

    # Agrupar por supermercado
    by_super = defaultdict(list)
    for o in offers:
        by_super[o["supermarket"]].append(o)

    today = date.today().strftime("%-d %B")
    lines = [f"🛒 Ofertas de hoy — {today}\n"]

    for supermarket, products in by_super.items():
        lines.append(supermarket.replace("_", " ").title())
        for p in products:
            lines.append(f"• {p['name']} → {p['price']:.2f} €")
        lines.append("")

    dashboard_url = os.getenv("DASHBOARD_URL", "")
    if dashboard_url:
        lines.append(f"Ver dashboard → {dashboard_url}")

    bot = telegram.Bot(token=TOKEN)
    import asyncio
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text="\n".join(lines)))
```

**Step: Commit**

```bash
git add bot/
git commit -m "feat: telegram bot notifications"
```

---

## Task 9: Dashboard FastAPI

**Files:**
- Create: `dashboard/__init__.py`
- Create: `dashboard/app.py`
- Create: `dashboard/templates/index.html`
- Create: `dashboard/templates/detail.html`

**dashboard/app.py**:

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
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
    # Agrupar por supermercado
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
```

**dashboard/templates/index.html**:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>La Compra</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 p-6 font-sans">
  <h1 class="text-2xl font-bold mb-6">🛒 La Compra</h1>
  {% for supermarket, products in grouped.items() %}
  <div class="mb-8">
    <h2 class="text-lg font-semibold text-gray-500 uppercase tracking-wide mb-2">
      {{ supermarket.replace('_', ' ').title() }}
    </h2>
    <div class="bg-white rounded-lg shadow divide-y">
      {% for p in products %}
      <a href="/product/{{ p.id }}" class="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
        <span class="text-gray-800">{{ p.name }}</span>
        <span class="flex items-center gap-3">
          {% if p.stale %}
          <span class="text-xs text-amber-500">⚠️ últ. dato: {{ p.last_date[:10] }}</span>
          {% endif %}
          {% if p.price %}
          <span class="font-mono font-medium">{{ "%.2f"|format(p.price) }} €</span>
          {% else %}
          <span class="text-gray-400 text-sm">sin datos</span>
          {% endif %}
          {% if p.offer %}
          <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full font-semibold">OFERTA</span>
          {% endif %}
        </span>
      </a>
      {% endfor %}
    </div>
  </div>
  {% endfor %}
</body>
</html>
```

**dashboard/templates/detail.html**:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>{{ product.name }}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-50 p-6 font-sans">
  <a href="/" class="text-blue-500 text-sm mb-4 inline-block">← Volver</a>
  <h1 class="text-xl font-bold mb-1">{{ product.name }}</h1>
  <p class="text-gray-500 mb-6">{{ product.supermarket.replace('_', ' ').title() }}</p>
  <div class="bg-white rounded-lg shadow p-4 max-w-2xl">
    <canvas id="chart"></canvas>
  </div>
  <script>
    const labels = {{ history | map(attribute='scraped_at') | map('truncate', 10, False, '') | list | tojson }};
    const prices = {{ history | map(attribute='price') | list | tojson }};
    const median = {{ median or 'null' }};
    new Chart(document.getElementById('chart'), {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'Precio', data: prices, borderColor: '#3b82f6', tension: 0.3, pointRadius: 3 },
          { label: 'Mediana', data: Array(labels.length).fill(median),
            borderColor: '#f59e0b', borderDash: [5,5], pointRadius: 0 }
        ]
      },
      options: { responsive: true, plugins: { legend: { position: 'top' } } }
    });
  </script>
</body>
</html>
```

**Step: Commit**

```bash
git add dashboard/
git commit -m "feat: fastapi dashboard"
```

---

## Task 10: main.py + deploy en Railway

**Files:**
- Create: `main.py`
- Create: `Procfile`
- Create: `railway.json`

**main.py**:

```python
import threading
from dotenv import load_dotenv
load_dotenv()

from db import init_db
from dashboard.app import app
from scheduler import run_daily_scrape
from apscheduler.schedulers.background import BackgroundScheduler

init_db()

scheduler = BackgroundScheduler()
scheduler.add_job(run_daily_scrape, "cron", hour=8, minute=0)
scheduler.start()

# app es el objeto FastAPI, Railway lo levanta con uvicorn
```

**Procfile**:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**railway.json**:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": { "builder": "NIXPACKS" },
  "deploy": { "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT" }
}
```

**Deploy:**

1. Crear cuenta en railway.app
2. New Project → Deploy from GitHub repo
3. Añadir variables de entorno: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `DASHBOARD_URL`
4. Añadir volumen persistente montado en `/app` para el SQLite

**Step: Commit final**

```bash
git add main.py Procfile railway.json
git commit -m "feat: entrypoint + railway config"
```

---

## Orden de ejecución

1. Task 1 — Setup
2. Task 2 — Base de datos
3. Task 3 — Lógica de oferta
4. Task 4 — Scraper base + Mercadona
5. Task 5 — Resto de scrapers
6. Task 6 — Seed productos
7. Task 7 — Scheduler
8. Task 8 — Bot Telegram
9. Task 9 — Dashboard
10. Task 10 — Deploy
