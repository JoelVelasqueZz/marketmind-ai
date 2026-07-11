import json
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

from backend.agents.graph import run_pipeline
from backend.config import DATA_DIR, DISCLAIMER
from backend.models import Signal, TaskAlert
from backend.providers.price_provider import MockPriceProvider
from backend.schemas import BriefingItemOut, BriefingOut, PriceComparison, SignalOut
from backend.services.radar import _news_provider

_price_provider = MockPriceProvider()

with open(DATA_DIR / "watchlists.json", encoding="utf-8") as f:
    _watchlists = {w["id"]: w for w in json.load(f)}


class WatchlistNotFound(Exception):
    pass


def _latest_news_for_instrument(instrument: str) -> Optional[dict]:
    matches = _news_provider.list_news(asset=instrument)
    return matches[0] if matches else None


def generate_briefing(watchlist_id: str, session: Session) -> BriefingOut:
    watchlist = _watchlists.get(watchlist_id)
    if watchlist is None:
        raise WatchlistNotFound(f"No existe la watchlist {watchlist_id}")

    items: list[BriefingItemOut] = []
    for instrument in watchlist["instruments"]:
        news = _latest_news_for_instrument(instrument)
        if news is None:
            continue

        price_comparison = _price_provider.compare_around_date(instrument, news["published_at"]) or {
            "instrument": instrument.upper(),
            "change_pct": 0.0,
            "window_days": 2,
            "note": f"No hay historico de precio disponible para {instrument.upper()}.",
        }

        result = run_pipeline(news, price_comparison)
        signal_data = result["signal"]
        briefing_item_data = result["briefing_item"]

        signal = Signal(**signal_data)
        session.add(signal)
        session.commit()
        session.refresh(signal)

        session.add(
            TaskAlert(
                signal_id=signal.id,
                instrument=instrument.upper(),
                title=briefing_item_data["research_action"],
                description=f"Generado a partir de: {news['headline']}",
            )
        )
        session.commit()

        items.append(
            BriefingItemOut(
                instrument=instrument.upper(),
                signal=SignalOut(
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
                ),
                news_headline=briefing_item_data["news_headline"],
                price_change_pct=briefing_item_data["price_change_pct"],
                research_action=briefing_item_data["research_action"],
                executive_summary=briefing_item_data["executive_summary"],
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
    return list(_watchlists.values())
