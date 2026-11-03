"""RAG: consulta la guía de colorimetría con búsqueda vectorial (y respaldo léxico)."""

import os
import re
import unicodedata
from pathlib import Path

from langchain.tools import tool
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config.settings import GEMINI_API_KEY

GUIA_FILE = Path(__file__).resolve().parents[1] / "data" / "guia_colorimetria.md"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")

_fragmentos: list[Document] | None = None
_store: InMemoryVectorStore | None = None


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def _cargar_fragmentos() -> list[Document]:
    """Divide la guía en un fragmento por sección '## ...'."""
    global _fragmentos
    if _fragmentos is None:
        texto = GUIA_FILE.read_text(encoding="utf-8")
        docs = []
        for bloque in re.split(r"\n(?=## )", texto):
            bloque = bloque.strip()
            if not bloque.startswith("## "):
                continue
            titulo, _, cuerpo = bloque.partition("\n")
            titulo = titulo[3:].strip()
            docs.append(
                Document(
                    page_content=f"{titulo}\n{cuerpo.strip()}",
                    metadata={"seccion": titulo, "fuente": "guia_colorimetria.md"},
                )
            )
        _fragmentos = docs
    return _fragmentos


def _buscar_vectorial(pregunta: str, k: int) -> list[Document]:
    global _store
    if _store is None:
        embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY
        )
        store = InMemoryVectorStore(embeddings)
        store.add_documents(_cargar_fragmentos())
        _store = store
    return _store.similarity_search(pregunta, k=k)


def _buscar_lexico(pregunta: str, k: int) -> list[Document]:
    """Respaldo sin API: puntúa por palabras en común."""
    palabras = {p for p in re.findall(r"\w+", _normalizar(pregunta)) if len(p) > 3}
    puntuados = []
    for doc in _cargar_fragmentos():
        texto = _normalizar(doc.page_content)
        puntos = sum(texto.count(p) for p in palabras)
        puntuados.append((puntos, doc))
    puntuados.sort(key=lambda x: x[0], reverse=True)
    return [d for p, d in puntuados[:k] if p > 0]


@tool
def consultar_guia_colorimetria(pregunta: str) -> dict:
    """Busca en la guía de colorimetría de Cromic (RAG). Úsala para preguntas
    de conocimiento: qué es la colorimetría, qué significan temperatura,
    intensidad o profundidad, cómo reconocer la estación en casa, cómo
    aplicar la paleta a la ropa o qué límites tiene. Devuelve fragmentos con
    su sección para citar la fuente."""
    try:
        docs = _buscar_vectorial(pregunta, k=3)
        metodo = "vectorial"
    except Exception as error:
        docs = _buscar_lexico(pregunta, k=3)
        metodo = f"lexico (respaldo: {str(error)[:80]})"

    if not docs:
        return {"estado": "sin_resultados", "metodo": metodo, "pregunta": pregunta}

    return {
        "estado": "ok",
        "metodo": metodo,
        "fragmentos": [
            {"seccion": d.metadata["seccion"], "texto": d.page_content} for d in docs
        ],
    }