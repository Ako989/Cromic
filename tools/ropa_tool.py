import json
from pathlib import Path
from typing import TypedDict


class Prenda(TypedDict):
    prenda: str
    tipo: str
    color: str


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "ropa.json"


def consultar_ropa(consulta: str = "") -> list[Prenda]:
    with DATA_FILE.open("r", encoding="utf-8") as archivo:
        ropa: list[Prenda] = json.load(archivo)

    criterio = consulta.lower().strip()

    if not criterio:
        return ropa

    return [
        prenda
        for prenda in ropa
        if criterio in prenda["prenda"].lower()
        or criterio in prenda["tipo"].lower()
        or criterio in prenda["color"].lower()
    ]
