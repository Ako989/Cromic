"""Interfaz Streamlit de Cromic v4 con LangGraph."""

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
    page_title="Cromic",
    page_icon="👕",
)

try:
    validar_configuracion()
except ValueError as error:
    st.error(str(error))
    st.stop()

inicializar_estado()
inicializar_thread()

if "ultima_metrica" not in st.session_state:
    st.session_state.ultima_metrica = None
if "historial_metricas" not in st.session_state:
    st.session_state.historial_metricas = []


def _mensaje_error_amigable(error: Exception) -> str:
    texto = str(error)
    if "RESOURCE_EXHAUSTED" in texto or "429" in texto:
        return (
            "Se alcanzó el límite de uso gratuito del modelo. "
            "Espera unos minutos o cambia GEMINI_MODEL en la configuración."
        )
    if "NOT_FOUND" in texto or "404" in texto:
        return (
            "El modelo configurado no está disponible. "
            "Revisa el valor de GEMINI_MODEL."
        )
    if "API key" in texto or "403" in texto:
        return "La API Key no es válida. Revisa GEMINI_API_KEY."
    return f"Ocurrió un error al procesar la solicitud: {texto[:200]}"


st.title("Cromic")
st.caption("Asesor de vestimenta y colorimetría")
st.write(
    "Versión con LangGraph: grafo de estado cíclico, nodos especializados, "
    "ToolNode, memoria con checkpointer y métricas de ejecución."
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
    st.subheader("Métricas del turno")

    m = st.session_state.ultima_metrica
    if m:
        col1, col2 = st.columns(2)
        col1.metric("Tiempo", f"{m['tiempo_total_s']} s")
        col2.metric("Llamadas al modelo", m["llamadas_modelo"])
        col1.metric("Tokens", m["tokens_total"])
        col2.metric("Tools", len(m["tools"]))

        if m["tiempos_nodos"]:
            with st.expander("Tiempo por nodo"):
                for n in m["tiempos_nodos"]:
                    st.write(f"{n['nodo']}: {n['segundos']} s")
        if m["errores"]:
            st.warning(f"Errores: {len(m['errores'])}")
    else:
        st.caption("Aún no hay ejecuciones.")

    historial = st.session_state.historial_metricas
    if historial:
        st.caption(
            f"Sesión: {len(historial)} consultas · "
            f"{sum(h['tokens_total'] for h in historial)} tokens · "
            f"{sum(h['llamadas_modelo'] for h in historial)} llamadas"
        )

    st.divider()
    st.caption(f"Thread ID: {st.session_state.thread_id}")

    with st.expander("Diagrama del grafo (Mermaid)"):
        st.code(obtener_grafo().get_graph().draw_mermaid(), language="text")

    if st.button("Reiniciar conversación"):
        reiniciar_estado()
        reiniciar_thread()
        st.session_state.ultima_metrica = None
        st.session_state.historial_metricas = []
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
        with st.spinner("Cromic está pensando..."):
            resultado = responder(
                mensaje_usuario=prompt,
                perfil=st.session_state.perfil,
            )
        respuesta = resultado["respuesta"]
        registrar_ejecucion(resultado)
        st.session_state.ultima_ejecucion["pasos"] = resultado.get("pasos", [])

        st.session_state.ultima_metrica = resultado["metricas"]
        st.session_state.historial_metricas.append(resultado["metricas"])
    except Exception as error:
        respuesta = _mensaje_error_amigable(error)

    with st.chat_message("assistant"):
        st.markdown(respuesta)

    agregar_mensaje("assistant", respuesta)

    st.rerun()