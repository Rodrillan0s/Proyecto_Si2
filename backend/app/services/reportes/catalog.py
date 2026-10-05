from dataclasses import dataclass


@dataclass(frozen=True)
class Definition:
    id: str
    titulo: str
    permiso: str
    aliases: tuple[str, ...]
    descripcion: str
    obra: bool = False
    actores: tuple[str, ...] = ()
    fecha: bool = False
    fecha_campo: str = ''
    permisos_extra: tuple[str, ...] = ()


REGISTRY = {d.id: d for d in (
    Definition("presupuestario", "Reporte presupuestario", "Visualizar_estimaciones", ("presupuesto", "estimaciones", "reporte presupuestario"), "Versiones de estimaciones por obra y moneda."),
    Definition("comparativo_costos", "Comparativo de costos", "Visualizar_control_costos", ("costos", "desvios", "comparativo de costos", "gastos"), "Comparación acumulada CU17 con línea base activa; no es un flujo de caja.", True),
    Definition("stock", "Stock de materiales", "Visualizar_inventario", ("stock", "inventario", "existencias", "materiales disponibles"), "Existencias actuales y mínimos por material."),
    Definition("consumo_materiales", "Salidas de materiales", "Visualizar_inventario", ("consumo de materiales", "salidas de materiales", "materiales consumidos"), "Salidas registradas a órdenes de trabajo; no acredita consumo físico.", fecha=True),
    Definition("asignacion_personal", "Asignación de personal", "Visualizar_obras", ("asignacion de personal", "personal", "trabajadores"), "Asignaciones vigentes a obras, sin datos de contacto.", actores=("trabajador",)),
    Definition("utilizacion_personal", "Carga de personal", "Visualizar_obras", ("utilizacion de personal", "carga de personal", "carga de trabajo"), "Cantidad de OT asignadas; no mide horas ni productividad.", actores=("trabajador",)),
    Definition("avance_ejecutivo", "Avance ejecutivo", "Visualizar_avances", ("avance", "avance ejecutivo", "progreso", "estado del proyecto"), "Último avance físico registrado por unidad; promedio sin ponderación.", actores=("CLIENTE",)),
    Definition("estado_unidades", "Estado de unidades", "Visualizar_avances", ("unidades", "estado de unidades", "viviendas", "casas"), "Estado actual de las unidades en obras accesibles.", actores=("CLIENTE",)),
    Definition("incidencias", "Reporte de incidencias", "Visualizar_incidencias", ("incidencias", "problemas", "incidentes"), "Incidencias y prioridad por obra.", actores=("trabajador",), fecha=True),
    Definition("incidencias_criticas", "Incidencias críticas", "Visualizar_incidencias", ("incidencias criticas", "problemas criticos", "incidentes graves", "incidencias urgentes", "problemas graves"), "Incidencias de prioridad CRITICA.", actores=("trabajador",), fecha=True),
)}

# Fecha significa el registro indicado, nunca una reconstrucción de estado histórico.
from dataclasses import replace
for key, label in {
    'presupuestario': 'Fecha de creación de la estimación',
    'asignacion_personal': 'Fecha de asignación a la obra',
    'utilizacion_personal': 'Fecha de inicio de la orden de trabajo',
    'avance_ejecutivo': 'Último avance registrado dentro del período',
    'consumo_materiales': 'Fecha de salida del almacén',
    'incidencias': 'Fecha de creación de la incidencia',
    'incidencias_criticas': 'Fecha de creación de la incidencia',
}.items():
    REGISTRY[key] = replace(REGISTRY[key], fecha=True, fecha_campo=label)
REGISTRY['costos_periodo'] = Definition('costos_periodo', 'Costos registrados por período',
    'Visualizar_control_costos', ('costos por periodo', 'gastos por periodo', 'costos registrados', 'gastos del mes'),
    'Costos REGISTRADO de la línea base activa por obra y moneda; excluye anulados.',
    fecha=True, fecha_campo='Fecha del costo ejecutado')
REGISTRY['saldo_comercial'] = Definition('saldo_comercial', 'Saldo comercial estimado por obra',
    'Visualizar_control_costos', ('ganancias', 'ganancia', 'rentabilidad', 'utilidades', 'saldo comercial', 'obras rentables', 'perdidas'),
    'Montos pactados VENDIDO/ENTREGADO menos costos registrados de la línea base activa. No acredita cobros ni ganancias reales.',
    permisos_extra=('Visualizar_clientes',))

# Esquemas estables para presentación y resultados vacíos; no contienen campos de acceso.
FIELDS = {
    'stock': 'id_material codigo nombre_material descripcion id_categoria categoria_nombre id_unidad_medida unidad_nombre unidad_abreviatura precio stock_actual stock_minimo valor_total estado_stock',
    'comparativo_costos': 'id_partida_presupuestaria item_codigo partida unidad cantidad_presupuestada costo_directo_unitario costo_presupuestado impacto_ordenes_aprobadas presupuesto_revisado costo_ejecutado nueva_partida variacion_original variacion_original_porcentaje variacion_revisada variacion_revisada_porcentaje id_obra moneda',
    'presupuestario': 'id_estimacion id_obra obra moneda nombre version estado monto_total created_at',
    'estado_unidades': 'id_unidad id_obra obra codigo tipo_unidad estado superficie',
    'avance_ejecutivo': 'id_unidad id_obra obra codigo estado porcentaje_avance fecha_registro',
    'asignacion_personal': 'id_obra obra id_usuario nombre_completo nombre_rol fecha_asignacion',
    'utilizacion_personal': 'id_obra obra id_usuario nombre_completo orden_nro tipo_trab estado fecha_inicio fecha_fin',
    'consumo_materiales': 'id_obra obra id_movimiento fecha_movimiento id_material nombre_material cantidad_asignada tipo_movimiento orden_nro',
    'incidencias': 'id_incidencia id_obra obra id_unidad titulo prioridad estado created_at',
    'incidencias_criticas': 'id_incidencia id_obra obra id_unidad titulo prioridad estado created_at',
    'costos_periodo': 'id_costo_ejecutado id_obra obra moneda fecha concepto categoria cantidad costo_unitario monto estado',
    'saldo_comercial': 'id_obra obra moneda unidades_vendidas ventas_sin_monto monto_pactado costos_registrados saldo_estimado estado',
}

WORKERS = {"ELECTRICO", "PLOMERO", "MAESTROALBAÑIL", "ALBAÑIL"}
