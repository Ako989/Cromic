"""Configuración central de Cromic v2 con LangChain."""

import os
from dotenv import load_dotenv


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def validar_configuracion() -> None:
    """Valida las variables mínimas requeridas."""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "TU_API_KEY_AQUI":
        raise ValueError(
            "Configura una API Key válida en el archivo .env "
            "usando GEMINI_API_KEY."
        )
