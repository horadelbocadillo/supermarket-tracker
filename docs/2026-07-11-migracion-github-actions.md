# Migración de Railway a GitHub Actions — 11/12 de julio de 2026

## Por qué dejaron de llegar las notificaciones

El 11 de julio se detectó que el bot de Telegram llevaba tiempo sin avisar de ofertas.
El diagnóstico fue rápido: la URL de producción devolvía el 404 del propio edge de Railway
(`{"message": "Application not found"}`), es decir, **la aplicación ya no existía en Railway**.
El periodo de prueba (crédito único de $5) se había agotado — un contenedor con Playwright
y Firefox corriendo 24/7 lo consume en semanas — y Railway eliminó el servicio.

Consecuencias:

- Sin app corriendo, no había scraping diario ni notificaciones desde semanas atrás.
- El volumen persistente de Railway (`/data/tracker.db`) se perdió con el servicio:
  **el histórico de precios acumulado desde abril desapareció** y se empezó de cero.

## La solución: GitHub Actions con cron (sin servidor, gratis)

El scraping es una tarea de una vez al día; no necesita un servidor 24/7. Se migró todo
a un workflow de GitHub Actions que corre en el propio repo:

| Antes (Railway) | Ahora (GitHub Actions) |
|---|---|
| Contenedor FastAPI + APScheduler 24/7 | Workflow `.github/workflows/scrape.yml`, cron `0 8 * * *` (08:00 UTC = 10:00 España en verano) |
| BD en volumen persistente `/data/tracker.db` | BD en `data/tracker.db`, **committeada al repo** tras cada pasada |
| Coste: crédito de prueba, luego ~$5/mes | Gratis (repo público, minutos de Actions ilimitados) |
| Dashboard web siempre disponible | Dashboard solo en local: `DB_PATH=data/tracker.db uvicorn main:app --reload` |
| Auto-seed solo si la BD está vacía | `run_scrape.py` sincroniza `products.json` → BD en cada pasada (añade nuevos, sin duplicar) |

Piezas nuevas o modificadas:

- **`.github/workflows/scrape.yml`** — instala dependencias y Playwright Firefox, ejecuta
  `run_scrape.py` y committea el histórico. El paso de commit lleva `if: always()`: aunque
  la pasada falle a medias (p. ej. Telegram caído), los precios ya scrapeados no se pierden.
  Si el workflow falla, GitHub avisa por email. Se puede lanzar a mano en
  **Actions → Daily price scrape → Run workflow**.
- **`run_scrape.py`** — punto de entrada: crea el directorio de la BD, sincroniza los
  productos nuevos de `products.json` y llama a `run_daily_scrape()`.
- **`scheduler.py`** — cada scraper va ahora envuelto en try/except. Antes, si un scraper
  lanzaba una excepción, abortaba la pasada entera y silenciaba las notificaciones.
- **`pyproject.toml`** — arreglado `pip install -e .` (setuptools no resolvía el flat-layout
  con varios paquetes top-level; el Dockerfile de Railway lo enmascaraba porque instalaba
  antes de copiar el código).
- Eliminados `railway.json`, `Procfile` y `Dockerfile`.

Secrets configurados en GitHub (Settings → Secrets and variables → Actions):
`TELEGRAM_TOKEN` (añadido a mano el 12 de julio) y `TELEGRAM_CHAT_ID` (1596005650).

## Nuevo supermercado: Día

Se añadió `scrapers/dia.py`. La web de Día renderiza en servidor un bloque JSON-LD
(`schema.org/Product`) con precio y stock en cada página de producto, así que basta
**httpx con User-Agent de navegador — sin Playwright**.

Productos añadidos (equivalentes a los que ya se seguían en otros súper):

| Producto | URL (ID) | Precio al alta |
|---|---|---|
| Yogurt griego de fresa | `.../yogures-y-postres/yogures-griegos/p/135291` — "Yogur griego con fresa Dia Fidias pack 6 x 125 g" | 1,65 € |
| Canonigos | `.../verduras/lechugas-y-hojas-verdes/p/105782` — "Canónigos Dia Vegecampo 70 g" | 0,99 € |
| Guacamole | `.../platos-preparados-y-pizzas/hummus-y-guacamoles/p/289182` — "Guacamole Dia Al Punto 200 g" | 1,80 € |

Nota (12 de julio): se verificó expresamente que el yogur griego seguido es **solo el de
sabor fresa** (ID 135291), no el natural ni el resto de variantes Fidias/Danone/Oikos.
El tracker sigue URLs de producto concretas, nunca categorías.

## Validación (run manual del 11 de julio, en verde)

Resultado por supermercado — 30 productos en BD:

- **Mercadona**: 11/11 ✓
- **Día**: 3/3 ✓ (1,65 € / 0,99 € / 1,80 €)
- **Carrefour**: 6/6 scrapean, pero 3 (yogur, canónigos, plátanos) devolvieron el conocido
  precio erróneo de **30,00 €** (productos sin stock o promociones). ⚠️ Esos valores entran
  al histórico y distorsionan mediana y mínimos — pendiente filtrarlos.
- **El Corte Inglés**: 4/7 ✓ (fallaron alcachofas, guisantes, judías verdes y arándanos) — preexistente.
- **El Jamón**: 0/3, roto desde abril — preexistente.

El workflow committeó `data/tracker.db` correctamente al terminar.

## Estado y pendientes

- La regla de oferta (`pricing.py`) exige ≥7 registros y precio en mínimo de 30 días por
  debajo de la mediana: como el histórico se perdió, **la primera alerta posible es hacia
  el 19 de julio de 2026**. Silencio hasta entonces es normal.
- Pendiente: filtrar los 30,00 € falsos de Carrefour antes de guardarlos en el histórico.
- Pendiente: revisar los 4 productos de ECI que fallan y el scraper de El Jamón.
- El clon de trabajo en `Documents/2. la compra/supermarket-tracker` se consulta con
  `git pull` (el workflow genera un commit de histórico al día).
