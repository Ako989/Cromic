"""Tool para consultar los eventos de la agenda del usuario."""

import json
from pathlib import Path

from langchain.tools import tool

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "agenda.json"


@tool
def consultar_agenda(consulta: str = "todos") -> dict:
    """Consulta eventos de la agenda por fecha (AAAA-MM-DD), nombre o lugar."""
    with DATA_FILE.open("r", encoding="utf-8") as archivo:
        eventos = json.load(archivo)

    criterio = consulta.lower().strip()

    if criterio in {"", "todos", "todo", "*"}:
        resultados = eventos
    else:
        resultados = [
            evento
            for evento in eventos
            if criterio in evento["fecha"].lower()
            or criterio in evento["evento"].lower()
            or criterio in evento["lugar"].lower()
        ]

    return {
        "consulta": consulta,
        "resultados": resultados,
        "cantidad": len(resultados),
    }
