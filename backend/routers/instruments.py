import json

from fastapi import APIRouter

from backend.config import DATA_DIR
from backend.schemas import InstrumentOut

router = APIRouter(prefix="/api/instruments", tags=["instruments"])

with open(DATA_DIR / "instruments.json", encoding="utf-8") as f:
    _instruments = json.load(f)


@router.get("", response_model=list[InstrumentOut])
def get_instruments():
    return _instruments
