"""Interfaz Streamlit de Cromic v4: LangGraph, RAG y observabilidad."""

import json
from pathlib import Path

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
    page_title="Cromic · Asesor de colorimetría",
    page_icon="🎨",
    layout="centered",
    initial_sidebar_state="expanded",
)

ESTACIONES_FILE = Path(__file__).resolve().parent / "data" / "colorimetria_estaciones.json"

SUGERENCIAS = [
    ("🌸", "¿Qué es la colorimetría?", "¿Qué es la colorimetría estacional?"),
    (
        "🔎",
        "Descubre mi estación",
        "Tengo ojos azul claro, cabello rubio ceniza y piel porcelana rosada, ¿qué estación soy?",
    ),
    ("🏠", "Reconocerme en casa", "¿Cómo reconozco mi estación en casa?"),
    ("👗", "Mi armario", "¿Qué ropa tengo?"),
]

ESTILO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Poppins:wght@400;500;600&display=swap');

html, body, [class*="css"], .stMarkdown, .stButton button {
    font-family: 'Poppins', sans-serif;
}
.block-container { padding-top: 1.5rem; max-width: 820px; }

/* Encabezado */
.hero {
    border-radius: 22px; overflow: hidden; margin-bottom: 1.2rem;
    box-shadow: 0 6px 24px rgba(139, 74, 107, .18);
    background: linear-gradient(135deg, #8B4A6B 0%, #C98B7A 100%);
}
.hero-body { padding: 1.4rem 1.6rem 1.1rem 1.6rem; color: #fff; }
.hero-body h1 {
    font-family: 'Playfair Display', serif; font-size: 2.4rem;
    margin: 0; color: #fff; letter-spacing: .5px;
}
.hero-body p { margin: .3rem 0 0 0; opacity: .95; font-size: .98rem; }
.estaciones { display: flex; height: 8px; }
.estaciones div { flex: 1; }

/* Burbujas de chat */
[data-testid="stChatMessage"] {
    background: #FFFFFF; border: 1px solid #F0DED2; border-radius: 18px;
    padding: .9rem 1.1rem; margin-bottom: .7rem;
    box-shadow: 0 2px 10px rgba(46, 42, 51, .05);
}

/* Botones de sugerencia */
.stButton button {
    border-radius: 14px; border: 1px solid #E5CFC2; background: #FFFFFF;
    padding: .7rem .9rem; transition: all .15s ease; font-weight: 500;
}
.stButton button:hover {
    border-color: #8B4A6B; color: #8B4A6B; transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(139, 74, 107, .15);
}

/* Paleta */
.sw-grid { display: flex; flex-wrap: wrap; gap: 10px; margin: 6px 0 12px 0; }
.sw { width: 78px; text-align: center; font-size: .72rem; line-height: 1.15; }
.sw div { height: 44px; border-radius: 12px; border: 1px solid rgba(0,0,0,.12);
          margin-bottom: 4px; box-shadow: 0 2px 6px rgba(0,0,0,.08); }

/* Línea de datos bajo cada respuesta */
.meta { font-size: .75rem; color: #8a7f86; margin-top: .4rem; }
.meta span {
    display: inline-block; background: #F6E9E0; border-radius: 999px;
    padding: 2px 10px; margin: 0 6px 4px 0;
}

/* Tarjeta de perfil */
.perfil {
    background: #FFFFFF; border: 1px solid #F0DED2; border-radius: 16px;
    padding: .8rem 1rem; font-size: .9rem; line-height: 1.7;
}

@media (max-width: 640px) {
    .hero-body h1 { font-size: 1.8rem; }
    .sw { width: 64px; }
}
</style>
"""

HEADER = """
<div class="hero">
  <div class="hero-body">
    <h1>Cromic</h1>
    <p>Descubre tu estación de color y viste lo que de verdad te favorece</p>
  </div>
  <div class="estaciones">
    <div style="background:#FF9E8F"></div>
    <div style="background:#B5D3EA"></div>
    <div style="background:#E8601C"></div>
    <div style="background:#4A2A7A"></div>
  </div>
</div>
"""

st.markdown(ESTILO, unsafe_allow_html=True)

try:
    validar_configuracion()
except ValueError as error:
    st.error(str(error))
    st.stop()

inicializar_estado()
inicializar_thread()

for clave, valor in {
    "ultima_metrica": None,
    "historial_metricas": [],
    "paletas": {},
    "meta": {},
    "pendiente": None,
}.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor


@st.cache_data
def _cargar_estaciones() -> dict:
    with ESTACIONES_FILE.open("r", encoding="utf-8") as archivo:
        return {e["estacion"]: e for e in json.load(archivo)}


def _html_colores(colores: list[dict]) -> str:
    items = "".join(
        f'<div class="sw"><div style="background:{c["hex"]}"></div>{c["nombre"]}</div>'
        for c in colores
    )
    return f'<div class="sw-grid">{items}</div>'


def mostrar_paleta(clave: str) -> None:
    estacion = _cargar_estaciones().get(clave)
    if not estacion:
        return
    with st.expander(f"🎨 Tu paleta: {estacion['nombre']}", expanded=True):
        st.caption(estacion["vibes"])
        st.markdown("**✨ Te favorecen**")
        st.markdown(_html_colores(estacion["paleta"]), unsafe_allow_html=True)
        st.markdown("**🚫 Mejor lejos del rostro**")
        st.markdown(_html_colores(estacion["evitar"]), unsafe_allow_html=True)


def mostrar_meta(meta: dict) -> None:
    chips = [f"⏱ {meta['tiempo']} s", f"🤖 {meta['llamadas']} llamadas"]
    chips += [f"🔧 {t}" for t in meta["tools"]]
    html = "".join(f"<span>{c}</span>" for c in chips)
    st.markdown(f'<div class="meta">{html}</div>', unsafe_allow_html=True)


def _mensaje_error_amigable(error: Exception) -> str:
    texto = str(error)
    if "RESOURCE_EXHAUSTED" in texto or "429" in texto:
        return (
            "⏳ Se alcanzó el límite de uso gratuito del modelo. "
            "Espera unos minutos o cambia GEMINI_MODEL en la configuración."
        )
    if "NOT_FOUND" in texto or "404" in texto:
        return "⚠️ El modelo configurado no está disponible. Revisa GEMINI_MODEL."
    if "API key" in texto or "403" in texto:
        return "🔑 La API Key no es válida. Revisa GEMINI_API_KEY."
    return f"⚠️ Ocurrió un error al procesar la solicitud: {texto[:200]}"


# ---------- Barra lateral ----------
with st.sidebar:
    st.markdown("### 👤 Tu perfil")
    perfil = st.session_state.perfil
    st.markdown(
        f"""
        <div class="perfil">
        <b>Nombre:</b> {perfil.get("nombre", "No registrado")}<br>
        <b>Ojos:</b> {perfil.get("color_ojos", "No registrado")}<br>
        <b>Piel:</b> {perfil.get("color_piel", "No registrado")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📊 Último turno")
    m = st.session_state.ultima_metrica
    if m:
        c1, c2 = st.columns(2)
        c1.metric("Tiempo", f"{m['tiempo_total_s']} s")
        c2.metric("Llamadas", m["llamadas_modelo"])
        c1.metric("Tokens", m["tokens_total"])
        c2.metric("Tools", len(m["tools"]))
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

    with st.expander("🧭 Ruta del agente"):
        ejecucion = st.session_state.ultima_ejecucion
        st.write("Ruta:", ejecucion.get("ruta", "Sin ejecución"))
        if ejecucion.get("motivo"):
            st.caption(ejecucion["motivo"])
        pasos = ejecucion.get("pasos", [])
        if pasos:
            st.code(" ➔ ".join(["START", *pasos, "END"]), language=None)
        tools = ejecucion.get("tools", [])
        st.write("Tools:", ", ".join(tools) if tools else "ninguna")
        if m and m["tiempos_nodos"]:
            st.markdown("**Tiempo por nodo**")
            for n in m["tiempos_nodos"]:
                st.write(f"{n['nodo']}: {n['segundos']} s")

    with st.expander("🕸️ Diagrama del grafo"):
        st.code(obtener_grafo().get_graph().draw_mermaid(), language="text")
        st.caption(f"Thread ID: {st.session_state.thread_id}")

    if st.button("🔄 Nueva conversación", use_container_width=True):
        reiniciar_estado()
        reiniciar_thread()
        st.session_state.ultima_metrica = None
        st.session_state.historial_metricas = []
        st.session_state.paletas = {}
        st.session_state.meta = {}
        st.rerun()

# ---------- Encabezado ----------
st.markdown(HEADER, unsafe_allow_html=True)

# ---------- Historial ----------
for i, mensaje in enumerate(st.session_state.mensajes):
    avatar = "🧑" if mensaje["role"] == "user" else "🎨"
    with st.chat_message(mensaje["role"], avatar=avatar):
        st.markdown(mensaje["content"])
        if i in st.session_state.paletas:
            mostrar_paleta(st.session_state.paletas[i])
        if i in st.session_state.meta:
            mostrar_meta(st.session_state.meta[i])

# ---------- Sugerencias ----------
if not st.session_state.mensajes:
    st.markdown("#### ¿Por dónde quieres empezar?")
    columnas = st.columns(2)
    for idx, (icono, titulo, texto) in enumerate(SUGERENCIAS):
        if columnas[idx % 2].button(
            f"{icono}  {titulo}", key=f"sug_{idx}", use_container_width=True
        ):
            st.session_state.pendiente = texto
            st.rerun()
    st.caption("O escribe abajo tus rasgos: color de ojos, cabello y piel.")

# ---------- Entrada ----------
prompt = st.chat_input("Cuéntame sobre ti o pregúntame qué ponerte...")
if st.session_state.pendiente:
    prompt = st.session_state.pendiente
    st.session_state.pendiente = None

if prompt:
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    actualizar_perfil_usuario(prompt)
    agregar_mensaje("user", prompt)

    estacion_paleta = None
    meta = None
    try:
        with st.spinner("Cromic está combinando colores..."):
            resultado = responder(
                mensaje_usuario=prompt,
                perfil=st.session_state.perfil,
            )
        respuesta = resultado["respuesta"]
        estacion_paleta = resultado.get("estacion_paleta")
        registrar_ejecucion(resultado)
        st.session_state.ultima_ejecucion["pasos"] = resultado.get("pasos", [])
        st.session_state.ultima_metrica = resultado["metricas"]
        st.session_state.historial_metricas.append(resultado["metricas"])
        meta = {
            "tiempo": resultado["metricas"]["tiempo_total_s"],
            "llamadas": resultado["metricas"]["llamadas_modelo"],
            "tools": resultado.get("tools", []),
        }
    except Exception as error:
        respuesta = _mensaje_error_amigable(error)

    indice = len(st.session_state.mensajes)
    if estacion_paleta:
        st.session_state.paletas[indice] = estacion_paleta
    if meta:
        st.session_state.meta[indice] = meta

    agregar_mensaje("assistant", respuesta)
    st.rerun()