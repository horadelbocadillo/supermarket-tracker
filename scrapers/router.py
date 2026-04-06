from scrapers import mercadona, carrefour, lidl, el_corte_ingles, el_jamon
from scrapers.base import ScrapeResult

_SCRAPERS = {
    "mercadona": mercadona.scrape,
    "carrefour": carrefour.scrape,
    "lidl": lidl.scrape,
    "el_corte_ingles": el_corte_ingles.scrape,
    "el_jamon": el_jamon.scrape,
}

def scrape(supermarket: str, url: str) -> ScrapeResult:
    fn = _SCRAPERS.get(supermarket)
    if not fn:
        return ScrapeResult(price=None, available=False)
    return fn(url)
