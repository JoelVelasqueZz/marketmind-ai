"""Compliance Gate 360: verificacion determinista antes de publicar una senal.

El guardrail (guardrails.py) ya sanea el lenguaje de ordenes; este gate ataca
la otra mitad — que las CIFRAS que el modelo cita en la evidencia coincidan
con el dato real del dataset (grounding numerico), que las fuentes citadas
sean las reales, y que la estructura cumpla el contrato. Todo 100% determinista
(regex + comparacion), sin LLM: la parte critica de la antialucinacion es
codigo verificable y testeable, no una instruccion al modelo.

run_compliance_checks devuelve una lista de checks {item, passed, detail, rule};
run_analyst reinyecta las violaciones al prompt del Analista (loop de
auto-correccion, contador acotado) o marca la senal si persisten.
"""
import re

# Tolerancia al comparar un % citado contra el movimiento real (permite el
# redondeo a 1-2 decimales de un LLM: "2.4%" vs 2.35%).
PCT_TOLERANCE = 0.15

_PCT_RE = re.compile(r"([-+]?\d+(?:[.,]\d+)?)\s*%")
# Un % precedido por lenguaje de confianza/probabilidad NO es una cifra de
# movimiento de precio — no se ancla contra change_pct.
_CONFIDENCE_CTX = re.compile(r"(confian|confidence|probabil|certeza|nivel)", re.IGNORECASE)


def _cited_move_pcts(evidence: list[str]) -> list[float]:
    pcts: list[float] = []
    for text in evidence:
        for match in _PCT_RE.finditer(text):
            context = text[max(0, match.start() - 25) : match.start()]
            if _CONFIDENCE_CTX.search(context):
                continue
            pcts.append(float(match.group(1).replace(",", ".")))
    return pcts


def _check_numeric_grounding(evidence: list[str], change_pct: float) -> dict:
    cited = _cited_move_pcts(evidence)
    mismatched = [p for p in cited if abs(abs(p) - abs(change_pct)) > PCT_TOLERANCE]
    if mismatched:
        detail = (
            f"Cifras de movimiento citadas que no coinciden con el dato real "
            f"({change_pct:+.2f}%): {', '.join(f'{p:+.2f}%' for p in mismatched)}."
        )
        return {"item": "cifras_ancladas_al_dato", "passed": False, "detail": detail}
    ok_detail = (
        f"Las {len(cited)} cifra(s) de movimiento citadas coinciden con el dato real "
        f"({change_pct:+.2f}%)."
        if cited
        else "La evidencia no cita cifras de movimiento a verificar."
    )
    return {"item": "cifras_ancladas_al_dato", "passed": True, "detail": ok_detail}


def run_compliance_checks(signal_data: dict, news: dict) -> list[dict]:
    """Checks deterministas de despacho. Cada uno lleva su regla literal."""
    evidence = signal_data.get("evidence", [])
    change_pct = signal_data["price_comparison"]["change_pct"]
    sources = signal_data.get("sources", [])
    action = signal_data.get("suggested_action") or ""

    checks: list[dict] = [
        {
            "item": "impacto_en_taxonomia",
            "rule": "impact ∈ {positive, negative, neutral, uncertain}",
            "passed": signal_data["impact"] in {"positive", "negative", "neutral", "uncertain"},
            "detail": f"impacto = {signal_data['impact']}",
        },
        {
            "item": "confianza_en_rango",
            "rule": "0 ≤ confidence ≤ 1",
            "passed": 0.0 <= signal_data["confidence"] <= 1.0,
            "detail": f"confianza = {signal_data['confidence']}",
        },
        {
            "item": "evidencia_suficiente",
            "rule": "2 ≤ len(evidence) ≤ 4",
            "passed": 2 <= len(evidence) <= 4,
            "detail": f"{len(evidence)} puntos de evidencia",
        },
        {
            "item": "fuente_verificada",
            "rule": "sources ⊆ {fuente de la noticia}",
            "passed": set(sources) <= {news["source"]},
            "detail": f"fuentes = {sources}",
        },
        {
            "item": "accion_no_es_orden",
            "rule": "suggested_action nunca ejecuta compra/venta",
            "passed": "descartada por contener lenguaje de ejecucion" not in action.lower()
            and bool(action),
            "detail": "accion de investigacion/revision humana",
        },
    ]
    checks.insert(3, _check_numeric_grounding(evidence, change_pct))
    # Regla del grounding numerico (para el visor).
    checks[3]["rule"] = f"cada % de movimiento citado ≈ {change_pct:+.2f}% (±{PCT_TOLERANCE})"
    return checks


def violations_prompt(failed_checks: list[dict]) -> str:
    """Bloque que se reinyecta al Analista para que corrija en el reintento."""
    lines = "\n".join(f"- {c['item']}: {c['detail']}" for c in failed_checks)
    return (
        "Tu respuesta anterior fue RECHAZADA por el control de cumplimiento por estas "
        "violaciones. Corrigelas: cita SOLO cifras que esten en el contexto, no inventes "
        "porcentajes de movimiento.\n"
        + lines
        + "\n\n"
    )
