import os
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)

# Sequence Diagrams Definitions
sequence_data = {
    "cu35": {
        "id": "secuencia_cu35_entrada_material",
        "sd_tag": "sd CU35 - Registrar entrada de material",
        "tab_name": "CU35 - Secuencia Entrada",
        "actor": "user : Supervisor",
        "lifelines": [
            {"id": "ui", "name": "ui : Form_Registrar_Entrada"},
            {"id": "router", "name": "router : inventario_routes"},
            {"id": "service", "name": "service : inventario_services"},
            {"id": "t_mat", "name": "t_material"},
            {"id": "t_mov", "name": "t_movimiento_almacen"}
        ],
        "events": [
            {"type": "msg", "from": 0, "to": 1, "text": "1: ingresar_datos(id_material, cantidad, obs, stock_min)", "style": "sync"},
            {"type": "self", "at": 1, "text": "2: validarFormulario()"},
            {"type": "msg", "from": 1, "to": 2, "text": "3: POST /api/inventario/ajuste (tipo='ENTRADA_AJUSTE', ...)", "style": "sync"},
            {"type": "msg", "from": 2, "to": 3, "text": "4: registrar_ajuste(data, token, ip)", "style": "sync"},
            {"type": "self", "at": 3, "text": "5: validar_permiso('Modificar_inventario') & tenant"},
            {"type": "msg", "from": 3, "to": 4, "text": "6: SELECT stock_actual FROM t_material WHERE id_material=:id", "style": "sync"},
            {"type": "ret", "from": 4, "to": 3, "text": "7: return stock_actual"},
            {"type": "msg", "from": 3, "to": 4, "text": "8: UPDATE t_material SET stock_actual = stock_actual + :cant", "style": "sync"},
            {"type": "ret", "from": 4, "to": 3, "text": "9: return material_actualizado"},
            {"type": "msg", "from": 3, "to": 5, "text": "10: INSERT INTO t_movimiento_almacen (id_material, tipo, cant, ...)", "style": "sync"},
            {"type": "ret", "from": 5, "to": 3, "text": "11: return id_movimiento"},
            {"type": "ret", "from": 3, "to": 2, "text": "12: return {success: true, data: resultado}"},
            {"type": "ret", "from": 2, "to": 1, "text": "13: 200 OK (Ajuste guardado correctamente)"},
            {"type": "self", "at": 1, "text": "14: cerrarModal() & refrescarStock()"},
            {"type": "ret", "from": 1, "to": 0, "text": "15: mostrar_confirmacion('Entrada registrada exitosamente')"}
        ]
    },
    "cu36": {
        "id": "secuencia_cu36_salida_material",
        "sd_tag": "sd CU36 - Registrar salida de material",
        "tab_name": "CU36 - Secuencia Salida",
        "actor": "user : Supervisor",
        "lifelines": [
            {"id": "ui", "name": "ui : Form_Registrar_Salida"},
            {"id": "router", "name": "router : inventario_routes"},
            {"id": "service", "name": "service : inventario_services"},
            {"id": "t_mat", "name": "t_material"},
            {"id": "t_mov", "name": "t_movimiento_almacen"}
        ],
        "events": [
            {"type": "msg", "from": 0, "to": 1, "text": "1: ingresar_datos_salida(id_material, cantidad, obs)", "style": "sync"},
            {"type": "self", "at": 1, "text": "2: verificarStockDisponible()"},
            {"type": "msg", "from": 1, "to": 2, "text": "3: POST /api/inventario/ajuste (tipo='SALIDA_AJUSTE', ...)", "style": "sync"},
            {"type": "msg", "from": 2, "to": 3, "text": "4: registrar_ajuste(data, token, ip)", "style": "sync"},
            {"type": "self", "at": 3, "text": "5: validar_permiso('Modificar_inventario')"},
            {"type": "msg", "from": 3, "to": 4, "text": "6: SELECT stock_actual FROM t_material WHERE id_material=:id", "style": "sync"},
            {"type": "ret", "from": 4, "to": 3, "text": "7: return stock_actual"},
            {"type": "alt_start", "cond": "[stock_actual >= cantidad]"},
            {"type": "msg", "from": 3, "to": 4, "text": "8: UPDATE t_material SET stock_actual = stock_actual - :cant", "style": "sync"},
            {"type": "ret", "from": 4, "to": 3, "text": "9: return ok"},
            {"type": "msg", "from": 3, "to": 5, "text": "10: INSERT INTO t_movimiento_almacen (id_material, tipo='SALIDA_AJUSTE', ...)", "style": "sync"},
            {"type": "ret", "from": 5, "to": 3, "text": "11: return id_movimiento"},
            {"type": "ret", "from": 3, "to": 2, "text": "12: return {success: true, data: resultado}"},
            {"type": "ret", "from": 2, "to": 1, "text": "13: 200 OK (Salida registrada)"},
            {"type": "ret", "from": 1, "to": 0, "text": "14: mostrar_exito('Salida de material registrada')"},
            {"type": "alt_else", "cond": "[else stock insuficiente]"},
            {"type": "ret", "from": 3, "to": 2, "text": "15: raise InventarioError(400, 'Stock insuficiente')"},
            {"type": "ret", "from": 2, "to": 1, "text": "16: 400 Bad Request ('Stock insuficiente')"},
            {"type": "ret", "from": 1, "to": 0, "text": "17: mostrar_alerta('No hay suficiente stock para despachar')"},
            {"type": "alt_end"}
        ]
    },
    "cu23": {
        "id": "secuencia_cu23_consultas_tecnicas",
        "sd_tag": "sd CU23 - Gestionar consultas tecnicas de obra (RFI)",
        "tab_name": "CU23 - Secuencia Consultas",
        "actor": "user : Jefe_de_Obra",
        "lifelines": [
            {"id": "ui", "name": "ui : Form_Consultas_Tecnicas"},
            {"id": "router", "name": "router : consulta_tecnica_routes"},
            {"id": "service", "name": "service : consulta_tecnica_services"},
            {"id": "t_ct", "name": "t_consulta_tecnica"},
            {"id": "t_resp", "name": "t_consulta_tecnica_respuesta"},
            {"id": "t_hist", "name": "t_consulta_tecnica_historial"}
        ],
        "events": [
            {"type": "msg", "from": 0, "to": 1, "text": "1: ingresar_consulta(id_obra, asunto, desc, ref_tecnica)", "style": "sync"},
            {"type": "msg", "from": 1, "to": 2, "text": "2: POST /api/proyectos/{id_obra}/consultas-tecnicas", "style": "sync"},
            {"type": "msg", "from": 2, "to": 3, "text": "3: registrar_consulta_obra_db(id_obra, data, token)", "style": "sync"},
            {"type": "self", "at": 3, "text": "4: generar_siguiente_codigo_ct(id_obra)"},
            {"type": "msg", "from": 3, "to": 4, "text": "5: INSERT INTO t_consulta_tecnica (codigo, asunto, estado='ABIERTA', ...)", "style": "sync"},
            {"type": "ret", "from": 4, "to": 3, "text": "6: return id_consulta_tecnica, codigo"},
            {"type": "msg", "from": 3, "to": 6, "text": "7: INSERT INTO t_consulta_tecnica_historial (tipo_evento='CREACION', ...)", "style": "sync"},
            {"type": "ret", "from": 6, "to": 3, "text": "8: return ok"},
            {"type": "ret", "from": 3, "to": 2, "text": "9: return consulta_registrada"},
            {"type": "ret", "from": 2, "to": 1, "text": "10: 201 Created (id_consulta, codigo)"},
            {"type": "msg", "from": 0, "to": 1, "text": "11: responder_consulta_db(id_consulta, respuesta_texto)", "style": "sync"},
            {"type": "msg", "from": 1, "to": 2, "text": "12: POST /api/consultas-tecnicas/{id}/respuestas", "style": "sync"},
            {"type": "msg", "from": 2, "to": 3, "text": "13: responder_consulta(id_ct, data, token)", "style": "sync"},
            {"type": "msg", "from": 3, "to": 5, "text": "14: INSERT INTO t_consulta_tecnica_respuesta (id_ct, autor_id, contenido)", "style": "sync"},
            {"type": "ret", "from": 5, "to": 3, "text": "15: return id_respuesta"},
            {"type": "msg", "from": 3, "to": 4, "text": "16: UPDATE t_consulta_tecnica SET estado='RESPONDIDA' WHERE id=:id", "style": "sync"},
            {"type": "msg", "from": 3, "to": 6, "text": "17: INSERT INTO t_consulta_tecnica_historial (tipo_evento='RESPUESTA', ...)", "style": "sync"},
            {"type": "ret", "from": 3, "to": 2, "text": "18: return {id_respuesta, estado: 'RESPONDIDA'}"},
            {"type": "ret", "from": 2, "to": 1, "text": "19: 201 Created (Respuesta guardada)"},
            {"type": "ret", "from": 1, "to": 0, "text": "20: mostrar_detalle_actualizado()"}
        ]
    },
    "cu34": {
        "id": "secuencia_cu34_asistente_comercial",
        "sd_tag": "sd CU34 - Consultar asistente comercial y recomendaciones",
        "tab_name": "CU34 - Secuencia Asistente",
        "actor": "user : Cliente_Potencial",
        "lifelines": [
            {"id": "ui", "name": "ui : Form_Asistente_Comercial"},
            {"id": "router", "name": "router : ai_routes"},
            {"id": "service", "name": "service : Control_Asistente_Comercial"},
            {"id": "t_asist", "name": "t_asistente_conversacion"},
            {"id": "t_unid", "name": "t_unidad_construccion"},
            {"id": "t_crm", "name": "t_crm_cliente"}
        ],
        "events": [
            {"type": "msg", "from": 0, "to": 1, "text": "1: ingresar_consulta('Busco depto 2 dorms', presupuesto)", "style": "sync"},
            {"type": "msg", "from": 1, "to": 2, "text": "2: POST /api/ai/crm/consulta (pregunta, presupuesto)", "style": "sync"},
            {"type": "msg", "from": 2, "to": 3, "text": "3: consultar_crm_ia(pregunta, presupuesto, token, ip)", "style": "sync"},
            {"type": "msg", "from": 3, "to": 4, "text": "4: SELECT / INSERT t_asistente_conversacion(id_cliente)", "style": "sync"},
            {"type": "ret", "from": 4, "to": 3, "text": "5: return id_conversacion"},
            {"type": "msg", "from": 3, "to": 5, "text": "6: SELECT * FROM t_unidad_construccion WHERE estado='DISPONIBLE'", "style": "sync"},
            {"type": "ret", "from": 5, "to": 3, "text": "7: return lista_unidades_compatibles"},
            {"type": "self", "at": 3, "text": "8: generar_analisis_recomendaciones_ia()"},
            {"type": "msg", "from": 3, "to": 4, "text": "9: INSERT INTO t_asistente_mensaje (conversacion, texto, respuesta)", "style": "sync"},
            {"type": "ret", "from": 4, "to": 3, "text": "10: return id_mensaje"},
            {"type": "msg", "from": 3, "to": 6, "text": "11: UPDATE t_crm_cliente SET clasificacion='INTERESADO' WHERE id=:id", "style": "sync"},
            {"type": "ret", "from": 6, "to": 3, "text": "12: return ok"},
            {"type": "ret", "from": 3, "to": 2, "text": "13: return {respuesta_ia, unidades_recomendadas, sugerencias}"},
            {"type": "ret", "from": 2, "to": 1, "text": "14: 200 OK (Mensaje IA y tarjetas de unidades)"},
            {"type": "self", "at": 1, "text": "15: renderizar_mensajes_y_tarjetas_inmuebles()"},
            {"type": "ret", "from": 1, "to": 0, "text": "16: visualizar_recomendaciones_comerciales()"}
        ]
    }
}

# Helper to render SVG Sequence Diagram in strict B&W UML style
def render_sequence_svg(d):
    n_ll = 1 + len(d["lifelines"])
    ll_w = 150
    gap = 25
    margin_l = 45
    margin_top = 40
    header_box_h = 36
    
    col_x = []
    # Actor column
    col_x.append(margin_l + 35) # actor center
    curr_x = margin_l + 70 + gap
    for ll in d["lifelines"]:
        col_x.append(curr_x + ll_w / 2.0)
        curr_x += ll_w + gap

    total_w = curr_x + 30
    
    # Calculate vertical spacing
    row_h = 28
    events = d["events"]
    n_rows = len(events)
    content_top = margin_top + 65
    total_h = content_top + n_rows * row_h + 80
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">')
    
    # Definitions: Markers for sync and ret arrows (strictly B&W)
    svg.append('''<defs>
      <marker id="arrow-sync" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <polygon points="0,1 9,5 0,9" fill="#000000"/>
      </marker>
      <marker id="arrow-ret" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 1 L 9 5 L 0 9" fill="none" stroke="#000000" stroke-width="1.3"/>
      </marker>
    </defs>''')
    
    # Background: Crisp white
    svg.append(f'<rect width="{total_w}" height="{total_h}" fill="#FFFFFF"/>')
    
    # Outer UML frame
    frame_x = 15
    frame_y = 15
    frame_w = total_w - 30
    frame_h = total_h - 30
    svg.append(f'<rect x="{frame_x}" y="{frame_y}" width="{frame_w}" height="{frame_h}" fill="none" stroke="#000000" stroke-width="1.3"/>')
    
    # Top-left folded frame tab: sd <name>
    tag_text = d["sd_tag"]
    tag_w = len(tag_text) * 7.5 + 24
    tag_h = 22
    # polygon with cut corner
    svg.append(f'<polygon points="{frame_x},{frame_y} {frame_x+tag_w},{frame_y} {frame_x+tag_w+8},{frame_y+tag_h/2} {frame_x+tag_w},{frame_y+tag_h} {frame_x},{frame_y+tag_h}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    svg.append(f'<text x="{frame_x+8}" y="{frame_y+15}" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#000000">{tag_text}</text>')

    # Draw Lifelines Header
    # 1. Actor (User stick figure)
    act_cx = col_x[0]
    act_y = margin_top + 10
    # Head
    svg.append(f'<circle cx="{act_cx}" cy="{act_y+8}" r="6" fill="#FFFFFF" stroke="#000000" stroke-width="1.2"/>')
    # Body
    svg.append(f'<line x1="{act_cx}" y1="{act_y+14}" x2="{act_cx}" y2="{act_y+27}" stroke="#000000" stroke-width="1.2"/>')
    # Arms
    svg.append(f'<line x1="{act_cx-10}" y1="{act_y+19}" x2="{act_cx+10}" y2="{act_y+19}" stroke="#000000" stroke-width="1.2"/>')
    # Legs
    svg.append(f'<line x1="{act_cx}" y1="{act_y+27}" x2="{act_cx-8}" y2="{act_y+38}" stroke="#000000" stroke-width="1.2"/>')
    svg.append(f'<line x1="{act_cx}" y1="{act_y+27}" x2="{act_cx+8}" y2="{act_y+38}" stroke="#000000" stroke-width="1.2"/>')
    # Label
    svg.append(f'<text x="{act_cx}" y="{act_y+50}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10.5" font-weight="bold" fill="#000000">{d["actor"]}</text>')

    # 2. Other Lifelines (rounded boxes, B&W)
    for idx, ll in enumerate(d["lifelines"]):
        cx = col_x[idx+1]
        bx = cx - ll_w / 2.0
        by = margin_top + 20
        svg.append(f'<rect x="{bx}" y="{by}" width="{ll_w}" height="{header_box_h}" rx="3" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
        svg.append(f'<text x="{cx}" y="{by+22}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#000000">{ll["name"]}</text>')

    # Lifeline vertical dashed lines
    line_bottom = total_h - 45
    for cx in col_x:
        svg.append(f'<line x1="{cx}" y1="{content_top - 5}" x2="{cx}" y2="{line_bottom}" stroke="#000000" stroke-width="1" stroke-dasharray="4,4"/>')

    # Draw Events & Messages
    curr_y = content_top + 20
    alt_start_y = None
    alt_else_y = None
    alt_cond_text = ""
    alt_else_text = ""

    for ev in events:
        ev_type = ev["type"]
        
        if ev_type == "alt_start":
            alt_start_y = curr_y - 12
            alt_cond_text = ev["cond"]
            curr_y += 10
            continue
        elif ev_type == "alt_else":
            alt_else_y = curr_y - 10
            alt_else_text = ev["cond"]
            curr_y += 15
            continue
        elif ev_type == "alt_end":
            alt_end_y = curr_y + 10
            # Draw alt box across the participants
            ab_x = col_x[2] - 40
            ab_w = (col_x[5] if len(col_x) > 5 else col_x[-1]) - ab_x + 40
            ab_h = alt_end_y - alt_start_y
            # Alt border
            svg.append(f'<rect x="{ab_x}" y="{alt_start_y}" width="{ab_w}" height="{ab_h}" fill="none" stroke="#000000" stroke-width="1.2"/>')
            # Alt tag
            svg.append(f'<polygon points="{ab_x},{alt_start_y} {ab_x+70},{alt_start_y} {ab_x+75},{alt_start_y+10} {ab_x+70},{alt_start_y+20} {ab_x},{alt_start_y+20}" fill="#FFFFFF" stroke="#000000" stroke-width="1.2"/>')
            svg.append(f'<text x="{ab_x+5}" y="{alt_start_y+14}" font-family="Arial, Helvetica, sans-serif" font-size="10.5" font-weight="bold" fill="#000000">alt {alt_cond_text}</text>')
            # Alt else dashed divider
            if alt_else_y:
                svg.append(f'<line x1="{ab_x}" y1="{alt_else_y}" x2="{ab_x+ab_w}" y2="{alt_else_y}" stroke="#000000" stroke-width="1.2" stroke-dasharray="6,4"/>')
                svg.append(f'<text x="{ab_x+8}" y="{alt_else_y+14}" font-family="Arial, Helvetica, sans-serif" font-size="10.5" font-weight="bold" fill="#000000">{alt_else_text}</text>')
            curr_y += 15
            continue

        if ev_type == "msg":
            f_idx = ev["from"]
            t_idx = ev["to"]
            x1 = col_x[f_idx]
            x2 = col_x[t_idx]
            
            # Activation bars (white with black border)
            svg.append(f'<rect x="{x1-5}" y="{curr_y-5}" width="10" height="18" fill="#FFFFFF" stroke="#000000" stroke-width="1.1"/>')
            svg.append(f'<rect x="{x2-5}" y="{curr_y-5}" width="10" height="18" fill="#FFFFFF" stroke="#000000" stroke-width="1.1"/>')
            
            # Line with sync arrow
            adj_x1 = x1 + (5 if x2 > x1 else -5)
            adj_x2 = x2 + (-5 if x2 > x1 else 5)
            svg.append(f'<line x1="{adj_x1}" y1="{curr_y}" x2="{adj_x2}" y2="{curr_y}" stroke="#000000" stroke-width="1.2" marker-end="url(#arrow-sync)"/>')
            
            # Label
            mid_x = (x1 + x2) / 2.0
            escaped_text = html.escape(ev["text"])
            svg.append(f'<text x="{mid_x}" y="{curr_y-4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">{escaped_text}</text>')
            curr_y += row_h

        elif ev_type == "ret":
            f_idx = ev["from"]
            t_idx = ev["to"]
            x1 = col_x[f_idx]
            x2 = col_x[t_idx]
            
            # Activation bars
            svg.append(f'<rect x="{x1-5}" y="{curr_y-5}" width="10" height="18" fill="#FFFFFF" stroke="#000000" stroke-width="1.1"/>')
            svg.append(f'<rect x="{x2-5}" y="{curr_y-5}" width="10" height="18" fill="#FFFFFF" stroke="#000000" stroke-width="1.1"/>')

            # Dashed return line
            adj_x1 = x1 + (5 if x2 > x1 else -5)
            adj_x2 = x2 + (-5 if x2 > x1 else 5)
            svg.append(f'<line x1="{adj_x1}" y1="{curr_y}" x2="{adj_x2}" y2="{curr_y}" stroke="#000000" stroke-width="1.2" stroke-dasharray="4,3" marker-end="url(#arrow-ret)"/>')
            
            # Label
            mid_x = (x1 + x2) / 2.0
            escaped_text = html.escape(ev["text"])
            svg.append(f'<text x="{mid_x}" y="{curr_y-4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" font-style="italic" fill="#000000">{escaped_text}</text>')
            curr_y += row_h

        elif ev_type == "self":
            idx = ev["at"]
            cx = col_x[idx]
            svg.append(f'<rect x="{cx-5}" y="{curr_y-5}" width="10" height="22" fill="#FFFFFF" stroke="#000000" stroke-width="1.1"/>')
            # Loop arrow
            loop_path = f"M {cx+5} {curr_y} L {cx+22} {curr_y} L {cx+22} {curr_y+14} L {cx+7} {curr_y+14}"
            svg.append(f'<path d="{loop_path}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#arrow-sync)"/>')
            escaped_text = html.escape(ev["text"])
            svg.append(f'<text x="{cx+28}" y="{curr_y+10}" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">{escaped_text}</text>')
            curr_y += row_h

    svg.append('</svg>')
    return total_w, total_h, "\n".join(svg)

# Generate SVG and PNG for each sequence diagram
for cu_key, d in sequence_data.items():
    w, h, svg_content = render_sequence_svg(d)
    
    # Save SVG
    svg_path = f"docs/diagramas/{d['id']}.svg"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    # Render PNG with resvg_py
    png_bytes = resvg_py.svg_to_bytes(svg_content)
    png_path = f"docs/diagramas/{d['id']}.png"
    with open(png_path, "wb") as f:
        f.write(png_bytes)
        
    print(f"Generated sequence diagram: {svg_path} & {png_path} ({len(png_bytes)} bytes)")

print("All 4 sequence SVG and PNG diagrams generated!")
