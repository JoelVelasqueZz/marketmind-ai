from typing import Optional

from fastapi import APIRouter, Query

from backend.schemas import NewsOut
from backend.services import radar

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("", response_model=list[NewsOut])
def get_news(
    type: Optional[str] = Query(default=None, description="equity | credit | crypto | other"),
    asset: Optional[str] = Query(default=None, description="Simbolo del instrumento, ej. AAPL"),
    max_age_days: Optional[float] = Query(default=None, ge=0),
    sector: Optional[str] = Query(default=None),
    topic: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None, description="Busqueda libre en titulo/resumen/fuente/instrumentos"),
):
    return radar.list_news(
        instrument_type=type,
        asset=asset,
        max_age_days=max_age_days,
        sector=sector,
        topic=topic,
        q=q,
    )
