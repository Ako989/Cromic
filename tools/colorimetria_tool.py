"""Tools de colorimetría estacional para Cromic."""

import json
import unicodedata
from pathlib import Path

from langchain.tools import tool

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ESTACIONES_FILE = DATA_DIR / "colorimetria_estaciones.json"
RASGOS_FILE = DATA_DIR / "colorimetria_rasgos.json"

EJES = ("temperatura", "intensidad", "profundidad")
OBLIGATORIOS = ("ojos", "cabello", "piel")


def _normalizar(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar textos."""
    texto = unicodedata.normalize("NFD", texto.lower().strip())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _cargar(ruta: Path) -> list[dict]:
    with ruta.open("r", encoding="utf-8") as archivo:
        return json.load(archivo)


def _buscar_rasgo(categoria: str, texto: str, rasgos: list[dict]) -> dict | None:
    """Busca el rasgo que mejor coincide con lo que escribió el usuario."""
    texto_n = _normalizar(texto)
    coincidencias = []

    for rasgo in rasgos:
        if rasgo["categoria"] != categoria:
            continue
        # "azul claro o gris" se separa en ["azul claro", "gris"]
        for opcion in rasgo["valor"].split(" o "):
            opcion_n = _normalizar(opcion)
            if opcion_n in texto_n:
                coincidencias.append((len(opcion_n), rasgo))

    if not coincidencias:
        return None

    # Gana la coincidencia más larga (la más específica)
    return max(coincidencias, key=lambda c: c[0])[1]


def _valores_validos(categoria: str, rasgos: list[dict]) -> list[str]:
    return [r["valor"] for r in rasgos if r["categoria"] == categoria]


@tool
def diagnosticar_estacion(
    ojos: str = "",
    cabello: str = "",
    piel: str = "",
    contraste: str = "",
    venas: str = "",
    joyeria: str = "",
) -> dict:
    """Diagnostica la estación de color (primavera, verano, otoño o invierno)
    a partir de los rasgos de la persona.

    Obligatorios: ojos, cabello y piel. Opcionales: contraste, venas, joyeria.
    Si falta un obligatorio, devuelve qué falta para que se le pregunte al usuario.

    Valores esperados:
    - ojos: azul claro, gris, azul intenso, verde, miel, ámbar, café claro,
      café oscuro, negro
    - cabello: rubio ceniza, rubio dorado, castaño claro, castaño rojizo,
      cobrizo, castaño oscuro, negro
    - piel: porcelana rosada, marfil, durazno, trigueña dorada, trigueña oliva,
      morena con fondo azulado, negra profunda
    - contraste: alto o bajo (entre piel, ojos y cabello)
    - venas: azules o moradas, verdes
    - joyeria: plata u oro (cuál le favorece más)
    """
    datos = {
        "ojos": ojos,
        "cabello": cabello,
        "piel": piel,
        "contraste": contraste,
        "venas": venas,
        "joyeria": joyeria,
    }

    faltan = [c for c in OBLIGATORIOS if not datos[c].strip()]
    if faltan:
        return {"estado": "faltan_datos", "faltan": faltan}

    rasgos = _cargar(RASGOS_FILE)
    estaciones = _cargar(ESTACIONES_FILE)

    votos: dict[str, dict[str, int]] = {eje: {} for eje in EJES}
    usados: list[dict] = []
    no_reconocidos: list[dict] = []

    for categoria, texto in datos.items():
        if not texto.strip():
            continue

        rasgo = _buscar_rasgo(categoria, texto, rasgos)

        if rasgo is None:
            no_reconocidos.append(
                {
                    "categoria": categoria,
                    "recibido": texto,
                    "valores_validos": _valores_validos(categoria, rasgos),
                }
            )
            continue

        usados.append({"categoria": categoria, "valor": rasgo["valor"]})

        for eje in EJES:
            valor_eje = rasgo[eje]
            if valor_eje:
                votos[eje][valor_eje] = votos[eje].get(valor_eje, 0) + 1

    if any(n["categoria"] in OBLIGATORIOS for n in no_reconocidos):
        return {"estado": "rasgo_no_reconocido", "no_reconocidos": no_reconocidos}

    total_votos = sum(sum(v.values()) for v in votos.values())

    puntajes = {
        est["estacion"]: sum(votos[eje].get(est[eje], 0) for eje in EJES)
        for est in estaciones
    }
    ranking = sorted(puntajes.items(), key=lambda p: p[1], reverse=True)

    mejor, puntaje_mejor = ranking[0]
    segunda, puntaje_segunda = ranking[1]
    confianza = round(puntaje_mejor / total_votos, 2) if total_votos else 0.0

    if confianza >= 0.75:
        nivel = "alta"
    elif confianza >= 0.55:
        nivel = "media"
    else:
        nivel = "baja"

    nombres = {e["estacion"]: e["nombre"] for e in estaciones}

    return {
        "estado": "ok",
        "estacion": mejor,
        "nombre": nombres[mejor],
        "confianza": confianza,
        "nivel_confianza": nivel,
        "alternativa": nombres[segunda] if puntaje_segunda == puntaje_mejor else None,
        "rasgos_usados": usados,
        "rasgos_no_reconocidos": no_reconocidos,
    }


@tool
def consultar_paleta_estacional(estacion: str) -> dict:
    """Devuelve la paleta, los colores a evitar y cómo se ve una estación de
    color. La estación debe ser: primavera, verano, otono/otoño o invierno."""
    estaciones = _cargar(ESTACIONES_FILE)
    criterio = _normalizar(estacion)

    for est in estaciones:
        if criterio in (_normalizar(est["estacion"]), _normalizar(est["nombre"])) \
                or _normalizar(est["estacion"]) in criterio:
            return {"estado": "ok", **est}

    return {
        "estado": "no_encontrada",
        "consulta": estacion,
        "estaciones_validas": [e["estacion"] for e in estaciones],
    }