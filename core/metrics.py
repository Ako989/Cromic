"""Observabilidad: mide tiempos, llamadas al modelo, tokens, tools y errores."""

import time

from langchain_core.callbacks import BaseCallbackHandler

NODOS = {"enrutador", "nodo_conceptual", "agente_cromic", "herramientas"}


class MetricasCallback(BaseCallbackHandler):
    """Se pasa al grafo en config['callbacks'] y acumula métricas de un turno."""

    def __init__(self) -> None:
        self.inicio = time.perf_counter()
        self.llamadas_modelo = 0
        self.tokens_entrada = 0
        self.tokens_salida = 0
        self.tools: list[str] = []
        self.errores: list[str] = []
        self.tiempos_nodos: list[dict] = []
        self._nodos_abiertos: dict = {}

    # --- modelo ---
    def on_chat_model_start(self, serialized, messages, **kwargs) -> None:
        self.llamadas_modelo += 1

    def on_llm_end(self, response, **kwargs) -> None:
        for generaciones in response.generations:
            for gen in generaciones:
                mensaje = getattr(gen, "message", None)
                uso = getattr(mensaje, "usage_metadata", None) or {}
                self.tokens_entrada += uso.get("input_tokens", 0)
                self.tokens_salida += uso.get("output_tokens", 0)

    def on_llm_error(self, error, **kwargs) -> None:
        self.errores.append(f"modelo: {str(error)[:200]}")

    # --- tools ---
    def on_tool_start(self, serialized, input_str, **kwargs) -> None:
        nombre = kwargs.get("name") or (serialized or {}).get("name", "tool")
        self.tools.append(nombre)

    def on_tool_error(self, error, **kwargs) -> None:
        self.errores.append(f"tool: {str(error)[:200]}")

    # --- nodos del grafo ---
    def on_chain_start(self, serialized, inputs, *, run_id, **kwargs) -> None:
        nombre = kwargs.get("name")
        if nombre in NODOS:
            self._nodos_abiertos[run_id] = (nombre, time.perf_counter())

    def on_chain_end(self, outputs, *, run_id, **kwargs) -> None:
        abierto = self._nodos_abiertos.pop(run_id, None)
        if abierto:
            nombre, t0 = abierto
            self.tiempos_nodos.append(
                {"nodo": nombre, "segundos": round(time.perf_counter() - t0, 2)}
            )

    def on_chain_error(self, error, *, run_id, **kwargs) -> None:
        self._nodos_abiertos.pop(run_id, None)

    # --- resultado ---
    def resumen(self) -> dict:
        return {
            "tiempo_total_s": round(time.perf_counter() - self.inicio, 2),
            "llamadas_modelo": self.llamadas_modelo,
            "tokens_entrada": self.tokens_entrada,
            "tokens_salida": self.tokens_salida,
            "tokens_total": self.tokens_entrada + self.tokens_salida,
            "tools": self.tools,
            "tiempos_nodos": self.tiempos_nodos,
            "errores": self.errores,
        }