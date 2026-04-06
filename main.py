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
