import os, sqlite3
from datetime import datetime

def _conn():
    return sqlite3.connect(os.getenv("DB_PATH", "tracker.db"))

def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supermarket TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            active INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id),
            price REAL,
            scraped_at TEXT NOT NULL
        );
        """)

def add_product(supermarket, name, url):
    with _conn() as c:
        c.execute(
            "INSERT INTO products (supermarket, name, url) VALUES (?,?,?)",
            (supermarket, name, url)
        )

def save_price(product_id, price):
    with _conn() as c:
        c.execute(
            "INSERT INTO price_history (product_id, price, scraped_at) VALUES (?,?,?)",
            (product_id, price, datetime.utcnow().isoformat())
        )

def get_last_price(product_id):
    with _conn() as c:
        row = c.execute(
            "SELECT price FROM price_history WHERE product_id=? ORDER BY scraped_at DESC LIMIT 1",
            (product_id,)
        ).fetchone()
    return row[0] if row else None

def get_price_history(product_id):
    with _conn() as c:
        rows = c.execute(
            "SELECT price, scraped_at FROM price_history WHERE product_id=? ORDER BY scraped_at ASC",
            (product_id,)
        ).fetchall()
    return [{"price": r[0], "scraped_at": r[1]} for r in rows]

def get_all_products():
    with _conn() as c:
        rows = c.execute(
            "SELECT id, supermarket, name, url FROM products WHERE active=1"
        ).fetchall()
    return [{"id": r[0], "supermarket": r[1], "name": r[2], "url": r[3]} for r in rows]
