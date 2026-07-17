"""Expediente 360: identidad y rol del revisor + cadena de custodia append-only."""


def _signal(client, news_id="n026", instrument="ECU2035"):
    return client.post(
        "/api/signals/generate", json={"news_id": news_id, "instrument": instrument}
    ).json()


def test_analista_cannot_escalate(client):
    s = _signal(client)
    r = client.post(
        f"/api/signals/{s['id']}/review",
        json={
            "status": "escalada",
            "justification": "Creo que amerita comité.",
            "reviewer": "Ana",
            "role": "analista",
        },
    )
    assert r.status_code == 403
    assert "lead" in r.json()["detail"].lower()


def test_lead_can_escalate_and_it_is_recorded(client):
    s = _signal(client)
    r = client.post(
        f"/api/signals/{s['id']}/review",
        json={
            "status": "escalada",
            "justification": "Exposición soberana relevante.",
            "reviewer": "Luis (Lead)",
            "role": "lead",
        },
    )
    assert r.status_code == 200
    assert r.json()["review_status"] == "escalada"
    assert r.json()["reviewed_by"] == "Luis (Lead)"


def test_analista_can_review_and_dismiss(client):
    s = _signal(client)
    for status in ("revisada", "descartada"):
        r = client.post(
            f"/api/signals/{s['id']}/review",
            json={
                "status": status,
                "justification": f"Marcada como {status}.",
                "reviewer": "Ana",
                "role": "analista",
            },
        )
        assert r.status_code == 200


def test_review_events_are_append_only(client):
    s = _signal(client)
    client.post(
        f"/api/signals/{s['id']}/review",
        json={"status": "revisada", "justification": "Primera revisión.", "reviewer": "Ana", "role": "analista"},
    )
    client.post(
        f"/api/signals/{s['id']}/review",
        json={
            "status": "escalada",
            "justification": "Reconsiderada, escalo.",
            "reviewer": "Luis",
            "role": "lead",
        },
    )

    events = client.get(f"/api/signals/{s['id']}/events").json()
    assert len(events) == 2  # cada transición deja su propia fila
    assert events[0]["from_status"] == "pending"
    assert events[0]["to_status"] == "revisada"
    assert events[0]["reviewer"] == "Ana"
    assert events[1]["from_status"] == "revisada"
    assert events[1]["to_status"] == "escalada"
    assert events[1]["role"] == "lead"


def test_events_404_for_unknown_signal(client):
    assert client.get("/api/signals/nope/events").status_code == 404
