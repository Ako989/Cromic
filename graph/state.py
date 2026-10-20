from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class UsuarioInfo(TypedDict):
    nombre: str
    color_ojos: str
    color_piel: str


class CromicState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    usuario: UsuarioInfo
    ruta: str
    motivo: str
    herramientas_usadas: list[str]
    pasos_ejecutados: list[str]