"""Triaje de senales (medicina de urgencias + severidad estilo CVSS).

Una sala de emergencias no atiende por orden de llegada: cada senal recibe un
nivel con SLA calculado por una REGLA LITERAL y reproducible (mismo patron que
MONITOR_RULE en backend/agents/graph.py). El nivel azul es exactamente la
arista condicional a monitoreo ($0 LLM), con nombre clinico.

Es un campo DERIVADO (se calcula al servir la senal): sin migracion de DB y
sin tocar la generacion. Cada regla vive dos veces — como predicado (el codigo
que decide) y como string literal (lo que el visor muestra) — y un test
verifica que coincidan caso por caso.
"""

# (nivel, prioridad para ordenar, SLA, regla literal, predicado). En orden.
TRIAGE_RULES = [
    (
        "azul", 4, "solo monitoreo — $0 LLM",
        "impact == 'neutral' and confidence < 0.5",
        lambda impact, confidence, change_pct: impact == "neutral" and confidence < 0.5,
    ),
    (
        "rojo", 0, "revisar en < 1h",
        "impact == 'negative' and confidence >= 0.75 and abs(change_pct) >= 3",
        lambda impact, confidence, change_pct: impact == "negative" and confidence >= 0.75 and abs(change_pct) >= 3,
    ),
    (
        "naranja", 1, "revisar en < 2h",
        "impact != 'neutral' and confidence >= 0.6 and abs(change_pct) >= 2",
        lambda impact, confidence, change_pct: impact != "neutral" and confidence >= 0.6 and abs(change_pct) >= 2,
    ),
    (
        "amarillo", 2, "revisar hoy (< 8h)",
        "confidence >= 0.5",
        lambda impact, confidence, change_pct: confidence >= 0.5,
    ),
    (
        "verde", 3, "revisar en < 24h",
        "resto",
        lambda impact, confidence, change_pct: True,
    ),
]


def compute_triage(impact: str, confidence: float, change_pct: float) -> dict:
    for level, priority, sla, rule, predicate in TRIAGE_RULES:
        if predicate(impact, confidence, change_pct):
            return {"level": level, "priority": priority, "sla": sla, "rule": rule}
    raise AssertionError("unreachable")  # pragma: no cover
