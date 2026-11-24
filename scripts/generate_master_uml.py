import csv
import os
from collections import defaultdict
import resvg_py

# 1. Parse Schema
tables = {}
fks = []

with open('schema_dump.tsv', 'r', encoding='utf-8') as f:
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
        if fk and ref_table:
            fks.append({
                'from_table': table,
                'from_col': attr,
                'to_table': ref_table,
                'to_col': ref_attr
            })

# Define Module Layout on Master Canvas
# 3 Columns of Modules
modules_grid = [
    # Column 0: Plataforma, Seguridad & Presupuestos
    [
        {
            "id": "mod_seguridad",
            "name": "SEGURIDAD, USUARIOS Y PLATAFORMA SAAS",
            "color": "#1E3A8A", # Dark Blue
            "cols_per_row": 3,
            "tables": [
                "t_empresa", "t_persona", "t_usuario", "t_seguridad_usuario", "t_rol", "t_permiso",
                "t_rol_permiso", "t_modulo", "t_bitacora",
                "t_plan_suscripcion", "t_plan_precio_saas", "t_plan_suscripcion_historial",
                "t_suscripcion_empresa", "t_suscripcion_cupo", "t_suscripcion_historial",
                "t_suscripcion_ia_uso", "t_pago_suscripcion"
            ]
        },
        {
            "id": "mod_presupuestos",
            "name": "PRESUPUESTOS, APU Y ESTIMACIONES",
            "color": "#065F46", # Emerald Green
            "cols_per_row": 3,
            "tables": [
                "t_unidad_medida", "t_presupuesto", "t_partida_presupuesto",
                "t_analisis_precio_unitario", "t_analisi_precio_unitario_insumo",
                "t_estimacion", "t_estimacion_analisis_precio_unitario", "t_parametro_estimacion", "t_obra_estimacion",
                "t_apu_detalle_mano_obra_archivo", "t_apu_legacy_archive"
            ]
        },
        {
            "id": "mod_inmobiliaria",
            "name": "INMOBILIARIA, UNIDADES Y CRM CLIENTES",
            "color": "#7C2D12", # Warm Amber / Terracotta
            "cols_per_row": 3,
            "tables": [
                "t_unidad_construccion", "t_modelo_unidad", "t_modelo_caracteristica",
                "t_unidad_ambiente", "t_unidad_caracteristica", "t_unidad_material",
                "t_unidad_personalizacion", "t_unidad_seguimiento",
                "t_crm_cliente", "t_crm_cliente_unidad", "t_crm_interaccion"
            ]
        }
    ],
    # Column 1: Obras, Control de Costos y Órdenes
    [
        {
            "id": "mod_obras",
            "name": "GESTIÓN DE OBRAS, ESTRUCTURAS Y RFI",
            "color": "#1E293B", # Slate
            "cols_per_row": 3,
            "tables": [
                "t_tipo_obra", "t_obra", "t_detalle_obra", "t_estructura_obra", "t_obra_usuario",
                "t_avance_obra", "t_consulta_tecnica", "t_consulta_tecnica_respuesta", "t_consulta_tecnica_historial",
                "t_incidencia", "t_incidencia_evidencia", "t_incidencia_seguimiento", "t_incidencia_orden_trabajo"
            ]
        },
        {
            "id": "mod_costos",
            "name": "CONTROL DE COSTOS, ÓRDENES DE CAMBIO Y TRABAJO",
            "color": "#831843", # Deep Rose
            "cols_per_row": 3,
            "tables": [
                "t_control_costo_obra", "t_costo_ejecutado", "t_costo_ejecutado_legacy",
                "t_orden_cambio", "t_orden_cambio_detalle", "t_orden_cambio_historial",
                "t_orden_trabajo", "t_orden_trabajo_usuario", "t_orden_trabajo_permiso", "t_usuario_orden_trabajo_permiso"
            ]
        },
        {
            "id": "mod_reportes_ia",
            "name": "INTELIGENCIA ARTIFICIAL, REPORTES Y NOTIFICACIONES",
            "color": "#4C1D95", # Deep Purple
            "cols_per_row": 3,
            "tables": [
                "notificacion", "t_asistente_conversacion", "t_asistente_mensaje",
                "t_reporte_ejecucion", "t_reporte_archivo", "t_reporte_envio",
                "t_reporte_programacion", "t_reporte_programacion_destinatario"
            ]
        }
    ],
    # Column 2: Cronogramas, Mano de Obra y Materiales / Almacén
    [
        {
            "id": "mod_cronogramas",
            "name": "PLANIFICACIÓN Y CRONOGRAMAS (CU39)",
            "color": "#0F766E", # Deep Teal
            "cols_per_row": 3,
            "tables": [
                "t_cronograma", "t_cronograma_actividad", "t_cronograma_dependencia"
            ]
        },
        {
            "id": "mod_mano_obra",
            "name": "MANO DE OBRA Y JORNADAS (CU32)",
            "color": "#9A3412", # Rust Orange
            "cols_per_row": 2,
            "tables": [
                "t_mano_obra", "t_salario_trabajador", "t_jornada_trabajador_obra", "t_cu32_mano_obra_cierre"
            ]
        },
        {
            "id": "mod_materiales",
            "name": "MATERIALES, COMPRAS, ALMACÉN Y EQUIPOS",
            "color": "#374151", # Charcoal
            "cols_per_row": 3,
            "tables": [
                "t_categoria_material", "t_material_base", "t_material", "t_material_caracteristica",
                "t_materiales_almacen", "t_movimiento_almacen",
                "t_proveedor", "t_proveedor_material",
                "t_orden_compra", "t_orden_compra_detalle", "t_recepcion_compra", "t_recepcion_compra_detalle",
                "t_equipo", "t_equipo_maquinaria", "t_equipo_maquinaria_obra"
            ]
        }
    ]
]

card_w = 250
line_h = 19
header_h = 32
gap_table_x = 40
gap_table_y = 35
module_padding_x = 35
module_padding_y = 45
module_gap_x = 70
module_gap_y = 60
canvas_margin_x = 60
canvas_margin_y = 110

# Compute Layout
all_table_boxes = {}
module_boxes = []

col_x_offsets = []
curr_col_x = canvas_margin_x

# Measure each column width
for col_modules in modules_grid:
    max_mod_w = 0
    for mod in col_modules:
        cpr = mod["cols_per_row"]
        mod_w = module_padding_x * 2 + cpr * card_w + (cpr - 1) * gap_table_x
        if mod_w > max_mod_w:
            max_mod_w = mod_w
    col_x_offsets.append((curr_col_x, max_mod_w))
    curr_col_x += max_mod_w + module_gap_x

total_canvas_w = curr_col_x - module_gap_x + canvas_margin_x

max_total_canvas_y = 0

for c_idx, col_modules in enumerate(modules_grid):
    col_x, col_w = col_x_offsets[c_idx]
    curr_mod_y = canvas_margin_y

    for mod in col_modules:
        cpr = mod["cols_per_row"]
        mod_start_x = col_x
        mod_start_y = curr_mod_y

        # Layout tables inside this module
        n_tables = len(mod["tables"])
        row_heights = defaultdict(int)
        mod_t_boxes = {}

        t_idx = 0
        for t_name in mod["tables"]:
            cols = tables.get(t_name, [])
            h = header_h + len(cols) * line_h + 10
            r = t_idx // cpr
            c = t_idx % cpr
            mod_t_boxes[t_name] = {
                'row': r,
                'col': c,
                'w': card_w,
                'h': h,
                'cols': cols,
                'mod_id': mod['id']
            }
            if h > row_heights[r]:
                row_heights[r] = h
            t_idx += 1

        n_rows = (n_tables + cpr - 1) // cpr if n_tables > 0 else 0
        curr_row_top = mod_start_y + module_padding_y + 35 # 35 for module header

        for r in range(n_rows):
            for t_name, b in mod_t_boxes.items():
                if b['row'] == r:
                    b['x'] = mod_start_x + module_padding_x + b['col'] * (card_w + gap_table_x)
                    b['y'] = curr_row_top
                    all_table_boxes[t_name] = b
            curr_row_top += row_heights[r] + gap_table_y

        mod_total_h = curr_row_top - mod_start_y - gap_table_y + module_padding_y
        mod_box = {
            'id': mod['id'],
            'name': mod['name'],
            'color': mod['color'],
            'x': mod_start_x,
            'y': mod_start_y,
            'w': col_w,
            'h': mod_total_h
        }
        module_boxes.append(mod_box)

        curr_mod_y += mod_total_h + module_gap_y

    if curr_mod_y > max_total_canvas_y:
        max_total_canvas_y = curr_mod_y

total_canvas_h = max_total_canvas_y + 50

print(f"Canvas size: {total_canvas_w} x {total_canvas_h}")

# Render Master SVG
svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_canvas_w}" height="{total_canvas_h}" viewBox="0 0 {total_canvas_w} {total_canvas_h}">')

# Background
svg.append(f'<rect width="{total_canvas_w}" height="{total_canvas_h}" fill="#F1F5F9"/>')

# Master Header
svg.append(f'<rect x="0" y="0" width="{total_canvas_w}" height="80" fill="#0F172A"/>')
svg.append(f'<text x="60" y="48" font-family="Arial, Helvetica, sans-serif" font-size="28" font-weight="bold" fill="#FFFFFF" letter-spacing="1">OBRATEC · DIAGRAMA RELACIONAL DE BASE DE DATOS (ESQUEMA OBRAS)</text>')
svg.append(f'<text x="{total_canvas_w - 60}" y="48" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="#94A3B8">92 Tablas · 196 Claves Foráneas · Modelo UML Estándar</text>')

# Draw Module Container Cards
for mb in module_boxes:
    # Outer module container with soft shadow
    svg.append(f'<rect x="{mb["x"]+3}" y="{mb["y"]+4}" width="{mb["w"]}" height="{mb["h"]}" rx="8" fill="#000000" fill-opacity="0.08"/>')
    svg.append(f'<rect x="{mb["x"]}" y="{mb["y"]}" width="{mb["w"]}" height="{mb["h"]}" rx="8" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1.5"/>')
    # Module Header Bar
    svg.append(f'<rect x="{mb["x"]}" y="{mb["y"]}" width="{mb["w"]}" height="42" rx="8" fill="{mb["color"]}"/>')
    # Flatten bottom corners of header bar
    svg.append(f'<rect x="{mb["x"]}" y="{mb["y"]+20}" width="{mb["w"]}" height="22" fill="{mb["color"]}"/>')
    svg.append(f'<text x="{mb["x"]+20}" y="{mb["y"]+27}" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="bold" fill="#FFFFFF" letter-spacing="0.8">{mb["name"]}</text>')

# Helper to render UML table card
def render_master_card(table_name, b):
    x, y, w, h = b['x'], b['y'], b['w'], b['h']
    cols = b['cols']
    xml = []
    # Drop shadow
    xml.append(f'<rect x="{x+2}" y="{y+3}" width="{w}" height="{h}" rx="1" fill="#000000" fill-opacity="0.12"/>')
    # White box
    xml.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFFFF" stroke="#222222" stroke-width="1.2"/>')

    # UML icon (top left)
    xml.append(f'<g transform="translate({x+8}, {y+9})">')
    xml.append('<rect x="0" y="0" width="13" height="11" fill="#FFFFFF" stroke="#444444" stroke-width="1"/>')
    xml.append('<line x1="0" y1="4" x2="13" y2="4" stroke="#444444" stroke-width="1"/>')
    xml.append('</g>')

    # Table Title (centered, bold, uppercase)
    xml.append(f'<text x="{x + w/2.0}" y="{y+21}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="bold" fill="#000000" letter-spacing="0.3">{table_name.upper()}</text>')

    # Divider line
    xml.append(f'<line x1="{x}" y1="{y+header_h}" x2="{x+w}" y2="{y+header_h}" stroke="#222222" stroke-width="1.2"/>')

    # Attributes
    curr_y = y + header_h + 15
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
            fill_col = "#475569"

        text_str = f"+ {attr_name}{pk_badge}{fk_badge}"
        xml.append(f'<text x="{x+10}" y="{curr_y}" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="{font_weight}" fill="{fill_col}">{text_str}</text>')
        curr_y += line_h

    return "".join(xml)

# Draw Intra-Module Relationship Lines
for fk in fks:
    t_from = fk['from_table']
    t_to = fk['to_table']
    if t_from in all_table_boxes and t_to in all_table_boxes:
        b_from = all_table_boxes[t_from]
        b_to = all_table_boxes[t_to]

        # Draw within the same module with clear lines
        if b_from['mod_id'] == b_to['mod_id']:
            from_cx = b_from['x'] + b_from['w'] / 2.0
            from_cy = b_from['y'] + b_from['h'] / 2.0
            to_cx = b_to['x'] + b_to['w'] / 2.0
            to_cy = b_to['y'] + b_to['h'] / 2.0

            if b_from['col'] < b_to['col']:
                p1 = (b_from['x'] + b_from['w'], from_cy)
                p4 = (b_to['x'], to_cy)
                mid_x = (p1[0] + p4[0]) / 2.0
                path_d = f"M {p1[0]} {p1[1]} L {mid_x} {p1[1]} L {mid_x} {p4[1]} L {p4[0]} {p4[1]}"
                card_p1 = (p1[0] + 6, p1[1] - 4, "0..*")
                card_p4 = (p4[0] - 16, p4[1] - 4, "1")
            elif b_from['col'] > b_to['col']:
                p1 = (b_from['x'], from_cy)
                p4 = (b_to['x'] + b_to['w'], to_cy)
                mid_x = (p1[0] + p4[0]) / 2.0
                path_d = f"M {p1[0]} {p1[1]} L {mid_x} {p1[1]} L {mid_x} {p4[1]} L {p4[0]} {p4[1]}"
                card_p1 = (p1[0] - 20, p1[1] - 4, "0..*")
                card_p4 = (p4[0] + 6, p4[1] - 4, "1")
            else:
                if b_from['row'] < b_to['row']:
                    p1 = (from_cx, b_from['y'] + b_from['h'])
                    p4 = (to_cx, b_to['y'])
                    path_d = f"M {p1[0]} {p1[1]} L {p4[0]} {p4[1]}"
                    card_p1 = (p1[0] + 5, p1[1] + 13, "0..*")
                    card_p4 = (p4[0] + 5, p4[1] - 7, "1")
                else:
                    p1 = (from_cx, b_from['y'])
                    p4 = (to_cx, b_to['y'] + b_to['h'])
                    path_d = f"M {p1[0]} {p1[1]} L {p4[0]} {p4[1]}"
                    card_p1 = (p1[0] + 5, p1[1] - 7, "0..*")
                    card_p4 = (p4[0] + 5, p4[1] + 13, "1")

            svg.append(f'<path d="{path_d}" fill="none" stroke="#64748B" stroke-width="1.2"/>')
            svg.append(f'<text x="{card_p1[0]}" y="{card_p1[1]}" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#334155">{card_p1[2]}</text>')
            svg.append(f'<text x="{card_p4[0]}" y="{card_p4[1]}" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#334155">{card_p4[2]}</text>')

# Draw Tables
for t_name, b in all_table_boxes.items():
    svg.append(render_master_card(t_name, b))

svg.append('</svg>')
master_svg_str = "\n".join(svg)

# Save Master SVG
master_svg_path = "docs/diagramas/diagrama_bd_obratec_master.svg"
with open(master_svg_path, "w", encoding="utf-8") as f:
    f.write(master_svg_str)

print(f"Master SVG saved to {master_svg_path} ({len(master_svg_str)} chars).")

# Render Master PNG
print("Rendering Master PNG with resvg_py...")
master_png_bytes = resvg_py.svg_to_bytes(master_svg_str)
master_png_path = "docs/diagramas/diagrama_bd_obratec_master.png"
with open(master_png_path, "wb") as f:
    f.write(master_png_bytes)

print(f"Master PNG successfully saved to {master_png_path} ({len(master_png_bytes)} bytes).")

