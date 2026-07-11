"""Generador determinista usado por LLMClient en MODE=mock.

No hace llamadas de red: interpreta el mismo contexto estructurado que se le
pasaria a un LLM real (embebido en el prompt como JSON) y produce una salida
coherente con las reglas de negocio, para poder construir y demostrar el
pipeline completo sin gastar creditos ni depender de una API key.
"""
import json
import re

from backend.schemas import AdvisorLLMOutput, AnalystLLMOutput


def _extract_context(user_prompt: str) -> dict:
    match = re.search(r"Contexto:\n(\{.*\})", user_prompt, re.DOTALL)
    if not match:
        return {}
    return json.loads(match.group(1))


def mock_response(schema, user_prompt: str):
    context = _extract_context(user_prompt)

    if schema is AnalystLLMOutput:
        return _mock_analyst(context)
    if schema is AdvisorLLMOutput:
        return _mock_advisor(context)
    raise ValueError(f"mock_llm: schema no soportado {schema}")


def _mock_analyst(context: dict) -> AnalystLLMOutput:
    change_pct = context.get("price_change_pct", 0.0)
    instrument = context.get("instrument", "el instrumento")
    headline = context.get("headline", "")
    price_note = context.get("price_note", "")
    source = context.get("source", "la fuente")

    magnitude = abs(change_pct)
    if change_pct >= 2:
        impact = "positive"
    elif change_pct <= -2:
        impact = "negative"
    elif magnitude < 0.5:
        impact = "neutral"
    else:
        impact = "uncertain"

    confidence = round(min(0.95, 0.55 + magnitude / 15), 2)

    evidence = [
        f"Noticia de {source}: \"{headline}\".",
        price_note,
        f"La magnitud del movimiento ({change_pct}%) es "
        + ("significativa" if magnitude >= 2 else "moderada" if magnitude >= 0.5 else "leve")
        + " en la ventana analizada.",
    ]

    reasoning = (
        f"El evento reportado se correlaciona con un cambio de {change_pct}% en {instrument} "
        f"dentro de la ventana analizada. Esta senal es informativa y no constituye asesoria "
        f"personalizada ni garantiza resultados futuros."
    )

    suggested_action = f"Investigar el impacto del evento sobre {instrument} antes de tomar cualquier decision."

    return AnalystLLMOutput(
        impact=impact,
        confidence=confidence,
        evidence=evidence,
        reasoning=reasoning,
        suggested_action=suggested_action,
    )


def _mock_advisor(context: dict) -> AdvisorLLMOutput:
    impact = context.get("impact", "uncertain")
    instrument = context.get("instrument", "el instrumento")
    headline = context.get("headline", "")
    evidence = context.get("evidence", [])
    confidence = context.get("confidence", 0.5)

    if impact == "negative":
        research_action = f"Escalar a comite de riesgo: revisar exposicion actual a {instrument}."
    elif impact == "positive":
        research_action = f"Investigar catalizadores y actualizar tesis de inversion sobre {instrument}."
    else:
        research_action = f"Monitorear evolucion de {instrument} antes de tomar cualquier accion."

    executive_summary = [
        f"{headline}",
        f"Senal del Analista: {impact} (confianza {round(confidence * 100)}%).",
    ]
    if evidence:
        executive_summary.append(evidence[0])

    return AdvisorLLMOutput(
        research_action=research_action,
        executive_summary=executive_summary,
    )
