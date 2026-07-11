from typing import Optional

from backend.providers.news_provider import MockNewsProvider
from backend.schemas import NewsOut

_news_provider = MockNewsProvider()


def list_news(
    instrument_type: Optional[str] = None,
    asset: Optional[str] = None,
    max_age_days: Optional[float] = None,
    sector: Optional[str] = None,
    topic: Optional[str] = None,
    q: Optional[str] = None,
) -> list[NewsOut]:
    raw = _news_provider.list_news(
        instrument_type=instrument_type,
        asset=asset,
        max_age_days=max_age_days,
        sector=sector,
        topic=topic,
        q=q,
    )
    return [NewsOut(**item) for item in raw]


def get_news(news_id: str) -> Optional[dict]:
    return _news_provider.get_news(news_id)
