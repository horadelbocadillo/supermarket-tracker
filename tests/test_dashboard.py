import pytest
from db import init_db, add_product, save_price

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    init_db()
    add_product("mercadona", "Leche", "https://example.com")
    save_price(1, 0.65)

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from dashboard.app import app
    return TestClient(app)

def test_index_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Leche" in r.text

def test_detail_renders(client):
    r = client.get("/product/1")
    assert r.status_code == 200
    assert "Leche" in r.text
