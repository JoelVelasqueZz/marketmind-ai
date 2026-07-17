"""Agente 1 - Analista de Coyuntura de Mercados IA.

Nodo LangGraph puro (funcion de estado -> estado) para que sea testeable de
forma aislada, con el LLM mockeable via LLMClient. Produce la senal
explicable de impacto (HU2): impact, confidence, evidence, price_comparison,
disclaimer, suggested_action. Nunca incluye una accion de compra/venta.

Compliance Gate 360: tras cada intento del LLM, checks deterministas
(grounding numerico, fuentes, estructura) verifican la salida ANTES de
publicarla; si hay violaciones, se reinyectan al prompt y se reintenta
(contador acotado) o se marca la senal. Todo queda en la traza.
"""
import time

from backend.agents.compliance import run_compliance_checks, violations_prompt
from backend.agents.guardrails import ensure_research_action
from backend.agents.llm import LLMClient
from backend.agents.pricing import usage_fields
from backend.agents.prompts import ANALYST_SYSTEM_PROMPT, analyst_user_prompt
from backend.config import DISCLAIMER
from backend.schemas import AnalystLLMOutput

MAX_GATE_ATTEMPTS = 2


def run_analyst(
    news: dict,
    price_comparison: dict,
    llm: LLMClient | None = None,
    review_examples: list | None = None,
    trace=None,
    contaminate: bool = False,
) -> dict:
    """Ejecuta el analisis y devuelve un dict listo para persistir como Signal.

    review_examples: revisiones humanas pasadas para este instrumento (HU3),
    reinyectadas como few-shot para calibrar el criterio del Analista.
    trace: TraceRecorder opcional — registra la ejecucion para la Caja de
    Cristal (nodos, llamada LLM, guardrail, gate).
    contaminate: SOLO demo (mock) — fuerza una salida alucinada para mostrar
    al gate rechazandola.
    """
    client = llm or LLMClient()

    if trace is not None:
        trace.event("node_start", node="analyst")
    node_started = time.perf_counter()

    violations: str | None = None
    verdict = "ok"
    result = None
    safe_action = ""
    replaced = False
    signal_data: dict = {}
    checks: list[dict] = []

    for attempt in range(1, MAX_GATE_ATTEMPTS + 1):
        call_started = time.perf_counter()
        result = client.generate_structured(
            system_prompt=ANALYST_SYSTEM_PROMPT,
            user_prompt=analyst_user_prompt(
                news,
                price_comparison,
                review_examples,
                violations=violations,
                contaminate=contaminate and attempt == 1,
            ),
            schema=AnalystLLMOutput,
        )
        if trace is not None:
            trace.event(
                "llm_call",
                provider=getattr(client, "mode", "fake"),
                model=getattr(client, "model", "-"),
                latency_ms=round((time.perf_counter() - call_started) * 1000),
                attempts=getattr(client, "_last_attempts", 0) or 1,
                **usage_fields(client),
            )

        safe_action, replaced = ensure_research_action(
            result.suggested_action, price_comparison["instrument"]
        )
        signal_data = {
            "news_id": news["id"],
            "instrument": price_comparison["instrument"],
            "impact": result.impact,
            "confidence": result.confidence,
            "evidence": result.evidence,
            "sources": [news["source"]],
            "price_comparison": price_comparison,
            "disclaimer": DISCLAIMER,
            "suggested_action": safe_action,
        }
        checks = run_compliance_checks(signal_data, news)
        failed = [c for c in checks if not c["passed"]]

        if not failed:
            verdict = "corregida" if attempt > 1 else "ok"
            break
        if attempt == MAX_GATE_ATTEMPTS:
            verdict = "marcada"
            break
        violations = violations_prompt(failed)
        if trace is not None:
            trace.event(
                "retry",
                reason="compliance_gate",
                attempt=attempt,
                violations=[c["item"] for c in failed],
            )

    passed = sum(1 for c in checks if c["passed"])
    signal_data["compliance"] = {
        "verdict": verdict,
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }

    if trace is not None:
        trace.annotate(reasoning=result.reasoning)
        if replaced:
            trace.event(
                "guardrail",
                field="suggested_action",
                action="reemplazada: contenia lenguaje de ejecucion de ordenes",
            )
        trace.event("gate", passed=passed, total=len(checks), verdict=verdict)
        trace.event(
            "node_end",
            node="analyst",
            duration_ms=round((time.perf_counter() - node_started) * 1000),
            output_digest={"impact": result.impact, "confidence": result.confidence},
        )

    return signal_data


def analyst_node(state: dict) -> dict:
    """Wrapper compatible con LangGraph StateGraph: state -> partial state update."""
    signal = run_analyst(
        state["news"],
        state["price_comparison"],
        state.get("llm"),
        state.get("review_examples"),
        trace=state.get("trace"),
    )
    return {"signal": signal}
