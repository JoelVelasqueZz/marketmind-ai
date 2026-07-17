"""Tests del sondeo contrafactual "¿Que peso mas?" (determinista en mock).

Caso de referencia (verificado contra los datos): n026 (Superintendencia de
Bancos) sobre ECU2035 -> +2.35% -> positive 0.71 en mock. Sin el movimiento
de precio la senal cae a neutral 0.30; sin el titular la confianza cae a 0.46.
"""


def _generate_ecu_signal(client) -> dict:
    return client.post(
        "/api/signals/generate", json={"news_id": "n026", "instrument": "ECU2035"}
    ).json()


def test_attribution_probes_are_deterministic_in_mock(client):
    signal = _generate_ecu_signal(client)
    assert signal["impact"] == "positive"
    assert signal["confidence"] == 0.71

    attribution = client.post(f"/api/signals/{signal['id']}/attribution").json()

    assert attribution["v"] == 1
    assert attribution["llm_mode"] == "mock"
    assert attribution["base"] == {"impact": "positive", "confidence": 0.71}

    probes = {p["key"]: p for p in attribution["probes"]}
    # Sin el movimiento de precio, la misma senal cae a neutral de baja confianza:
    # el precio es lo que sostiene la clasificacion.
    assert probes["sin_movimiento"]["impact"] == "neutral"
    assert probes["sin_movimiento"]["confidence"] == 0.3
    # Sin el titular, el impacto (que en mock depende del precio) se sostiene,
    # pero la confianza cae: la noticia aportaba evidencia.
    assert probes["sin_titular"]["confidence"] < signal["confidence"]
    assert "sondeo empirico" in attribution["note"].lower()


def test_attribution_is_cached_until_forced(client):
    signal = _generate_ecu_signal(client)

    first = client.post(f"/api/signals/{signal['id']}/attribution").json()
    second = client.post(f"/api/signals/{signal['id']}/attribution").json()
    assert first["generated_at"] == second["generated_at"]

    refreshed = client.get("/api/signals?asset=ECU2035").json()[0]
    assert refreshed["has_attribution"] is True

    forced = client.post(f"/api/signals/{signal['id']}/attribution?force=true").json()
    assert forced["probes"] == first["probes"]


def test_attribution_unknown_signal_404(client):
    r = client.post("/api/signals/nope/attribution")
    assert r.status_code == 404
