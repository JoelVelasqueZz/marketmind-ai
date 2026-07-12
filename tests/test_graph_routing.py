"""Tests del ruteo condicional del grafo (LangGraph).

Senal neutral de baja confianza -> monitor_node (sin gastar la llamada del
Asesor); cualquier otra senal -> advisor_node. El LLM se inyecta como fake a
traves del estado del grafo para controlar la salida del Analista.
"""
from backend.agents.graph import route_after_analyst, run_pipeline
from backend.schemas import AdvisorLLMOutput, AnalystLLMOutput

NEWS = {
    "id": "n998",
    "headline": "Regulator publishes routine quarterly liquidity report",
    "summary": "No material changes versus the previous quarter.",
    "source": "Test Wire",
    "published_at": "2026-07-09T10:00:00Z",
    "instruments": ["TST"],
    "sector": "Macro",
    "topic": "Regulacion",
}

PRICE_COMPARISON = {
    "instrument": "TST",
    "change_pct": 0.1,
    "window_days": 2,
    "note": "TST practicamente sin cambio (0.1%) tras la publicacion.",
}


class FakeLLM:
    """Devuelve una salida fija del Analista y cuenta las llamadas al Asesor."""

    def __init__(self, impact: str, confidence: float):
        self.impact = impact
        self.confidence = confidence
        self.advisor_calls = 0

    def generate_structured(self, system_prompt, user_prompt, schema):
        if schema is AnalystLLMOutput:
            return AnalystLLMOutput(
                impact=self.impact,
                confidence=self.confidence,
                evidence=["Evidencia de prueba.", "Movimiento leve en la ventana."],
                reasoning="Razonamiento de prueba.",
                suggested_action="Monitorear el instrumento antes de cualquier decision.",
            )
        self.advisor_calls += 1
        return AdvisorLLMOutput(
            research_action="Investigar el evento en detalle.",
            executive_summary=["Resumen de prueba."],
        )


def test_neutral_low_confidence_routes_to_monitor_without_advisor_call():
    fake = FakeLLM(impact="neutral", confidence=0.3)

    result = run_pipeline(NEWS, PRICE_COMPARISON, llm=fake)

    assert fake.advisor_calls == 0
    item = result["briefing_item"]
    assert "monitoreo" in item["research_action"].lower()
    assert item["instrument"] == "TST"
    assert item["news_headline"] == NEWS["headline"]
    assert item["price_change_pct"] == PRICE_COMPARISON["change_pct"]
    assert item["executive_summary"]


def test_clear_signal_still_routes_to_advisor():
    fake = FakeLLM(impact="positive", confidence=0.9)

    result = run_pipeline(NEWS, PRICE_COMPARISON, llm=fake)

    assert fake.advisor_calls == 1
    assert result["briefing_item"]["research_action"] == "Investigar el evento en detalle."


def test_route_after_analyst_thresholds():
    assert route_after_analyst({"signal": {"impact": "neutral", "confidence": 0.49}}) == "monitor"
    assert route_after_analyst({"signal": {"impact": "neutral", "confidence": 0.5}}) == "advisor"
    assert route_after_analyst({"signal": {"impact": "uncertain", "confidence": 0.1}}) == "advisor"
    assert route_after_analyst({"signal": {"impact": "negative", "confidence": 0.2}}) == "advisor"


def test_briefing_reuse_applies_monitor_route_for_low_confidence_neutral(client, monkeypatch):
    """La ruta de reuso de briefing.py aplica el mismo ruteo que el grafo:
    una senal neutral < 0.5 ya persistida tampoco gasta la llamada del Asesor."""
    from sqlmodel import Session

    from backend.db import engine
    from backend.models import Signal
    from backend.services import briefing as briefing_service

    def _no_advisor(*args, **kwargs):
        raise AssertionError("run_advisor no debe llamarse para una senal neutral de baja confianza")

    monkeypatch.setattr(briefing_service, "run_advisor", _no_advisor)

    with Session(engine) as session:
        news = briefing_service._latest_news_for_instrument("ECU2035")
        session.add(
            Signal(
                news_id=news["id"],
                instrument="ECU2035",
                impact="neutral",
                confidence=0.3,
                evidence=["Sin movimiento relevante.", "Noticia informativa."],
                sources=[news["source"]],
                price_comparison={
                    "instrument": "ECU2035",
                    "change_pct": 0.1,
                    "window_days": 2,
                    "note": "ECU2035 practicamente sin cambio.",
                },
                disclaimer="Contenido informativo, no es asesoria personalizada.",
                suggested_action="Monitorear el instrumento.",
            )
        )
        session.commit()

        briefing = briefing_service.generate_briefing("ecuador-latam", session)

    item = next(i for i in briefing.items if i.instrument == "ECU2035")
    assert "monitoreo" in item.research_action.lower()
