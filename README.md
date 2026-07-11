# Supermarket Tracker

Web personal que scrapea precios de supermercados, guarda un histórico en SQLite, muestra un dashboard con precios actuales e indicador de oferta, y avisa por Telegram una vez al día si hay productos en mínimo de precio.

---

## Qué hace

- Scrapea precios diariamente de Mercadona, Carrefour, Día, Lidl, El Corte Inglés y El Jamón
- Guarda el histórico en SQLite
- Detecta ofertas: precio actual < mediana histórica y mínimo de los últimos 30 días
- Envía un mensaje agrupado por Telegram si hay ofertas
- Dashboard web con lista de productos, precios y gráfico histórico por producto

---

## Stack

| Capa | Tecnología |
|---|---|
| Web / API | FastAPI + Jinja2 |
| Scraping | Playwright (Lidl, ECI) + httpx + BeautifulSoup (El Jamón, Carrefour, Mercadona API) |
| Base de datos | SQLite (stdlib) |
| Scheduler | APScheduler |
| Notificaciones | python-telegram-bot |
| Frontend | Tailwind CSS + Chart.js (ambos por CDN) |
| Deploy | GitHub Actions (cron diario, sin servidor) |

---

## Estructura del proyecto

```
supermarket-tracker/
├── main.py                  # Entrypoint: arranca FastAPI + scheduler
├── db.py                    # Capa SQLite: products + price_history
├── pricing.py               # Lógica de detección de ofertas
├── scheduler.py             # Scraping diario con APScheduler
├── seed.py                  # Poblar la BD desde products.json
├── products.json            # Lista de productos a rastrear
├── run_scrape.py            # Entrypoint de GitHub Actions: sync + scrape
├── data/
│   └── tracker.db           # Histórico de precios (committeado por el workflow)
├── .github/workflows/
│   └── scrape.yml           # Cron diario a las 08:00 UTC
├── scrapers/
│   ├── base.py              # Dataclass ScrapeResult
│   ├── mercadona.py         # API JSON no oficial
│   ├── carrefour.py         # Playwright (Firefox)
│   ├── dia.py               # httpx + JSON-LD de la página de producto
│   ├── lidl.py              # Playwright
│   ├── el_corte_ingles.py   # Playwright
│   ├── el_jamon.py          # BeautifulSoup
│   └── router.py            # Despacha al scraper según supermercado
├── bot/
│   └── telegram.py          # Envía mensaje agrupado por supermercado
├── dashboard/
│   ├── app.py               # Rutas FastAPI
│   └── templates/
│       ├── index.html       # Lista de productos con badge OFERTA
│       └── detail.html      # Gráfico histórico + mediana
├── tests/
│   ├── test_db.py
│   ├── test_pricing.py
│   └── test_scrapers.py
├── pyproject.toml
├── .env.example
└── Procfile
```

---

## Arrancar en local

```bash
# 1. Crear entorno virtual e instalar dependencias
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium

# 2. Configurar variables de entorno
cp .env.example .env
# Edita .env con tu TELEGRAM_TOKEN y TELEGRAM_CHAT_ID

# 3. Rellenar productos.json con tus URLs reales y poblar la BD
python seed.py

# 4. Arrancar
uvicorn main:app --reload
# Dashboard en http://localhost:8000

# 5. Lanzar scraping manualmente (sin esperar al cron de las 08:00 UTC)
python -c "from scheduler import run_daily_scrape; run_daily_scrape()"
```

---

## Añadir o cambiar productos

Edita `products.json` con el formato:

```json
[
  {"supermarket": "mercadona", "name": "Nombre del producto", "url": "https://tienda.mercadona.es/product/ID/slug"},
  {"supermarket": "carrefour", "name": "Nombre del producto", "url": "https://..."}
]
```

Supermercados disponibles: `mercadona`, `carrefour`, `dia`, `lidl`, `el_corte_ingles`, `el_jamon`

En GitHub Actions no hace falta nada más: `run_scrape.py` añade automáticamente los productos nuevos de `products.json` a la BD en la siguiente pasada. En local, ejecuta `python seed.py` para poblar la BD desde cero.

---

## Tests

```bash
pytest -v
# 8 tests: db (2), pricing (4), scrapers (2)
```

---

## Deploy en GitHub Actions

No hay servidor: el workflow `.github/workflows/scrape.yml` corre cada día a las **08:00 UTC** (10:00 en España en verano), scrapea todos los productos, envía el aviso de Telegram si hay ofertas y committea el histórico actualizado (`data/tracker.db`) al propio repo.

### 1. Secrets del repositorio

En GitHub → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Valor |
|---|---|
| `TELEGRAM_TOKEN` | Token de @BotFather |
| `TELEGRAM_CHAT_ID` | Tu chat ID (consúltalo con @userinfobot) |

### 2. Lanzar una pasada manual

En GitHub → **Actions → Daily price scrape → Run workflow**. Útil para probar sin esperar al cron.

### Notas

- El histórico vive en `data/tracker.db`, committeado por el workflow tras cada pasada. Para consultarlo en local basta con `git pull`.
- Si el workflow falla (scrapers rotos, Telegram caído…), GitHub avisa por email. El histórico se committea igualmente con lo que se haya podido scrapear.
- El dashboard ya no está desplegado, pero funciona en local: `git pull && DB_PATH=data/tracker.db uvicorn main:app --reload`.
