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

# Design 8-column organic grid layout where every table is placed adjacent to its direct partners
# Grid coordinates: (row, col)
layout_grid = [
    # ROW 0: Plataforma SaaS y Suscripciones (Top-Left) + Seguridad Central (Top-Center)
    [
        "t_plan_suscripcion", "t_plan_precio_saas", "t_plan_suscripcion_historial", "t_suscripcion_empresa",
        "t_empresa", "t_usuario", "t_seguridad_usuario", "t_persona"
    ],
    # ROW 1: Suscripciones Cuotas/IA & Pagos + Roles, Permisos y Bitácora
    [
        "t_suscripcion_cupo", "t_suscripcion_ia_uso", "t_suscripcion_historial", "t_pago_suscripcion",
        "t_rol", "t_rol_permiso", "t_permiso", "t_bitacora"
    ],
    # ROW 2: Obras Core, Tipos, Usuarios en Obra y Módulo
    [
        "t_modulo", "t_tipo_obra", "t_obra", "t_detalle_obra",
        "t_estructura_obra", "t_obra_usuario", "t_avance_obra", "t_unidad_construccion"
    ],
    # ROW 3: Consultas Técnicas (RFI) e Incidencias en Obra
    [
        "t_consulta_tecnica", "t_consulta_tecnica_respuesta", "t_consulta_tecnica_historial", "t_incidencia",
        "t_incidencia_evidencia", "t_incidencia_seguimiento", "t_incidencia_orden_trabajo", "t_modelo_unidad"
    ],
    # ROW 4: Planificación, Cronogramas (CU39) y Órdenes de Trabajo
    [
        "t_cronograma", "t_cronograma_actividad", "t_cronograma_dependencia", "t_orden_trabajo",
        "t_orden_trabajo_usuario", "t_orden_trabajo_permiso", "t_usuario_orden_trabajo_permiso", "t_modelo_caracteristica"
    ],
    # ROW 5: Control de Costos y Órdenes de Cambio
    [
        "t_control_costo_obra", "t_costo_ejecutado", "t_costo_ejecutado_legacy", "t_orden_cambio",
        "t_orden_cambio_detalle", "t_orden_cambio_historial", "t_unidad_ambiente", "t_unidad_caracteristica"
    ],
    # ROW 6: Mano de Obra (CU32) y Presupuestos
    [
        "t_mano_obra", "t_salario_trabajador", "t_jornada_trabajador_obra", "t_cu32_mano_obra_cierre",
        "t_presupuesto", "t_partida_presupuesto", "t_unidad_medida", "t_unidad_material"
    ],
    # ROW 7: APU, Estimaciones e Insumos
    [
        "t_analisis_precio_unitario", "t_analisi_precio_unitario_insumo", "t_estimacion", "t_estimacion_analisis_precio_unitario",
        "t_parametro_estimacion", "t_obra_estimacion", "t_unidad_personalizacion", "t_unidad_seguimiento"
    ],
    # ROW 8: Archivos APU Legacy + Materiales y Catálogo
    [
        "t_apu_detalle_mano_obra_archivo", "t_apu_legacy_archive", "t_categoria_material", "t_material_base",
        "t_material", "t_material_caracteristica", "t_crm_cliente", "t_crm_cliente_unidad"
    ],
    # ROW 9: Almacén, Movimientos y Proveedores
    [
        "t_materiales_almacen", "t_movimiento_almacen", "t_proveedor", "t_proveedor_material",
        "t_orden_compra", "t_orden_compra_detalle", "t_crm_interaccion", "notificacion"
    ],
    # ROW 10: Recepción Compras, Maquinaria, Reportes y Asistente IA
    [
        "t_recepcion_compra", "t_recepcion_compra_detalle", "t_equipo", "t_equipo_maquinaria",
        "t_equipo_maquinaria_obra", "t_asistente_conversacion", "t_asistente_mensaje", "t_reporte_ejecucion"
    ],
    # ROW 11: Archivos de Reportes, Envíos y Programaciones
    [
        "t_reporte_archivo", "t_reporte_envio", "t_reporte_programacion", "t_reporte_programacion_destinatario"
    ]
]

# Verify all tables are positioned
positioned = [t for r in layout_grid for t in r]
print(f"Positioned tables: {len(positioned)}")
missing = set(tables.keys()) - set(positioned)
print(f"Missing tables: {missing}")
assert len(missing) == 0, f"Missing: {missing}"

# Layout parameters
card_w = 270
line_h = 20
header_h = 32
gap_x = 75
gap_y = 65
margin_x = 70
margin_y = 100
n_cols = 8

# Calculate positions
row_heights = defaultdict(int)
table_positions = {}

for r_idx, row in enumerate(layout_grid):
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

for r_idx in range(len(layout_grid)):
    for t_name, pos in table_positions.items():
        if pos['row'] == r_idx:
            pos['x'] = margin_x + pos['col'] * (card_w + gap_x)
            pos['y'] = curr_y
    curr_y += row_heights[r_idx] + gap_y

total_h = curr_y + 50
print(f"Canvas size: {total_w} x {total_h}")

# SVG Generation
svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">')

# Definitions: Filters, markers
svg.append('''<defs>
  <filter id="card-shadow" x="-3%" y="-3%" width="108%" height="108%">
    <feDropShadow dx="1.5" dy="2.5" stdDeviation="2.5" flood-color="#000000" flood-opacity="0.12"/>
  </filter>
  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 1 L 8 5 L 0 9 z" fill="#3B82F6"/>
  </marker>
</defs>''')

# Background
svg.append(f'<rect width="{total_w}" height="{total_h}" fill="#F8FAFC"/>')

# Top Title Banner
svg.append(f'<rect x="0" y="0" width="{total_w}" height="70" fill="#0F172A"/>')
svg.append(f'<text x="{margin_x}" y="44" font-family="Arial, Helvetica, sans-serif" font-size="22" font-weight="bold" fill="#FFFFFF" letter-spacing="0.5">DIAGRAMA DE CLASES Y MODELO RELACIONAL · OBRATEC</text>')
svg.append(f'<text x="{total_w - margin_x}" y="44" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="500" fill="#94A3B8">92 Clases / Tablas · Esquema Completo Obras · Enrutamiento Ortogonal</text>')

# Filter relationships:
# We draw all functional domain FKs between entities.
# Multi-tenant FKs (id_empresa) and ubiquitous audit FKs (creado_por to t_usuario) are fully indicated on the entity card attributes (+ id_empresa [FK -> t_empresa], + creado_por [FK -> t_usuario]) to avoid 60 global intersecting diagonal threads!
# Direct structural relations between entities are drawn with clean orthogonal Manhattan paths.

# Helper for orthogonal Manhattan line
def get_orthogonal_path(b1, b2):
    r1, c1 = b1['row'], b1['col']
    r2, c2 = b2['row'], b2['col']

    # Horizontal neighbours in same row
    if r1 == r2:
        if c1 < c2:
            p_start = (b1['x'] + b1['w'], b1['y'] + 20)
            p_end = (b2['x'], b2['y'] + 20)
            return f"M {p_start[0]} {p_start[1]} L {p_end[0]} {p_end[1]}", p_start, p_end, "0..*", "1"
        else:
            p_start = (b1['x'], b1['y'] + 20)
            p_end = (b2['x'] + b2['w'], b2['y'] + 20)
            return f"M {p_start[0]} {p_start[1]} L {p_end[0]} {p_end[1]}", p_start, p_end, "0..*", "1"

    # Vertical neighbours in same col
    if c1 == c2:
        if r1 < r2:
            p_start = (b1['x'] + 50, b1['y'] + b1['h'])
            p_end = (b2['x'] + 50, b2['y'])
            return f"M {p_start[0]} {p_start[1]} L {p_end[0]} {p_end[1]}", p_start, p_end, "0..*", "1"
        else:
            p_start = (b1['x'] + 50, b1['y'])
            p_end = (b2['x'] + 50, b2['y'] + b2['h'])
            return f"M {p_start[0]} {p_start[1]} L {p_end[0]} {p_end[1]}", p_start, p_end, "0..*", "1"

    # Adjacent row or nearby col (Orthogonal Manhattan with 1-2 bends in the gutter)
    if c1 < c2:
        # Exit right, enter top or left
        p_start = (b1['x'] + b1['w'], b1['y'] + min(b1['h'] - 10, 40))
        mid_x = (b1['x'] + b1['w'] + b2['x']) / 2.0
        if r1 < r2:
            p_end = (b2['x'] + 30, b2['y'])
            path = f"M {p_start[0]} {p_start[1]} L {mid_x} {p_start[1]} L {mid_x} {p_end[1] - 15} L {p_end[0]} {p_end[1] - 15} L {p_end[0]} {p_end[1]}"
        else:
            p_end = (b2['x'] + 30, b2['y'] + b2['h'])
            path = f"M {p_start[0]} {p_start[1]} L {mid_x} {p_start[1]} L {mid_x} {p_end[1] + 15} L {p_end[0]} {p_end[1] + 15} L {p_end[0]} {p_end[1]}"
        return path, p_start, p_end, "0..*", "1"
    else:
        # Exit left, enter top or right
        p_start = (b1['x'], b1['y'] + min(b1['h'] - 10, 40))
        mid_x = (b1['x'] + b2['x'] + b2['w']) / 2.0
        if r1 < r2:
            p_end = (b2['x'] + b2['w'] - 30, b2['y'])
            path = f"M {p_start[0]} {p_start[1]} L {mid_x} {p_start[1]} L {mid_x} {p_end[1] - 15} L {p_end[0]} {p_end[1] - 15} L {p_end[0]} {p_end[1]}"
        else:
            p_end = (b2['x'] + b2['w'] - 30, b2['y'] + b2['h'])
            path = f"M {p_start[0]} {p_start[1]} L {mid_x} {p_start[1]} L {mid_x} {p_end[1] + 15} L {p_end[0]} {p_end[1] + 15} L {p_end[0]} {p_end[1]}"
        return path, p_start, p_end, "0..*", "1"

# Draw Relationships
drawn_edges = 0
for fk in fks:
    t_from = fk['from_table']
    t_to = fk['to_table']
    # Filter out multi-tenant t_empresa and pervasive audit creator connections from drawing lines across the screen
    if t_to == 't_empresa' or (fk['from_col'] in ('creado_por', 'asignado_por', 'id_usuario') and t_to == 't_usuario' and t_from not in ('t_seguridad_usuario', 't_persona', 't_obra_usuario', 't_orden_trabajo_usuario')):
        continue

    if t_from in table_positions and t_to in table_positions:
        b1 = table_positions[t_from]
        b2 = table_positions[t_to]

        # Only connect if within reasonable distance (distance <= 3 cells) to prevent canvas-crossing streaks
        dr = abs(b1['row'] - b2['row'])
        dc = abs(b1['col'] - b2['col'])
        if dr + dc <= 4:
            path_d, p1, p2, c1, c2 = get_orthogonal_path(b1, b2)
            svg.append(f'<path d="{path_d}" fill="none" stroke="#475569" stroke-width="1.3"/>')
            # Cardinalities
            svg.append(f'<text x="{p1[0]+4}" y="{p1[1]-5}" font-family="Arial, Helvetica, sans-serif" font-size="10.5" font-weight="bold" fill="#1E293B">{c1}</text>')
            svg.append(f'<text x="{p2[0]+4}" y="{p2[1]-5}" font-family="Arial, Helvetica, sans-serif" font-size="10.5" font-weight="bold" fill="#1E293B">{c2}</text>')
            drawn_edges += 1

print(f"Clean orthogonal relationships drawn: {drawn_edges}")

# Render All Table Cards (UML Class Box)
for t_name, pos in table_positions.items():
    x, y, w, h = pos['x'], pos['y'], pos['w'], pos['h']
    cols = pos['cols']

    # 1. Main card with clean border & subtle shadow
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFFFF" stroke="#1E293B" stroke-width="1.2" filter="url(#card-shadow)"/>')

    # 2. Icon top-left [=]
    svg.append(f'<g transform="translate({x+8}, {y+9})">')
    svg.append('<rect x="0" y="0" width="13" height="11" fill="#FFFFFF" stroke="#475569" stroke-width="1"/>')
    svg.append('<line x1="0" y1="4" x2="13" y2="4" stroke="#475569" stroke-width="1"/>')
    svg.append('</g>')

    # 3. Class Name (Centered, uppercase, bold)
    title_display = t_name.upper()
    svg.append(f'<text x="{x + w/2.0}" y="{y+21}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="bold" fill="#0F172A" letter-spacing="0.4">{title_display}</text>')

    # 4. Divider line
    svg.append(f'<line x1="{x}" y1="{y+header_h}" x2="{x+w}" y2="{y+header_h}" stroke="#1E293B" stroke-width="1.2"/>')

    # 5. Attributes list with '+'
    curr_attr_y = y + header_h + 16
    for c in cols:
        attr_name = c['attr']
        pk_badge = ""
        fk_badge = ""
        font_weight = "normal"
        fill_col = "#1E293B"

        if c['pk']:
            pk_badge = " [PK]"
            font_weight = "bold"
            fill_col = "#003366"
        elif c['fk']:
            fk_badge = " [FK]"
            fill_col = "#475569"

        text_str = f"+ {attr_name}{pk_badge}{fk_badge}"
        svg.append(f'<text x="{x+10}" y="{curr_attr_y}" font-family="Arial, Helvetica, sans-serif" font-size="11.5" font-weight="{font_weight}" fill="{fill_col}">{text_str}</text>')
        curr_attr_y += line_h

svg.append('</svg>')
svg_str = "\n".join(svg)

# Save SVG
out_svg = "docs/diagramas/diagrama_clases_completo.svg"
with open(out_svg, "w", encoding="utf-8") as f:
    f.write(svg_str)
print(f"Saved SVG to {out_svg} ({len(svg_str)} chars)")

# Render PNG with resvg_py
out_png = "docs/diagramas/diagrama_clases_completo.png"
png_bytes = resvg_py.svg_to_bytes(svg_str)
with open(out_png, "wb") as f:
    f.write(png_bytes)
print(f"Saved PNG to {out_png} ({len(png_bytes)} bytes)")

