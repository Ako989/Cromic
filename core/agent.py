"""Núcleo de Cromic con LangChain: un Agent con múltiples Tools."""

from typing import TypedDict

from langchain.agents import create_agent
from langchain_core.tools import StructuredTool
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from prompts.colorimetria_prompt import COLORIMETRIA_REGLAS
from tools.colorimetria_tool import (
    consultar_paleta_estacional,
    diagnosticar_estacion,
)
from tools.ropa_tool import consultar_ropa


class Perfil(TypedDict):
    nombre: str
    color_ojos: str
    color_piel: str


# Envoltura temporal: cuando tu compañero ponga @tool en consultar_ropa,
# se elimina esta parte y se usa consultar_ropa directo en TOOLS.
consultar_ropa_tool = StructuredTool.from_function(
    func=consultar_ropa,
    name="consultar_ropa",
    description=(
        "Consulta las prendas del armario del usuario por nombre de prenda, "
        "tipo o color. Sin consulta devuelve todas."
    ),
)

TOOLS = [
    consultar_ropa_tool,
    diagnosticar_estacion,
    consultar_paleta_estacional,
]


def construir_contexto(perfil: Perfil, memoria: str) -> str:
    return f"""
Eres el asistente de Cromic, una guía de vestimenta y colorimetría.

PERFIL ACTUAL DEL USUARIO:
Nombre: {perfil["nombre"]}
Color de ojos: {perfil["color_ojos"]}
Color de piel: {perfil["color_piel"]}

MEMORIA RECIENTE:
{memoria or "Sin memoria reciente."}

HERRAMIENTAS:
- consultar_ropa: cuando pregunten por su ropa, prendas o armario.
- diagnosticar_estacion y consultar_paleta_estacional: para colorimetría.

{COLORIMETRIA_REGLAS}

El perfil es aproximado: solo guarda la primera palabra que el usuario
escribió (por ejemplo "azul" en vez de "azul claro"). Para diagnosticar,
usa el detalle completo que aparezca en el mensaje actual o en la MEMORIA
RECIENTE, y usa el perfil solo si no hay más información. Si un dato
aparece como "No registrado", trátalo como faltante.
Si la herramienta indica que un rasgo no fue reconocido, elige el valor
válido más cercano a lo que dijo el usuario o pídele que precise.

No inventes prendas ni datos que el usuario no haya dado.
Sé breve, claro y cordial.
""".strip()


def _crear_modelo() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=0.1,
    )


def _extraer_texto_final(result: dict) -> str:
    """Extrae el texto del último mensaje del Agent."""
    mensajes = result.get("messages", [])
    if not mensajes:
        return "No fue posible generar una respuesta."

    contenido = mensajes[-1].content

    if isinstance(contenido, str):
        return contenido or "No fue posible generar una respuesta."

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


def responder(
    mensaje_usuario: str,
    perfil: Perfil,
    memoria: str,
) -> str:
    agent = create_agent(
        model=_crear_modelo(),
        tools=TOOLS,
        system_prompt=construir_contexto(perfil, memoria),
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": mensaje_usuario}]}
    )

    return _extraer_texto_final(result)