import pytest
from run_scrape import missing_notification_config

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for v in ("TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "SKIP_TELEGRAM"):
        monkeypatch.delenv(v, raising=False)

def test_detecta_el_token_que_falta(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    assert missing_notification_config() == ["TELEGRAM_TOKEN"]

def test_sin_nada_configurado_faltan_las_dos():
    assert missing_notification_config() == ["TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID"]

def test_no_falta_nada_con_ambos_configurados(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    assert missing_notification_config() == []

def test_skip_telegram_permite_probar_scrapers(monkeypatch):
    monkeypatch.setenv("SKIP_TELEGRAM", "1")
    assert missing_notification_config() == []
