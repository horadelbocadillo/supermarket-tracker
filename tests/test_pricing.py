from pricing import is_offer, compute_median

def test_no_offer_insufficient_history():
    # Menos de 7 registros → nunca oferta
    history = [{"price": p} for p in [1.0, 0.9, 0.8]]
    assert is_offer(0.8, history) is False

def test_offer_when_below_median_and_min_30d():
    history = [{"price": p} for p in [1.0]*10 + [0.5]]  # 11 registros
    # precio actual 0.5 == mínimo 30d y < mediana (1.0)
    assert is_offer(0.5, history) is True

def test_no_offer_when_above_median():
    history = [{"price": p} for p in [1.0]*10 + [1.2]]
    assert is_offer(1.2, history) is False

def test_median_calculation():
    assert compute_median([1, 2, 3, 4, 5]) == 3
    assert compute_median([1, 2, 3, 4]) == 2.5
