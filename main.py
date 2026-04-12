import json
from dotenv import load_dotenv
load_dotenv()

from db import init_db, add_product, get_all_products
from dashboard.app import app
from scheduler import run_daily_scrape
from apscheduler.schedulers.background import BackgroundScheduler

init_db()

# Auto-seed si la BD está vacía
if not get_all_products():
    with open("products.json") as f:
        products = json.load(f)
    for p in products:
        add_product(p["supermarket"], p["name"], p["url"])
    print(f"Auto-seeded {len(products)} products.")

scheduler = BackgroundScheduler()
scheduler.add_job(run_daily_scrape, "cron", hour=8, minute=0)
scheduler.start()

# app es el objeto FastAPI, Railway lo levanta con uvicorn
