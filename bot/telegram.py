import os
from collections import defaultdict
from datetime import date
import telegram  # python-telegram-bot

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_offers(offers: list[dict]):
    """Envía un mensaje agrupado por supermercado con los productos en oferta."""
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("TELEGRAM_TOKEN y TELEGRAM_CHAT_ID son obligatorios")

    # Agrupar por supermercado
    by_super = defaultdict(list)
    for o in offers:
        by_super[o["supermarket"]].append(o)

    today = date.today().strftime("%-d %B")
    lines = [f"🛒 Ofertas de hoy — {today}\n"]

    for supermarket, products in by_super.items():
        lines.append(supermarket.replace("_", " ").title())
        for p in products:
            lines.append(f"• {p['name']} → {p['price']:.2f} €")
        lines.append("")

    dashboard_url = os.getenv("DASHBOARD_URL", "")
    if dashboard_url:
        lines.append(f"Ver dashboard → {dashboard_url}")

    bot = telegram.Bot(token=TOKEN)
    import asyncio
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text="\n".join(lines)))


def send_all_prices(products_with_prices: list[dict]):
    """Envía un resumen de todos los precios actuales (para testing)."""
    if not TOKEN or not CHAT_ID:
        raise RuntimeError("TELEGRAM_TOKEN y TELEGRAM_CHAT_ID son obligatorios")

    by_super = defaultdict(list)
    for p in products_with_prices:
        by_super[p["supermarket"]].append(p)

    today = date.today().strftime("%-d %B")
    lines = [f"📊 Precios de hoy — {today}\n"]

    for supermarket, products in sorted(by_super.items()):
        lines.append(f"🏪 {supermarket.replace('_', ' ').title()}")
        for p in sorted(products, key=lambda x: x["name"]):
            if p.get("price") is not None:
                lines.append(f"  • {p['name']} → {p['price']:.2f} €")
            else:
                lines.append(f"  • {p['name']} → ❌ sin precio")
        lines.append("")

    dashboard_url = os.getenv("DASHBOARD_URL", "")
    if dashboard_url:
        lines.append(f"Ver dashboard → {dashboard_url}")

    bot = telegram.Bot(token=TOKEN)
    import asyncio
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text="\n".join(lines)))
