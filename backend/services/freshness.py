"""Vigencia: cada senal declara su propia caducidad.

Decaimiento exponencial por vida media segun la clase del instrumento (cripto
decae en dias; un soberano como ECU2035, en semanas). Las vidas medias son
PARAMETROS DE PRODUCTO por clase de activo — configurables, no una verdad
estadistica: la honestidad de declararlo es parte del feature.

Campo derivado (se calcula al servir la senal): sin migracion de DB.
"""
import json
from datetime import datetime, timezone
from typing import Optional

from backend.config import DATA_DIR

# Vida media en dias por tipo de instrumento (override por simbolo via
# data/instruments.json campo "half_life_days" si existe).
HALF_LIFE_DAYS_BY_TYPE = {"crypto": 2.0, "equity": 5.0, "credit": 10.0, "other": 3.0}
STALE_THRESHOLD = 0.5  # vigencia < 50% (mas vieja que su vida media) = re-evaluar

FRESHNESS_RULE = "vigencia = 0.5 ** (edad_dias / vida_media_del_tipo); re-evaluar si < 0.5"

with open(DATA_DIR / "instruments.json", encoding="utf-8") as f:
    _instruments_by_symbol = {i["symbol"]: i for i in json.load(f)}


def _half_life_days(instrument: str) -> float:
    info = _instruments_by_symbol.get(instrument.upper(), {})
    if "half_life_days" in info:
        return float(info["half_life_days"])
    return HALF_LIFE_DAYS_BY_TYPE.get(info.get("type", "other"), HALF_LIFE_DAYS_BY_TYPE["other"])


def compute_freshness(
    created_at: datetime, instrument: str, now: Optional[datetime] = None
) -> dict:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    age_days = max(0.0, (now - created_at).total_seconds() / 86400)
    half_life = _half_life_days(instrument)
    pct = round(0.5 ** (age_days / half_life), 2)
    return {
        "pct": pct,
        "age_days": round(age_days, 2),
        "half_life_days": half_life,
        "stale": pct < STALE_THRESHOLD,
        "rule": FRESHNESS_RULE,
    }
