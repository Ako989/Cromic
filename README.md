# Cromic v2 · Asesor de vestimenta

Agente de moda con LangChain: un Router Chain (Pydantic) decide si la consulta
se responde con una Response Chain directa o con un Agent con 6 tools. La barra
lateral muestra la ruta elegida, el motivo y las tools ejecutadas.

## Ejecutar

```bash
pip install -r requirements.txt
streamlit run app.py
```

`.env`:

```
GEMINI_API_KEY=TU_API_KEY_REAL
GEMINI_MODEL=gemini-3.5-flash-lite   # opcional
```

## Estructura

```
app.py                      UI + panel de trazabilidad
config/settings.py          API key y modelo
prompts/fashion_prompt.py   prompts del router, chain, agent y outfit
chains/router_chain.py      clasificador chain/agent (RutaConsulta)
chains/response_chain.py    respuesta directa LCEL
chains/outfit_chain.py      chain anidada para armar outfits
tools/fecha_tool.py         obtener_fecha
tools/ropa_tool.py          consultar_ropa, sugerir_outfit (chain anidada)
tools/agenda_tool.py        consultar_agenda
tools/paleta_tool.py        consultar_paleta_colores
tools/codigo_vestimenta_tool.py  consultar_codigo_vestimenta
core/agent.py               router + create_agent
core/state.py               perfil, memoria y última ejecución
data/                       ropa, agenda, paletas, códigos de vestimenta
```

## Consultas de prueba

| Consulta | Ruta | Tools |
|---|---|---|
| ¿Qué es el color block? | Chain | ninguna |
| ¿Qué chaquetas tengo? | Agent | consultar_ropa |
| ¿Qué colores me quedan si tengo piel morena? | Agent | consultar_paleta_colores |
| ¿Qué significa business casual? | Agent | consultar_codigo_vestimenta |
| Mañana tengo algo, ¿qué me pongo? | Agent | obtener_fecha, consultar_agenda, sugerir_outfit |
| Hola, me llamo Laura, mis ojos son cafés y mi piel es morena | Chain/Agent | perfil en la barra lateral |
