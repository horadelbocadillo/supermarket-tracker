"""Punto de entrada para GitHub Actions.

Sincroniza products.json con la BD (añade productos nuevos sin duplicar)
y lanza la pasada de scraping. Si el envío de Telegram falla, el proceso
sale con error para que el workflow quede en rojo — el histórico ya está
guardado en la BD y el workflow lo committea igualmente (if: always()).
"""
import json
import os

from dotenv import load_dotenv
load_dotenv()

# Crear el directorio de la BD si no existe (en Actions: data/tracker.db)
db_path = os.getenv("DB_PATH", "tracker.db")
db_dir = os.path.dirname(db_path)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

from db import init_db, add_product, get_all_products
from scheduler import run_daily_scrape


def sync_products():
    existing = {p["url"] for p in get_all_products()}
    with open("products.json") as f:
        wanted = json.load(f)
    added = [p for p in wanted if p["url"] not in existing]
    for p in added:
        add_product(p["supermarket"], p["name"], p["url"])
    if added:
        print(f"Añadidos {len(added)} productos nuevos desde products.json:")
        for p in added:
            print(f"  + [{p['supermarket']}] {p['name']}")


def check_notification_config():
    """Falla antes de scrapear si falta la configuración de Telegram.

    Una pasada que recoge precios pero no puede avisar no sirve de nada, y
    enterarse tras cinco minutos de scraping hace el fallo difícil de leer.
    Para probar scrapers sin avisos: SKIP_TELEGRAM=1 python run_scrape.py
    """
    if os.getenv("SKIP_TELEGRAM"):
        return
    missing = [v for v in ("TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID") if not os.getenv(v)]
    if missing:
        raise SystemExit(
            f"Falta configuración de Telegram: {', '.join(missing)}\n"
            "  En GitHub Actions son secrets del repo:  gh secret set TELEGRAM_TOKEN\n"
            "  En local van en un fichero .env          (ver .env.example)\n"
            "  Para probar scrapers sin avisos:         SKIP_TELEGRAM=1 python run_scrape.py"
        )


if __name__ == "__main__":
    check_notification_config()
    init_db()
    sync_products()
    run_daily_scrape()
