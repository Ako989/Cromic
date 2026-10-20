"""Interfaz Streamlit de Cromic v3 con LangGraph."""

import streamlit as st

from config.settings import validar_configuracion
from core.session import (
    inicializar_thread,
    obtener_grafo,
    reiniciar_thread,
    responder,
)
from core.state import (
    actualizar_perfil_usuario,
    agregar_mensaje,
    inicializar_estado,
    registrar_ejecucion,
    reiniciar_estado,
)

st.set_page_config(
    page_title="Cromic v3",
    page_icon="👕",
)

try:
    validar_configuracion()
except ValueError as error:
    st.error(str(error))
    st.stop()

inicializar_estado()
inicializar_thread()

st.title("Cromic v3")
st.caption("Asesor de vestimenta")
st.write(
    "Versión con LangGraph: grafo de estado cíclico, nodos especializados, "
    "ToolNode y memoria con checkpointer."
)

with st.sidebar:
    st.subheader("Perfil del usuario")

    perfil = st.session_state.perfil

    st.write("Nombre:", perfil.get("nombre", "No registrado"))
    st.write("Color de ojos:", perfil.get("color_ojos", "No registrado"))
    st.write("Color de piel:", perfil.get("color_piel", "No registrado"))

    st.divider()
    st.subheader("Última ejecución")

    ejecucion = st.session_state.ultima_ejecucion
    st.write("Ruta:", ejecucion.get("ruta", "Sin ejecución"))

    if ejecucion.get("motivo"):
        st.caption(ejecucion["motivo"])

    pasos = ejecucion.get("pasos", [])
    if pasos:
        st.write("Nodos recorridos:")
        st.code(" ➔ ".join(["START", *pasos, "END"]), language=None)

    tools = ejecucion.get("tools", [])
    if tools:
        st.write("Tools utilizadas:")
        for nombre in tools:
            st.write(f"- {nombre}")
    else:
        st.write("Tools utilizadas: ninguna")

    st.divider()
    st.caption(f"Thread ID: {st.session_state.thread_id}")

    with st.expander("Diagrama del grafo (Mermaid)"):
        st.code(obtener_grafo().get_graph().draw_mermaid(), language="text")

    if st.button("Reiniciar conversación"):
        reiniciar_estado()
        reiniciar_thread()
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
        )
        respuesta = resultado["respuesta"]
        registrar_ejecucion(resultado)

        # Respaldo: guarda los pasos directamente
        st.session_state.ultima_ejecucion["pasos"] = resultado.get("pasos", [])

        # Diagnóstico temporal (puedes borrarlo después)
        st.toast(f"pasos: {resultado.get('pasos')}")
    except Exception as error:
        respuesta = f"Ocurrió un error al procesar la solicitud: {error}"

    with st.chat_message("assistant"):
        st.markdown(respuesta)

    agregar_mensaje("assistant", respuesta)

    st.rerun()