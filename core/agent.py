"""Núcleo de Cromic v2 con LangChain.

Decide si una solicitud se resuelve mediante una Chain determinista o
mediante un Agent con múltiples Tools.
"""

from typing import TypedDict

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from chains.response_chain import crear_respuesta_chain
from chains.router_chain import crear_router_chain
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from prompts.fashion_prompt import AGENT_SYSTEM_TEMPLATE
from tools.agenda_tool import consultar_agenda
from tools.codigo_vestimenta_tool import consultar_codigo_vestimenta
from tools.fecha_tool import obtener_fecha
from tools.paleta_tool import consultar_paleta_colores
from tools.ropa_tool import consultar_ropa, sugerir_outfit


class Perfil(TypedDict):
    nombre: str
    color_ojos: str
    color_piel: str


TOOLS = [
    obtener_fecha,
    consultar_ropa,
    consultar_agenda,
    consultar_paleta_colores,
    consultar_codigo_vestimenta,
    sugerir_outfit,
]


def _crear_modelo() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=0.1,
    )


def _construir_system_prompt(perfil: Perfil, memoria: str) -> str:
    return AGENT_SYSTEM_TEMPLATE.format(
        nombre=perfil["nombre"],
        color_ojos=perfil["color_ojos"],
        color_piel=perfil["color_piel"],
        memoria=memoria or "Sin memoria reciente.",
    )


def _extraer_texto_final(result: dict) -> str:
    """Extrae el contenido textual del último mensaje del Agent."""
    mensajes = result.get("messages", [])

    if not mensajes:
        return "No fue posible generar una respuesta."

    contenido = mensajes[-1].content

    if isinstance(contenido, str):
        return contenido

    if isinstance(contenido, list):
        partes = []
        for bloque in contenido:
            if isinstance(bloque, dict) and bloque.get("type") == "text":
                partes.append(str(bloque.get("text", "")))
            elif isinstance(bloque, str):
                partes.append(bloque)
        texto = "\n".join(p for p in partes if p).strip()
        return texto or "No fue posible generar una respuesta."

    return str(contenido)


def _detectar_tools_usadas(result: dict) -> list[str]:
    """Obtiene nombres de Tools solicitadas por el modelo."""
    usadas: list[str] = []

    for mensaje in result.get("messages", []):
        tool_calls = getattr(mensaje, "tool_calls", None) or []

        for call in tool_calls:
            nombre = call.get("name")
            if nombre and nombre not in usadas:
                usadas.append(nombre)

    return usadas


def responder(
    mensaje_usuario: str,
    perfil: Perfil,
    memoria: str,
) -> dict:
    """Responde mediante Chain o Agent según la naturaleza de la consulta."""
    router = crear_router_chain()
    decision = router.invoke({"pregunta": mensaje_usuario})

    if decision.ruta == "chain":
        chain = crear_respuesta_chain()
        texto = chain.invoke({"pregunta": mensaje_usuario})

        return {
            "respuesta": texto,
            "ruta": "Chain",
            "motivo": decision.motivo,
            "tools": [],
        }

    agent = create_agent(
        model=_crear_modelo(),
        tools=TOOLS,
        system_prompt=_construir_system_prompt(perfil=perfil, memoria=memoria),
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": mensaje_usuario}]}
    )

    return {
        "respuesta": _extraer_texto_final(result),
        "ruta": "Agent",
        "motivo": decision.motivo,
        "tools": _detectar_tools_usadas(result),
    }
