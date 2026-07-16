"""Agente 1 - Analista de Coyuntura de Mercados IA.

Nodo LangGraph puro (funcion de estado -> estado) para que sea testeable de
forma aislada, con el LLM mockeable via LLMClient. Produce la senal
explicable de impacto (HU2): impact, confidence, evidence, price_comparison,
disclaimer, suggested_action. Nunca incluye una accion de compra/venta.
"""
from backend.agents.llm import LLMClient
from backend.agents.prompts import ANALYST_SYSTEM_PROMPT, analyst_user_prompt
from backend.config import DISCLAIMER
from backend.schemas import AnalystLLMOutput


def run_analyst(
    news: dict,
    price_comparison: dict,
    llm: LLMClient | None = None,
    review_examples: list | None = None,
) -> dict:
    """Ejecuta el analisis y devuelve un dict listo para persistir como Signal.

    review_examples: revisiones humanas pasadas para este instrumento (HU3),
    reinyectadas como few-shot para calibrar el criterio del Analista.
    """
    client = llm or LLMClient()
    result: AnalystLLMOutput = client.generate_structured(
        system_prompt=ANALYST_SYSTEM_PROMPT,
        user_prompt=analyst_user_prompt(news, price_comparison, review_examples),
        schema=AnalystLLMOutput,
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
        "suggested_action": result.suggested_action,
    }


def analyst_node(state: dict) -> dict:
    """Wrapper compatible con LangGraph StateGraph: state -> partial state update."""
    signal = run_analyst(
        state["news"], state["price_comparison"], state.get("llm"), state.get("review_examples")
    )
    return {"signal": signal}
