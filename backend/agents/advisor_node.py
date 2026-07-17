"""Agente 2 - Asesor Financiero e Inversiones IA.

Nodo LangGraph puro que consume la senal del Analista y arma el item de
briefing (HU3): noticia + movimiento + accion de investigacion sugerida.
Nunca ejecuta ni sugiere una compra/venta: solo genera texto para una tarea
o alerta de revision humana.
"""
from backend.agents.guardrails import ensure_research_action
from backend.agents.llm import LLMClient
from backend.agents.prompts import ADVISOR_SYSTEM_PROMPT, advisor_user_prompt
from backend.schemas import AdvisorLLMOutput


def run_advisor(signal: dict, news: dict, llm: LLMClient | None = None) -> dict:
    client = llm or LLMClient()
    result: AdvisorLLMOutput = client.generate_structured(
        system_prompt=ADVISOR_SYSTEM_PROMPT,
        user_prompt=advisor_user_prompt(signal, news),
        schema=AdvisorLLMOutput,
    )

    research_action, _ = ensure_research_action(result.research_action, signal["instrument"])

    return {
        "instrument": signal["instrument"],
        "news_headline": news["headline"],
        "price_change_pct": signal["price_comparison"]["change_pct"],
        "research_action": research_action,
        "executive_summary": result.executive_summary,
    }


def advisor_node(state: dict) -> dict:
    """Wrapper compatible con LangGraph StateGraph: state -> partial state update."""
    briefing_item = run_advisor(state["signal"], state["news"], state.get("llm"))
    return {"briefing_item": briefing_item}
