from tools.agenda_tool import consultar_agenda
from tools.codigo_vestimenta_tool import consultar_codigo_vestimenta
from tools.fecha_tool import obtener_fecha
from tools.paleta_tool import consultar_paleta_colores
from tools.ropa_tool import consultar_ropa, sugerir_outfit

TOOLS_CROMIC = [
    obtener_fecha,
    consultar_agenda,
    consultar_codigo_vestimenta,
    consultar_paleta_colores,
    consultar_ropa,
    sugerir_outfit,
]