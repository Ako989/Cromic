"""Interfaz Streamlit de Cromic v2 con LangChain."""

import streamlit as st

from config.settings import validar_configuracion
from core.agent import responder
from core.state import (
    agregar_mensaje,
    actualizar_perfil_usuario,
    inicializar_estado,
    obtener_memoria,
    registrar_ejecucion,
    reiniciar_estado,
)

st.set_page_config(
    page_title="Cromic v2",
    page_icon="👕",
)

try:
    validar_configuracion()
except ValueError as error:
    st.error(str(error))
    st.stop()

inicializar_estado()

st.title("Cromic v2")
st.caption("Asesor de vestimenta")
st.write(
    "Versión con LangChain, Chain de enrutamiento, Agent y múltiples Tools."
)

with st.sidebar:
    st.subheader("Perfil del usuario")

    perfil = st.session_state.perfil

    st.write("Nombre:", perfil["nombre"])
    st.write("Color de ojos:", perfil["color_ojos"])
    st.write("Color de piel:", perfil["color_piel"])

    st.divider()
    st.subheader("Última ejecución")

    ejecucion = st.session_state.ultima_ejecucion
    st.write("Ruta:", ejecucion["ruta"])

    if ejecucion["motivo"]:
        st.caption(ejecucion["motivo"])

    if ejecucion["tools"]:
        st.write("Tools utilizadas:")
        for nombre in ejecucion["tools"]:
            st.write(f"- {nombre}")
    else:
        st.write("Tools utilizadas: ninguna")

    st.divider()

    if st.button("Reiniciar conversación"):
        reiniciar_estado()
        st.rerun()

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

prompt = st.chat_input("Cuéntame sobre ti o pregúntame qué ponerte...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    actualizar_perfil_usuario(prompt)
    agregar_mensaje("user", prompt)

    try:
        resultado = responder(
            mensaje_usuario=prompt,
            perfil=st.session_state.perfil,
            memoria=obtener_memoria(),
        )
        respuesta = resultado["respuesta"]
        registrar_ejecucion(resultado)
    except Exception as error:
        respuesta = f"Ocurrió un error al procesar la solicitud: {error}"

    with st.chat_message("assistant"):
        st.markdown(respuesta)

    agregar_mensaje("assistant", respuesta)

    st.rerun()
