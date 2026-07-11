"""NewsProvider: interfaz para obtener noticias + implementacion Mock.

Cambiar a datos en vivo (NewsAPI/RSS) mas adelante solo requiere una nueva
clase que implemente el mismo protocolo, sin tocar routers/services.
"""
import json
from datetime import datetime, timezone
from typing import Optional, Protocol

from backend.config import DATA_DIR


class NewsProvider(Protocol):
    def list_news(
        self,
        instrument_type: Optional[str] = None,
        asset: Optional[str] = None,
        max_age_days: Optional[float] = None,
        sector: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> list[dict]: ...

    def get_news(self, news_id: str) -> Optional[dict]: ...


class MockNewsProvider:
    def __init__(self) -> None:
        with open(DATA_DIR / "mock_news.json", encoding="utf-8") as f:
            self._news = json.load(f)
        with open(DATA_DIR / "instruments.json", encoding="utf-8") as f:
            self._instruments_by_symbol = {i["symbol"]: i for i in json.load(f)}

    def list_news(
        self,
        instrument_type: Optional[str] = None,
        asset: Optional[str] = None,
        max_age_days: Optional[float] = None,
        sector: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> list[dict]:
        now = datetime.now(timezone.utc)
        results = []
        for item in self._news:
            published_at = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
            age_days = (now - published_at).total_seconds() / 86400

            if asset and asset.upper() not in item["instruments"]:
                continue
            if instrument_type:
                item_types = {
                    self._instruments_by_symbol[sym]["type"]
                    for sym in item["instruments"]
                    if sym in self._instruments_by_symbol
                }
                if instrument_type.lower() not in item_types:
                    continue
            if max_age_days is not None and age_days > max_age_days:
                continue
            if sector and item["sector"].lower() != sector.lower():
                continue
            if topic and topic.lower() not in item["topic"].lower():
                continue

            results.append({**item, "age_days": round(age_days, 2)})

        results.sort(key=lambda n: n["published_at"], reverse=True)
        return results

    def get_news(self, news_id: str) -> Optional[dict]:
        for item in self._news:
            if item["id"] == news_id:
                now = datetime.now(timezone.utc)
                published_at = datetime.fromisoformat(item["published_at"].replace("Z", "+00:00"))
                age_days = (now - published_at).total_seconds() / 86400
                return {**item, "age_days": round(age_days, 2)}
        return None
