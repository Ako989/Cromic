# Cromic · Asesor de colorimetría y vestimenta

Cromic es un agente conversacional que aconseja cómo vestirse según los
rasgos de la persona (ojos, cabello y piel), su armario y su agenda.
Diagnostica la **estación de color** (primavera, verano, otoño o invierno),
muestra la paleta que le favorece y arma outfits con la ropa disponible.

**Versión actual: v4.** Está construido con **LangGraph** (grafo cíclico
ReAct), **LangChain**, **Gemini** y una interfaz en **Streamlit**. Incluye
RAG sobre una guía de colorimetría y un panel de observabilidad (tiempos,
llamadas al modelo, tokens y tools por turno).

## Funcionalidades

- **Enrutamiento:** un nodo clasificador con salida estructurada (Pydantic)
  decide si la consulta es *conceptual* (se responde sin tools) o necesita
  *herramientas*.
- **Agente ReAct con 9 tools:** armario, outfits, agenda, fecha, códigos de
  vestimenta, paletas por tono de piel, diagnóstico de estación, paleta
  estacional y guía de colorimetría.
- **Diagnóstico de estación:** sistema de votos sobre tres ejes
  (temperatura, intensidad y profundidad) con nivel de confianza.
- **RAG:** búsqueda vectorial con embeddings de Gemini sobre
  `data/guia_colorimetria.md`, con respaldo léxico si la API de embeddings
  falla. Las respuestas citan la sección usada.
- **Memoria por conversación:** `MemorySaver` + `thread_id`. "Nueva
  conversación" crea un hilo nuevo.
- **Observabilidad:** métricas por turno en la barra lateral y en
  `logs/metricas.jsonl`.
- **Interfaz:** sugerencias iniciales, perfil detectado, paleta con muestras
  de color, ruta del agente y diagrama Mermaid del grafo.

## Requisitos

- Python 3.10 o superior (el código usa `X | None` y `list[str]`)
- Una API key de Google Gemini ([Google AI Studio](https://aistudio.google.com/))

## Instalación y ejecución

```bash
git clone https://github.com/Ako989/Cromic.git
cd Cromic
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz:

```env
GEMINI_API_KEY=tu_api_key_real
GEMINI_MODEL=gemini-3.5-flash-lite          # opcional
EMBEDDING_MODEL=models/gemini-embedding-001 # opcional
```

Ejecuta la app:

```bash
streamlit run app.py
```

| Variable | Obligatoria | Valor por defecto | Uso |
|---|---|---|---|
| `GEMINI_API_KEY` | Sí | — | Autenticación con Gemini (chat y embeddings) |
| `GEMINI_MODEL` | No | `gemini-3.5-flash-lite` | Modelo de los nodos y de la chain de outfits |
| `EMBEDDING_MODEL` | No | `models/gemini-embedding-001` | Embeddings del RAG |

Si `GEMINI_API_KEY` falta o vale `TU_API_KEY_AQUI`, la app muestra un error y
no arranca.

## Estructura del proyecto

```
app.py                         Interfaz Streamlit (chat, barra lateral, paletas)
.streamlit/config.toml         Tema visual
config/settings.py             Variables de entorno y validación
graph/
  state.py                     CromicState (estado compartido del grafo)
  nodes.py                     Nodos: enrutador, conceptual, agente, herramientas
  workflow.py                  Topología del grafo + MemorySaver
core/
  session.py                   Puente Streamlit ↔ grafo: thread_id, invocación, logs
  metrics.py                   MetricasCallback (tiempos, tokens, tools, errores)
  state.py                     Perfil, historial de mensajes y última ejecución
prompts/
  fashion_prompt.py            Prompts del enrutador, conceptual, agente y outfit
  colorimetria_prompt.py       Reglas de colorimetría añadidas al agente
chains/
  outfit_chain.py              Chain LCEL usada por la tool sugerir_outfit
tools/                         Las 9 tools (ver docs/herramientas-y-datos.md)
data/                          Fuentes JSON y guía Markdown del RAG
logs/metricas.jsonl            Se genera al usar la app (ignorado por git)
```

## Consultas de prueba

| Consulta | Ruta esperada | Tools esperadas |
|---|---|---|
| ¿Qué es el color block? | conceptual | ninguna |
| ¿Qué es la colorimetría estacional? | herramientas | `consultar_guia_colorimetria` |
| Tengo ojos azul claro, cabello rubio ceniza y piel porcelana rosada, ¿qué estación soy? | herramientas | `diagnosticar_estacion`, `consultar_paleta_estacional` |
| ¿Cómo reconozco mi estación en casa? | herramientas | `consultar_guia_colorimetria` |
| ¿Qué chaquetas tengo? | herramientas | `consultar_ropa` |
| ¿Qué significa business casual? | herramientas | `consultar_codigo_vestimenta` |
| Mañana tengo algo, ¿qué me pongo? | herramientas | `obtener_fecha`, `consultar_agenda`, `sugerir_outfit` |
| Hola, me llamo Laura, mis ojos son cafés y mi piel es morena | cualquiera | el perfil se actualiza en la barra lateral |

El modelo decide qué tools usa, así que la lista real puede variar.

## Documentación

- [Arquitectura](docs/arquitectura.md): grafo, estado, nodos, memoria y observabilidad
- [Herramientas y datos](docs/herramientas-y-datos.md): las 9 tools, el algoritmo de diagnóstico, el RAG y los archivos de `data/`
- [Historial de versiones](docs/versiones.md): evolución v1 → v4 y pendientes conocidos

## Equipo

Proyecto del curso *Agentes y Orquestadores de IA*.
Repositorio: [github.com/Ako989/Cromic](https://github.com/Ako989/Cromic)
