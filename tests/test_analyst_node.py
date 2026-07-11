from backend.agents.analyst_node import run_analyst

FORBIDDEN_WORDS = ["comprar", "vender", "buy", "sell", "compra ahora", "venta inmediata"]

NEWS = {
    "id": "n999",
    "headline": "Test company reports strong earnings beat",
    "summary": "Revenue and margins both exceeded consensus estimates.",
    "source": "Test Wire",
    "published_at": "2026-07-10T10:00:00Z",
    "instruments": ["TST"],
    "sector": "Technology",
    "topic": "Earnings",
}


def _price_comparison(change_pct: float) -> dict:
    return {
        "instrument": "TST",
        "change_pct": change_pct,
        "window_days": 2,
        "note": f"TST movio {change_pct}% en la ventana.",
    }


def test_positive_price_move_yields_positive_impact():
    signal = run_analyst(NEWS, _price_comparison(6.5))
    assert signal["impact"] == "positive"
    assert 0.0 <= signal["confidence"] <= 1.0


def test_negative_price_move_yields_negative_impact():
    signal = run_analyst(NEWS, _price_comparison(-7.2))
    assert signal["impact"] == "negative"


def test_flat_price_move_yields_neutral_impact():
    signal = run_analyst(NEWS, _price_comparison(0.1))
    assert signal["impact"] == "neutral"


def test_signal_never_suggests_trade_execution():
    signal = run_analyst(NEWS, _price_comparison(5.0))
    action = signal["suggested_action"].lower()
    for word in FORBIDDEN_WORDS:
        assert word not in action, f"suggested_action no debe sugerir '{word}': {action}"


def test_signal_includes_disclaimer_and_sources():
    signal = run_analyst(NEWS, _price_comparison(3.0))
    assert signal["disclaimer"]
    assert signal["sources"] == ["Test Wire"]
    assert len(signal["evidence"]) >= 2
