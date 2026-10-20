"""Topología del grafo de Cromic."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    agente_cromic_node,
    conceptual_node,
    enrutador_node,
    herramientas_node,
)
from graph.state import CromicState


def _decidir_ruta(state: CromicState) -> str:
    return "conceptual" if state.get("ruta") == "conceptual" else "herramientas"


def _evaluar_tools(state: CromicState) -> str:
    ultimo = state["messages"][-1]
    if getattr(ultimo, "tool_calls", None):
        return "herramientas"
    return "fin"


def crear_grafo_cromic():
    builder = StateGraph(CromicState)

    builder.add_node("enrutador", enrutador_node)
    builder.add_node("nodo_conceptual", conceptual_node)
    builder.add_node("agente_cromic", agente_cromic_node)
    builder.add_node("herramientas", herramientas_node)

    builder.add_edge(START, "enrutador")

    builder.add_conditional_edges(
        "enrutador",
        _decidir_ruta,
        {"conceptual": "nodo_conceptual", "herramientas": "agente_cromic"},
    )

    builder.add_conditional_edges(
        "agente_cromic",
        _evaluar_tools,
        {"herramientas": "herramientas", "fin": END},
    )

    # Bucle cíclico ReAct
    builder.add_edge("herramientas", "agente_cromic")
    builder.add_edge("nodo_conceptual", END)

    return builder.compile(checkpointer=MemorySaver())