"""Nodos del grafo de Cromic (LangGraph)."""

from typing import Literal

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from graph.state import CromicState
from prompts.fashion_prompt import (
    AGENT_SYSTEM_TEMPLATE,
    GENERAL_SYSTEM_PROMPT,
    ROUTER_SYSTEM_PROMPT,
)
from tools import TOOLS_CROMIC


class RutaConsulta(BaseModel):
    """Ruta seleccionada para atender la solicitud."""

    ruta: Literal["conceptual", "herramientas"] = Field(
        description="'conceptual' para consultas generales sin Tools y "
        "'herramientas' cuando se requieren datos del usuario o Tools."
    )
    motivo: str = Field(description="Justificación breve de la selección.")


def _crear_modelo(temperatura: float) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=temperatura,
    )


_modelo_router = _crear_modelo(0).with_structured_output(RutaConsulta)
_modelo_conceptual = _crear_modelo(0.3)
_modelo_agente = _crear_modelo(0.1).bind_tools(TOOLS_CROMIC)
_ejecutor_tools = ToolNode(TOOLS_CROMIC)


def _traza(state: CromicState, nodo: str) -> list[str]:
    return state.get("pasos_ejecutados", []) + [nodo]


# Nodo 1: clasificador estructurado
def enrutador_node(state: CromicState) -> dict:
    decision = _modelo_router.invoke(
        [SystemMessage(content=ROUTER_SYSTEM_PROMPT), state["messages"][-1]]
    )
    return {
        "ruta": decision.ruta,
        "motivo": decision.motivo,
        "pasos_ejecutados": _traza(state, "enrutador"),
    }


# Nodo 2: respuesta general sin herramientas
def conceptual_node(state: CromicState) -> dict:
    respuesta = _modelo_conceptual.invoke(
        [SystemMessage(content=GENERAL_SYSTEM_PROMPT), *state["messages"]]
    )
    return {
        "messages": [respuesta],
        "pasos_ejecutados": _traza(state, "nodo_conceptual"),
    }


# Nodo 3: razonamiento con herramientas vinculadas
def agente_cromic_node(state: CromicState) -> dict:
    usuario = state["usuario"]
    prompt = AGENT_SYSTEM_TEMPLATE.format(
        nombre=usuario["nombre"],
        color_ojos=usuario["color_ojos"],
        color_piel=usuario["color_piel"],
    )
    respuesta = _modelo_agente.invoke(
        [SystemMessage(content=prompt), *state["messages"]]
    )
    return {
        "messages": [respuesta],
        "pasos_ejecutados": _traza(state, "agente_cromic"),
    }


# Nodo 4: ejecución de herramientas con ToolNode
def herramientas_node(state: CromicState) -> dict:
    resultado = _ejecutor_tools.invoke(state)

    usadas = list(state.get("herramientas_usadas", []))
    for msg in resultado["messages"]:
        if isinstance(msg, ToolMessage) and msg.name and msg.name not in usadas:
            usadas.append(msg.name)

    return {
        "messages": resultado["messages"],
        "herramientas_usadas": usadas,
        "pasos_ejecutados": _traza(state, "herramientas"),
    }