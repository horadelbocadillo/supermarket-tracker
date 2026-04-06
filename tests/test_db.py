import os, pytest
from db import init_db, add_product, save_price, get_last_price, get_price_history

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))

def test_save_and_retrieve_price():
    init_db()
    add_product("mercadona", "Leche", "https://example.com")
    save_price(1, 0.65)
    price = get_last_price(1)
    assert price == 0.65

def test_price_history():
    init_db()
    add_product("lidl", "Aceite", "https://example.com")
    save_price(1, 4.99)
    save_price(1, 4.49)
    history = get_price_history(1)
    assert len(history) == 2
    assert history[0]["price"] == 4.99
