import json
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from backend.agents.advisor_node import run_advisor
from backend.agents.graph import (
    build_monitor_item,
    record_edge_decision,
    run_pipeline,
    should_route_to_monitor,
)
from backend.agents.trace import TraceRecorder
from backend.config import DATA_DIR, DISCLAIMER, LLM_MODE, LLM_MODEL
from backend.models import Signal, TaskAlert
from backend.providers.price_provider import MockPriceProvider
from backend.schemas import (
    AssetOverview,
    AssetSignalSummary,
    BriefingItemOut,
    BriefingOut,
    PriceComparison,
    SignalOut,
    WatchlistOverviewOut,
)
from backend.services import signals as signals_service
from backend.services.radar import _news_provider

_price_provider = MockPriceProvider()

with open(DATA_DIR / "watchlists.json", encoding="utf-8") as f:
    _watchlists = {w["id"]: w for w in json.load(f)}

with open(DATA_DIR / "instruments.json", encoding="utf-8") as f:
    _instruments_by_symbol = {i["symbol"]: i for i in json.load(f)}

ALL_WATCHLIST_ID = "all"
_ALL_WATCHLIST = {
    "id": ALL_WATCHLIST_ID,
    "name": "Todos los instrumentos",
    "instruments": list(_instruments_by_symbol.keys()),
}


class WatchlistNotFound(Exception):
    pass


def _latest_news_for_instrument(instrument: str) -> Optional[dict]:
    matches = _news_provider.list_news(asset=instrument)
    return matches[0] if matches else None


def _latest_task_for_signal(signal_id: str, session: Session) -> Optional[TaskAlert]:
    query = select(TaskAlert).where(TaskAlert.signal_id == signal_id).order_by(TaskAlert.created_at.desc())
    return session.exec(query).first()


def _signal_out(signal: Signal) -> SignalOut:
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
        has_trace=bool(signal.execution_trace),
        has_attribution=bool(signal.attribution),
    )


def generate_briefing(watchlist_id: str, session: Session, force: bool = False) -> BriefingOut:
    watchlist = _ALL_WATCHLIST if watchlist_id == ALL_WATCHLIST_ID else _watchlists.get(watchlist_id)
    if watchlist is None:
        raise WatchlistNotFound(f"No existe la watchlist {watchlist_id}")

    items: list[BriefingItemOut] = []
    for instrument in watchlist["instruments"]:
        news = _latest_news_for_instrument(instrument)
        if news is None:
            continue

        existing_signal = None if force else signals_service.find_existing_signal(news["id"], instrument, session)

        if existing_signal is not None:
            signal = existing_signal
            existing_task = _latest_task_for_signal(signal.id, session)
            if existing_task is not None:
                # Ya existe un analisis Y una tarea para este par (noticia, instrumento):
                # reusar sin volver a llamar al LLM (ahorra cuota, evita duplicados).
                # El resumen del Asesor viene persistido en la tarea; tareas
                # anteriores a esa columna caen a la evidencia del Analista.
                research_action = existing_task.title
                executive_summary = existing_task.executive_summary or signal.evidence
            else:
                # Hay senal pero nunca se armo un briefing con ella: aplica el
                # mismo ruteo que el grafo (neutral de baja confianza no gasta
                # la llamada del Asesor). Esta corrida SI puede llamar al LLM,
                # asi que anexa su propio run a la traza de la senal
                # (scope=signal-only; el reuso total no escribe traza).
                recorder = TraceRecorder(llm_mode=LLM_MODE, model=LLM_MODEL, path="briefing-reuse")
                recorder.event("reuse", signal_id=signal.id, scope="signal-only")
                signal_data = {
                    "instrument": signal.instrument,
                    "impact": signal.impact,
                    "confidence": signal.confidence,
                    "evidence": signal.evidence,
                    "price_comparison": signal.price_comparison,
                }
                to_monitor = should_route_to_monitor(signal.impact, signal.confidence)
                record_edge_decision(
                    recorder, signal.impact, signal.confidence,
                    "monitor" if to_monitor else "advisor",
                )
                if to_monitor:
                    recorder.event("node_start", node="monitor")
                    advisor_result = build_monitor_item(signal_data, news)
                    recorder.event(
                        "node_end",
                        node="monitor",
                        duration_ms=0,
                        output_digest={"research_action": advisor_result["research_action"][:80]},
                    )
                else:
                    advisor_result = run_advisor(signal_data, news, trace=recorder)
                research_action = advisor_result["research_action"]
                executive_summary = advisor_result["executive_summary"]
                signal.execution_trace = TraceRecorder.merge(
                    signal.execution_trace, recorder.to_json()
                )
                session.add(signal)
                session.add(
                    TaskAlert(
                        signal_id=signal.id,
                        instrument=instrument.upper(),
                        title=research_action,
                        description=f"Generado a partir de: {news['headline']}",
                        executive_summary=executive_summary,
                    )
                )
                session.commit()
                session.refresh(signal)
            price_change_pct = signal.price_comparison["change_pct"]
        else:
            price_comparison = _price_provider.compare_around_date(instrument, news["published_at"]) or {
                "instrument": instrument.upper(),
                "change_pct": 0.0,
                "window_days": 2,
                "note": f"No hay historico de precio disponible para {instrument.upper()}.",
            }

            review_examples = signals_service.list_review_examples(instrument, session)
            recorder = TraceRecorder(llm_mode=LLM_MODE, model=LLM_MODEL, path="briefing")
            result = run_pipeline(
                news, price_comparison, review_examples=review_examples, trace=recorder
            )
            signal_data = result["signal"]
            briefing_item_data = result["briefing_item"]

            signal = Signal(**signal_data)
            signal.execution_trace = recorder.to_json()
            session.add(signal)
            session.commit()
            session.refresh(signal)

            session.add(
                TaskAlert(
                    signal_id=signal.id,
                    instrument=instrument.upper(),
                    title=briefing_item_data["research_action"],
                    description=f"Generado a partir de: {news['headline']}",
                    executive_summary=briefing_item_data["executive_summary"],
                )
            )
            session.commit()

            research_action = briefing_item_data["research_action"]
            executive_summary = briefing_item_data["executive_summary"]
            price_change_pct = briefing_item_data["price_change_pct"]

        items.append(
            BriefingItemOut(
                instrument=instrument.upper(),
                signal=_signal_out(signal),
                news_headline=news["headline"],
                price_change_pct=price_change_pct,
                research_action=research_action,
                executive_summary=executive_summary,
            )
        )

    return BriefingOut(
        watchlist_id=watchlist["id"],
        watchlist_name=watchlist["name"],
        generated_at=datetime.now(timezone.utc),
        items=items,
        disclaimer=DISCLAIMER,
    )


def list_watchlists() -> list[dict]:
    return [_ALL_WATCHLIST, *_watchlists.values()]


def get_watchlist_overview(watchlist_id: str, session: Session) -> WatchlistOverviewOut:
    watchlist = _ALL_WATCHLIST if watchlist_id == ALL_WATCHLIST_ID else _watchlists.get(watchlist_id)
    if watchlist is None:
        raise WatchlistNotFound(f"No existe la watchlist {watchlist_id}")

    assets: list[AssetOverview] = []
    for symbol in watchlist["instruments"]:
        instrument = _instruments_by_symbol.get(symbol)
        if instrument is None:
            continue

        history = _price_provider.get_history(symbol)
        price = history[-1]["close"] if history else None
        change_pct_1d = None
        if len(history) >= 2:
            prev_close = history[-2]["close"]
            change_pct_1d = round((history[-1]["close"] - prev_close) / prev_close * 100, 2)

        latest_signal = session.exec(
            select(Signal).where(Signal.instrument == symbol).order_by(Signal.created_at.desc())
        ).first()

        assets.append(
            AssetOverview(
                symbol=symbol,
                name=instrument["name"],
                type=instrument["type"],
                price=price,
                change_pct_1d=change_pct_1d,
                signal=(
                    None
                    if latest_signal is None
                    else AssetSignalSummary(
                        impact=latest_signal.impact,
                        confidence=latest_signal.confidence,
                        created_at=latest_signal.created_at,
                    )
                ),
            )
        )

    return WatchlistOverviewOut(
        watchlist_id=watchlist["id"], watchlist_name=watchlist["name"], assets=assets
    )
