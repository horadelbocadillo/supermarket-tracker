import json
from db import init_db, add_product

if __name__ == "__main__":
    init_db()
    with open("products.json") as f:
        products = json.load(f)
    for p in products:
        add_product(p["supermarket"], p["name"], p["url"])
    print(f"Seeded {len(products)} products.")
