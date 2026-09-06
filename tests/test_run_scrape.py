import pytest
from run_scrape import check_notification_config

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for v in ("TELEGRAM_TOKEN", "TELEGRAM_CHAT_ID", "SKIP_TELEGRAM"):
        monkeypatch.delenv(v, raising=False)

def test_falla_si_falta_el_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    with pytest.raises(SystemExit) as e:
        check_notification_config()
    assert "TELEGRAM_TOKEN" in str(e.value)
    assert "TELEGRAM_CHAT_ID" not in str(e.value).split("\n")[0]

def test_pasa_con_ambos_configurados(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    check_notification_config()

def test_skip_telegram_permite_probar_scrapers(monkeypatch):
    monkeypatch.setenv("SKIP_TELEGRAM", "1")
    check_notification_config()
