"""Post-filtro determinista: ninguna accion sugerida puede ser una orden de compra/venta.

Los prompts ya lo prohiben, pero con un LLM real la regla tiene que ser codigo
verificable, no una instruccion al modelo. Regex de alta precision (verbos de
ejecucion y frases de orden) para no marcar usos descriptivos como "la compra
de bonos por el BCE".
"""
import re

_FORBIDDEN_TRADE_LANGUAGE = re.compile(
    r"\b(comprar|compra ya|compra ahora|vender|vende|buy|sell|shortear)\b"
    r"|orden de (compra|venta)"
    r"|ejecutar (la )?(orden|operacion)"
    r"|(abrir|cerrar|tomar) (una )?posicion",
    re.IGNORECASE,
)


def ensure_research_action(text: str, instrument: str) -> tuple[str, bool]:
    """Devuelve (accion_segura, fue_reemplazada).

    Si la accion contiene lenguaje de ejecucion de ordenes, se sustituye por
    una accion de revision humana en vez de publicarse.
    """
    if _FORBIDDEN_TRADE_LANGUAGE.search(text):
        return (
            f"Revisar manualmente este evento sobre {instrument} con un analista humano "
            "(la accion propuesta por el modelo fue descartada por contener lenguaje de "
            "ejecucion de ordenes).",
            True,
        )
    return text, False
