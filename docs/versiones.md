# Historial de versiones

## v1: demo con Gemini SDK
*Commits iniciales y PR #1 (`feature/etiqueta`)*

- Llamada directa a `google-genai` con *function calling* automático.
- Una sola tool: `consultar_ropa` sobre `data/ropa.json` (5 prendas).
- Perfil (nombre, ojos y piel) extraído con regex; memoria = últimos 6
  mensajes como texto en el *system prompt*.

## v2: LangChain, Router + Chain + Agent
*PR #2 (`feature/v2-LangChain`)*

- `router_chain` con salida estructurada (`RutaConsulta`) que decide entre
  `chain` y `agent`.
- `response_chain` (LCEL) para respuestas sin tools.
- Agent con `create_agent` y 6 tools: fecha, ropa, agenda, paleta por tono
  de piel, código de vestimenta y `sugerir_outfit` (chain anidada).
- Barra lateral con ruta, motivo y tools ejecutadas.

## v3: LangGraph
*PR #3 (rama `tonalidades`)*

- Nuevo paquete `graph/` con `StateGraph` cíclico: `enrutador`,
  `nodo_conceptual`, `agente_cromic` y `herramientas` (`ToolNode`).
- Memoria con `MemorySaver` + `thread_id` (`core/session.py`).
- Tools de colorimetría estacional: `diagnosticar_estacion` y
  `consultar_paleta_estacional` (rama `feauture/colorimetria_estacional`).
- La interfaz muestra la traza de nodos, el Thread ID y el diagrama Mermaid.

## v4: RAG, observabilidad y rediseño (actual)
*PR #4 (`feature/v4-final`)*

- RAG con `consultar_guia_colorimetria` sobre `guia_colorimetria.md`
  (embeddings de Gemini + respaldo léxico) y cita de la sección.
- `core/metrics.py`: tiempos por nodo, llamadas, tokens, tools y errores;
  log en `logs/metricas.jsonl`.
- Rediseño de la interfaz: encabezado, sugerencias iniciales, tarjeta de
  perfil, muestras de color de la paleta y mensajes de error legibles.
- `GEMINI_MODEL` y `EMBEDDING_MODEL` configurables por `.env`.

## Pendientes conocidos

- **Código heredado de v2 sin uso:** la descripción del PR #3 dice que se
  retiraban `core/agent.py`, `chains/router_chain.py` y
  `chains/response_chain.py`, pero siguen en `main`. Ningún módulo de v4 los
  importa, así que se pueden eliminar.
- **`core/state.obtener_memoria`** ya no se usa; la memoria la gestiona
  `MemorySaver`.
- **`COLORIMETRIA_REDACCION_PROMPT`** está definido pero ninguna parte del
  código lo usa.
- **La memoria no persiste:** `MemorySaver` vive en RAM y se pierde al
  reiniciar Streamlit. Para persistir, se puede usar `SqliteSaver`.
- **Perfil por regex limitado:** solo captura una palabra por rasgo (p. ej.
  "azul" en vez de "azul claro") y no detecta el cabello.
- **`requirements.txt` sin versiones fijas** (salvo `langgraph>=0.2.0`):
  conviene fijarlas para que el proyecto sea reproducible.
- **`data/etiqueta.json`** (catálogo de ocasiones: entrevista, trabajo,
  universidad…) se creó en la rama `feature/etiqueta`, pero nunca llegó a
  `main`.
- **No hay pruebas automatizadas.** Las tools de datos
  (`diagnosticar_estacion`, `consultar_ropa`…) son funciones puras y fáciles
  de probar con `pytest` sin llamar a la API.
