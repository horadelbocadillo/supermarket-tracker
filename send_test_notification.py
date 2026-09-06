"""Manda por Telegram el listado completo de precios actuales.

Comprobación manual del camino de notificación de punta a punta. No scrapea:
solo lee los últimos precios ya guardados en la BD y los envía, así que tarda
segundos y no depende de Firefox ni de las webs de los supermercados.

Sirve para confirmar que TELEGRAM_TOKEN y TELEGRAM_CHAT_ID son correctos sin
tener que esperar a que algún producto entre en oferta.

Se lanza desde Actions → "Test Telegram notification" → Run workflow.
"""
import os

from dotenv import load_dotenv
load_dotenv()

from db import get_all_products, get_last_price
from bot.telegram import send_all_prices


def build_payload():
    return [{**p, "price": get_last_price(p["id"])} for p in get_all_products()]


if __name__ == "__main__":
    payload = build_payload()
    con_precio = sum(1 for p in payload if p["price"] is not None)
    print(f"Enviando {con_precio} precios de {len(payload)} productos a Telegram...")
    send_all_prices(payload)
    print("Mensaje enviado.")
