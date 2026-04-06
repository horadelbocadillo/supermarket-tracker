import pytest
from scrapers.base import ScrapeResult

def test_scrape_result_structure():
    r = ScrapeResult(price=1.29, available=True)
    assert r.price == 1.29
    assert r.available is True

def test_scrape_result_failed():
    r = ScrapeResult(price=None, available=False)
    assert r.price is None
