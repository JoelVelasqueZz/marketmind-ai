def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_instruments(client):
    r = client.get("/api/instruments")
    assert r.status_code == 200
    symbols = {i["symbol"] for i in r.json()}
    assert {"AAPL", "BTC", "NVDA"}.issubset(symbols)


def test_news_filters_by_asset(client):
    r = client.get("/api/news", params={"asset": "NVDA"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) > 0
    for item in body:
        assert "NVDA" in item["instruments"]
        assert item["source"]
        assert item["published_at"]


def test_news_filters_by_max_age(client):
    r_all = client.get("/api/news")
    r_recent = client.get("/api/news", params={"max_age_days": 1})
    assert len(r_recent.json()) <= len(r_all.json())
    for item in r_recent.json():
        assert item["age_days"] <= 1


def test_signal_generate_and_review_flow(client):
    r = client.post("/api/signals/generate", json={"news_id": "n002", "instrument": "NVDA"})
    assert r.status_code == 200
    signal = r.json()
    assert signal["impact"] in {"positive", "negative", "neutral", "uncertain"}
    assert signal["review_status"] == "pending"

    r2 = client.post(
        f"/api/signals/{signal['id']}/review",
        json={"status": "revisada", "justification": "Confirmado manualmente para el test."},
    )
    assert r2.status_code == 200
    assert r2.json()["review_status"] == "revisada"
    assert r2.json()["review_justification"]


def test_signal_generate_unknown_news_returns_404(client):
    r = client.post("/api/signals/generate", json={"news_id": "does-not-exist", "instrument": "AAPL"})
    assert r.status_code == 404


def test_briefing_generate_creates_tasks_not_orders(client):
    r = client.post("/api/briefing/generate", params={"watchlist": "tech-megacaps"})
    assert r.status_code == 200
    briefing = r.json()
    assert briefing["watchlist_id"] == "tech-megacaps"
    assert len(briefing["items"]) > 0
    for item in briefing["items"]:
        action_text = item["research_action"].lower()
        assert "comprar" not in action_text
        assert "vender" not in action_text

    r_tasks = client.get("/api/tasks")
    assert r_tasks.status_code == 200
    assert len(r_tasks.json()) >= len(briefing["items"])
