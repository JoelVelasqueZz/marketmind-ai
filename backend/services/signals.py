from typing import Optional

from sqlmodel import Session, select

from backend.agents.analyst_node import run_analyst
from backend.models import Signal
from backend.providers.price_provider import MockPriceProvider
from backend.services.radar import get_news
from backend.schemas import PriceComparison, SignalOut

_price_provider = MockPriceProvider()


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

    signal_data = run_analyst(news, price_comparison)
    signal = Signal(**signal_data)
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return _to_out(signal)


def list_signals(instrument: Optional[str], session: Session) -> list[SignalOut]:
    query = select(Signal)
    if instrument:
        query = query.where(Signal.instrument == instrument.upper())
    signals = session.exec(query.order_by(Signal.created_at.desc())).all()
    return [_to_out(s) for s in signals]


def get_signal(signal_id: str, session: Session) -> Optional[Signal]:
    return session.get(Signal, signal_id)


def review_signal(signal_id: str, status: str, justification: str, session: Session) -> Optional[SignalOut]:
    from datetime import datetime, timezone

    signal = session.get(Signal, signal_id)
    if signal is None:
        return None
    signal.review_status = status
    signal.review_justification = justification
    signal.reviewed_at = datetime.now(timezone.utc)
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return _to_out(signal)


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
    )
