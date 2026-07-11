"""PriceProvider: interfaz para obtener historico de precios + implementacion Mock.

Cambiar a datos en vivo (yfinance/CoinGecko) mas adelante solo requiere una
nueva clase que implemente el mismo protocolo, sin tocar routers/services.
"""
import json
from typing import Optional, Protocol

from backend.config import DATA_DIR


class PriceProvider(Protocol):
    def get_history(self, symbol: str) -> list[dict]: ...

    def compare_around_date(self, symbol: str, date_str: str, window_days: int = 2) -> Optional[dict]: ...


class MockPriceProvider:
    def __init__(self) -> None:
        with open(DATA_DIR / "mock_prices.json", encoding="utf-8") as f:
            self._prices: dict[str, list[dict]] = json.load(f)

    def get_history(self, symbol: str) -> list[dict]:
        return self._prices.get(symbol.upper(), [])

    def compare_around_date(self, symbol: str, date_str: str, window_days: int = 2) -> Optional[dict]:
        """Compara el precio de cierre antes/despues de una fecha (evento de noticia)."""
        history = self.get_history(symbol)
        if not history:
            return None

        target_date = date_str[:10]
        dates = [p["date"] for p in history]
        if target_date not in dates:
            # usar la fecha mas cercana disponible
            target_date = min(dates, key=lambda d: abs((_to_ord(d) - _to_ord(target_date))))

        idx = dates.index(target_date)
        before_idx = max(0, idx - window_days)
        after_idx = min(len(history) - 1, idx + window_days)

        before_price = history[before_idx]["close"]
        after_price = history[after_idx]["close"]
        change_pct = round((after_price - before_price) / before_price * 100, 2)

        return {
            "instrument": symbol.upper(),
            "change_pct": change_pct,
            "window_days": window_days,
            "note": (
                f"{symbol.upper()} paso de {before_price} a {after_price} "
                f"({'+' if change_pct >= 0 else ''}{change_pct}%) en una ventana de "
                f"{window_days} dias alrededor de {target_date}."
            ),
        }


def _to_ord(date_str: str) -> int:
    from datetime import date

    y, m, d = (int(x) for x in date_str.split("-"))
    return date(y, m, d).toordinal()
