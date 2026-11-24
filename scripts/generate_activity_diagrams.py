import os
import shutil
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)
brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'
os.makedirs(brain_diag_dir, exist_ok=True)

# Definition of the 5 key business activities (Requirements Phase - No "CUXX" codes)
activities_data = [
    {
        "id": "act_01_entrada_material",
        "title": "Registrar Entrada de Material en Obra",
        "description": "Proceso de recepción, inspección física y registro de ingreso de materiales a los almacenes de obra contra orden de compra.",
        "swimlanes": ["Jefe de Obra / Almacenero", "Sistema OBRATEC"],
        "w": 900,
        "h": 820,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 230},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 140, "w": 180, "h": 50, "text": "Recibir remisión física\ny cargamento en obra"},
            {"id": "a2", "type": "action", "lane": 0, "y": 200, "x": 140, "w": 180, "h": 50, "text": "Ingresar código de material\no número de orden de compra"},
            {"id": "a3", "type": "action", "lane": 1, "y": 200, "x": 580, "w": 180, "h": 50, "text": "Validar orden de compra\ny especificaciones vigentes"},
            {"id": "d1", "type": "decision", "lane": 0, "y": 290, "x": 210, "w": 40, "h": 40, "text": "¿Cumple calidad\ny especificación?"},
            {"id": "a_rechazo", "type": "action", "lane": 0, "y": 380, "x": 50, "w": 160, "h": 50, "text": "Rechazar cargamento\ny registrar motivo de falla"},
            {"id": "a_alerta", "type": "action", "lane": 1, "y": 380, "x": 400, "w": 170, "h": 50, "text": "Emitir alerta de no conformidad\ny notificar a compras"},
            {"id": "end_rechazo", "type": "end", "lane": 1, "y": 460, "x": 475},
            {"id": "a4", "type": "action", "lane": 0, "y": 380, "x": 250, "w": 160, "h": 50, "text": "Ingresar cantidad real recibida,\nlote y almacén de destino"},
            {"id": "a5", "type": "action", "lane": 1, "y": 500, "x": 580, "w": 190, "h": 55, "text": "Actualizar kardex de inventario\ny saldos de orden de compra"},
            {"id": "a6", "type": "action", "lane": 1, "y": 590, "x": 580, "w": 190, "h": 50, "text": "Generar comprobante digital\nde ingreso a almacén"},
            {"id": "a7", "type": "action", "lane": 0, "y": 680, "x": 140, "w": 180, "h": 50, "text": "Archivar comprobante y remisión\ncon código de recepción"},
            {"id": "end_exito", "type": "end", "lane": 0, "y": 760, "x": 220}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", ""),
            ("a3", "d1", ""),
            ("d1", "a_rechazo", "[No cumple]"),
            ("d1", "a4", "[Cumple calidad]"),
            ("a_rechazo", "a_alerta", ""),
            ("a_alerta", "end_rechazo", ""),
            ("a4", "a5", ""),
            ("a5", "a6", ""),
            ("a6", "a7", ""),
            ("a7", "end_exito", "")
        ]
    },
    {
        "id": "act_02_salida_material",
        "title": "Registrar Salida de Material de Obra",
        "description": "Proceso de solicitud, verificación de disponibilidad, aprobación del supervisor y despacho físico de materiales hacia los frentes de trabajo.",
        "swimlanes": ["Encargado de Cuadrilla", "Supervisor / Jefe de Obra", "Sistema OBRATEC"],
        "w": 1100,
        "h": 840,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 170},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 90, "w": 170, "h": 50, "text": "Solicitar vale de salida\nindicando frente y actividad"},
            {"id": "a2", "type": "action", "lane": 2, "y": 120, "x": 830, "w": 170, "h": 50, "text": "Verificar stock disponible\nen almacén de la obra"},
            {"id": "d1", "type": "decision", "lane": 2, "y": 210, "x": 895, "w": 40, "h": 40, "text": "¿Hay stock\nsuficiente?"},
            {"id": "a_nostock", "type": "action", "lane": 2, "y": 290, "x": 760, "w": 160, "h": 50, "text": "Notificar desabastecimiento\ny sugerir reposición"},
            {"id": "end_nostock", "type": "end", "lane": 2, "y": 380, "x": 830},
            {"id": "a3", "type": "action", "lane": 1, "y": 290, "x": 460, "w": 170, "h": 55, "text": "Evaluar pertinencia técnica\nsegún avance programado"},
            {"id": "d2", "type": "decision", "lane": 1, "y": 380, "x": 525, "w": 40, "h": 40, "text": "¿Autoriza\ndespacho?"},
            {"id": "a_rechazo", "type": "action", "lane": 1, "y": 460, "x": 390, "w": 150, "h": 50, "text": "Registrar justificación\nde rechazo del pedido"},
            {"id": "end_rechazo", "type": "end", "lane": 0, "y": 550, "x": 170},
            {"id": "a4", "type": "action", "lane": 1, "y": 460, "x": 570, "w": 150, "h": 50, "text": "Firmar digitalmente\nautorización de salida"},
            {"id": "a5", "type": "action", "lane": 2, "y": 550, "x": 830, "w": 180, "h": 55, "text": "Descontar inventario real\ne imputar costo a la partida"},
            {"id": "a6", "type": "action", "lane": 0, "y": 650, "x": 90, "w": 170, "h": 50, "text": "Retirar material de almacén\ny firmar recepción en terreno"},
            {"id": "end_exito", "type": "end", "lane": 0, "y": 740, "x": 170}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "d1", ""),
            ("d1", "a_nostock", "[No disponible]"),
            ("a_nostock", "end_nostock", ""),
            ("d1", "a3", "[Stock OK]"),
            ("a3", "d2", ""),
            ("d2", "a_rechazo", "[Rechazado]"),
            ("a_rechazo", "end_rechazo", ""),
            ("d2", "a4", "[Aprobado]"),
            ("a4", "a5", ""),
            ("a5", "a6", ""),
            ("a6", "end_exito", "")
        ]
    },
    {
        "id": "act_03_consultas_tecnicas",
        "title": "Gestionar Solicitudes Técnicas y Aclaraciones de Obra",
        "description": "Flujo de resolución de dudas técnicas, inconsistencias de planos o solicitudes de información (RFI) entre terreno y proyectistas.",
        "swimlanes": ["Supervisor en Obra", "Proyectista / Especialista", "Sistema OBRATEC"],
        "w": 1150,
        "h": 860,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 180},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 90, "w": 180, "h": 55, "text": "Detectar discrepancia o duda\nen planos / especificaciones"},
            {"id": "a2", "type": "action", "lane": 0, "y": 210, "x": 90, "w": 180, "h": 55, "text": "Registrar consulta técnica,\nadjuntar fotos y fijar urgencia"},
            {"id": "a3", "type": "action", "lane": 2, "y": 210, "x": 860, "w": 180, "h": 50, "text": "Asignar código único (RFI)\ny notificar al especialista"},
            {"id": "a4", "type": "action", "lane": 1, "y": 300, "x": 480, "w": 180, "h": 50, "text": "Examinar antecedentes,\nplanos base y memorias"},
            {"id": "d1", "type": "decision", "lane": 1, "y": 390, "x": 550, "w": 40, "h": 40, "text": "¿Modifica diseño\no presupuesto?"},
            {"id": "a_costos", "type": "action", "lane": 1, "y": 480, "x": 400, "w": 170, "h": 50, "text": "Elaborar orden de cambio\ny convocar a comité de costos"},
            {"id": "a_directa", "type": "action", "lane": 1, "y": 480, "x": 590, "w": 170, "h": 50, "text": "Redactar dictamen técnico\ny adjuntar plano aclaratorio"},
            {"id": "merge1", "type": "join", "lane": 1, "y": 570, "x": 550, "w": 40, "h": 20, "text": ""},
            {"id": "a5", "type": "action", "lane": 2, "y": 620, "x": 860, "w": 180, "h": 55, "text": "Marcar RFI como RESUELTA\ny distribuir respuesta oficial"},
            {"id": "a6", "type": "action", "lane": 0, "y": 710, "x": 90, "w": 180, "h": 50, "text": "Aplicar resolución en terreno\ny cerrar consulta técnica"},
            {"id": "end_exito", "type": "end", "lane": 0, "y": 790, "x": 180}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", ""),
            ("a3", "a4", ""),
            ("a4", "d1", ""),
            ("d1", "a_costos", "[Impacto mayor]"),
            ("d1", "a_directa", "[Aclaración directa]"),
            ("a_costos", "merge1", ""),
            ("a_directa", "merge1", ""),
            ("merge1", "a5", ""),
            ("a5", "a6", ""),
            ("a6", "end_exito", "")
        ]
    },
    {
        "id": "act_04_operacion_offline",
        "title": "Operación Offline y Sincronización de Datos en Terreno",
        "description": "Ciclo de trabajo sin conectividad para captura de avances e incidencias, con sincronización automática e idempotente al detectar red.",
        "swimlanes": ["Personal de Campo", "Aplicación Móvil (Offline)", "Servidor Central OBRATEC"],
        "w": 1180,
        "h": 900,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 180},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 90, "w": 180, "h": 50, "text": "Ingresar a frente de obra\nsin cobertura de red"},
            {"id": "a2", "type": "action", "lane": 1, "y": 120, "x": 480, "w": 180, "h": 50, "text": "Cargar snapshot local de obra,\nfrentes y cronograma"},
            {"id": "a3", "type": "action", "lane": 0, "y": 210, "x": 90, "w": 180, "h": 55, "text": "Registrar avance físico o\nreportar incidencia con fotos"},
            {"id": "a4", "type": "action", "lane": 1, "y": 210, "x": 480, "w": 190, "h": 55, "text": "Encolar registro en SQLite local\ncomo PENDIENTE_SYNC"},
            {"id": "a5", "type": "action", "lane": 1, "y": 300, "x": 480, "w": 190, "h": 50, "text": "Mostrar confirmación local\ny actualizar badge de cola"},
            {"id": "d1", "type": "decision", "lane": 1, "y": 390, "x": 555, "w": 40, "h": 40, "text": "¿Detecta red\n(WiFi/4G)?"},
            {"id": "a_espera", "type": "action", "lane": 0, "y": 470, "x": 90, "w": 180, "h": 50, "text": "Continuar jornada de trabajo\ny consultas sobre caché"},
            {"id": "a6", "type": "action", "lane": 1, "y": 470, "x": 480, "w": 190, "h": 50, "text": "Empaquetar lote de pendientes\ny enviar petición HTTP batch"},
            {"id": "a7", "type": "action", "lane": 2, "y": 470, "x": 890, "w": 190, "h": 55, "text": "Validar autenticación,\npermisos e idempotencia"},
            {"id": "d2", "type": "decision", "lane": 2, "y": 570, "x": 965, "w": 40, "h": 40, "text": "¿Hay conflictos\nde versión?"},
            {"id": "a_resolve", "type": "action", "lane": 2, "y": 660, "x": 810, "w": 160, "h": 50, "text": "Aplicar regla Last-Write\ny registrar en log de auditoría"},
            {"id": "a_insert", "type": "action", "lane": 2, "y": 660, "x": 990, "w": 160, "h": 50, "text": "Consolidar avances e\nincidencias en base de datos"},
            {"id": "merge1", "type": "join", "lane": 2, "y": 740, "x": 965, "w": 40, "h": 20, "text": ""},
            {"id": "a8", "type": "action", "lane": 1, "y": 790, "x": 480, "w": 190, "h": 50, "text": "Actualizar registros locales\na SINCRONIZADO y limpiar"},
            {"id": "end_exito", "type": "end", "lane": 0, "y": 850, "x": 180}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", ""),
            ("a3", "a4", ""),
            ("a4", "a5", ""),
            ("a5", "d1", ""),
            ("d1", "a_espera", "[Sin señal]"),
            ("d1", "a6", "[Conexión restaurada]"),
            ("a6", "a7", ""),
            ("a7", "d2", ""),
            ("d2", "a_resolve", "[Conflicto]"),
            ("d2", "a_insert", "[Sin conflicto]"),
            ("a_resolve", "merge1", ""),
            ("a_insert", "merge1", ""),
            ("merge1", "a8", "Confirmación de lote"),
            ("a8", "end_exito", "Notificar éxito")
        ]
    },
    {
        "id": "act_05_asistente_comercial",
        "title": "Consultar Asistente Comercial y Recomendaciones",
        "description": "Interacción interactiva del cliente potencial con el motor de IA para perfilamiento, recomendación de inmuebles y captura de oportunidades CRM.",
        "swimlanes": ["Cliente Potencial", "Asistente Inteligente (IA)", "Asesor Comercial (CRM)"],
        "w": 1120,
        "h": 840,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 170},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 90, "w": 170, "h": 50, "text": "Ingresar consulta en lenguaje\nnatural sobre proyectos"},
            {"id": "a2", "type": "action", "lane": 1, "y": 120, "x": 470, "w": 180, "h": 50, "text": "Interpretar intención, presupuesto\ny zona de interés"},
            {"id": "a3", "type": "action", "lane": 1, "y": 210, "x": 470, "w": 180, "h": 50, "text": "Consultar catálogo de unidades\ny disponibilidad en vivo"},
            {"id": "d1", "type": "decision", "lane": 1, "y": 300, "x": 540, "w": 40, "h": 40, "text": "¿Coincidencias\nencontradas?"},
            {"id": "a_alt", "type": "action", "lane": 1, "y": 390, "x": 380, "w": 160, "h": 50, "text": "Sugerir proyectos cercanos\no solicitar ampliar filtros"},
            {"id": "a_propuesta", "type": "action", "lane": 1, "y": 390, "x": 570, "w": 170, "h": 50, "text": "Presentar unidades recomendadas,\nplanos y simulador de cuotas"},
            {"id": "merge1", "type": "join", "lane": 1, "y": 480, "x": 540, "w": 40, "h": 20, "text": ""},
            {"id": "a4", "type": "action", "lane": 0, "y": 530, "x": 90, "w": 170, "h": 50, "text": "Seleccionar inmueble y solicitar\nagendar visita o cotización"},
            {"id": "a5", "type": "action", "lane": 1, "y": 620, "x": 470, "w": 180, "h": 50, "text": "Registrar lead en CRM y\ncalcular score comercial"},
            {"id": "a6", "type": "action", "lane": 2, "y": 710, "x": 840, "w": 180, "h": 50, "text": "Recibir notificación en vivo\ny expediente del prospecto"},
            {"id": "end_exito", "type": "end", "lane": 2, "y": 790, "x": 930}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", ""),
            ("a3", "d1", ""),
            ("d1", "a_alt", "[Sin stock exacto]"),
            ("d1", "a_propuesta", "[Disponibles]"),
            ("a_alt", "merge1", ""),
            ("a_propuesta", "merge1", ""),
            ("merge1", "a4", "Mostrar opciones"),
            ("a4", "a5", "Datos de contacto"),
            ("a5", "a6", "Asignación de oportunidad"),
            ("a6", "end_exito", "Contacto comercial")
        ]
    }
]

# Helper to generate SVG and PNG for each activity
for act in activities_data:
    w = act["w"]
    h = act["h"]
    lanes = act["swimlanes"]
    num_lanes = len(lanes)
    lane_w = (w - 60) / num_lanes

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    svg.append('''<defs>
      <marker id="act-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
      </marker>
    </defs>''')
    svg.append(f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>')

    # Title
    svg.append(f'<text x="30" y="32" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="bold" fill="#000000">Diagrama de Actividades: {act["title"]}</text>')
    svg.append(f'<text x="30" y="48" font-family="Arial, Helvetica, sans-serif" font-size="10.5" fill="#555555">{act["description"]}</text>')

    # Outer border
    svg.append(f'<rect x="30" y="60" width="{w-60}" height="{h-80}" fill="none" stroke="#000000" stroke-width="1.3"/>')

    # Swimlanes
    for i, lname in enumerate(lanes):
        lx = 30 + i * lane_w
        # Header box
        svg.append(f'<rect x="{lx}" y="60" width="{lane_w}" height="32" fill="#F4F4F4" stroke="#000000" stroke-width="1.2"/>')
        svg.append(f'<text x="{lx + lane_w/2}" y="81" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#000000">{lname}</text>')
        # Vertical divider
        if i > 0:
            svg.append(f'<line x1="{lx}" y1="92" x2="{lx}" y2="{h-20}" stroke="#000000" stroke-width="1.2"/>')

    # Node map for coordinate lookup
    node_map = {}
    for n in act["nodes"]:
        node_map[n["id"]] = n

    # Draw Edges first
    for src_id, dst_id, lbl in act["edges"]:
        n1 = node_map[src_id]
        n2 = node_map[dst_id]

        # Calculate connection points
        if n1["type"] == "start":
            x1, y1 = n1["x"], n1["y"] + 10
        elif n1["type"] == "decision":
            x1, y1 = n1["x"] + n1["w"]/2, n1["y"] + n1["h"]
        elif n1["type"] == "join":
            x1, y1 = n1["x"] + n1["w"]/2, n1["y"] + n1["h"]
        else:
            x1, y1 = n1["x"] + n1["w"]/2, n1["y"] + n1["h"]

        if n2["type"] == "end":
            x2, y2 = n2["x"], n2["y"] - 10
        elif n2["type"] == "decision":
            x2, y2 = n2["x"] + n2["w"]/2, n2["y"]
        elif n2["type"] == "join":
            x2, y2 = n2["x"] + n2["w"]/2, n2["y"]
        else:
            x2, y2 = n2["x"] + n2["w"]/2, n2["y"]

        # Orthogonal routing
        if abs(x1 - x2) < 5:
            # Straight vertical
            svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000000" stroke-width="1.2" marker-end="url(#act-arr)"/>')
            if lbl:
                svg.append(f'<text x="{x1 + 8}" y="{(y1+y2)/2}" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#000000">{lbl}</text>')
        else:
            # Step route
            mid_y = y1 + (y2 - y1) * 0.45
            svg.append(f'<path d="M {x1} {y1} L {x1} {mid_y} L {x2} {mid_y} L {x2} {y2}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#act-arr)"/>')
            if lbl:
                svg.append(f'<text x="{(x1+x2)/2}" y="{mid_y - 4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#000000">{lbl}</text>')

    # Draw Nodes
    for n in act["nodes"]:
        nt = n["type"]
        if nt == "start":
            svg.append(f'<circle cx="{n["x"]}" cy="{n["y"]}" r="11" fill="#000000" stroke="#000000" stroke-width="1.2"/>')
        elif nt == "end":
            svg.append(f'<circle cx="{n["x"]}" cy="{n["y"]}" r="12" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
            svg.append(f'<circle cx="{n["x"]}" cy="{n["y"]}" r="7" fill="#000000"/>')
        elif nt == "decision":
            dx, dy, dw, dh = n["x"], n["y"], n["w"], n["h"]
            cx, cy = dx + dw/2, dy + dh/2
            svg.append(f'<polygon points="{cx},{dy} {dx+dw},{cy} {cx},{dy+dh} {dx},{cy}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
            if "text" in n and n["text"]:
                lines = n["text"].split("\n")
                ty = dy - len(lines)*11 - 2
                for l in lines:
                    svg.append(f'<text x="{cx}" y="{ty}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#000000">{l}</text>')
                    ty += 12
        elif nt == "join":
            jx, jy, jw, jh = n["x"], n["y"], n["w"], n["h"]
            svg.append(f'<rect x="{jx}" y="{jy}" width="{jw}" height="{jh}" fill="#000000" rx="3"/>')
        elif nt == "action":
            ax, ay, aw, ah = n["x"], n["y"], n["w"], n["h"]
            svg.append(f'<rect x="{ax}" y="{ay}" width="{aw}" height="{ah}" rx="12" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
            lines = n["text"].split("\n")
            start_ty = ay + ah/2 - (len(lines)-1)*6 + 3
            for l in lines:
                svg.append(f'<text x="{ax + aw/2}" y="{start_ty}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">{l}</text>')
                start_ty += 13

    svg.append('</svg>')
    svg_content = "\n".join(svg)
    svg_path = f'docs/diagramas/{act["id"]}.svg'
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    png_path = f'docs/diagramas/{act["id"]}.png'
    png_bytes = resvg_py.svg_to_bytes(svg_content)
    with open(png_path, 'wb') as f:
        f.write(png_bytes)

    shutil.copyfile(svg_path, os.path.join(brain_diag_dir, f'{act["id"]}.svg'))
    shutil.copyfile(png_path, os.path.join(brain_diag_dir, f'{act["id"]}.png'))
    print(f"Generated SVG and PNG for: {act['title']}")

# ==============================================================================
# CONSOLIDATED MULTI-TAB DRAW.IO FILE (All 5 Activities in separate tabs)
# ==============================================================================
drawio_xml = []
drawio_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
drawio_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-22T21:00:00.000Z" agent="Antigravity" version="24.0.0" type="device">')

for act in activities_data:
    act_id = act["id"]
    tab_name = act["title"]
    w = act["w"]
    h = act["h"]
    lanes = act["swimlanes"]
    num_lanes = len(lanes)
    lane_w = (w - 60) / num_lanes

    drawio_xml.append(f'  <diagram id="{act_id}" name="{html.escape(tab_name)}">')
    drawio_xml.append(f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{w}" pageHeight="{h}" background="#FFFFFF" math="0" shadow="0">')
    drawio_xml.append('      <root>')
    drawio_xml.append('        <mxCell id="0" />')
    drawio_xml.append('        <mxCell id="1" parent="0" />')

    # Title
    drawio_xml.append(f'        <mxCell id="title_{act_id}" value="&lt;b&gt;Diagrama de Actividades: {html.escape(act["title"])}&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;{html.escape(act["description"])}&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=12;fontColor=#000000;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="30" y="15" width="{w-60}" height="35" as="geometry" />')
    drawio_xml.append('        </mxCell>')

    # Outer Pool Container
    drawio_xml.append(f'        <mxCell id="pool_{act_id}" value="" style="swimlane;html=1;childLayout=stackLayout;resizeParent=1;resizeParentMax=0;startSize=0;horizontal=1;horizontalStack=1;fillColor=none;strokeColor=#000000;strokeWidth=1.3;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="30" y="55" width="{w-60}" height="{h-75}" as="geometry" />')
    drawio_xml.append('        </mxCell>')

    # Lanes
    for idx, lname in enumerate(lanes):
        drawio_xml.append(f'        <mxCell id="lane_{act_id}_{idx}" value="&lt;b&gt;{html.escape(lname)}&lt;/b&gt;" style="swimlane;html=1;startSize=30;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=11;fontColor=#000000;" vertex="1" parent="pool_{act_id}">')
        drawio_xml.append(f'          <mxGeometry x="{int(idx*lane_w)}" y="0" width="{int(lane_w)}" height="{h-75}" as="geometry" />')
        drawio_xml.append('        </mxCell>')

    # Nodes
    for n in act["nodes"]:
        nid = f"{act_id}_{n['id']}"
        lane_idx = n["lane"]
        parent_id = f"lane_{act_id}_{lane_idx}"
        # Relative coordinates inside the lane
        rx = n["x"] - (30 + lane_idx * lane_w)
        ry = n["y"] - 55

        if n["type"] == "start":
            drawio_xml.append(f'        <mxCell id="{nid}" value="" style="ellipse;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=#000000;strokeWidth=1.2;" vertex="1" parent="{parent_id}">')
            drawio_xml.append(f'          <mxGeometry x="{int(rx-11)}" y="{int(ry-11)}" width="22" height="22" as="geometry" />')
            drawio_xml.append('        </mxCell>')
        elif n["type"] == "end":
            drawio_xml.append(f'        <mxCell id="{nid}" value="" style="ellipse;shape=doubleEllipse;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=#000000;strokeWidth=1.4;" vertex="1" parent="{parent_id}">')
            drawio_xml.append(f'          <mxGeometry x="{int(rx-12)}" y="{int(ry-12)}" width="24" height="24" as="geometry" />')
            drawio_xml.append('        </mxCell>')
        elif n["type"] == "decision":
            drawio_xml.append(f'        <mxCell id="{nid}" value="" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;" vertex="1" parent="{parent_id}">')
            drawio_xml.append(f'          <mxGeometry x="{int(rx)}" y="{int(ry)}" width="{int(n["w"])}" height="{int(n["h"])}" as="geometry" />')
            drawio_xml.append('        </mxCell>')
            if "text" in n and n["text"]:
                txt = html.escape(n["text"]).replace("\n", "&lt;br&gt;")
                drawio_xml.append(f'        <mxCell id="{nid}_lbl" value="&lt;b&gt;{txt}&lt;/b&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=bottom;fontSize=9.5;fontFamily=Arial;fontColor=#000000;" vertex="1" parent="{parent_id}">')
                drawio_xml.append(f'          <mxGeometry x="{int(rx - 40)}" y="{int(ry - 30)}" width="120" height="25" as="geometry" />')
                drawio_xml.append('        </mxCell>')
        elif n["type"] == "join":
            drawio_xml.append(f'        <mxCell id="{nid}" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=#000000;strokeWidth=1.2;" vertex="1" parent="{parent_id}">')
            drawio_xml.append(f'          <mxGeometry x="{int(rx)}" y="{int(ry)}" width="{int(n["w"])}" height="{int(n["h"])}" as="geometry" />')
            drawio_xml.append('        </mxCell>')
        elif n["type"] == "action":
            txt = html.escape(n["text"]).replace("\n", "&lt;br&gt;")
            drawio_xml.append(f'        <mxCell id="{nid}" value="{txt}" style="rounded=1;arcSize=24;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontColor=#000000;align=center;" vertex="1" parent="{parent_id}">')
            drawio_xml.append(f'          <mxGeometry x="{int(rx)}" y="{int(ry)}" width="{int(n["w"])}" height="{int(n["h"])}" as="geometry" />')
            drawio_xml.append('        </mxCell>')

    # Edges
    for edge_idx, (src_id, dst_id, lbl) in enumerate(act["edges"]):
        eid = f"edge_{act_id}_{edge_idx}"
        full_src = f"{act_id}_{src_id}"
        full_dst = f"{act_id}_{dst_id}"
        lbl_escaped = html.escape(lbl) if lbl else ""
        drawio_xml.append(f'        <mxCell id="{eid}" value="{lbl_escaped}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;" edge="1" parent="1" source="{full_src}" target="{full_dst}">')
        drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
        drawio_xml.append('        </mxCell>')

    drawio_xml.append('      </root>')
    drawio_xml.append('    </mxGraphModel>')
    drawio_xml.append('  </diagram>')

drawio_xml.append('</mxfile>')

drawio_path = 'docs/diagramas/diagramas_actividades.drawio'
with open(drawio_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(drawio_xml))

shutil.copyfile(drawio_path, os.path.join(brain_diag_dir, 'diagramas_actividades.drawio'))
print("Generated Multi-tab Draw.io file for all 5 Activities!")
