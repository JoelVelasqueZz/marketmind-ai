from backend.agents.advisor_node import run_advisor

FORBIDDEN_WORDS = ["comprar", "vender", "buy", "sell", "ejecutar orden", "place order"]

NEWS = {"headline": "Test company reports strong earnings beat"}


def _signal(impact: str) -> dict:
    return {
        "instrument": "TST",
        "impact": impact,
        "confidence": 0.8,
        "evidence": ["Evidencia de prueba basada en la noticia y el movimiento de precio."],
        "price_comparison": {"instrument": "TST", "change_pct": 5.0, "window_days": 2, "note": "nota"},
    }


def test_advisor_never_suggests_trade_execution():
    for impact in ["positive", "negative", "neutral", "uncertain"]:
        briefing_item = run_advisor(_signal(impact), NEWS)
        action = briefing_item["research_action"].lower()
        for word in FORBIDDEN_WORDS:
            assert word not in action, f"research_action no debe sugerir '{word}': {action}"


def test_advisor_produces_executive_summary():
    briefing_item = run_advisor(_signal("positive"), NEWS)
    assert len(briefing_item["executive_summary"]) >= 2
    assert briefing_item["instrument"] == "TST"
    assert briefing_item["news_headline"] == NEWS["headline"]
