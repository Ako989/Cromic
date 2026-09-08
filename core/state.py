import re

import streamlit as st

PERFIL_INICIAL = {
    "nombre": "No registrado",
    "color_ojos": "No registrado",
    "color_piel": "No registrado",
}


def inicializar_estado() -> None:
    if "perfil" not in st.session_state:
        st.session_state.perfil = PERFIL_INICIAL.copy()

    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []


def actualizar_perfil_usuario(texto: str) -> None:
    texto_lower = texto.lower()

    patron_nombre = r"(?:soy|me llamo)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ]+)"
    coincidencia_nombre = re.search(patron_nombre, texto, re.IGNORECASE)

    if coincidencia_nombre:
        st.session_state.perfil["nombre"] = coincidencia_nombre.group(1).capitalize()

    patron_ojos = r"ojos (?:son|de color)?\s*([a-záéíóúñ]+)"
    coincidencia_ojos = re.search(patron_ojos, texto_lower)

    if coincidencia_ojos:
        st.session_state.perfil["color_ojos"] = coincidencia_ojos.group(1)

    patron_piel = r"piel (?:es|de color)?\s*([a-záéíóúñ]+)"
    coincidencia_piel = re.search(patron_piel, texto_lower)

    if coincidencia_piel:
        st.session_state.perfil["color_piel"] = coincidencia_piel.group(1)


def agregar_mensaje(role: str, content: str) -> None:
    st.session_state.mensajes.append(
        {
            "role": role,
            "content": content,
        }
    )


def obtener_memoria(limite: int = 6) -> str:
    mensajes = st.session_state.mensajes[-limite:]

    return "\n".join(
        f"{mensaje['role']}: {mensaje['content']}"
        for mensaje in mensajes
    )


def reiniciar_estado() -> None:
    st.session_state.mensajes = []
    st.session_state.perfil = PERFIL_INICIAL.copy()
