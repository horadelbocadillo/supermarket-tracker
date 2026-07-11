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


if __name__ == "__main__":
    init_db()
    sync_products()
    run_daily_scrape()
