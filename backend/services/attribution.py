"""Sondeo contrafactual: que peso mas en la decision del Analista.

Dos re-ejecuciones controladas con el MISMO run_analyst de produccion:
- sin_movimiento: el cambio de precio se anula -> ¿se sostiene el impacto?
- sin_titular: la noticia se neutraliza -> ¿se sostiene la confianza?

Es un experimento sobre el modelo (etiqueta honesta: "sondeo empirico"), no
una lectura de sus pesos: la explicacion resultante es causal y demostrable
("sin el movimiento de precio, la misma senal cae a neutral"). El resultado
se cachea en Signal.attribution con el llm_mode usado — si difiere del de la
senal original, el visor debe avisarlo (comparar manzanas con manzanas).
"""
from datetime import datetime, timezone

from sqlmodel import Session

from backend.agents.analyst_node import run_analyst
from backend.config import LLM_MODE, LLM_MODEL
from backend.models import Signal
from backend.services.radar import get_news
from backend.services.signals import NewsNotFound, list_review_examples

ATTRIBUTION_VERSION = 1

DISCLAIMER_SONDEO = (
    "Sondeo empirico: 2 re-ejecuciones controladas del Analista con entradas "
    "modificadas. No es una lectura interna del modelo ni una prediccion."
)


def compute_attribution(signal: Signal, session: Session, force: bool = False) -> dict:
    """Calcula (o devuelve cacheado) el sondeo contrafactual de una senal."""
    if signal.attribution and not force:
        return signal.attribution

    news = get_news(signal.news_id)
    if news is None:
        raise NewsNotFound(f"No existe la noticia {signal.news_id} para sondear la senal")

    base_pc = signal.price_comparison
    # Experimento controlado: TODO lo demas (incluido el few-shot del Comite
    # que uso la senal original) se mantiene constante; solo cambia la
    # variable sondeada.
    review_examples = list_review_examples(signal.instrument, session)

    flat_pc = {
        **base_pc,
        "change_pct": 0.0,
        "note": "(sondeo contrafactual: sin variacion de precio)",
    }
    no_price = run_analyst(news, flat_pc, review_examples=review_examples)

    neutral_news = {**news, "headline": "", "summary": ""}
    no_headline = run_analyst(neutral_news, base_pc, review_examples=review_examples)

    attribution = {
        "v": ATTRIBUTION_VERSION,
        "llm_mode": LLM_MODE,
        "model": LLM_MODEL,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base": {"impact": signal.impact, "confidence": signal.confidence},
        "probes": [
            {
                "key": "sin_movimiento",
                "label": "Sin el movimiento de precio",
                "impact": no_price["impact"],
                "confidence": no_price["confidence"],
            },
            {
                "key": "sin_titular",
                "label": "Sin la noticia (solo el precio)",
                "impact": no_headline["impact"],
                "confidence": no_headline["confidence"],
            },
        ],
        "note": DISCLAIMER_SONDEO,
    }

    signal.attribution = attribution
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return attribution
