"""Grafo de estados (LangGraph) que encadena los dos agentes del Track 5.

analyst_node -> advisor_node

El analyst_node tambien se invoca de forma independiente (via run_analyst,
en backend/services/signals.py) para HU2, sin pasar por el advisor. El grafo
completo se usa para armar el briefing end-to-end (HU3) en
backend/services/briefing.py.
"""
from typing import Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.agents.advisor_node import advisor_node
from backend.agents.analyst_node import analyst_node


class AgentState(TypedDict, total=False):
    news: dict
    price_comparison: dict
    signal: Optional[dict]
    briefing_item: Optional[dict]


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("analyst", analyst_node)
    builder.add_node("advisor", advisor_node)
    builder.add_edge(START, "analyst")
    builder.add_edge("analyst", "advisor")
    builder.add_edge("advisor", END)
    return builder.compile()


graph = build_graph()


def run_pipeline(news: dict, price_comparison: dict) -> AgentState:
    """Ejecuta analyst_node -> advisor_node end-to-end para un item de briefing."""
    return graph.invoke({"news": news, "price_comparison": price_comparison})
