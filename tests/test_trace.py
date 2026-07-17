"""Tests de la Caja de Cristal: la traza de ejecucion por los 3 caminos.

En LLM_MODE=mock la SECUENCIA de eventos (types/nodes/targets) es determinista;
los campos de tiempo (t_ms, latency_ms, started_at) se excluyen del assert.
"""
from backend.agents.graph import run_pipeline
from backend.agents.trace import TraceRecorder
from backend.schemas import AdvisorLLMOutput, AnalystLLMOutput

NEWS = {
    "id": "n996",
    "headline": "Issuer publishes routine liquidity report",
    "summary": "No material changes.",
    "source": "Test Wire",
    "published_at": "2026-07-09T10:00:00Z",
    "instruments": ["TST"],
    "sector": "Macro",
    "topic": "Regulacion",
}


def _price(change_pct: float) -> dict:
    return {
        "instrument": "TST",
        "change_pct": change_pct,
        "window_days": 2,
        "note": f"TST movio {change_pct}% en la ventana.",
    }


class FakeLLM:
    def __init__(self, impact: str, confidence: float):
        self.impact = impact
        self.confidence = confidence

    def generate_structured(self, system_prompt, user_prompt, schema):
        if schema is AnalystLLMOutput:
            return AnalystLLMOutput(
                impact=self.impact,
                confidence=self.confidence,
                evidence=["Evidencia uno.", "Evidencia dos."],
                reasoning="Razonamiento de prueba.",
                suggested_action="Monitorear el instrumento.",
            )
        return AdvisorLLMOutput(
            research_action="Investigar el evento.", executive_summary=["Resumen."]
        )


def _sequence(recorder: TraceRecorder) -> list[tuple]:
    return [(e["type"], e.get("node") or e.get("target")) for e in recorder.events]


def test_trace_sequence_monitor_path():
    rec = TraceRecorder(llm_mode="mock", model="-", path="briefing")
    run_pipeline(NEWS, _price(0.1), llm=FakeLLM("neutral", 0.3), trace=rec)

    assert _sequence(rec) == [
        ("node_start", "analyst"),
        ("llm_call", None),
        ("node_end", "analyst"),
        ("edge_decision", "monitor"),
        ("node_start", "monitor"),
        ("node_end", "monitor"),
    ]
    edge = next(e for e in rec.events if e["type"] == "edge_decision")
    assert edge["rule"] == "impact == 'neutral' and confidence < 0.5"
    assert edge["inputs"] == {"impact": "neutral", "confidence": 0.3}
    assert edge["llm_cost"].startswith("$0")


def test_trace_sequence_advisor_path():
    rec = TraceRecorder(llm_mode="mock", model="-", path="briefing")
    run_pipeline(NEWS, _price(3.5), llm=FakeLLM("positive", 0.8), trace=rec)

    assert _sequence(rec) == [
        ("node_start", "analyst"),
        ("llm_call", None),
        ("node_end", "analyst"),
        ("edge_decision", "advisor"),
        ("node_start", "advisor"),
        ("llm_call", None),
        ("node_end", "advisor"),
    ]
    assert rec.run["reasoning"] == "Razonamiento de prueba."


def test_hu2_trace_persisted_and_served(client):
    generated = client.post(
        "/api/signals/generate", json={"news_id": "n001", "instrument": "TSLA"}
    ).json()
    assert generated["has_trace"] is True

    trace = client.get(f"/api/signals/{generated['id']}/trace").json()
    assert trace["v"] == 1
    assert len(trace["runs"]) == 1
    run = trace["runs"][0]
    assert run["path"] == "analysis"
    assert run["llm_mode"] == "mock"
    types = [e["type"] for e in run["events"]]
    assert types[0] == "node_start"
    assert "llm_call" in types
    # HU2 no rutea: la arista es exclusiva del pipeline del briefing.
    assert "edge_decision" not in types


def test_briefing_trace_uses_pipeline_path(client):
    briefing = client.post("/api/briefing/generate?watchlist=tech-megacaps").json()
    for item in briefing["items"]:
        trace = client.get(f"/api/signals/{item['signal']['id']}/trace").json()
        assert trace["runs"][0]["path"] == "briefing"
        types = [e["type"] for e in trace["runs"][0]["events"]]
        assert "edge_decision" in types


def test_briefing_signal_only_reuse_appends_run(client):
    # Senal creada por HU2 (sin tarea) -> el briefing anexa un run de reuso.
    generated = client.post(
        "/api/signals/generate", json={"news_id": "n026", "instrument": "ECU2035"}
    ).json()
    client.post("/api/briefing/generate?watchlist=ecuador-latam")

    trace = client.get(f"/api/signals/{generated['id']}/trace").json()
    assert [r["path"] for r in trace["runs"]] == ["analysis", "briefing-reuse"]
    reuse_events = trace["runs"][1]["events"]
    assert reuse_events[0]["type"] == "reuse"
    assert reuse_events[0]["scope"] == "signal-only"
    assert any(e["type"] == "edge_decision" for e in reuse_events)


def test_briefing_full_reuse_does_not_grow_trace(client):
    client.post("/api/briefing/generate?watchlist=tech-megacaps")
    first = {
        i["signal"]["id"]: len(
            client.get(f"/api/signals/{i['signal']['id']}/trace").json()["runs"]
        )
        for i in client.post("/api/briefing/generate?watchlist=tech-megacaps").json()["items"]
    }
    second = {
        i["signal"]["id"]: len(
            client.get(f"/api/signals/{i['signal']['id']}/trace").json()["runs"]
        )
        for i in client.post("/api/briefing/generate?watchlist=tech-megacaps").json()["items"]
    }
    assert first == second


def test_force_creates_new_signal_with_own_trace(client):
    first = client.post(
        "/api/signals/generate", json={"news_id": "n001", "instrument": "TSLA"}
    ).json()
    second = client.post(
        "/api/signals/generate", json={"news_id": "n001", "instrument": "TSLA", "force": True}
    ).json()

    assert first["id"] != second["id"]
    t1 = client.get(f"/api/signals/{first['id']}/trace").json()
    t2 = client.get(f"/api/signals/{second['id']}/trace").json()
    assert len(t1["runs"]) == 1
    assert len(t2["runs"]) == 1


def test_trace_404_for_legacy_signal(client):
    from sqlmodel import Session

    from backend.db import engine
    from backend.models import Signal

    with Session(engine) as session:
        legacy = Signal(
            news_id="n001",
            instrument="TSLA",
            impact="neutral",
            confidence=0.5,
            evidence=["e1", "e2"],
            sources=["Test"],
            price_comparison={"instrument": "TSLA", "change_pct": 0.0, "window_days": 2, "note": "-"},
            disclaimer="d",
        )
        session.add(legacy)
        session.commit()
        legacy_id = legacy.id

    r = client.get(f"/api/signals/{legacy_id}/trace")
    assert r.status_code == 404
    assert "anterior a la trazabilidad" in r.json()["detail"]


def test_trace_truncation_is_structural():
    rec = TraceRecorder(llm_mode="mock", model="-", path="analysis")
    for i in range(250):
        rec.event("node_start", node=f"n{i}")
    doc = rec.to_json()
    run = doc["runs"][0]
    assert len(run["events"]) == 100
    assert run["truncated"] is True
    # Se conservan inicio y final, se recorta por el medio.
    assert run["events"][0]["node"] == "n0"
    assert run["events"][-1]["node"] == "n249"
