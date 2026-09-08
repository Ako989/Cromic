import streamlit as st

from config.settings import validar_configuracion
from core.agent import responder
from core.state import (
    agregar_mensaje,
    actualizar_perfil_usuario,
    inicializar_estado,
    obtener_memoria,
    reiniciar_estado,
)

st.set_page_config(
    page_title="Cromic",
    page_icon="👕",
)

try:
    validar_configuracion()
except ValueError as error:
    st.error(str(error))
    st.stop()

inicializar_estado()

st.title("Cromic")
st.caption("Asesor de vestimenta")
st.write("Demo con Gemini, contexto, memoria, perfil y una herramienta.")

with st.sidebar:
    st.subheader("Perfil del usuario")

    perfil = st.session_state.perfil

    st.write("Nombre:", perfil["nombre"])
    st.write("Color de ojos:", perfil["color_ojos"])
    st.write("Color de piel:", perfil["color_piel"])

    st.divider()

    if st.button("Reiniciar conversación"):
        reiniciar_estado()
        st.rerun()

for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

prompt = st.chat_input("Cuéntame sobre ti o pregúntame por tu ropa...")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    actualizar_perfil_usuario(prompt)
    agregar_mensaje("user", prompt)

    try:
        respuesta = responder(
            mensaje_usuario=prompt,
            perfil=st.session_state.perfil,
            memoria=obtener_memoria(),
        )
    except Exception as error:
        respuesta = f"Ocurrió un error al consultar Gemini: {error}"

    with st.chat_message("assistant"):
        st.markdown(respuesta)

    agregar_mensaje("assistant", respuesta)

    st.rerun()
