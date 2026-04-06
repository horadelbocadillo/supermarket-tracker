from statistics import median

MIN_HISTORY = 7
DAYS_30 = 30

def compute_median(prices: list[float]) -> float:
    return median(prices)

def is_offer(current_price: float, history: list[dict]) -> bool:
    """
    Devuelve True si:
    1. Hay al menos MIN_HISTORY registros
    2. current_price < mediana histórica
    3. current_price == mínimo de los últimos DAYS_30 registros
    """
    prices = [h["price"] for h in history if h["price"] is not None]
    if len(prices) < MIN_HISTORY:
        return False
    med = compute_median(prices)
    recent = prices[-DAYS_30:]
    return current_price < med and current_price <= min(recent)
