# Supermarket Tracker

Web personal que scrapea precios de supermercados, guarda un histórico en SQLite, muestra un dashboard con precios actuales e indicador de oferta, y avisa por Telegram una vez al día si hay productos en mínimo de precio.

---

## Qué hace

- Scrapea precios diariamente de Mercadona, Carrefour, Lidl, El Corte Inglés y El Jamón
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
| Deploy | Railway |

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
├── scrapers/
│   ├── base.py              # Dataclass ScrapeResult
│   ├── mercadona.py         # API JSON no oficial
│   ├── carrefour.py         # API JSON
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

Supermercados disponibles: `mercadona`, `carrefour`, `lidl`, `el_corte_ingles`, `el_jamon`

Después vuelve a ejecutar `python seed.py` para insertar los nuevos productos.

---

## Tests

```bash
pytest -v
# 8 tests: db (2), pricing (4), scrapers (2)
```

---

## Deploy en Railway

### 1. Subir el repo a GitHub

```bash
git remote add origin https://github.com/TU_USUARIO/supermarket-tracker.git
git push -u origin master
```

### 2. Crear proyecto en Railway

1. Ve a **railway.app** → **Start a New Project**
2. Selecciona **Deploy from GitHub repo**
3. Autoriza Railway en GitHub si es la primera vez
4. Busca y selecciona `supermarket-tracker`

### 3. Variables de entorno

En el servicio → pestaña **Variables** → **New Variable**:

| Variable | Valor |
|---|---|
| `TELEGRAM_TOKEN` | Token de @BotFather |
| `TELEGRAM_CHAT_ID` | Tu chat ID (consúltalo con @userinfobot) |
| `DASHBOARD_URL` | URL pública asignada por Railway (Settings → Domains) |
| `DB_PATH` | `/app/tracker.db` |

### 4. Volumen persistente para SQLite

Sin volumen el archivo `.db` se borra en cada redeploy.

1. En el proyecto → **+ New** → **Volume**
2. Asígnalo al servicio
3. **Mount Path**: `/app`
4. Guarda — Railway redeploya automáticamente

### 5. Poblar la BD y verificar

Una vez desplegado, usa la terminal integrada del servicio en Railway:

```bash
python seed.py
```

Para lanzar el scraping sin esperar al cron:

```bash
python -c "from scheduler import run_daily_scrape; run_daily_scrape()"
```

El scraping automático corre cada día a las **08:00 UTC**.
