"""Post-filtro determinista: ninguna accion sugerida puede ser una orden de compra/venta.

Los prompts ya lo prohiben, pero con un LLM real la regla tiene que ser codigo
verificable, no una instruccion al modelo. El texto se normaliza (sin tildes,
minusculas) antes de matchear — un LLM real escribe "posición" u "operación" —
y el patron cubre conjugaciones de orden (compre, venda, adquiera) pero excluye
jerga descriptiva de mercado ("sell-off", "sell-side", "la compra de bonos").
"""
import re
import unicodedata

_FORBIDDEN_TRADE_LANGUAGE = re.compile(
    r"\b(comprar|compre(n)?|compra (ya|ahora)|vender|vende(n)?|venda(n)?"
    r"|adquirir|adquiera(n)?|liquidar|liquide(n)?|shortear)\b"
    r"|\bbuy\b(?![\s-]?(back|side))"
    r"|\bsell\b(?![\s-]?(off|side))"
    r"|orden de (compra|venta)"
    r"|ejecutar (la )?(orden|operacion)"
    r"|(abrir|cerrar|tomar) (una )?posicion"
)


def _normalize(text: str) -> str:
    """Minusculas y sin marcas diacriticas: 'Posición' -> 'posicion'."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def ensure_research_action(text: str, instrument: str) -> tuple[str, bool]:
    """Devuelve (accion_segura, fue_reemplazada).

    Si la accion contiene lenguaje de ejecucion de ordenes, se sustituye por
    una accion de revision humana en vez de publicarse.
    """
    if _FORBIDDEN_TRADE_LANGUAGE.search(_normalize(text)):
        return (
            f"Revisar manualmente este evento sobre {instrument} con un analista humano "
            "(la accion propuesta por el modelo fue descartada por contener lenguaje de "
            "ejecucion de ordenes).",
            True,
        )
    return text, False
