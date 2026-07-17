"""Compliance Gate 360: verificación determinista + loop de auto-corrección."""
from backend.agents.compliance import _check_numeric_grounding, run_compliance_checks


def _signal(evidence, change_pct=2.35, action="Investigar el evento.", sources=("Primicias",)):
    return {
        "impact": "positive",
        "confidence": 0.71,
        "evidence": list(evidence),
        "sources": list(sources),
        "price_comparison": {"instrument": "ECU2035", "change_pct": change_pct},
        "suggested_action": action,
    }


NEWS = {"source": "Primicias", "headline": "h"}


def test_numeric_grounding_passes_when_cited_pct_matches():
    check = _check_numeric_grounding(["El bono subió +2.35% en la ventana."], 2.35)
    assert check["passed"]


def test_numeric_grounding_fails_on_fabricated_pct():
    check = _check_numeric_grounding(["El bono se disparó +7.0% según el mercado."], 2.35)
    assert not check["passed"]
    assert "7" in check["detail"]


def test_numeric_grounding_ignores_confidence_percentages():
    # "confianza del 90%" no es una cifra de movimiento — no debe marcarse.
    check = _check_numeric_grounding(["Impacto claro con confianza del 90%.", "Subió +2.4%."], 2.35)
    assert check["passed"]


def test_grounding_tolerates_rounding():
    check = _check_numeric_grounding(["Movimiento de +2.4% aprox."], 2.35)
    assert check["passed"]


def test_all_checks_pass_for_grounded_signal():
    checks = run_compliance_checks(_signal(["Fuente Primicias.", "Subió +2.35%."]), NEWS)
    assert all(c["passed"] for c in checks)
    assert {c["item"] for c in checks} >= {
        "cifras_ancladas_al_dato",
        "fuente_verificada",
        "accion_no_es_orden",
        "evidencia_suficiente",
    }


def test_check_flags_fabricated_source():
    sig = _signal(["e1", "e2"], sources=["Fuente Inventada SA"])
    checks = run_compliance_checks(sig, NEWS)
    assert not next(c for c in checks if c["item"] == "fuente_verificada")["passed"]


# --- Loop de auto-corrección end-to-end (mock) ---


def test_contaminated_signal_is_rejected_then_corrected(client):
    signal = client.post(
        "/api/signals/generate",
        json={"news_id": "n026", "instrument": "ECU2035", "demo_contaminate": True},
    ).json()

    # Tras la auto-corrección, la señal publicada cumple el gate.
    assert signal["compliance"]["verdict"] == "corregida"
    assert signal["compliance"]["passed"] == signal["compliance"]["total"]

    trace = client.get(f"/api/signals/{signal['id']}/trace").json()
    events = [e for r in trace["runs"] for e in r["events"]]
    types = [e["type"] for e in events]
    assert "retry" in types  # el primer intento fue rechazado
    assert "gate" in types
    # dos llamadas al LLM: la contaminada + la corregida
    assert types.count("llm_call") == 2
    retry = next(e for e in events if e["type"] == "retry")
    assert "cifras_ancladas_al_dato" in retry["violations"]


def test_clean_signal_passes_gate_first_try(client):
    signal = client.post(
        "/api/signals/generate", json={"news_id": "n026", "instrument": "ECU2035"}
    ).json()
    assert signal["compliance"]["verdict"] == "ok"
    assert signal["compliance"]["passed"] == signal["compliance"]["total"]

    trace = client.get(f"/api/signals/{signal['id']}/trace").json()
    types = [e["type"] for r in trace["runs"] for e in r["events"]]
    assert "retry" not in types
    assert types.count("llm_call") == 1


def test_gate_checks_exposed_in_signal_out(client):
    signal = client.post(
        "/api/signals/generate", json={"news_id": "n001", "instrument": "TSLA"}
    ).json()
    checks = signal["compliance"]["checks"]
    grounding = next(c for c in checks if c["item"] == "cifras_ancladas_al_dato")
    assert grounding["passed"]
    assert grounding["rule"]  # la regla literal viaja al visor
