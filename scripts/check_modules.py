import csv
from collections import defaultdict

tables = {}
fks = []

with open('schema_dump.tsv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    header = next(reader)
    for row in reader:
        if not row or len(row) < 4:
            continue
        schema = row[0].strip('"')
        table = row[1].strip('"')
        if table == 'tabla':
            continue
        pos = row[2].strip('"') if len(row) > 2 else ''
        attr = row[3].strip('"') if len(row) > 3 else ''
        tipo = row[4].strip('"') if len(row) > 4 else ''
        pk = (row[8].strip('"') if len(row) > 8 else '') == 'PK'
        fk = (row[9].strip('"') if len(row) > 9 else '') == 'FK'
        ref_table = row[10].strip('"') if len(row) > 10 else ''
        ref_attr = row[11].strip('"') if len(row) > 11 else ''

        if table not in tables:
            tables[table] = []
        tables[table].append({
            'attr': attr,
            'tipo': tipo,
            'pk': pk,
            'fk': fk,
            'ref_table': ref_table,
            'ref_attr': ref_attr
        })
        if fk and ref_table:
            fks.append({
                'from_table': table,
                'from_col': attr,
                'to_table': ref_table,
                'to_col': ref_attr
            })

print(f"Total tables: {len(tables)}, Total FK relationships: {len(fks)}")

# Check isolated tables vs connected tables
connected_tables = set()
for r in fks:
    connected_tables.add(r['from_table'])
    connected_tables.add(r['to_table'])

isolated = set(tables.keys()) - connected_tables
print(f"Isolated tables ({len(isolated)}): {isolated}")

# Define modules/clusters
modules = {
    "1. SEGURIDAD, USUARIOS Y SAAS": [
        "t_persona", "t_usuario", "t_seguridad_usuario", "t_rol", "t_permiso", "t_rol_permiso",
        "t_modulo", "t_bitacora", "t_empresa",
        "t_plan_suscripcion", "t_plan_precio_saas", "t_plan_suscripcion_historial",
        "t_suscripcion_empresa", "t_suscripcion_cupo", "t_suscripcion_historial",
        "t_suscripcion_ia_uso", "t_pago_suscripcion"
    ],
    "2. GESTION DE OBRAS Y PROYECTOS": [
        "t_obra", "t_tipo_obra", "t_detalle_obra", "t_estructura_obra", "t_obra_usuario",
        "t_avance_obra", "t_consulta_tecnica", "t_consulta_tecnica_respuesta", "t_consulta_tecnica_historial",
        "t_incidencia", "t_incidencia_evidencia", "t_incidencia_seguimiento", "t_incidencia_orden_trabajo"
    ],
    "3. PLANIFICACION Y CRONOGRAMAS": [
        "t_cronograma", "t_cronograma_actividad", "t_cronograma_dependencia"
    ],
    "4. PRESUPUESTOS, APU Y ESTIMACIONES": [
        "t_unidad_medida", "t_presupuesto", "t_partida_presupuesto",
        "t_analisis_precio_unitario", "t_analisi_precio_unitario_insumo",
        "t_estimacion", "t_estimacion_analisis_precio_unitario", "t_parametro_estimacion", "t_obra_estimacion",
        "t_apu_detalle_mano_obra_archivo", "t_apu_legacy_archive"
    ],
    "5. CONTROL DE COSTOS Y ORDENES": [
        "t_control_costo_obra", "t_costo_ejecutado", "t_costo_ejecutado_legacy",
        "t_orden_cambio", "t_orden_cambio_detalle", "t_orden_cambio_historial",
        "t_orden_trabajo", "t_orden_trabajo_usuario", "t_orden_trabajo_permiso", "t_usuario_orden_trabajo_permiso"
    ],
    "6. MANO DE OBRA Y JORNADAS": [
        "t_mano_obra", "t_salario_trabajador", "t_jornada_trabajador_obra", "t_cu32_mano_obra_cierre"
    ],
    "7. MATERIALES, COMPRAS Y ALMACEN": [
        "t_categoria_material", "t_material_base", "t_material", "t_material_caracteristica",
        "t_materiales_almacen", "t_movimiento_almacen",
        "t_proveedor", "t_proveedor_material",
        "t_orden_compra", "t_orden_compra_detalle", "t_recepcion_compra", "t_recepcion_compra_detalle",
        "t_equipo", "t_equipo_maquinaria", "t_equipo_maquinaria_obra"
    ],
    "8. INMOBILIARIA, UNIDADES Y CRM": [
        "t_unidad_construccion", "t_modelo_unidad", "t_modelo_caracteristica",
        "t_unidad_ambiente", "t_unidad_caracteristica", "t_unidad_material",
        "t_unidad_personalizacion", "t_unidad_seguimiento",
        "t_crm_cliente", "t_crm_cliente_unidad", "t_crm_interaccion"
    ],
    "9. REPORTES, ASISTENTE IA Y NOTIFICACIONES": [
        "notificacion", "t_asistente_conversacion", "t_asistente_mensaje",
        "t_reporte_ejecucion", "t_reporte_archivo", "t_reporte_envio",
        "t_reporte_programacion", "t_reporte_programacion_destinatario"
    ]
}

categorized = set()
for mod, t_list in modules.items():
    for t in t_list:
        categorized.add(t)

all_tables = set(tables.keys())
missing = all_tables - categorized
print(f"Missing from modules ({len(missing)}): {missing}")
print(f"Total in modules: {len(categorized)}")

