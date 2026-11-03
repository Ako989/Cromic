# Herramientas y datos

Todas las tools se definen con `@tool` de LangChain y se registran en
`tools/__init__.py` dentro de `TOOLS_CROMIC`. El nodo `agente_cromic` las
recibe con `bind_tools` y el nodo `herramientas` las ejecuta con `ToolNode`.

## Resumen de tools

| Tool | Archivo | Parámetros | Fuente de datos |
|---|---|---|---|
| `obtener_fecha` | `fecha_tool.py` | — | reloj del sistema |
| `consultar_agenda` | `agenda_tool.py` | `consulta="todos"` | `data/agenda.json` |
| `consultar_codigo_vestimenta` | `codigo_vestimenta_tool.py` | `consulta` | `data/codigos_vestimenta.json` |
| `consultar_paleta_colores` | `paleta_tool.py` | `color_piel` | `data/paletas.json` |
| `consultar_ropa` | `ropa_tool.py` | `consulta="todas"` | `data/ropa.json` |
| `sugerir_outfit` | `ropa_tool.py` | `ocasion`, `perfil=""` | `data/ropa.json` + chain LLM |
| `diagnosticar_estacion` | `colorimetria_tool.py` | `ojos`, `cabello`, `piel`, `contraste`, `venas`, `joyeria` | `data/colorimetria_rasgos.json`, `data/colorimetria_estaciones.json` |
| `consultar_paleta_estacional` | `colorimetria_tool.py` | `estacion` | `data/colorimetria_estaciones.json` |
| `consultar_guia_colorimetria` | `guia_tool.py` | `pregunta` | `data/guia_colorimetria.md` (RAG) |

## Detalle por tool

### `obtener_fecha()`
Devuelve `{fecha: "AAAA-MM-DD", dia: "lunes"…, hora: "HH:MM"}`. El agente la
usa para resolver expresiones como "mañana" o "este sábado" antes de
consultar la agenda.

### `consultar_agenda(consulta="todos")`
Filtra los eventos cuya `fecha`, `evento` o `lugar` contengan el texto. Con
`""`, `todos`, `todo` o `*` devuelve todos.
Retorna `{consulta, resultados, cantidad}`.

### `consultar_codigo_vestimenta(consulta)`
Busca en `codigo` y `descripcion`. Los códigos disponibles son `casual`,
`business casual`, `cocktail` y `formal`.
Retorna `{consulta, resultados, cantidad}`.

### `consultar_paleta_colores(color_piel)`
Paleta **simple por tono de piel** (`clara`, `media`, `morena`, `oscura`). Es
distinta de la colorimetría estacional. La coincidencia funciona en ambos
sentidos: "morena" encuentra "morena" y "piel morena" también.
Retorna `{consulta, resultados, cantidad}`.

### `consultar_ropa(consulta="todas")`
Busca el texto en **cualquier campo** de la prenda (nombre, tipo, color,
estilo o clima). Con `""`, `todas`, `todo` o `*` devuelve todo el armario.

### `sugerir_outfit(ocasion, perfil="")`
Es una **chain anidada** dentro de una tool. Carga todo el armario y ejecuta
`chains/outfit_chain.py`, que es `ChatPromptTemplate | Gemini (temp 0.3) |
StrOutputParser`. Devuelve texto con el outfit propuesto y una justificación
breve de cada prenda. Implica **una llamada extra al modelo**.

### `diagnosticar_estacion(ojos, cabello, piel, contraste="", venas="", joyeria="")`

Determina la estación de color con un sistema de votos.

1. **Validación:** si falta `ojos`, `cabello` o `piel`, devuelve
   `{estado: "faltan_datos", faltan: [...]}` para que el agente lo pregunte.
2. **Reconocimiento de rasgos:** el texto se normaliza (minúsculas y sin
   tildes) y se compara con los valores de `colorimetria_rasgos.json`. Los
   valores con " o " se separan ("azul claro o gris" → "azul claro", "gris")
   y gana la coincidencia **más larga** (la más específica). Si un rasgo
   obligatorio no se reconoce, devuelve `estado: "rasgo_no_reconocido"` con
   los valores válidos.
3. **Votos:** cada rasgo reconocido vota en los ejes que define:
   `temperatura` (cálida/fría), `intensidad` (brillante/suave) y
   `profundidad` (clara/profunda).
4. **Puntaje por estación:** suma los votos que coinciden con sus tres ejes:

   | Estación | Temperatura | Intensidad | Profundidad |
   |---|---|---|---|
   | Primavera cálida | cálida | brillante | clara |
   | Verano frío | fría | suave | clara |
   | Otoño cálido | cálida | suave | profunda |
   | Invierno frío | fría | brillante | profunda |

5. **Confianza:** `puntaje_ganador / votos_totales`.
   `≥ 0.75` → alta, `≥ 0.55` → media, si no → baja. Si las dos primeras
   estaciones empatan, se informa la segunda como `alternativa`.

Retorna `{estado: "ok", estacion, nombre, confianza, nivel_confianza,
alternativa, rasgos_usados, rasgos_no_reconocidos}`.

**Ejemplo:** ojos *azul claro* (fría, suave, clara) + cabello *rubio ceniza*
(fría, suave, clara) + piel *porcelana rosada* (fría, clara). Verano recibe
3 + 3 + 2 = 8 de 8 votos → confianza 1.0, alta.

### `consultar_paleta_estacional(estacion)`
Acepta `primavera`, `verano`, `otono`/`otoño`, `invierno` o el nombre
completo ("Verano frío"). Devuelve el registro completo de la estación:
`paleta` y `evitar` con códigos hex, y `vibes`. Si no la encuentra, devuelve
`estado: "no_encontrada"` con las estaciones válidas.

`core/session.py` revisa la respuesta de esta tool para saber qué estación
mostrar como muestras de color bajo el mensaje.

### `consultar_guia_colorimetria(pregunta)` (RAG)

1. **Fragmentación:** `guia_colorimetria.md` se divide en un fragmento por
   cada sección `## …`, con `metadata.seccion` para poder citarla.
2. **Búsqueda vectorial:** `GoogleGenerativeAIEmbeddings`
   (`EMBEDDING_MODEL`) + `InMemoryVectorStore`, top-k = 3. El índice se crea
   en la primera consulta y se guarda en memoria del proceso.
3. **Respaldo léxico:** si falla la búsqueda vectorial (cuota, red o modelo),
   puntúa las secciones por palabras en común (de más de 3 letras) y devuelve
   las 3 mejores. El campo `metodo` indica qué búsqueda se usó.

Retorna `{estado, metodo, fragmentos: [{seccion, texto}]}` o
`estado: "sin_resultados"`.

## Archivos de datos (`data/`)

| Archivo | Registros | Esquema |
|---|---|---|
| `ropa.json` | 10 prendas | `{prenda, tipo, color, estilo, clima}` |
| `agenda.json` | 4 eventos | `{fecha, evento, lugar, codigo}` (el `codigo` enlaza con los códigos de vestimenta) |
| `codigos_vestimenta.json` | 4 códigos | `{codigo, descripcion, recomendado[], evitar[]}` |
| `paletas.json` | 4 tonos de piel | `{tono_piel, subtono, favorecen[], evitar[], nota}` |
| `colorimetria_rasgos.json` | 25 rasgos | `{categoria, valor, temperatura, intensidad, profundidad}` (ejes `null` = no vota) |
| `colorimetria_estaciones.json` | 4 estaciones | `{estacion, nombre, temperatura, intensidad, profundidad, vibes, paleta[{nombre, hex}], evitar[{nombre, hex}]}` |
| `guia_colorimetria.md` | 10 secciones | Markdown; cada `##` es un fragmento del RAG |

Las fechas de `agenda.json` son de octubre de 2026. Para probar consultas
como "mañana tengo algo", ajusta las fechas a días cercanos a la fecha actual.

### Cómo añadir datos

- **Prendas, eventos o códigos:** agrega objetos con el mismo esquema; las
  tools leen el JSON en cada llamada, así que no hace falta reiniciar.
- **Rasgos de colorimetría:** usa una `categoria` existente (`ojos`,
  `cabello`, `piel`, `contraste`, `venas`, `joyeria`). Separa sinónimos con
  " o " y deja en `null` los ejes que el rasgo no indica.
- **Guía RAG:** añade secciones con `## Título`. El índice vectorial se
  construye una vez por proceso, así que **reinicia Streamlit** para que
  incluya los cambios.

## Cómo añadir una tool nueva

1. Crea `tools/mi_tool.py` con una función decorada con `@tool`. El
   *docstring* es lo que lee el modelo para decidir cuándo usarla: explica
   qué hace y qué valores acepta.
2. Impórtala y agrégala a `TOOLS_CROMIC` en `tools/__init__.py`.
3. Si el enrutador debe enviar a `herramientas` las consultas de ese tema,
   menciónalo en `ROUTER_SYSTEM_PROMPT`.
4. Si hay reglas de uso, añádelas al prompt del agente **sin llaves `{}`**.
