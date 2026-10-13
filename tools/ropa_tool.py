"""Tools para consultar el armario y sugerir outfits."""

import json
from pathlib import Path

from langchain.tools import tool

from chains.outfit_chain import crear_outfit_chain, serializar_prendas

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "ropa.json"


def _cargar_ropa() -> list[dict]:
    with DATA_FILE.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


@tool
def consultar_ropa(consulta: str = "todas") -> dict:
    """Consulta las prendas del armario por nombre, tipo, color, estilo o clima."""
    ropa = _cargar_ropa()
    criterio = consulta.lower().strip()

    if criterio in {"", "todas", "todo", "*"}:
        resultados = ropa
    else:
        resultados = [
            prenda
            for prenda in ropa
            if any(criterio in str(valor).lower() for valor in prenda.values())
        ]

    return {
        "consulta": consulta,
        "resultados": resultados,
        "cantidad": len(resultados),
    }


@tool
def sugerir_outfit(ocasion: str, perfil: str = "") -> str:
    """Arma un outfit con la ropa del armario mediante una Chain determinista.

    ocasion: evento o código de vestimenta (ej. "entrevista, business casual").
    perfil: color de piel, ojos y colores que le favorecen al usuario.
    """
    chain = crear_outfit_chain()

    return chain.invoke(
        {
            "prendas": serializar_prendas(_cargar_ropa()),
            "ocasion": ocasion,
            "perfil": perfil or "Sin datos del perfil.",
        }
    )
