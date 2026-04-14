# Supermarket Price Tracker — Diseño

**Fecha:** 2026-04-06

## Objetivo

Web personal que scrapea productos de supermercados habituales, guarda el histórico de precios y avisa por Telegram cuando un producto está en oferta.

---

## Supermercados

- Mercadona
- Carrefour
- Lidl
- El Corte Inglés
- El Jamón

## Stack

| Capa | Tecnología |
|------|-----------|
| Scraping | Playwright + BeautifulSoup |
| Base de datos | SQLite |
| Backend / Dashboard | FastAPI + Jinja2 |
| Gráficas | Chart.js (CDN) |
| Estilos | Tailwind CSS (CDN) |
| Scheduler | APScheduler |
| Notificaciones | python-telegram-bot |
| Hosting | Railway (gratuito) |

---

## Base de datos

```sql
-- Productos vigilados (lista fija)
products
  id, supermarket, name, url, active

-- Un registro por producto por día
price_history
  id, product_id, price, scraped_at
```

---

## Lógica de oferta

Un producto está **en oferta** si se cumplen los dos criterios simultáneamente:

1. `precio_actual < mediana(todos los registros históricos)`
2. `precio_actual == min(últimos 30 días)`

**Arranque:** hasta tener 7 registros no se activa la lógica — no se muestra indicador de oferta.

**Precio de referencia interno:** la mediana se recalcula cada día tras el scraping. No se muestra al usuario en la vista principal.

---

## Gestión de fallos de scraping

- Si un scraper falla → se muestra el último precio conocido
- No se activa el indicador de oferta si el dato tiene más de 1 día
- Si han pasado **más de 3 días** sin actualizar → aviso visual con fecha del último dato:
  ```
  Leche Hacendado 1L    0,65 €  ⚠️ últ. dato: 4 dic
  ```

---

## Dashboard web

### Vista principal

Lista de productos agrupados por supermercado. Solo precio actual e indicador de oferta.

```
Mercadona
─────────────────────────────────────────────
Leche Hacendado 1L        0,65 €   🟢 OFERTA
Aceite Hacendado 750ml    3,49 €

El Corte Inglés
─────────────────────────────────────────────
Salmón noruego 200g       4,20 €
Jamón serrano loncheado   2,99 €   🟢 OFERTA
```

### Vista detalle (al clicar un producto)

- Gráfica de evolución de precios (línea temporal)
- Línea horizontal marcando la mediana actual

---

## Scrapers

| Supermercado | Método | Motivo |
|---|---|---|
| Mercadona | API JSON interna | API no oficial disponible |
| Carrefour | API JSON interna | Responde JSON por EAN |
| Lidl | Playwright | Web renderizada con React |
| El Corte Inglés | Playwright | Web renderizada con JS |
| El Jamón | BeautifulSoup | HTML estático |

Todos devuelven el mismo formato: `{ "price": float, "available": bool }`

Rotación de User-Agent y delays aleatorios entre requests.

---

## Bot de Telegram

- Setup: token vía @BotFather + chat_id personal como variables de entorno en Railway
- Se ejecuta una vez al día tras el scraping
- Solo envía mensaje si hay productos en oferta
- Formato agrupado por supermercado:

```
🛒 Ofertas de hoy — 6 abril

Mercadona
• Leche Hacendado 1L → 0,65 €

El Corte Inglés
• Jamón serrano loncheado → 2,99 €

Ver dashboard → https://tu-app.railway.app
```

---

## Estructura de carpetas

```
supermarket-tracker/
├── scrapers/
│   ├── mercadona.py
│   ├── carrefour.py
│   ├── lidl.py
│   ├── el_corte_ingles.py
│   └── el_jamon.py
├── dashboard/
│   ├── templates/
│   └── static/
├── bot/
│   └── telegram.py
├── db.py
├── scheduler.py
├── products.json
└── main.py
```

### products.json (ejemplo)

```json
[
  { "supermarket": "mercadona", "name": "Leche Hacendado 1L", "url": "https://..." },
  { "supermarket": "lidl", "name": "Aceite oliva Belive", "url": "https://..." }
]
```

---

## Deploy en Railway

- Variables de entorno: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`
- SQLite persistido en volumen de Railway
- Sin autenticación web (URL con nombre aleatorio, uso personal)
