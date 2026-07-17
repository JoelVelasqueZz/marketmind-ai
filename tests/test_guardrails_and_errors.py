"""Tests de mitigacion de riesgos en runtime (no solo en prompts):

- Guardrail anti-ordenes: lenguaje de compra/venta del LLM se descarta y
  sustituye por una accion de revision humana (HU2/HU3).
- Salida invalida del LLM -> LLMOutputInvalid -> HTTP 502 honesto (no un 500).
- Modo claude reescrito para anthropic==0.40.0 (messages.create + validacion
  Pydantic), verificado con el cliente mockeado.
- La justificacion de revision no puede ser vacia (HU3).
- El executive_summary del briefing es reproducible entre regeneraciones.
"""
import json

import pytest

from backend.agents.advisor_node import run_advisor
from backend.agents.analyst_node import run_analyst
from backend.agents.guardrails import ensure_research_action
from backend.agents.llm import LLMClient, LLMOutputInvalid
from backend.schemas import AdvisorLLMOutput, AnalystLLMOutput

NEWS = {
    "id": "n997",
    "headline": "Test issuer announces buyback program",
    "summary": "Details pending.",
    "source": "Test Wire",
    "published_at": "2026-07-09T10:00:00Z",
    "instruments": ["TST"],
    "sector": "Macro",
    "topic": "Corporativo",
}

PRICE_COMPARISON = {
    "instrument": "TST",
    "change_pct": 3.0,
    "window_days": 2,
    "note": "TST subio 3.0% en la ventana.",
}


class ForbiddenActionLLM:
    """Simula un LLM real que desobedece el prompt y sugiere una orden."""

    def generate_structured(self, system_prompt, user_prompt, schema):
        if schema is AnalystLLMOutput:
            return AnalystLLMOutput(
                impact="positive",
                confidence=0.8,
                evidence=["Evidencia uno.", "Evidencia dos."],
                reasoning="Razonamiento de prueba.",
                suggested_action="Comprar TST antes del cierre de la sesion.",
            )
        return AdvisorLLMOutput(
            research_action="Ejecutar la orden de compra de TST inmediatamente.",
            executive_summary=["Resumen de prueba."],
        )


def test_guardrail_replaces_trade_language():
    action, replaced = ensure_research_action("Comprar TSLA ahora mismo", "TSLA")
    assert replaced
    assert "comprar" not in action.lower()
    assert "analista humano" in action


def test_guardrail_keeps_descriptive_mentions():
    text = "Monitorear el impacto de la compra de bonos por el BCE sobre ECU2035."
    action, replaced = ensure_research_action(text, "ECU2035")
    assert not replaced
    assert action == text


def test_guardrail_keeps_research_actions():
    text = "Investigar resultados trimestrales y actualizar la tesis."
    action, replaced = ensure_research_action(text, "TST")
    assert not replaced
    assert action == text


def test_analyst_discards_trade_action_from_real_llm():
    signal = run_analyst(NEWS, PRICE_COMPARISON, llm=ForbiddenActionLLM())
    assert "comprar" not in signal["suggested_action"].lower()
    assert "analista humano" in signal["suggested_action"]


def test_advisor_discards_trade_action_from_real_llm():
    signal = {
        "instrument": "TST",
        "impact": "positive",
        "confidence": 0.8,
        "evidence": ["e1", "e2"],
        "price_comparison": PRICE_COMPARISON,
    }
    item = run_advisor(signal, NEWS, llm=ForbiddenActionLLM())
    assert "orden" not in item["research_action"].lower() or "descartada" in item["research_action"].lower()
    assert "analista humano" in item["research_action"]


def test_invalid_llm_output_maps_to_502(client, monkeypatch):
    from backend.services import signals as signals_service

    def broken_analyst(*args, **kwargs):
        raise LLMOutputInvalid("salida malformada de prueba")

    monkeypatch.setattr(signals_service, "run_analyst", broken_analyst)
    r = client.post("/api/signals/generate", json={"news_id": "n001", "instrument": "TSLA"})
    assert r.status_code == 502
    assert "descartada por seguridad" in r.json()["detail"]


class _FakeAnthropicMessage:
    def __init__(self, text: str):
        self.content = [type("Block", (), {"text": text})()]


class _FakeAnthropicClient:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.messages = self

    def create(self, **kwargs):
        assert kwargs.get("temperature") == 0.2
        return _FakeAnthropicMessage(self._response_text)


def test_claude_mode_parses_structured_output(monkeypatch):
    import anthropic

    valid = json.dumps(
        {
            "impact": "positive",
            "confidence": 0.7,
            "evidence": ["e1", "e2"],
            "reasoning": "r",
            "suggested_action": "Investigar el evento.",
        }
    )
    monkeypatch.setattr(anthropic, "Anthropic", lambda api_key=None: _FakeAnthropicClient(valid))
    result = LLMClient(mode="claude", model="claude-sonnet-5").generate_structured(
        "sys", "user", AnalystLLMOutput
    )
    assert result.impact == "positive"
    assert result.confidence == 0.7


def test_claude_mode_invalid_json_raises_llm_output_invalid(monkeypatch):
    import anthropic

    monkeypatch.setattr(
        anthropic, "Anthropic", lambda api_key=None: _FakeAnthropicClient("no soy JSON")
    )
    with pytest.raises(LLMOutputInvalid):
        LLMClient(mode="claude", model="claude-sonnet-5").generate_structured(
            "sys", "user", AnalystLLMOutput
        )


def test_review_rejects_empty_justification(client):
    generated = client.post(
        "/api/signals/generate", json={"news_id": "n001", "instrument": "TSLA"}
    ).json()
    r = client.post(
        f"/api/signals/{generated['id']}/review",
        json={"status": "revisada", "justification": ""},
    )
    assert r.status_code == 422


def test_briefing_executive_summary_is_reproducible(client):
    b1 = client.post("/api/briefing/generate?watchlist=tech-megacaps").json()
    b2 = client.post("/api/briefing/generate?watchlist=tech-megacaps").json()

    summaries_1 = {i["instrument"]: i["executive_summary"] for i in b1["items"]}
    summaries_2 = {i["instrument"]: i["executive_summary"] for i in b2["items"]}
    assert summaries_1 == summaries_2
