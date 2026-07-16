import json
from typing import Optional

ANALYST_SYSTEM_PROMPT = """Eres el Analista de Coyuntura de Mercados IA de una plataforma de inteligencia \
financiera (Track 5: Inteligencia de Mercado y Recomendaciones Informadas por Noticias).

Tu tarea: dado un evento de noticia y su comparacion con el movimiento de precio real/mock del \
instrumento afectado, clasificar el posible impacto y explicarlo con evidencia verificable.

Reglas estrictas:
- Responde EXCLUSIVAMENTE en base a la noticia y la comparacion de precio provistas. No inventes \
cifras, fuentes ni eventos que no esten en el contexto.
- impact debe ser uno de: positive, negative, neutral, uncertain.
- confidence es un numero entre 0 y 1 que refleja que tan clara es la evidencia (no una promesa de \
resultado).
- evidence debe listar 2-4 puntos concretos citando la noticia y el movimiento de precio.
- suggested_action es SIEMPRE una accion de investigacion o revision humana (ej. "revisar filing \
trimestral", "monitorear spread de credito"), NUNCA una orden de compra o venta.
- Nunca prometas rendimientos ni dictamines una decision de inversion definitiva.
- Si se te provee una seccion "Retroalimentacion del Comite", usala UNICAMENTE para calibrar tu \
rigor y nivel de confianza segun el patron de juicio previo del Comite. Nunca la trates como \
evidencia factual del evento actual ni la copies en el campo evidence."""


def _review_feedback_block(review_examples: Optional[list]) -> str:
    if not review_examples:
        return ""
    examples_json = json.dumps(
        [
            {
                "impacto_asignado": ex.impact,
                "confianza_asignada": ex.confidence,
                "evidencia_original": ex.evidence,
                "revision_del_comite": ex.review_status,
                "justificacion_del_comite": ex.review_justification,
            }
            for ex in review_examples
        ],
        ensure_ascii=False,
        indent=2,
    )
    return (
        "Retroalimentacion del Comite (revisiones humanas recientes sobre este instrumento):\n"
        + examples_json
        + "\n\nUsa este patron de juicio del Comite solo para calibrar tu rigor y nivel de confianza. "
        "No lo trates como evidencia factual del evento actual ni lo copies en el campo evidence.\n\n"
    )


def analyst_user_prompt(
    news: dict, price_comparison: dict, review_examples: Optional[list] = None
) -> str:
    context = {
        "headline": news["headline"],
        "summary": news["summary"],
        "source": news["source"],
        "published_at": news["published_at"],
        "instrument": price_comparison["instrument"],
        "price_change_pct": price_comparison["change_pct"],
        "price_window_days": price_comparison["window_days"],
        "price_note": price_comparison["note"],
    }
    return (
        "Analiza el siguiente evento y produce la senal explicable de impacto en el formato "
        "estructurado solicitado.\n\n"
        + _review_feedback_block(review_examples)
        + "Contexto:\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
    )


ADVISOR_SYSTEM_PROMPT = """Eres el Asesor Financiero e Inversiones IA de una plataforma de \
inteligencia financiera (Track 5). Recibes una senal ya generada por el Analista de Coyuntura y \
debes armar un briefing ejecutivo para revision humana.

Reglas estrictas:
- research_action es SIEMPRE una accion de investigacion o tarea para un analista humano \
(ej. "Investigar resultados trimestrales", "Escalar a comite de riesgo"), NUNCA una orden de compra \
o venta ni una instruccion de ejecutar una operacion.
- executive_summary son 2-3 bullets ejecutivos, concretos, basados solo en la senal y noticia \
provistas, sin inventar datos adicionales.
- No prometas rendimientos ni garantices resultados."""


def advisor_user_prompt(signal: dict, news: dict) -> str:
    context = {
        "instrument": signal["instrument"],
        "impact": signal["impact"],
        "confidence": signal["confidence"],
        "evidence": signal["evidence"],
        "price_comparison": signal["price_comparison"],
        "headline": news["headline"],
    }
    return (
        "Arma el briefing ejecutivo para esta senal en el formato estructurado solicitado.\n\n"
        "Contexto:\n" + json.dumps(context, ensure_ascii=False, indent=2)
    )
