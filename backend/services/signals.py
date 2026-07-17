from typing import Optional

from sqlmodel import Session, select

from backend.agents.analyst_node import run_analyst
from backend.agents.trace import TraceRecorder
from backend.config import LLM_MODE, LLM_MODEL
from backend.models import Signal
from backend.providers.price_provider import MockPriceProvider
from backend.services.freshness import compute_freshness
from backend.services.radar import get_news
from backend.services.triage import compute_triage
from backend.schemas import FreshnessOut, PriceComparison, ReviewExample, SignalOut, TriageOut

_price_provider = MockPriceProvider()

MAX_REVIEW_EXAMPLES = 3


class NewsNotFound(Exception):
    pass


def find_existing_signal(news_id: str, instrument: str, session: Session) -> Optional[Signal]:
    """Busca una senal ya generada para este (noticia, instrumento).

    Reusarla evita crear duplicados en cada clic de "Generar" y no gasta
    cuota del LLM de mas para un analisis que ya existe.
    """
    query = (
        select(Signal)
        .where(Signal.news_id == news_id, Signal.instrument == instrument.upper())
        .order_by(Signal.created_at.desc())
    )
    return session.exec(query).first()


def list_review_examples(
    instrument: str, session: Session, limit: int = MAX_REVIEW_EXAMPLES
) -> list[ReviewExample]:
    """Ultimas senales revisadas por un humano para este instrumento (HU3).

    Se reinyectan como ejemplos few-shot al Analista para que su criterio se
    calibre con el juicio ya emitido por el Comite, sin reentrenar el modelo.
    """
    query = (
        select(Signal)
        .where(Signal.instrument == instrument.upper(), Signal.review_status != "pending")
        .order_by(Signal.reviewed_at.desc())
        .limit(limit)
    )
    return [
        ReviewExample(
            instrument=s.instrument,
            impact=s.impact,
            confidence=s.confidence,
            evidence=s.evidence,
            review_status=s.review_status,
            review_justification=s.review_justification or "",
            cause=s.review_cause,
        )
        for s in session.exec(query).all()
    ]


def generate_signal(news_id: str, instrument: str, session: Session, force: bool = False) -> SignalOut:
    if not force:
        existing = find_existing_signal(news_id, instrument, session)
        if existing is not None:
            return _to_out(existing)

    news = get_news(news_id)
    if news is None:
        raise NewsNotFound(f"No existe la noticia {news_id}")

    price_comparison = _price_provider.compare_around_date(instrument, news["published_at"])
    if price_comparison is None:
        price_comparison = {
            "instrument": instrument.upper(),
            "change_pct": 0.0,
            "window_days": 2,
            "note": f"No hay historico de precio disponible para {instrument.upper()} en el rango mock.",
        }

    review_examples = list_review_examples(instrument, session)
    recorder = TraceRecorder(llm_mode=LLM_MODE, model=LLM_MODEL, path="analysis")
    signal_data = run_analyst(
        news, price_comparison, review_examples=review_examples, trace=recorder
    )
    signal = Signal(**signal_data)
    signal.execution_trace = recorder.to_json()
    session.add(signal)
    session.commit()
    session.refresh(signal)
    out = _to_out(signal)
    out.review_examples_used = review_examples
    return out


def list_signals(instrument: Optional[str], session: Session) -> list[SignalOut]:
    query = select(Signal)
    if instrument:
        query = query.where(Signal.instrument == instrument.upper())
    signals = session.exec(query.order_by(Signal.created_at.desc())).all()
    return [_to_out(s) for s in signals]


def get_signal(signal_id: str, session: Session) -> Optional[Signal]:
    return session.get(Signal, signal_id)


def review_signal(
    signal_id: str,
    status: str,
    justification: str,
    session: Session,
    cause: Optional[str] = None,
) -> Optional[SignalOut]:
    from datetime import datetime, timezone

    signal = session.get(Signal, signal_id)
    if signal is None:
        return None
    # La revision es un overwrite completo del estado actual. La causa raiz
    # (NTSB) solo aplica a escalada/descartada: aprobar una senal nunca debe
    # contar en el tablero de modos de fallo.
    if status not in ("escalada", "descartada"):
        cause = None
    signal.review_status = status
    signal.review_justification = justification
    signal.review_cause = cause
    signal.reviewed_at = datetime.now(timezone.utc)
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return _to_out(signal)


def review_cause_counts(session: Session) -> dict[str, int]:
    """Tablero NTSB: ¿de que se equivoca el Analista segun el Comite?"""
    reviewed = session.exec(
        select(Signal).where(Signal.review_cause != None)  # noqa: E711 - SQLAlchemy
    ).all()
    counts: dict[str, int] = {}
    for s in reviewed:
        counts[s.review_cause] = counts.get(s.review_cause, 0) + 1
    return counts


def _to_out(signal: Signal) -> SignalOut:
    return SignalOut(
        id=signal.id,
        news_id=signal.news_id,
        instrument=signal.instrument,
        impact=signal.impact,
        confidence=signal.confidence,
        evidence=signal.evidence,
        sources=signal.sources,
        price_comparison=PriceComparison(**signal.price_comparison),
        disclaimer=signal.disclaimer,
        suggested_action=signal.suggested_action,
        created_at=signal.created_at,
        review_status=signal.review_status,
        review_justification=signal.review_justification,
        review_cause=signal.review_cause,
        has_trace=bool(signal.execution_trace),
        has_attribution=bool(signal.attribution),
        triage=TriageOut(
            **compute_triage(signal.impact, signal.confidence, signal.price_comparison["change_pct"])
        ),
        freshness=FreshnessOut(**compute_freshness(signal.created_at, signal.instrument)),
    )
