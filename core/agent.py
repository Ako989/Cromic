from typing import TypedDict

from google import genai
from google.genai import types

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from tools.ropa_tool import consultar_ropa


class Perfil(TypedDict):
    nombre: str
    color_ojos: str
    color_piel: str


client = genai.Client(api_key=GEMINI_API_KEY)


def construir_contexto(perfil: Perfil, memoria: str) -> str:
    return f"""
Eres el asistente de Cromic.

Tu única función es recordar y devolver la información que el usuario
ya te proporcionó: su nombre, color de ojos, color de piel y la ropa
que tiene disponible.

PERFIL ACTUAL DEL USUARIO:
Nombre: {perfil["nombre"]}
Color de ojos: {perfil["color_ojos"]}
Color de piel: {perfil["color_piel"]}

MEMORIA RECIENTE:
{memoria}

Dispones de una herramienta llamada consultar_ropa.

Usa consultar_ropa cuando el usuario pregunte por su ropa, prendas,
armario o disponibilidad de alguna prenda en particular.

No inventes prendas ni datos que el usuario no haya dado.
Si puedes responder usando el perfil o la memoria, responde directamente.
Sé breve, claro y cordial.
""".strip()


def responder(
    mensaje_usuario: str,
    perfil: Perfil,
    memoria: str,
) -> str:
    contexto = construir_contexto(perfil, memoria)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=mensaje_usuario,
        config=types.GenerateContentConfig(
            system_instruction=contexto,
            tools=[consultar_ropa],
        ),
    )

    return response.text or "No fue posible generar una respuesta."
