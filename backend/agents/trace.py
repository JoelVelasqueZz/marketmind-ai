"""TraceRecorder: el expediente de ejecucion de cada senal (Caja de Cristal).

Registra QUE hizo el orquestador — nodos ejecutados, decision de cada arista
con su regla y valores, llamadas LLM con latencia e intentos, reusos — en una
estructura versionada que se persiste con la senal y se puede rebobinar.

Lo alimentan los TRES caminos de generacion (HU2 directo, pipeline del
briefing, y reuso parcial del briefing), no solo el grafo: por eso vive aqui
y no dentro de LangGraph. on_event permite ademas transmitir los mismos
eventos en vivo (SSE/polling) sin duplicar la fuente.

Contrato v1:
  {"v": 1, "runs": [{llm_mode, model, path, started_at, truncated,
                     reasoning?, events: [{t_ms, type, ...}]}]}
  path: "analysis" | "briefing" | "briefing-reuse"
  Tipos de evento: node_start, node_end, edge_decision, llm_call, reuse,
  guardrail (y "gate", reservado). Campos nuevos son aditivos y NO suben v;
  el visor ignora tipos que no conoce.
"""
import time
from datetime import datetime, timezone
from typing import Callable, Optional

TRACE_VERSION = 1
MAX_EVENTS = 100
MAX_REASONING_CHARS = 1500


class TraceRecorder:
    def __init__(
        self,
        llm_mode: str,
        model: str,
        path: str,
        on_event: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self._t0 = time.perf_counter()
        self._on_event = on_event
        self.events: list[dict] = []
        self.run: dict = {
            "llm_mode": llm_mode,
            "model": model,
            "path": path,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "truncated": False,
            "reasoning": None,
        }

    def event(self, type: str, **data) -> None:
        evt = {"t_ms": round((time.perf_counter() - self._t0) * 1000), "type": type, **data}
        self.events.append(evt)
        if self._on_event is not None:
            self._on_event(evt)

    def annotate(self, **fields) -> None:
        """Campos a nivel de run (p. ej. el reasoning declarado por el modelo)."""
        for key, value in fields.items():
            if key == "reasoning" and isinstance(value, str) and len(value) > MAX_REASONING_CHARS:
                value = value[:MAX_REASONING_CHARS] + "…"
            self.run[key] = value

    def to_json(self) -> dict:
        events = self.events
        truncated = bool(self.run.get("truncated"))
        if len(events) > MAX_EVENTS:
            # Recorte estructural (nunca de bytes): se conservan inicio y final.
            head = MAX_EVENTS // 2
            events = events[:head] + events[-(MAX_EVENTS - head) :]
            truncated = True
        return {"v": TRACE_VERSION, "runs": [{**self.run, "truncated": truncated, "events": events}]}

    @staticmethod
    def merge(existing: Optional[dict], new_doc: dict) -> dict:
        """Anexa las corridas de new_doc a una traza ya persistida (runs[])."""
        if not existing:
            return new_doc
        return {"v": TRACE_VERSION, "runs": [*existing.get("runs", []), *new_doc["runs"]]}
