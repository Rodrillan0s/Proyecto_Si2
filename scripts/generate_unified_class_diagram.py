import csv
import math
from collections import defaultdict
import resvg_py

# 1. Parse Schema Dump
tables = {}
fks = []

with open('docs/diagramas/schema_dump.tsv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        if not row or len(row) < 4:
            continue
        table = row[1].strip('"')
        if table in ('tabla', '<USER_REQUEST>'):
            continue
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
        if fk and ref_table and ref_table != table:
            fks.append({
                'from_table': table,
                'from_col': attr,
                'to_table': ref_table,
                'to_col': ref_attr
            })

print(f"Total tables: {len(tables)}, Total FK relationships: {len(fks)}")

# Unified 10-column layout matrix placing related entities naturally adjacent
# Total 92 tables across 10 columns
matrix_rows = [
    # Row 0: Plataforma SaaS, Planes y Seguridad Central
    [
        "t_plan_suscripcion", "t_plan_precio_saas", "t_plan_suscripcion_historial",
        "t_suscripcion_empresa", "t_suscripcion_cupo", "t_suscripcion_historial", "t_suscripcion_ia_uso",
        "t_pago_suscripcion", "t_empresa", "t_bitacora"
    ],
    # Row 1: Usuarios, Roles, Permisos y Obras
    [
        "t_rol", "t_rol_permiso", "t_permiso", "t_modulo",
        "t_persona", "t_usuario", "t_seguridad_usuario",
        "t_obra_usuario", "t_tipo_obra", "t_obra"
    ],
    # Row 2: Estructuras de Obra, Detalle, Avance y Consultas Técnicas
    [
        "t_detalle_obra", "t_estructura_obra", "t_avance_obra",
        "t_consulta_tecnica", "t_consulta_tecnica_respuesta", "t_consulta_tecnica_historial",
        "t_incidencia", "t_incidencia_evidencia", "t_incidencia_seguimiento", "t_incidencia_orden_trabajo"
    ],
    # Row 3: Planificación y Cronogramas (CU39) & Mano de Obra (CU32)
    [
        "t_cronograma", "t_cronograma_actividad", "t_cronograma_dependencia",
        "t_mano_obra", "t_salario_trabajador", "t_jornada_trabajador_obra", "t_cu32_mano_obra_cierre",
        "t_orden_trabajo", "t_orden_trabajo_usuario", "t_orden_trabajo_permiso"
    ],
    # Row 4: Control de Costos, Órdenes de Trabajo y Órdenes de Cambio
    [
        "t_usuario_orden_trabajo_permiso", "t_orden_cambio", "t_orden_cambio_detalle", "t_orden_cambio_historial",
        "t_control_costo_obra", "t_costo_ejecutado", "t_costo_ejecutado_legacy",
        "t_presupuesto", "t_partida_presupuesto", "t_unidad_medida"
    ],
    # Row 5: Presupuestos, APU y Estimaciones
    [
        "t_analisis_precio_unitario", "t_analisi_precio_unitario_insumo",
        "t_estimacion", "t_estimacion_analisis_precio_unitario", "t_parametro_estimacion", "t_obra_estimacion",
        "t_apu_detalle_mano_obra_archivo", "t_apu_legacy_archive",
        "t_categoria_material", "t_material_base"
    ],
    # Row 6: Materiales, Catálogo, Almacén y Movimientos
    [
        "t_material", "t_material_caracteristica", "t_materiales_almacen", "t_movimiento_almacen",
        "t_proveedor", "t_proveedor_material",
        "t_orden_compra", "t_orden_compra_detalle", "t_recepcion_compra", "t_recepcion_compra_detalle"
    ],
    # Row 7: Maquinaria, Equipos y Unidades de Construcción
    [
        "t_equipo", "t_equipo_maquinaria", "t_equipo_maquinaria_obra",
        "t_modelo_unidad", "t_modelo_caracteristica", "t_unidad_construccion",
        "t_unidad_ambiente", "t_unidad_caracteristica", "t_unidad_material", "t_unidad_personalizacion"
    ],
    # Row 8: CRM Inmobiliario, Clientes, Reportes y Asistente IA
    [
        "t_unidad_seguimiento", "t_crm_cliente", "t_crm_cliente_unidad", "t_crm_interaccion",
        "notificacion", "t_asistente_conversacion", "t_asistente_mensaje",
        "t_reporte_ejecucion", "t_reporte_archivo", "t_reporte_envio"
    ],
    # Row 9: Programación de Reportes
    [
        "t_reporte_programacion", "t_reporte_programacion_destinatario"
    ]
]

# Verify all 92 tables are present in matrix
flattened = [t for row in matrix_rows for t in row]
print(f"Total tables in matrix: {len(flattened)}")
diff = set(tables.keys()) - set(flattened)
print(f"Missing from matrix: {diff}")

# Parameters for UML styling
card_w = 260
line_h = 20
header_h = 32
gap_x = 65
gap_y = 55
margin_x = 60
margin_y = 90
n_cols = 10

# Calculate heights and positions
row_heights = defaultdict(int)
table_positions = {}

for r_idx, row in enumerate(matrix_rows):
    for c_idx, t_name in enumerate(row):
        cols = tables.get(t_name, [])
        h = header_h + len(cols) * line_h + 10
        table_positions[t_name] = {
            'row': r_idx,
            'col': c_idx,
            'w': card_w,
            'h': h,
            'cols': cols
        }
        if h > row_heights[r_idx]:
            row_heights[r_idx] = h

total_w = margin_x * 2 + n_cols * card_w + (n_cols - 1) * gap_x
curr_y = margin_y

for r_idx in range(len(matrix_rows)):
    for t_name, pos in table_positions.items():
        if pos['row'] == r_idx:
            pos['x'] = margin_x + pos['col'] * (card_w + gap_x)
            pos['y'] = curr_y
    curr_y += row_heights[r_idx] + gap_y

total_h = curr_y + 40

print(f"Unified Canvas Dimensions: {total_w} x {total_h}")

# Render SVG
svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">')

# Background: Crisp white/clean canvas
svg.append(f'<rect width="{total_w}" height="{total_h}" fill="#FAFAFA"/>')

# Top Header Banner
svg.append(f'<rect x="0" y="0" width="{total_w}" height="65" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5"/>')
svg.append(f'<text x="{margin_x}" y="41" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="bold" fill="#0F172A" letter-spacing="0.5">DIAGRAMA GENERAL DE CLASES Y MODELO RELACIONAL (ESQUEMA OBRAS)</text>')
svg.append(f'<text x="{total_w - margin_x}" y="41" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="500" fill="#64748B">OBRATEC · 92 Clases / Tablas · 194 Relaciones Foráneas</text>')

# Draw Relationship Connectors
# To keep diagram clean and lines distinct, route with smooth cubic bezier or orthogonal paths
for fk in fks:
    t_from = fk['from_table']
    t_to = fk['to_table']
    if t_from in table_positions and t_to in table_positions:
        b_from = table_positions[t_from]
        b_to = table_positions[t_to]

        from_cx = b_from['x'] + b_from['w'] / 2.0
        from_cy = b_from['y'] + b_from['h'] / 2.0
        to_cx = b_to['x'] + b_to['w'] / 2.0
        to_cy = b_to['y'] + b_to['h'] / 2.0

        # Choose best ports
        dx = to_cx - from_cx
        dy = to_cy - from_cy

        if abs(dx) > abs(dy):
            if dx > 0:
                p_from = (b_from['x'] + b_from['w'], from_cy)
                p_to = (b_to['x'], to_cy)
                card_from = (p_from[0] + 6, p_from[1] - 4, "0..*")
                card_to = (p_to[0] - 16, p_to[1] - 4, "1")
            else:
                p_from = (b_from['x'], from_cy)
                p_to = (b_to['x'] + b_to['w'], to_cy)
                card_from = (p_from[0] - 22, p_from[1] - 4, "0..*")
                card_to = (p_to[0] + 6, p_to[1] - 4, "1")
            
            mid_x = (p_from[0] + p_to[0]) / 2.0
            path_d = f"M {p_from[0]} {p_from[1]} C {mid_x} {p_from[1]}, {mid_x} {p_to[1]}, {p_to[0]} {p_to[1]}"
        else:
            if dy > 0:
                p_from = (from_cx, b_from['y'] + b_from['h'])
                p_to = (to_cx, b_to['y'])
                card_from = (p_from[0] + 5, p_from[1] + 13, "0..*")
                card_to = (p_to[0] + 5, p_to[1] - 6, "1")
            else:
                p_from = (from_cx, b_from['y'])
                p_to = (to_cx, b_to['y'] + b_to['h'])
                card_from = (p_from[0] + 5, p_from[1] - 6, "0..*")
                card_to = (p_to[0] + 5, p_to[1] + 13, "1")

            mid_y = (p_from[1] + p_to[1]) / 2.0
            path_d = f"M {p_from[0]} {p_from[1]} C {p_from[0]} {mid_y}, {p_to[0]} {mid_y}, {p_to[0]} {p_to[1]}"

        # Render connection path
        svg.append(f'<path d="{path_d}" fill="none" stroke="#64748B" stroke-width="1.1" stroke-opacity="0.85"/>')
        svg.append(f'<text x="{card_from[0]}" y="{card_from[1]}" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#334155">{card_from[2]}</text>')
        svg.append(f'<text x="{card_to[0]}" y="{card_to[1]}" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#334155">{card_to[2]}</text>')

# Render Table Cards (UML Class style matching user reference image)
for t_name, pos in table_positions.items():
    x, y, w, h = pos['x'], pos['y'], pos['w'], pos['h']
    cols = pos['cols']

    # 1. Drop shadow
    svg.append(f'<rect x="{x+2}" y="{y+3}" width="{w}" height="{h}" fill="#000000" fill-opacity="0.14"/>')
    # 2. Main white box with clean solid border
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFFFF" stroke="#222222" stroke-width="1.2"/>')

    # 3. Small UML class/table icon in top-left
    svg.append(f'<g transform="translate({x+8}, {y+9})">')
    svg.append('<rect x="0" y="0" width="13" height="11" fill="#FFFFFF" stroke="#444444" stroke-width="1"/>')
    svg.append('<line x1="0" y1="4" x2="13" y2="4" stroke="#444444" stroke-width="1"/>')
    svg.append('</g>')

    # 4. Class/Table title (centered, uppercase, bold)
    title_str = t_name.upper()
    svg.append(f'<text x="{x + w/2.0}" y="{y+21}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="bold" fill="#000000" letter-spacing="0.3">{title_str}</text>')

    # 5. Divider line below header
    svg.append(f'<line x1="{x}" y1="{y+header_h}" x2="{x+w}" y2="{y+header_h}" stroke="#222222" stroke-width="1.2"/>')

    # 6. Attributes list with '+' visibility indicator
    curr_attr_y = y + header_h + 16
    for c in cols:
        attr_name = c['attr']
        pk_badge = ""
        fk_badge = ""
        font_weight = "normal"
        fill_col = "#111111"

        if c['pk']:
            pk_badge = " [PK]"
            font_weight = "bold"
            fill_col = "#002B66"
        elif c['fk']:
            fk_badge = " [FK]"
            fill_col = "#334155"

        text_str = f"+ {attr_name}{pk_badge}{fk_badge}"
        svg.append(f'<text x="{x+10}" y="{curr_attr_y}" font-family="Arial, Helvetica, sans-serif" font-size="11.5" font-weight="{font_weight}" fill="{fill_col}">{text_str}</text>')
        curr_attr_y += line_h

svg.append('</svg>')
svg_content = "\n".join(svg)

# Save SVG
svg_path = "docs/diagramas/diagrama_clases_completo.svg"
with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg_content)
print(f"Unified diagram SVG saved to {svg_path} ({len(svg_content)} chars)")

# Render High-Resolution PNG with resvg_py
print("Rendering unified PNG with resvg_py...")
png_bytes = resvg_py.svg_to_bytes(svg_content)
png_path = "docs/diagramas/diagrama_clases_completo.png"
with open(png_path, "wb") as f:
    f.write(png_bytes)
print(f"Unified diagram PNG saved to {png_path} ({len(png_bytes)} bytes)")

