def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_instruments(client):
    r = client.get("/api/instruments")
    assert r.status_code == 200
    symbols = {i["symbol"] for i in r.json()}
    assert {"AAPL", "BTC", "NVDA", "ECU2035"}.issubset(symbols)


def test_price_history(client):
    r = client.get("/api/prices/BTC", params={"days": 7})
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 7
    for point in body:
        assert point["date"]
        assert point["close"] > 0


def test_price_history_unknown_symbol_returns_empty(client):
    r = client.get("/api/prices/DOES-NOT-EXIST")
    assert r.status_code == 200
    assert r.json() == []


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


def test_news_free_text_search(client):
    r = client.get("/api/news", params={"q": "bitcoin"})
    assert r.status_code == 200
    body = r.json()
    assert len(body) > 0
    for item in body:
        haystack = " ".join(
            [item["headline"], item["summary"], item["source"], item["topic"], *item["instruments"]]
        ).lower()
        assert "bitcoin" in haystack

    r_none = client.get("/api/news", params={"q": "palabra-que-no-existe-en-ninguna-noticia"})
    assert r_none.json() == []


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


def test_signal_generate_reuses_existing_by_default(client):
    r1 = client.post("/api/signals/generate", json={"news_id": "n004", "instrument": "BTC"})
    r2 = client.post("/api/signals/generate", json={"news_id": "n004", "instrument": "BTC"})
    assert r1.json()["id"] == r2.json()["id"]

    r3 = client.post(
        "/api/signals/generate", json={"news_id": "n004", "instrument": "BTC", "force": True}
    )
    assert r3.json()["id"] != r1.json()["id"]


def test_briefing_generate_reuses_signals_and_does_not_duplicate_tasks(client):
    r1 = client.post("/api/briefing/generate", params={"watchlist": "crypto-core"})
    signal_ids_1 = {item["signal"]["id"] for item in r1.json()["items"]}
    tasks_after_first = client.get("/api/tasks").json()

    r2 = client.post("/api/briefing/generate", params={"watchlist": "crypto-core"})
    signal_ids_2 = {item["signal"]["id"] for item in r2.json()["items"]}
    tasks_after_second = client.get("/api/tasks").json()

    assert signal_ids_1 == signal_ids_2
    assert len(tasks_after_second) == len(tasks_after_first)


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


def test_task_complete_and_reopen_flow(client):
    r = client.post(
        "/api/tasks",
        json={"instrument": "AAPL", "title": "Revisar tarea de prueba", "description": "desc"},
    )
    task = r.json()
    assert task["status"] == "open"

    r_done = client.post(f"/api/tasks/{task['id']}/complete")
    assert r_done.status_code == 200
    assert r_done.json()["status"] == "done"

    r_reopen = client.post(f"/api/tasks/{task['id']}/reopen")
    assert r_reopen.status_code == 200
    assert r_reopen.json()["status"] == "open"


def test_task_complete_unknown_returns_404(client):
    r = client.post("/api/tasks/does-not-exist/complete")
    assert r.status_code == 404


def test_watchlist_overview_includes_price_and_signal(client):
    client.post("/api/signals/generate", json={"news_id": "n004", "instrument": "BTC"})

    r = client.get("/api/briefing/watchlists/crypto-core/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["watchlist_id"] == "crypto-core"
    symbols = {a["symbol"] for a in body["assets"]}
    assert {"BTC", "ETH"} == symbols

    btc = next(a for a in body["assets"] if a["symbol"] == "BTC")
    assert btc["price"] is not None
    assert btc["signal"] is not None
    assert btc["signal"]["impact"] in {"positive", "negative", "neutral", "uncertain"}

    eth = next(a for a in body["assets"] if a["symbol"] == "ETH")
    assert eth["signal"] is None


def test_watchlist_overview_unknown_returns_404(client):
    r = client.get("/api/briefing/watchlists/does-not-exist/overview")
    assert r.status_code == 404


def test_watchlists_include_all_option_first(client):
    r = client.get("/api/briefing/watchlists")
    assert r.status_code == 200
    watchlists = r.json()
    assert watchlists[0]["id"] == "all"
    assert len(watchlists[0]["instruments"]) >= 9


def test_all_watchlist_overview_covers_every_instrument_with_price(client):
    r = client.get("/api/briefing/watchlists/all/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["watchlist_id"] == "all"
    for asset in body["assets"]:
        assert asset["price"] is not None, f"{asset['symbol']} no tiene historico de precio"
        assert asset["change_pct_1d"] is not None
