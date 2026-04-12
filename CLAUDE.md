# Supermarket Tracker - Contexto del Proyecto

## Repositorios y Deploy
- **GitHub**: https://github.com/horadelbocadillo/supermarket-tracker
- **Railway**: https://supermarket-tracker-production.up.railway.app
- **Rama principal**: master

## Credenciales y Configuración
- **Telegram Bot Token**: Configurado en Railway como `TELEGRAM_TOKEN`
- **Telegram Chat ID**: 1596005650 (configurado en Railway como `TELEGRAM_CHAT_ID`)
- **DB_PATH**: `/data/tracker.db` (volumen persistente en Railway)
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
- En Railway puede requerir configuración adicional del build para instalar Firefox

## Scheduler
- Scraping automático a las **08:00 UTC** (10:00 España)
- Configurado en `scheduler.py` con APScheduler
- Auto-seed de la BD al arrancar si está vacía (`main.py`)

## Base de Datos
- SQLite con tablas: `products`, `price_history`
- Volumen persistente en Railway montado en `/data`
- Localmente usa `tracker.db` en el directorio del proyecto

## Productos Configurados (products.json)
- 11 de Mercadona (frutos secos, yogures, congelados)
- 6 de Carrefour (yogures, plátanos, cosmética)
- 7 de El Corte Inglés (congelados, huevos)
- 3 de El Jamón (limpieza) - no funcionan

## Comandos Útiles

```bash
# Ejecutar scraping manual
python -c "from scheduler import run_daily_scrape; run_daily_scrape()"

# Resetear y poblar BD
rm tracker.db && python seed.py

# Probar un scraper individual
python -c "from scrapers.mercadona import scrape; print(scrape('URL'))"

# Probar notificación Telegram
python -c "from bot.telegram import send_offers; send_offers([{'name': 'Test', 'supermarket': 'mercadona', 'price': 1.99}])"
```

## Notas de Troubleshooting
- Si Carrefour/ECI fallan con "Access Denied", verificar que Firefox esté instalado
- Si Telegram da "Chat not found", el usuario debe iniciar conversación con el bot primero
- Los precios de 30€ en Carrefour son errores de la web (productos sin stock o promociones)
