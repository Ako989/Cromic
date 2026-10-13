"""Chain para armar un outfit a partir de prendas conocidas."""

import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from prompts.fashion_prompt import OUTFIT_SYSTEM_PROMPT


def crear_outfit_chain():
    """Crea una Chain fija: datos -> prompt -> modelo -> salida."""
    model = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=0.3,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", OUTFIT_SYSTEM_PROMPT),
            (
                "human",
                "Prendas disponibles:\n{prendas}\n\n"
                "Ocasión: {ocasion}\n"
                "Perfil y colores que favorecen: {perfil}",
            ),
        ]
    )

    return prompt | model | StrOutputParser()


def serializar_prendas(prendas) -> str:
    """Convierte las prendas a JSON legible para la Chain."""
    return json.dumps(prendas, ensure_ascii=False, indent=2)
