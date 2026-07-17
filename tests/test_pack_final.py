"""Tests del pack final: Taximetro, Triaje, Vigencia y causa raiz NTSB."""
from datetime import datetime, timedelta, timezone

from backend.agents.pricing import estimate_cost_usd
from backend.services.freshness import compute_freshness
from backend.services.triage import TRIAGE_RULES, compute_triage

# --- Triaje ---


def test_triage_levels_match_their_literal_rules():
    cases = [
        # (impact, confidence, change_pct) -> nivel esperado
        (("neutral", 0.33, -0.15), "azul"),      # HYG del dataset: ruta monitor
        (("negative", 0.8, -3.5), "rojo"),
        (("positive", 0.71, 2.35), "naranja"),   # ECU2035/n026: el caso de la demo
        (("uncertain", 0.63, -1.26), "amarillo"),  # TLT del dataset
        (("uncertain", 0.4, 0.6), "verde"),
        (("neutral", 0.55, 0.3), "amarillo"),    # neutral pero >= umbral: no es azul
    ]
    for args, expected in cases:
        result = compute_triage(*args)
        assert result["level"] == expected, f"{args} -> {result['level']}, esperaba {expected}"
        assert result["sla"]
        assert result["rule"]


def test_triage_rules_have_unique_priorities():
    priorities = [priority for _, priority, _, _, _ in TRIAGE_RULES]
    assert sorted(priorities) == [0, 1, 2, 3, 4]


def test_signal_out_includes_triage(client):
    s = client.post(
        "/api/signals/generate", json={"news_id": "n026", "instrument": "ECU2035"}
    ).json()
    assert s["triage"]["level"] == "naranja"
    assert s["triage"]["sla"] == "revisar en < 2h"
    assert "confidence >= 0.6" in s["triage"]["rule"]


# --- Vigencia ---


def test_freshness_decays_by_half_life():
    now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
    fresh = compute_freshness(now, "ECU2035", now=now)
    assert fresh["pct"] == 1.0
    assert not fresh["stale"]
    assert fresh["half_life_days"] == 10.0  # credit

    one_half_life = compute_freshness(now - timedelta(days=10), "ECU2035", now=now)
    assert one_half_life["pct"] == 0.5
    assert not one_half_life["stale"]  # el umbral es estricto (< 0.5)

    old = compute_freshness(now - timedelta(days=20), "ECU2035", now=now)
    assert old["pct"] == 0.25
    assert old["stale"]


def test_freshness_crypto_decays_faster_than_credit():
    now = datetime(2026, 7, 17, 12, 0, tzinfo=timezone.utc)
    created = now - timedelta(days=4)
    crypto = compute_freshness(created, "BTC", now=now)
    credit = compute_freshness(created, "ECU2035", now=now)
    assert crypto["half_life_days"] == 2.0
    assert crypto["pct"] < credit["pct"]
    assert crypto["stale"] and not credit["stale"]


def test_freshness_handles_naive_created_at():
    naive = datetime(2026, 7, 17, 12, 0)  # como llega de sqlite
    result = compute_freshness(naive, "AAPL", now=naive.replace(tzinfo=timezone.utc))
    assert result["pct"] == 1.0


def test_signal_out_includes_fresh_freshness(client):
    s = client.post(
        "/api/signals/generate", json={"news_id": "n001", "instrument": "TSLA"}
    ).json()
    assert s["freshness"]["pct"] >= 0.99
    assert s["freshness"]["stale"] is False


# --- Taximetro ---


def test_pricing_table():
    assert estimate_cost_usd("gemini", "gemini-flash-latest", 1_000_000, 0) == 0.10
    assert estimate_cost_usd("claude", "claude-sonnet-5", 0, 1_000_000) == 15.0
    assert estimate_cost_usd("mock", "gemini-flash-latest", 999, 999) == 0.0
    assert estimate_cost_usd("desconocido", "x", 1000, 1000) == 0.0


def test_trace_llm_call_includes_tokens_and_cost(client):
    s = client.post(
        "/api/signals/generate", json={"news_id": "n001", "instrument": "TSLA"}
    ).json()
    trace = client.get(f"/api/signals/{s['id']}/trace").json()
    llm_calls = [e for r in trace["runs"] for e in r["events"] if e["type"] == "llm_call"]
    assert llm_calls
    for call in llm_calls:
        assert call["tokens_in"] > 0
        assert call["tokens_out"] > 0
        assert call["cost_usd"] == 0.0  # mock: $0, honesto
        assert call["measured"] is False  # mock: estimado len/4


def test_monitor_edge_records_saved_cost(client):
    # HYG/n007 rutea a monitor en el briefing de credit-macro (verificado en demo).
    briefing = client.post("/api/briefing/generate?watchlist=credit-macro").json()
    hyg = next(i for i in briefing["items"] if i["instrument"] == "HYG")
    trace = client.get(f"/api/signals/{hyg['signal']['id']}/trace").json()
    edges = [e for r in trace["runs"] for e in r["events"] if e["type"] == "edge_decision"]
    monitor_edges = [e for e in edges if e["target"] == "monitor"]
    assert monitor_edges
    assert "saved_usd_est" in monitor_edges[0]


# --- NTSB: causa raiz ---


def test_review_with_cause_persists_and_feeds_dashboard(client):
    s = client.post(
        "/api/signals/generate", json={"news_id": "n026", "instrument": "ECU2035"}
    ).json()
    reviewed = client.post(
        f"/api/signals/{s['id']}/review",
        json={
            "status": "descartada",
            "justification": "El precio ya habia descontado la noticia.",
            "cause": "sobre_reaccion_al_precio",
        },
    ).json()
    assert reviewed["review_cause"] == "sobre_reaccion_al_precio"

    counts = client.get("/api/signals/review-causes").json()
    assert counts["sobre_reaccion_al_precio"] == 1


def test_review_rejects_cause_outside_taxonomy(client):
    s = client.post(
        "/api/signals/generate", json={"news_id": "n001", "instrument": "TSLA"}
    ).json()
    r = client.post(
        f"/api/signals/{s['id']}/review",
        json={"status": "descartada", "justification": "n/a", "cause": "porque_si"},
    )
    assert r.status_code == 422


def test_cause_flows_into_few_shot_prompt(client):
    from backend.agents.prompts import _review_feedback_block
    from backend.schemas import ReviewExample

    example = ReviewExample(
        instrument="ECU2035",
        impact="positive",
        confidence=0.71,
        evidence=["e1", "e2"],
        review_status="descartada",
        review_justification="Sobre-reaccion.",
        cause="sobre_reaccion_al_precio",
    )
    block = _review_feedback_block([example])
    assert "causa_raiz" in block
    assert "sobre_reaccion_al_precio" in block

    sin_causa = ReviewExample(
        instrument="ECU2035",
        impact="positive",
        confidence=0.71,
        evidence=["e1", "e2"],
        review_status="revisada",
        review_justification="ok",
    )
    assert "causa_raiz" not in _review_feedback_block([sin_causa])
