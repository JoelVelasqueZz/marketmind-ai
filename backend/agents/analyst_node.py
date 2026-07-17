"""Agente 1 - Analista de Coyuntura de Mercados IA.

Nodo LangGraph puro (funcion de estado -> estado) para que sea testeable de
forma aislada, con el LLM mockeable via LLMClient. Produce la senal
explicable de impacto (HU2): impact, confidence, evidence, price_comparison,
disclaimer, suggested_action. Nunca incluye una accion de compra/venta.
"""
import time

from backend.agents.guardrails import ensure_research_action
from backend.agents.llm import LLMClient
from backend.agents.pricing import usage_fields
from backend.agents.prompts import ANALYST_SYSTEM_PROMPT, analyst_user_prompt
from backend.config import DISCLAIMER
from backend.schemas import AnalystLLMOutput


def run_analyst(
    news: dict,
    price_comparison: dict,
    llm: LLMClient | None = None,
    review_examples: list | None = None,
    trace=None,
) -> dict:
    """Ejecuta el analisis y devuelve un dict listo para persistir como Signal.

    review_examples: revisiones humanas pasadas para este instrumento (HU3),
    reinyectadas como few-shot para calibrar el criterio del Analista.
    trace: TraceRecorder opcional — registra la ejecucion para la Caja de
    Cristal (eventos de nodo, llamada LLM y guardrail).
    """
    client = llm or LLMClient()

    if trace is not None:
        trace.event("node_start", node="analyst")
    started = time.perf_counter()

    result: AnalystLLMOutput = client.generate_structured(
        system_prompt=ANALYST_SYSTEM_PROMPT,
        user_prompt=analyst_user_prompt(news, price_comparison, review_examples),
        schema=AnalystLLMOutput,
    )

    if trace is not None:
        trace.event(
            "llm_call",
            provider=getattr(client, "mode", "fake"),
            model=getattr(client, "model", "-"),
            latency_ms=round((time.perf_counter() - started) * 1000),
            attempts=getattr(client, "_last_attempts", 0) or 1,
            **usage_fields(client),
        )
        # Declarado por el modelo (no verificado): se guarda para el visor.
        trace.annotate(reasoning=result.reasoning)

    suggested_action, replaced = ensure_research_action(
        result.suggested_action, price_comparison["instrument"]
    )
    if replaced and trace is not None:
        trace.event(
            "guardrail",
            field="suggested_action",
            action="reemplazada: contenia lenguaje de ejecucion de ordenes",
        )

    if trace is not None:
        trace.event(
            "node_end",
            node="analyst",
            duration_ms=round((time.perf_counter() - started) * 1000),
            output_digest={"impact": result.impact, "confidence": result.confidence},
        )

    return {
        "news_id": news["id"],
        "instrument": price_comparison["instrument"],
        "impact": result.impact,
        "confidence": result.confidence,
        "evidence": result.evidence,
        "sources": [news["source"]],
        "price_comparison": price_comparison,
        "disclaimer": DISCLAIMER,
        "suggested_action": suggested_action,
    }


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
