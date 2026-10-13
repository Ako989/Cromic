"""Tool para consultar códigos de vestimenta."""

import json
from pathlib import Path

from langchain.tools import tool

DATA_FILE = (
    Path(__file__).resolve().parents[1] / "data" / "codigos_vestimenta.json"
)


@tool
def consultar_codigo_vestimenta(consulta: str) -> dict:
    """Consulta qué implica un código de vestimenta (casual, business casual,
    cocktail, formal) y qué prendas se recomiendan o evitan."""
    with DATA_FILE.open("r", encoding="utf-8") as archivo:
        codigos = json.load(archivo)

    criterio = consulta.lower().strip()

    resultados = [
        codigo
        for codigo in codigos
        if criterio in codigo["codigo"].lower()
        or criterio in codigo["descripcion"].lower()
    ]

    return {
        "consulta": consulta,
        "resultados": resultados,
        "cantidad": len(resultados),
    }
