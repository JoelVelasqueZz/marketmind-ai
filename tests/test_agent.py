"""Smoke test del grafo de estados completo (LangGraph): analyst_node -> advisor_node.

Confirma que el pipeline de los dos agentes responde algo coherente end-to-end,
sin llamadas de red (LLM_MODE=mock, fijado en conftest.py).
"""
from backend.agents.graph import run_pipeline

NEWS = {
    "id": "n999",
    "headline": "Central bank surprises markets with emergency rate cut",
    "summary": "Policymakers cited rising recession risk as the primary driver.",
    "source": "Test Wire",
    "published_at": "2026-07-09T10:00:00Z",
    "instruments": ["TST"],
    "sector": "Macro",
    "topic": "Bancos centrales",
}

PRICE_COMPARISON = {
    "instrument": "TST",
    "change_pct": 4.2,
    "window_days": 2,
    "note": "TST subio 4.2% tras el anuncio.",
}


def test_pipeline_runs_end_to_end_and_produces_coherent_output():
    result = run_pipeline(NEWS, PRICE_COMPARISON)

    signal = result["signal"]
    briefing_item = result["briefing_item"]

    assert signal["impact"] in {"positive", "negative", "neutral", "uncertain"}
    assert 0.0 <= signal["confidence"] <= 1.0
    assert signal["disclaimer"]

    assert briefing_item["instrument"] == "TST"
    assert briefing_item["research_action"]
    assert briefing_item["executive_summary"]
