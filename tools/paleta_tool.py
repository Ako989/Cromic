"""Tool para consultar la paleta de colores según el tono de piel."""

import json
from pathlib import Path

from langchain.tools import tool

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "paletas.json"


@tool
def consultar_paleta_colores(color_piel: str) -> dict:
    """Consulta qué colores favorecen o conviene evitar según el tono de piel
    (clara, media, morena u oscura)."""
    with DATA_FILE.open("r", encoding="utf-8") as archivo:
        paletas = json.load(archivo)

    criterio = color_piel.lower().strip()

    resultados = [
        paleta
        for paleta in paletas
        if criterio in paleta["tono_piel"].lower()
        or paleta["tono_piel"].lower() in criterio
    ]

    return {
        "consulta": color_piel,
        "resultados": resultados,
        "cantidad": len(resultados),
    }
