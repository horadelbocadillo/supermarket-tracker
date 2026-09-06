# Supermarket Tracker - Contexto del Proyecto

## Repositorios y Deploy
- **GitHub**: https://github.com/horadelbocadillo/supermarket-tracker
- **Tablero**: https://github.com/users/horadelbocadillo/projects/4 (La Compra — Supermarket Tracker)
- **Deploy**: GitHub Actions (`.github/workflows/scrape.yml`), cron diario a las 08:23 UTC. Sin servidor — Railway se abandonó en julio 2026 al acabar el trial.
- **Rama principal**: master

## Credenciales y Configuración
- **Telegram Bot Token**: secret de GitHub Actions `TELEGRAM_TOKEN` (Settings → Secrets → Actions)
- **Telegram Chat ID**: 1596005650 (secret `TELEGRAM_CHAT_ID`)
- **DB_PATH**: `data/tracker.db` en Actions (el workflow committea el fichero al repo tras cada pasada); `tracker.db` en local por defecto
- **Código postal usuario**: 41005 (Sevilla) - no es necesario para la API de Mercadona

## Scrapers - Estado Actual

### Mercadona (✅ Funciona)
- Usa API JSON no oficial: `https://tienda.mercadona.es/api/products/{ID}/`
- El ID se extrae de la URL buscando el segmento numérico
- No requiere Playwright, usa httpx
- **Archivo**: `scrapers/mercadona.py`

### Carrefour (✅ Funciona)
- Requiere **Firefox headless** (Chromium es bloqueado por Cloudflare)
- Usa selector `.buybox__price` para extraer el precio
- **Archivo**: `scrapers/carrefour.py`

### Día (✅ Funciona)
- La página de producto (`https://www.dia.es/.../p/{ID}`) trae un bloque
  JSON-LD (`schema.org/Product`) renderizado en servidor con precio y stock
- No requiere Playwright, usa httpx con User-Agent de navegador
- **Archivo**: `scrapers/dia.py`

### El Corte Inglés (✅ Funciona)
- Requiere **Firefox headless** con configuración especial:
  - User-agent personalizado
  - Viewport 1920x1080
  - Locale es-ES
- Usa regex para extraer precio del HTML
- **Archivo**: `scrapers/el_corte_ingles.py`

### El Jamón (❌ No funciona)
- Pendiente de arreglar
- **Archivo**: `scrapers/el_jamon.py`

## Dependencias Importantes
- `playwright` + `playwright-stealth` para scrapers con navegador
- **Firefox** debe estar instalado (`playwright install firefox`)
- En Actions lo instala el propio workflow (`playwright install --with-deps firefox`)

## Ejecución diaria (GitHub Actions)
- Workflow `.github/workflows/scrape.yml`, cron a las **08:23 UTC** (10:23 España en verano; minuto impar porque GitHub retrasa/salta los crons del minuto :00)
- Entrypoint: `run_scrape.py` — sincroniza productos nuevos de `products.json` a la BD y llama a `run_daily_scrape()`
- Cada scraper va envuelto en try/except: si uno revienta, la pasada continúa
- Al final el workflow committea `data/tracker.db` al repo (paso con `if: always()`, así el histórico no se pierde aunque falle Telegram)
- Se puede lanzar a mano: Actions → Daily price scrape → Run workflow
- `main.py` + APScheduler siguen existiendo solo para correr el dashboard en local

## Base de Datos
- SQLite con tablas: `products`, `price_history`
- En Actions: `data/tracker.db`, versionada en git (excepción en `.gitignore`)
- Localmente usa `tracker.db` en el directorio del proyecto (ignorada)

## Productos Configurados (products.json)
- 11 de Mercadona (frutos secos, yogures, congelados)
- 6 de Carrefour (yogures, plátanos, cosmética)
- 3 de Día (yogur griego de fresa, canónigos, guacamole)
- 7 de El Corte Inglés (congelados, huevos)
- 3 de El Jamón (limpieza) - no funcionan
- Los productos nuevos se añaden a la BD automáticamente en la siguiente pasada (`run_scrape.py`)

## Comandos Útiles

```bash
# Ejecutar la pasada completa como en Actions
DB_PATH=data/tracker.db python run_scrape.py

# Resetear y poblar BD local
rm tracker.db && python seed.py

# Probar un scraper individual
python -c "from scrapers.dia import scrape; print(scrape('https://www.dia.es/platos-preparados-y-pizzas/hummus-y-guacamoles/p/289182'))"

# Probar notificación Telegram
python -c "from bot.telegram import send_offers; send_offers([{'name': 'Test', 'supermarket': 'mercadona', 'price': 1.99}])"
```

## Notas de Troubleshooting
- Si Carrefour/ECI fallan con "Access Denied", verificar que Firefox esté instalado
- Si Telegram da "Chat not found", el usuario debe iniciar conversación con el bot primero
- Los precios de 30€ en Carrefour son errores de la web (productos sin stock o promociones)
- Si el log empieza con "AVISO: falta configuración de Telegram", el secret que nombre
  no existe en el repo: `gh secret set TELEGRAM_TOKEN`. Comprobar con `gh secret list`.
  La pasada recoge los precios igualmente y los committea; solo termina en rojo al final
  para que el fallo no pase desapercibido — el histórico nunca se sacrifica por el aviso
- Para probar scrapers en local sin configurar Telegram: `SKIP_TELEGRAM=1 python run_scrape.py`
- El aviso de Telegram solo salta con ≥7 días de histórico y precio en mínimo de 30 días por debajo de la mediana — silencio prolongado puede ser normal
