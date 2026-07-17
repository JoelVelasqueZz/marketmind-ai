"""Agente 2 - Asesor Financiero e Inversiones IA.

Nodo LangGraph puro que consume la senal del Analista y arma el item de
briefing (HU3): noticia + movimiento + accion de investigacion sugerida.
Nunca ejecuta ni sugiere una compra/venta: solo genera texto para una tarea
o alerta de revision humana.
"""
import time

from backend.agents.guardrails import ensure_research_action
from backend.agents.llm import LLMClient
from backend.agents.prompts import ADVISOR_SYSTEM_PROMPT, advisor_user_prompt
from backend.schemas import AdvisorLLMOutput


def run_advisor(signal: dict, news: dict, llm: LLMClient | None = None, trace=None) -> dict:
    client = llm or LLMClient()

    if trace is not None:
        trace.event("node_start", node="advisor")
    started = time.perf_counter()

    result: AdvisorLLMOutput = client.generate_structured(
        system_prompt=ADVISOR_SYSTEM_PROMPT,
        user_prompt=advisor_user_prompt(signal, news),
        schema=AdvisorLLMOutput,
    )

    if trace is not None:
        trace.event(
            "llm_call",
            provider=getattr(client, "mode", "fake"),
            model=getattr(client, "model", "-"),
            latency_ms=round((time.perf_counter() - started) * 1000),
            attempts=getattr(client, "_last_attempts", 0) or 1,
        )

    research_action, replaced = ensure_research_action(result.research_action, signal["instrument"])
    if replaced and trace is not None:
        trace.event(
            "guardrail",
            field="research_action",
            action="reemplazada: contenia lenguaje de ejecucion de ordenes",
        )

    if trace is not None:
        trace.event(
            "node_end",
            node="advisor",
            duration_ms=round((time.perf_counter() - started) * 1000),
            output_digest={"research_action": research_action[:80]},
        )

    return {
        "instrument": signal["instrument"],
        "news_headline": news["headline"],
        "price_change_pct": signal["price_comparison"]["change_pct"],
        "research_action": research_action,
        "executive_summary": result.executive_summary,
    }


def advisor_node(state: dict) -> dict:
    """Wrapper compatible con LangGraph StateGraph: state -> partial state update."""
    briefing_item = run_advisor(
        state["signal"], state["news"], state.get("llm"), trace=state.get("trace")
    )
    return {"briefing_item": briefing_item}
