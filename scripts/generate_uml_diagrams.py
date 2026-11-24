import csv
import os
import math
from collections import defaultdict
import resvg_py

os.makedirs('docs/diagramas/modulos', exist_ok=True)

# 1. Parse Schema Dump
tables = {}
fks = []

with open('schema_dump.tsv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        if not row or len(row) < 4:
            continue
        schema = row[0].strip('"')
        table = row[1].strip('"')
        if table in ('tabla', '<USER_REQUEST>'):
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

print(f"Loaded {len(tables)} tables and {len(fks)} foreign key relationships.")

# Group into 9 modules
modules = {
    "01_seguridad_saas": {
        "title": "Módulo 1: Seguridad, Usuarios y Plataforma SaaS",
        "tables": [
            "t_persona", "t_usuario", "t_seguridad_usuario", "t_rol", "t_permiso", "t_rol_permiso",
            "t_modulo", "t_bitacora", "t_empresa",
            "t_plan_suscripcion", "t_plan_precio_saas", "t_plan_suscripcion_historial",
            "t_suscripcion_empresa", "t_suscripcion_cupo", "t_suscripcion_historial",
            "t_suscripcion_ia_uso", "t_pago_suscripcion"
        ]
    },
    "02_obras_proyectos": {
        "title": "Módulo 2: Gestión de Obras, Estructuras y Consultas Técnicas (RFI)",
        "tables": [
            "t_obra", "t_tipo_obra", "t_detalle_obra", "t_estructura_obra", "t_obra_usuario",
            "t_avance_obra", "t_consulta_tecnica", "t_consulta_tecnica_respuesta", "t_consulta_tecnica_historial",
            "t_incidencia", "t_incidencia_evidencia", "t_incidencia_seguimiento", "t_incidencia_orden_trabajo"
        ]
    },
    "03_cronogramas_planificacion": {
        "title": "Módulo 3: Planificación de Obras y Cronogramas (CU39)",
        "tables": [
            "t_cronograma", "t_cronograma_actividad", "t_cronograma_dependencia"
        ]
    },
    "04_presupuestos_apu": {
        "title": "Módulo 4: Presupuestos, APU y Estimaciones",
        "tables": [
            "t_unidad_medida", "t_presupuesto", "t_partida_presupuesto",
            "t_analisis_precio_unitario", "t_analisi_precio_unitario_insumo",
            "t_estimacion", "t_estimacion_analisis_precio_unitario", "t_parametro_estimacion", "t_obra_estimacion",
            "t_apu_detalle_mano_obra_archivo", "t_apu_legacy_archive"
        ]
    },
    "05_control_costos_ordenes": {
        "title": "Módulo 5: Control de Costos, Órdenes de Trabajo y Órdenes de Cambio",
        "tables": [
            "t_control_costo_obra", "t_costo_ejecutado", "t_costo_ejecutado_legacy",
            "t_orden_cambio", "t_orden_cambio_detalle", "t_orden_cambio_historial",
            "t_orden_trabajo", "t_orden_trabajo_usuario", "t_orden_trabajo_permiso", "t_usuario_orden_trabajo_permiso"
        ]
    },
    "06_mano_obra_jornadas": {
        "title": "Módulo 6: Mano de Obra, Salarios y Jornadas Diarias (CU32)",
        "tables": [
            "t_mano_obra", "t_salario_trabajador", "t_jornada_trabajador_obra", "t_cu32_mano_obra_cierre"
        ]
    },
    "07_materiales_almacen_compras": {
        "title": "Módulo 7: Materiales, Catálogo, Almacén, Compras y Equipos",
        "tables": [
            "t_categoria_material", "t_material_base", "t_material", "t_material_caracteristica",
            "t_materiales_almacen", "t_movimiento_almacen",
            "t_proveedor", "t_proveedor_material",
            "t_orden_compra", "t_orden_compra_detalle", "t_recepcion_compra", "t_recepcion_compra_detalle",
            "t_equipo", "t_equipo_maquinaria", "t_equipo_maquinaria_obra"
        ]
    },
    "08_crm_inmobiliaria_unidades": {
        "title": "Módulo 8: Inmobiliaria, Unidades de Construcción y CRM Clientes",
        "tables": [
            "t_unidad_construccion", "t_modelo_unidad", "t_modelo_caracteristica",
            "t_unidad_ambiente", "t_unidad_caracteristica", "t_unidad_material",
            "t_unidad_personalizacion", "t_unidad_seguimiento",
            "t_crm_cliente", "t_crm_cliente_unidad", "t_crm_interaccion"
        ]
    },
    "09_reportes_ia_notificaciones": {
        "title": "Módulo 9: Inteligencia Artificial, Reportes Programados y Notificaciones",
        "tables": [
            "notificacion", "t_asistente_conversacion", "t_asistente_mensaje",
            "t_reporte_ejecucion", "t_reporte_archivo", "t_reporte_envio",
            "t_reporte_programacion", "t_reporte_programacion_destinatario"
        ]
    }
}

# Helper to render SVG entity card in exact UML style
def render_uml_card(table_name, cols, x, y, width):
    header_h = 32
    line_h = 20
    body_h = len(cols) * line_h + 10
    total_h = header_h + body_h

    # Card background with border
    xml = []
    # Drop shadow
    xml.append(f'<rect x="{x+2}" y="{y+3}" width="{width}" height="{total_h}" rx="1" fill="#000000" fill-opacity="0.12"/>')
    # White box
    xml.append(f'<rect x="{x}" y="{y}" width="{width}" height="{total_h}" fill="#FFFFFF" stroke="#222222" stroke-width="1.2"/>')
    
    # UML icon (top left)
    icon_x = x + 8
    icon_y = y + 9
    xml.append(f'<g transform="translate({icon_x}, {icon_y})">')
    xml.append('<rect x="0" y="0" width="13" height="11" fill="#FFFFFF" stroke="#444444" stroke-width="1"/>')
    xml.append('<line x1="0" y1="4" x2="13" y2="4" stroke="#444444" stroke-width="1"/>')
    xml.append('</g>')

    # Table Title (centered, bold, uppercase)
    title_display = table_name.upper()
    title_x = x + (width / 2.0)
    title_y = y + 21
    xml.append(f'<text x="{title_x}" y="{title_y}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="12.5" font-weight="bold" fill="#000000" letter-spacing="0.3">{title_display}</text>')

    # Divider line
    div_y = y + header_h
    xml.append(f'<line x1="{x}" y1="{div_y}" x2="{x+width}" y2="{div_y}" stroke="#222222" stroke-width="1.2"/>')

    # Attributes
    curr_y = div_y + 16
    for c in cols:
        attr_name = c['attr']
        pk_badge = ""
        fk_badge = ""
        font_weight = "normal"
        fill_col = "#111111"
        if c['pk']:
            pk_badge = " [PK]"
            font_weight = "bold"
            fill_col = "#002b66"
        elif c['fk']:
            fk_badge = " [FK]"
            fill_col = "#333333"

        text_str = f"+ {attr_name}{pk_badge}{fk_badge}"
        xml.append(f'<text x="{x+10}" y="{curr_y}" font-family="Arial, Helvetica, sans-serif" font-size="11.5" font-weight="{font_weight}" fill="{fill_col}">{text_str}</text>')
        curr_y += line_h

    return total_h, "".join(xml)

# Generate Module Diagrams
for mod_id, mod_info in modules.items():
    mod_title = mod_info["title"]
    mod_table_names = mod_info["tables"]
    
    # Calculate dimensions and positions
    # 2, 3 or 4 columns based on table count
    n_tables = len(mod_table_names)
    cols_per_row = 3 if n_tables > 6 else (2 if n_tables > 1 else 1)
    card_w = 260
    gap_x = 70
    gap_y = 50
    margin_x = 50
    margin_y = 90

    # First pass: compute heights
    table_boxes = {}
    row_heights = defaultdict(int)
    
    col_idx = 0
    row_idx = 0
    for t_name in mod_table_names:
        cols = tables.get(t_name, [])
        h = 32 + len(cols) * 20 + 10
        table_boxes[t_name] = {
            'col': col_idx,
            'row': row_idx,
            'h': h,
            'w': card_w,
            'cols': cols
        }
        if h > row_heights[row_idx]:
            row_heights[row_idx] = h
        
        col_idx += 1
        if col_idx >= cols_per_row:
            col_idx = 0
            row_idx += 1

    # Second pass: calculate absolute X, Y
    total_w = margin_x * 2 + cols_per_row * card_w + (cols_per_row - 1) * gap_x
    curr_top = margin_y
    for r in range(row_idx + 1):
        for t_name, b in table_boxes.items():
            if b['row'] == r:
                b['x'] = margin_x + b['col'] * (card_w + gap_x)
                b['y'] = curr_top
        curr_top += row_heights[r] + gap_y

    total_h = curr_top + 30

    # Build SVG content
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">')
    svg_lines.append(f'<rect width="{total_w}" height="{total_h}" fill="#F8FAFC"/>')
    
    # Header Banner
    svg_lines.append(f'<rect x="0" y="0" width="{total_w}" height="60" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>')
    svg_lines.append(f'<line x1="0" y1="58" x2="{total_w}" y2="58" stroke="#E2E8F0" stroke-width="2"/>')
    svg_lines.append(f'<text x="{margin_x}" y="38" font-family="Arial, Helvetica, sans-serif" font-size="19" font-weight="bold" fill="#0F172A">{mod_title}</text>')
    svg_lines.append(f'<text x="{total_w - margin_x}" y="38" text-anchor="end" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="#64748B">Modelo Relacional UML · OBRATEC</text>')

    # Collect relationships within this module
    active_tables_set = set(mod_table_names)
    mod_fks = [fk for fk in fks if fk['from_table'] in active_tables_set and fk['to_table'] in active_tables_set]

    # Draw Relationship Lines first (behind cards)
    for fk in mod_fks:
        tb_from = table_boxes[fk['from_table']]
        tb_to = table_boxes[fk['to_table']]

        # Compute optimal connection points
        from_cx = tb_from['x'] + tb_from['w'] / 2.0
        from_cy = tb_from['y'] + tb_from['h'] / 2.0
        to_cx = tb_to['x'] + tb_to['w'] / 2.0
        to_cy = tb_to['y'] + tb_to['h'] / 2.0

        if tb_from['col'] < tb_to['col']:
            p1 = (tb_from['x'] + tb_from['w'], from_cy)
            p4 = (tb_to['x'], to_cy)
            mid_x = (p1[0] + p4[0]) / 2.0
            path_d = f"M {p1[0]} {p1[1]} L {mid_x} {p1[1]} L {mid_x} {p4[1]} L {p4[0]} {p4[1]}"
            card_p1 = (p1[0] + 8, p1[1] - 5, "0..*")
            card_p4 = (p4[0] - 18, p4[1] - 5, "1")
        elif tb_from['col'] > tb_to['col']:
            p1 = (tb_from['x'], from_cy)
            p4 = (tb_to['x'] + tb_to['w'], to_cy)
            mid_x = (p1[0] + p4[0]) / 2.0
            path_d = f"M {p1[0]} {p1[1]} L {mid_x} {p1[1]} L {mid_x} {p4[1]} L {p4[0]} {p4[1]}"
            card_p1 = (p1[0] - 22, p1[1] - 5, "0..*")
            card_p4 = (p4[0] + 8, p4[1] - 5, "1")
        else: # same column
            if tb_from['row'] < tb_to['row']:
                p1 = (from_cx, tb_from['y'] + tb_from['h'])
                p4 = (to_cx, tb_to['y'])
                path_d = f"M {p1[0]} {p1[1]} L {p4[0]} {p4[1]}"
                card_p1 = (p1[0] + 6, p1[1] + 14, "0..*")
                card_p4 = (p4[0] + 6, p4[1] - 8, "1")
            else:
                p1 = (from_cx, tb_from['y'])
                p4 = (to_cx, tb_to['y'] + tb_to['h'])
                path_d = f"M {p1[0]} {p1[1]} L {p4[0]} {p4[1]}"
                card_p1 = (p1[0] + 6, p1[1] - 8, "0..*")
                card_p4 = (p4[0] + 6, p4[1] + 14, "1")

        svg_lines.append(f'<path d="{path_d}" fill="none" stroke="#475569" stroke-width="1.3" stroke-dasharray="solid"/>')
        svg_lines.append(f'<text x="{card_p1[0]}" y="{card_p1[1]}" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#1E293B">{card_p1[2]}</text>')
        svg_lines.append(f'<text x="{card_p4[0]}" y="{card_p4[1]}" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#1E293B">{card_p4[2]}</text>')

    # Draw Table Cards
    for t_name, b in table_boxes.items():
        _, card_svg = render_uml_card(t_name, b['cols'], b['x'], b['y'], b['w'])
        svg_lines.append(card_svg)

    svg_lines.append('</svg>')
    svg_str = "\n".join(svg_lines)

    # Save SVG
    svg_file = f"docs/diagramas/modulos/{mod_id}.svg"
    with open(svg_file, "w", encoding="utf-8") as f:
        f.write(svg_str)

    # Save PNG
    png_file = f"docs/diagramas/modulos/{mod_id}.png"
    png_bytes = resvg_py.svg_to_bytes(svg_str)
    with open(png_file, "wb") as f:
        f.write(png_bytes)

    print(f"Generated module diagram: {svg_file} ({len(png_bytes)} bytes PNG)")

print("All 9 module diagrams successfully generated!")

