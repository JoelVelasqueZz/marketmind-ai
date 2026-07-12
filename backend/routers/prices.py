from fastapi import APIRouter, Query

from backend.providers.price_provider import MockPriceProvider
from backend.schemas import PricePoint

router = APIRouter(prefix="/api/prices", tags=["prices"])

_price_provider = MockPriceProvider()


@router.get("/{symbol}", response_model=list[PricePoint])
def get_price_history(symbol: str, days: int = Query(default=14, ge=1, le=90)):
    history = _price_provider.get_history(symbol)
    return history[-days:] if history else []
