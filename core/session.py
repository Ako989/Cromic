"""Integración entre Streamlit y el grafo de LangGraph (threads y checkpoints)."""

import uuid

import streamlit as st
from langchain_core.messages import HumanMessage

from graph.workflow import crear_grafo_cromic

import json
import time
from pathlib import Path

from core.metrics import MetricasCallback

LOG_FILE = Path(__file__).resolve().parents[1] / "logs" / "metricas.jsonl"

@st.cache_resource
def obtener_grafo():
    """Compila el grafo una sola vez para conservar el MemorySaver."""
    return crear_grafo_cromic()


def inicializar_thread() -> None:
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())


def reiniciar_thread() -> None:
    """Un thread_id nuevo equivale a una memoria nueva."""
    st.session_state.thread_id = str(uuid.uuid4())


def _extraer_texto_final(result: dict) -> str:
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


def _guardar_log(mensaje: str, ruta: str, metricas: dict) -> None:
    """Agrega una línea por turno a logs/metricas.jsonl (evidencia del taller)."""
    try:
        LOG_FILE.parent.mkdir(exist_ok=True)
        registro = {
            "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mensaje": mensaje,
            "ruta": ruta,
            **metricas,
        }
        with LOG_FILE.open("a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except OSError:
        pass


def responder(mensaje_usuario: str, perfil: dict) -> dict:
    """Ejecuta un turno en el grafo y devuelve respuesta + métricas."""
    grafo = obtener_grafo()
    medidor = MetricasCallback()

    config = {
        "configurable": {"thread_id": st.session_state.thread_id},
        "recursion_limit": 15,
        "callbacks": [medidor],
    }

    estado_entrada = {
        "messages": [HumanMessage(content=mensaje_usuario)],
        "usuario": dict(perfil),
        "ruta": "",
        "motivo": "",
        "herramientas_usadas": [],
        "pasos_ejecutados": [],
    }

    try:
        resultado = grafo.invoke(estado_entrada, config=config)
    except Exception as error:
        medidor.errores.append(str(error)[:300])
        _guardar_log(mensaje_usuario, "error", medidor.resumen())
        raise

    metricas = medidor.resumen()
    ruta = resultado.get("ruta", "Desconocida")
    _guardar_log(mensaje_usuario, ruta, metricas)

    return {
        "respuesta": _extraer_texto_final(resultado),
        "ruta": ruta,
        "motivo": resultado.get("motivo", ""),
        "tools": resultado.get("herramientas_usadas", []),
        "pasos": resultado.get("pasos_ejecutados", []),
        "metricas": metricas,
    }