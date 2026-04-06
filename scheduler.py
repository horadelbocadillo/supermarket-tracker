import logging
from datetime import datetime
from db import init_db, get_all_products, save_price, get_price_history
from scrapers.router import scrape as do_scrape
from pricing import is_offer

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def run_daily_scrape():
    log.info("Starting daily scrape %s", datetime.utcnow())
    products = get_all_products()
    offers = []

    for product in products:
        result = do_scrape(product["supermarket"], product["url"])
        if result.price is not None:
            save_price(product["id"], result.price)
            log.info("✓ %s → %.2f€", product["name"], result.price)
        else:
            log.warning("✗ %s → scrape failed", product["name"])

        history = get_price_history(product["id"])
        current = result.price or (history[-1]["price"] if history else None)
        if current and is_offer(current, history):
            offers.append({**product, "price": current})

    if offers:
        from bot.telegram import send_offers
        send_offers(offers)
        log.info("Telegram alert sent for %d offers", len(offers))


if __name__ == "__main__":
    from apscheduler.schedulers.blocking import BlockingScheduler
    init_db()
    scheduler = BlockingScheduler()
    scheduler.add_job(run_daily_scrape, "cron", hour=8, minute=0)
    log.info("Scheduler started — runs every day at 08:00 UTC")
    scheduler.start()
