"""Grafo de estados (LangGraph) que orquesta los dos agentes del Track 5.

analyst_node -> (ruteo condicional) -> advisor_node | monitor_node

El analyst_node tambien se invoca de forma independiente (via run_analyst,
en backend/services/signals.py) para HU2, sin pasar por el advisor. El grafo
completo se usa para armar el briefing end-to-end (HU3) en
backend/services/briefing.py.

Ruteo condicional: una senal neutral con confianza < 0.5 no tiene nada
accionable que un Asesor pueda convertir en tarea de investigacion — el grafo
la deriva a monitor_node, que arma un item de monitoreo determinista sin
gastar una llamada extra al LLM. Cualquier otra senal sigue al advisor_node.
"""
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.agents.advisor_node import advisor_node
from backend.agents.analyst_node import analyst_node
from backend.agents.llm import LLMClient
from backend.agents.trace import TraceRecorder

MONITOR_CONFIDENCE_THRESHOLD = 0.5

# Regla de la arista como string literal: la traza la registra tal cual para
# que el visor muestre la condicion exacta que se evaluo (no una parafrasis).
MONITOR_RULE = "impact == 'neutral' and confidence < 0.5"


class AgentState(TypedDict, total=False):
    news: dict
    price_comparison: dict
    llm: Optional[LLMClient]
    review_examples: Optional[list]
    trace: Optional[TraceRecorder]
    signal: Optional[dict]
    briefing_item: Optional[dict]


def should_route_to_monitor(impact: str, confidence: float) -> bool:
    """Una senal neutral de baja confianza no amerita gastar la llamada del Asesor."""
    return impact == "neutral" and confidence < MONITOR_CONFIDENCE_THRESHOLD


def build_monitor_item(signal: dict, news: dict) -> dict:
    """Item de briefing determinista (sin LLM) para senales derivadas a monitoreo.

    Tambien lo usa backend/services/briefing.py cuando reutiliza una senal ya
    persistida, para que el criterio de ruteo sea el mismo en ambos caminos.
    """
    instrument = signal["instrument"]
    return {
        "instrument": instrument,
        "news_headline": news["headline"],
        "price_change_pct": signal["price_comparison"]["change_pct"],
        "research_action": (
            f"Mantener {instrument} en monitoreo: senal neutral de baja confianza, "
            "sin accion de investigacion inmediata."
        ),
        "executive_summary": [
            news["headline"],
            (
                f"Senal del Analista: neutral (confianza {round(signal['confidence'] * 100)}%) — "
                "por debajo del umbral para escalar al Asesor."
            ),
        ],
    }


def record_edge_decision(trace, impact: str, confidence: float, target: str) -> None:
    """Evento edge_decision con la regla literal y sus valores.

    Compartido entre el grafo (route_after_analyst) y la rama de reuso del
    briefing, que aplica el mismo criterio fuera del grafo.
    """
    if trace is None:
        return
    trace.event(
        "edge_decision",
        edge="route_after_analyst",
        rule=MONITOR_RULE,
        inputs={"impact": impact, "confidence": confidence},
        threshold=MONITOR_CONFIDENCE_THRESHOLD,
        target=target,
        llm_cost="$0 (sin llamada LLM)" if target == "monitor" else "1 llamada LLM (Asesor)",
    )


def route_after_analyst(state: AgentState) -> str:
    """Decide si la senal del Analista amerita al Asesor o solo monitoreo."""
    signal = state["signal"]
    target = "monitor" if should_route_to_monitor(signal["impact"], signal["confidence"]) else "advisor"
    # El evento nace donde se decide: single source of truth del ruteo.
    record_edge_decision(state.get("trace"), signal["impact"], signal["confidence"], target)
    return target


def monitor_node(state: AgentState) -> dict:
    """Genera una tarea de monitoreo (no de investigacion) sin llamar al LLM."""
    trace = state.get("trace")
    if trace is not None:
        trace.event("node_start", node="monitor")
    item = build_monitor_item(state["signal"], state["news"])
    if trace is not None:
        trace.event(
            "node_end",
            node="monitor",
            duration_ms=0,
            output_digest={"research_action": item["research_action"][:80]},
        )
    return {"briefing_item": item}


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("analyst", analyst_node)
    builder.add_node("advisor", advisor_node)
    builder.add_node("monitor", monitor_node)
    builder.add_edge(START, "analyst")
    builder.add_conditional_edges(
        "analyst", route_after_analyst, {"advisor": "advisor", "monitor": "monitor"}
    )
    builder.add_edge("advisor", END)
    builder.add_edge("monitor", END)
    return builder.compile()


graph = build_graph()


def run_pipeline(
    news: dict,
    price_comparison: dict,
    llm: LLMClient | None = None,
    review_examples: list | None = None,
    trace: TraceRecorder | None = None,
) -> AgentState:
    """Ejecuta analyst_node -> (advisor|monitor) end-to-end para un item de briefing.

    llm permite inyectar un cliente fake en tests para controlar la senal del
    Analista y verificar el ruteo; en produccion queda None y cada nodo crea
    su LLMClient segun LLM_MODE. review_examples son revisiones humanas
    pasadas del mismo instrumento, reinyectadas como few-shot (HU3).
    trace registra la ejecucion completa para la Caja de Cristal: viaja por
    referencia en el estado del grafo hasta los nodos y la arista condicional.
    """
    return graph.invoke(
        {
            "news": news,
            "price_comparison": price_comparison,
            "llm": llm,
            "review_examples": review_examples,
            "trace": trace,
        }
    )
