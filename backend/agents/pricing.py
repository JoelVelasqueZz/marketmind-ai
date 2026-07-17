"""Tarifas publicas de los proveedores LLM (Taximetro de la Caja de Cristal).

USD por 1 MILLON de tokens, tarifas publicas a jul-2026 — referenciales, no
contractuales. El costo por senal se calcula con los tokens REPORTADOS por el
proveedor (usage de la respuesta); en modo mock los tokens son estimados
(len/4) y el costo es $0, etiquetado measured=False.
"""

PRICES_PER_MTOK = {
    # (proveedor, prefijo de modelo) -> (usd_in, usd_out)
    # gemini-flash-latest apunta al Flash mas reciente (2.5+): $0.30/$2.50.
    ("gemini", "gemini"): (0.30, 2.50),
    # claude-sonnet-5 lista $3/$15 (precio introductorio $2/$10 hasta ago-2026).
    ("claude", "claude"): (3.00, 15.00),
    # deepseek-chat V3.2 tras el recorte de sept-2025.
    ("deepseek", "deepseek"): (0.28, 0.42),
    ("mock", ""): (0.0, 0.0),
}

PRICES_AS_OF = "jul-2026"


def estimate_cost_usd(provider: str, model: str, tokens_in: int, tokens_out: int) -> float:
    """Costo en USD segun la tabla; proveedor desconocido -> 0.0 (honesto: no inventar)."""
    for (prov, prefix), (usd_in, usd_out) in PRICES_PER_MTOK.items():
        if provider == prov and (not prefix or model.startswith(prefix) or prefix in model):
            return round((tokens_in * usd_in + tokens_out * usd_out) / 1_000_000, 6)
    return 0.0


def usage_fields(client) -> dict:
    """Campos del taximetro para el evento llm_call de la traza.

    Lee la telemetria del ultimo generate_structured del cliente; con un LLM
    fake de tests (sin _last_usage) devuelve {} y el evento queda como antes.
    """
    usage = getattr(client, "_last_usage", None)
    if not usage:
        return {}
    cost = estimate_cost_usd(
        getattr(client, "mode", ""), getattr(client, "model", ""),
        usage["tokens_in"], usage["tokens_out"],
    )
    return {
        "tokens_in": usage["tokens_in"],
        "tokens_out": usage["tokens_out"],
        "cost_usd": cost,
        "measured": usage["measured"],
    }
