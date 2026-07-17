"""Sala de Máquinas: el endpoint SSE transmite los eventos del pipeline en vivo."""
import json


def _consume_sse(client, url) -> list[dict]:
    events = []
    with client.stream("GET", url) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        for line in response.iter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))
    return events


def test_stream_emits_pipeline_events_and_done(client):
    events = _consume_sse(
        client, "/api/signals/generate/stream?news_id=n026&instrument=ECU2035"
    )
    types = [e["type"] for e in events]
    # Los eventos del pipeline llegan en vivo, y el stream cierra con "done".
    assert "node_start" in types
    assert "llm_call" in types
    assert "gate" in types
    assert types[-1] == "done"

    signal_id = events[-1]["signal_id"]
    # La señal quedó persistida y su traza coincide con lo transmitido.
    trace = client.get(f"/api/signals/{signal_id}/trace").json()
    assert trace["runs"][0]["path"] == "analysis"


def test_stream_reports_error_for_unknown_news(client):
    events = _consume_sse(
        client, "/api/signals/generate/stream?news_id=nope&instrument=TSLA"
    )
    assert events[-1]["type"] == "error"
    assert "nope" in events[-1]["detail"]


def test_stream_shows_gate_correction_live(client):
    events = _consume_sse(
        client,
        "/api/signals/generate/stream?news_id=n026&instrument=ECU2035&demo_contaminate=true",
    )
    types = [e["type"] for e in events]
    assert "retry" in types  # el jurado ve el rechazo del gate en vivo
    assert types[-1] == "done"
