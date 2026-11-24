import os
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)

# Define the 4 Analysis Class Diagrams specifications
diagrams_data = {
    "cu35": {
        "id": "analisis_cu35_entrada_material",
        "cu_title": "CU35: Registrar entrada de material (Jefe de Obra / Supervisor | Web)",
        "tab_name": "CU35 - Entrada Material",
        "form": {
            "title": "Form Registrar_Entrada_Material",
            "attrs": [
                "+ id_material",
                "+ tipo_movimiento = \"ENTRADA_AJUSTE\"",
                "+ cantidad",
                "+ observaciones",
                "+ stock_minimo",
                "+ id_empresa"
            ],
            "methods": [
                "+ abrirModalEntrada()",
                "+ validarFormulario()",
                "+ registrar_entrada_db()",
                "+ cerrarModal()"
            ]
        },
        "control": {
            "title": "Control_Inventario",
            "attrs": [],
            "methods": [
                "- registrar_ajuste_db()",
                "- validar_permiso_modificar_inventario()",
                "- registrar_movimiento_almacen_db()",
                "- incrementar_stock_material_db()",
                "- registrar_evento_bitacora()"
            ]
        },
        "main_entity": {
            "title": "MATERIAL",
            "attrs": [
                "+ id_material",
                "+ codigo",
                "+ nombre",
                "+ stock_actual",
                "+ stock_minimo",
                "+ precio_unitario",
                "+ id_categoria",
                "+ id_unidad_medida",
                "+ id_empresa"
            ],
            "methods": []
        },
        "related_top": {
            "title": "CATEGORIA_MATERIAL",
            "attrs": [
                "+ id_categoria",
                "+ nombre",
                "+ descripcion"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "1"
        },
        "related_right": {
            "title": "UNIDAD_MEDIDA",
            "attrs": [
                "+ id_unidad_medida",
                "+ nombre",
                "+ abreviatura"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "1"
        },
        "related_bottom": {
            "title": "Empresa",
            "attrs": [
                "+ id_empresa",
                "+ nombre_empresa"
            ],
            "methods": [],
            "is_diamond": True,
            "card_main": "",
            "card_rel": "1"
        },
        "related_extra": {
            "title": "MOVIMIENTO_ALMACEN",
            "attrs": [
                "+ id_movimiento",
                "+ id_material",
                "+ tipo_movimiento",
                "+ cantidad",
                "+ stock_anterior",
                "+ stock_nuevo",
                "+ observaciones",
                "+ fecha_movimiento",
                "+ id_usuario",
                "+ id_empresa"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "0..*"
        }
    },
    "cu36": {
        "id": "analisis_cu36_salida_material",
        "cu_title": "CU36: Registrar salida de material (Jefe de Obra / Supervisor | Web)",
        "tab_name": "CU36 - Salida Material",
        "form": {
            "title": "Form Registrar_Salida_Material",
            "attrs": [
                "+ id_material",
                "+ tipo_movimiento = \"SALIDA_AJUSTE\"",
                "+ cantidad",
                "+ stock_actual_disponible",
                "+ observaciones",
                "+ id_empresa"
            ],
            "methods": [
                "+ abrirModalSalida()",
                "+ verificarStockDisponible()",
                "+ registrar_salida_db()",
                "+ cerrarModal()"
            ]
        },
        "control": {
            "title": "Control_Despacho_Inventario",
            "attrs": [],
            "methods": [
                "- registrar_ajuste_db()",
                "- validar_stock_suficiente()",
                "- decrementar_stock_material_db()",
                "- registrar_movimiento_salida_db()",
                "- registrar_evento_bitacora()"
            ]
        },
        "main_entity": {
            "title": "MATERIAL",
            "attrs": [
                "+ id_material",
                "+ codigo",
                "+ nombre",
                "+ stock_actual",
                "+ stock_minimo",
                "+ precio_unitario",
                "+ id_categoria",
                "+ id_unidad_medida",
                "+ id_empresa"
            ],
            "methods": []
        },
        "related_top": {
            "title": "CATEGORIA_MATERIAL",
            "attrs": [
                "+ id_categoria",
                "+ nombre"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "1"
        },
        "related_right": {
            "title": "UNIDAD_MEDIDA",
            "attrs": [
                "+ id_unidad_medida",
                "+ nombre",
                "+ abreviatura"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "1"
        },
        "related_bottom": {
            "title": "Empresa",
            "attrs": [
                "+ id_empresa",
                "+ nombre_empresa"
            ],
            "methods": [],
            "is_diamond": True,
            "card_main": "",
            "card_rel": "1"
        },
        "related_extra": {
            "title": "MOVIMIENTO_ALMACEN",
            "attrs": [
                "+ id_movimiento",
                "+ id_material",
                "+ tipo_movimiento",
                "+ cantidad",
                "+ stock_anterior",
                "+ stock_nuevo",
                "+ observaciones",
                "+ fecha_movimiento",
                "+ id_usuario",
                "+ id_empresa"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "0..*"
        }
    },
    "cu23": {
        "id": "analisis_cu23_consultas_tecnicas",
        "cu_title": "CU23: Gestionar solicitudes técnicas y aclaraciones de obra (RFI) (Jefe de Obra / Supervisor | Web / Móvil)",
        "tab_name": "CU23 - Consultas Técnicas",
        "form": {
            "title": "Form Consultas_Tecnicas_RFI",
            "attrs": [
                "+ id_obra",
                "+ codigo",
                "+ asunto",
                "+ descripcion",
                "+ referencia_tecnica",
                "+ asignado_a",
                "+ respuesta_texto",
                "+ motivo_cierre"
            ],
            "methods": [
                "+ abrirModalCrear()",
                "+ guardar_nueva_consulta_db()",
                "+ abrirDetalleConsulta()",
                "+ asignar_responsable_db()",
                "+ registrar_respuesta_db()",
                "+ cerrar_consulta_db()"
            ]
        },
        "control": {
            "title": "Control_Consultas_Tecnicas",
            "attrs": [],
            "methods": [
                "- registrar_consulta_obra_db()",
                "- validar_estado_abierto()",
                "- asignar_responsable_db()",
                "- agregar_respuesta_tecnica_db()",
                "- cambiar_estado_consulta_db()",
                "- registrar_historial_evento()"
            ]
        },
        "main_entity": {
            "title": "CONSULTA_TECNICA",
            "attrs": [
                "+ id_consulta_tecnica",
                "+ id_obra",
                "+ id_empresa",
                "+ codigo",
                "+ asunto",
                "+ descripcion",
                "+ referencia_tecnica",
                "+ estado",
                "+ creado_por",
                "+ asignado_a",
                "+ fecha_asignacion",
                "+ fecha_cierre",
                "+ motivo_cierre"
            ],
            "methods": []
        },
        "related_top": {
            "title": "OBRA",
            "attrs": [
                "+ id_obra",
                "+ nombre",
                "+ codigo",
                "+ estado"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "1"
        },
        "related_right": {
            "title": "CONSULTA_TECNICA_RESPUESTA",
            "attrs": [
                "+ id_consulta_tecnica_respuesta",
                "+ id_consulta_tecnica",
                "+ autor_id",
                "+ contenido",
                "+ created_at"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "0..*"
        },
        "related_bottom": {
            "title": "Empresa",
            "attrs": [
                "+ id_empresa",
                "+ nombre_empresa"
            ],
            "methods": [],
            "is_diamond": True,
            "card_main": "",
            "card_rel": "1"
        },
        "related_extra": {
            "title": "CONSULTA_TECNICA_HISTORIAL",
            "attrs": [
                "+ id_historial",
                "+ id_consulta_tecnica",
                "+ actor_id",
                "+ tipo_evento",
                "+ estado_anterior",
                "+ estado_nuevo",
                "+ detalle",
                "+ created_at"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "0..*"
        }
    },
    "cu34": {
        "id": "analisis_cu34_asistente_comercial",
        "cu_title": "CU34: Consultar asistente comercial y recomendaciones (Cliente potencial | Web)",
        "tab_name": "CU34 - Asistente Comercial",
        "form": {
            "title": "Form Asistente_Comercial_Recomendaciones",
            "attrs": [
                "+ pregunta_consulta",
                "+ id_cliente_potencial",
                "+ presupuesto_maximo",
                "+ preferencias_inmueble",
                "+ historial_conversacion",
                "+ sugerencias_activas"
            ],
            "methods": [
                "+ enviar_pregunta_asistente_db()",
                "+ solicitar_recomendaciones_inmuebles_db()",
                "+ seleccionarSugerencia()",
                "+ registrar_interes_cliente_db()"
            ]
        },
        "control": {
            "title": "Control_Asistente_Comercial",
            "attrs": [],
            "methods": [
                "- consultar_crm_ia()",
                "- obtener_sugerencias_comerciales()",
                "- buscar_unidades_compatibles_db()",
                "- registrar_mensaje_conversacion_db()",
                "- registrar_interaccion_cliente_db()"
            ]
        },
        "main_entity": {
            "title": "CRM_CLIENTE",
            "attrs": [
                "+ id_cliente",
                "+ nombre_completo",
                "+ correo",
                "+ telefono",
                "+ clasificacion",
                "+ estado",
                "+ origen",
                "+ id_usuario",
                "+ id_empresa"
            ],
            "methods": []
        },
        "related_top": {
            "title": "MODELO_UNIDAD",
            "attrs": [
                "+ id_modelo",
                "+ nombre_modelo",
                "+ dormitorios",
                "+ banos",
                "+ descripcion"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "0..*"
        },
        "related_right": {
            "title": "UNIDAD_CONSTRUCCION",
            "attrs": [
                "+ id_unidad",
                "+ id_obra",
                "+ codigo_unidad",
                "+ estado",
                "+ precio_lista",
                "+ superficie_m2",
                "+ id_modelo"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "0..*"
        },
        "related_bottom": {
            "title": "Empresa",
            "attrs": [
                "+ id_empresa",
                "+ nombre_empresa"
            ],
            "methods": [],
            "is_diamond": True,
            "card_main": "",
            "card_rel": "1"
        },
        "related_extra": {
            "title": "CRM_INTERACCION",
            "attrs": [
                "+ id_interaccion",
                "+ id_cliente",
                "+ tipo_interaccion",
                "+ notas",
                "+ fecha_interaccion",
                "+ id_usuario"
            ],
            "methods": [],
            "card_main": "1",
            "card_rel": "0..*"
        }
    }
}

# Helper to render a class box in SVG matching user's image exactly
def render_class_box_svg(title, attrs, methods, x, y, width):
    header_h = 30
    line_h = 18
    attrs_h = max(25, len(attrs) * line_h + 10)
    methods_h = (len(methods) * line_h + 10) if methods else 0
    total_h = header_h + attrs_h + (methods_h if methods else 0)
    
    xml = []
    # Main white rectangle with solid black border
    xml.append(f'<rect x="{x}" y="{y}" width="{width}" height="{total_h}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    
    # Title
    xml.append(f'<text x="{x + width/2.0}" y="{y+20}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="12" font-weight="bold" fill="#000000">{title}</text>')
    
    # Divider below title
    xml.append(f'<line x1="{x}" y1="{y+header_h}" x2="{x+width}" y2="{y+header_h}" stroke="#000000" stroke-width="1.3"/>')
    
    # Attributes
    curr_y = y + header_h + 16
    for attr in attrs:
        xml.append(f'<text x="{x+8}" y="{curr_y}" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#000000">{attr}</text>')
        curr_y += line_h
        
    # Divider below attributes (if methods exist)
    if methods:
        div2_y = y + header_h + attrs_h
        xml.append(f'<line x1="{x}" y1="{div2_y}" x2="{x+width}" y2="{div2_y}" stroke="#000000" stroke-width="1.3"/>')
        curr_y = div2_y + 16
        for m in methods:
            xml.append(f'<text x="{x+8}" y="{curr_y}" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#000000">{m}</text>')
            curr_y += line_h

    return total_h, "".join(xml)

# Helper to generate SVG and PNG for each CU
for cu_key, d in diagrams_data.items():
    svg_w = 1200
    svg_h = 750
    
    # Positions based on user's layout
    # Center: main_entity
    # Left: form -> control -> main_entity
    # Top: related_top
    # Right: related_right
    # Bottom: related_bottom
    # Far Right / Bottom-Right: related_extra
    
    boxes = {}
    # Form
    boxes['form'] = {'x': 40, 'y': 220, 'w': 210, 'title': d['form']['title'], 'attrs': d['form']['attrs'], 'methods': d['form']['methods']}
    # Control
    boxes['control'] = {'x': 300, 'y': 240, 'w': 200, 'title': d['control']['title'], 'attrs': d['control']['attrs'], 'methods': d['control']['methods']}
    # Main Entity
    boxes['main'] = {'x': 550, 'y': 220, 'w': 180, 'title': d['main_entity']['title'], 'attrs': d['main_entity']['attrs'], 'methods': d['main_entity']['methods']}
    # Top
    boxes['top'] = {'x': 565, 'y': 45, 'w': 150, 'title': d['related_top']['title'], 'attrs': d['related_top']['attrs'], 'methods': d['related_top']['methods']}
    # Right
    boxes['right'] = {'x': 790, 'y': 220, 'w': 180, 'title': d['related_right']['title'], 'attrs': d['related_right']['attrs'], 'methods': d['related_right']['methods']}
    # Bottom
    boxes['bottom'] = {'x': 565, 'y': 490, 'w': 150, 'title': d['related_bottom']['title'], 'attrs': d['related_bottom']['attrs'], 'methods': d['related_bottom']['methods']}
    # Extra (bottom-right)
    boxes['extra'] = {'x': 790, 'y': 440, 'w': 190, 'title': d['related_extra']['title'], 'attrs': d['related_extra']['attrs'], 'methods': d['related_extra']['methods']}

    # Compute heights
    for k, b in boxes.items():
        h, _ = render_class_box_svg(b['title'], b['attrs'], b['methods'], b['x'], b['y'], b['w'])
        b['h'] = h

    # Build SVG
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">')
    svg_lines.append(f'<rect width="{svg_w}" height="{svg_h}" fill="#FFFFFF"/>')
    
    # Title Header
    svg_lines.append(f'<text x="40" y="30" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="bold" fill="#333333">{d["cu_title"]}</text>')
    
    # Lines
    # 1. Form to Control
    y_fc = boxes['form']['y'] + 100
    svg_lines.append(f'<line x1="{boxes["form"]["x"] + boxes["form"]["w"]}" y1="{y_fc}" x2="{boxes["control"]["x"]}" y2="{y_fc}" stroke="#000000" stroke-width="1.3"/>')
    
    # 2. Control to Main Entity
    y_cm = boxes['main']['y'] + 60
    svg_lines.append(f'<line x1="{boxes["control"]["x"] + boxes["control"]["w"]}" y1="{y_cm}" x2="{boxes["main"]["x"]}" y2="{y_cm}" stroke="#000000" stroke-width="1.3"/>')
    
    # 3. Main Entity to Top
    x_top = boxes['main']['x'] + boxes['main']['w'] / 2.0
    svg_lines.append(f'<line x1="{x_top}" y1="{boxes["top"]["y"] + boxes["top"]["h"]}" x2="{x_top}" y2="{boxes["main"]["y"]}" stroke="#000000" stroke-width="1.3"/>')
    svg_lines.append(f'<text x="{x_top - 14}" y="{boxes["top"]["y"] + boxes["top"]["h"] + 16}" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#000000">{d["related_top"]["card_rel"]}</text>')
    svg_lines.append(f'<text x="{x_top - 14}" y="{boxes["main"]["y"] - 6}" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#000000">{d["related_top"]["card_main"]}</text>')
    
    # 4. Main Entity to Right
    y_mr = boxes['main']['y'] + 50
    svg_lines.append(f'<line x1="{boxes["main"]["x"] + boxes["main"]["w"]}" y1="{y_mr}" x2="{boxes["right"]["x"]}" y2="{y_mr}" stroke="#000000" stroke-width="1.3"/>')
    svg_lines.append(f'<text x="{boxes["main"]["x"] + boxes["main"]["w"] + 8}" y="{y_mr + 14}" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#000000">{d["related_right"]["card_main"]}</text>')
    svg_lines.append(f'<text x="{boxes["right"]["x"] - 18}" y="{y_mr + 14}" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#000000">{d["related_right"]["card_rel"]}</text>')
    
    # 5. Main Entity to Bottom (with diamond aggregation as in user sample)
    x_bot = boxes['main']['x'] + boxes['main']['w'] / 2.0
    y_m_bot = boxes['main']['y'] + boxes['main']['h']
    y_b_top = boxes['bottom']['y']
    # Diamond at main entity bottom
    dia_h = 14
    dia_w = 10
    svg_lines.append(f'<polygon points="{x_bot},{y_m_bot} {x_bot-dia_w/2},{y_m_bot+dia_h/2} {x_bot},{y_m_bot+dia_h} {x_bot+dia_w/2},{y_m_bot+dia_h/2}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    svg_lines.append(f'<line x1="{x_bot}" y1="{y_m_bot + dia_h}" x2="{x_bot}" y2="{y_b_top}" stroke="#000000" stroke-width="1.3"/>')
    svg_lines.append(f'<text x="{x_bot + 8}" y="{y_b_top - 6}" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#000000">{d["related_bottom"]["card_rel"]}</text>')

    # 6. Main Entity to Extra
    y_me = boxes['main']['y'] + boxes['main']['h'] - 30
    mid_x_extra = (boxes['main']['x'] + boxes['main']['w'] + boxes['extra']['x']) / 2.0
    y_extra = boxes['extra']['y'] + 40
    svg_lines.append(f'<path d="M {boxes["main"]["x"] + boxes["main"]["w"]} {y_me} L {mid_x_extra} {y_me} L {mid_x_extra} {y_extra} L {boxes["extra"]["x"]} {y_extra}" fill="none" stroke="#000000" stroke-width="1.3"/>')
    svg_lines.append(f'<text x="{boxes["main"]["x"] + boxes["main"]["w"] + 8}" y="{y_me - 5}" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#000000">{d["related_extra"]["card_main"]}</text>')
    svg_lines.append(f'<text x="{boxes["extra"]["x"] - 22}" y="{y_extra - 5}" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#000000">{d["related_extra"]["card_rel"]}</text>')

    # Render class boxes
    for k, b in boxes.items():
        _, box_xml = render_class_box_svg(b['title'], b['attrs'], b['methods'], b['x'], b['y'], b['w'])
        svg_lines.append(box_xml)

    svg_lines.append('</svg>')
    svg_str = "\n".join(svg_lines)

    # Save SVG
    svg_file = f"docs/diagramas/{d['id']}.svg"
    with open(svg_file, "w", encoding="utf-8") as f:
        f.write(svg_str)

    # Save PNG
    png_file = f"docs/diagramas/{d['id']}.png"
    png_bytes = resvg_py.svg_to_bytes(svg_str)
    with open(png_file, "wb") as f:
        f.write(png_bytes)

    print(f"Generated {svg_file} and {png_file} ({len(png_bytes)} bytes)")

print("All single CU SVG/PNG diagrams generated!")

