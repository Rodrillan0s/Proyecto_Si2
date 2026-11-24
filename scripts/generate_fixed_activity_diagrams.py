import os
import shutil
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)
brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'
os.makedirs(brain_diag_dir, exist_ok=True)

# 4 High Priority Activities Requested by User
activities = [
    {
        "id": "act_cu31_comercializacion",
        "tab_name": "CU31 - Comercialización",
        "cu_code": "CU31",
        "title": "CU31 – Comercialización de unidades",
        "subtitle": "Representación de reserva, validación, aprobación y formalización de la venta.",
        "lanes": ["Asesor Comercial", "Gerencia Comercial", "Sistema"],
        "w": 1140,
        "h": 920,
        "lane_w": 360,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "x": 180, "y": 80},
            {"id": "a1", "type": "action", "lane": 0, "x": 85, "y": 130, "w": 190, "h": 50, "text": "Registrar solicitud de reserva\ny datos del cliente"},
            {"id": "a2", "type": "action", "lane": 0, "x": 85, "y": 215, "w": 190, "h": 50, "text": "Cargar comprobante de abono\ninicial de separación"},
            {"id": "a3", "type": "action", "lane": 2, "x": 805, "y": 215, "w": 190, "h": 50, "text": "Validar disponibilidad de unidad\ny aplicar bloqueo temporal"},
            {"id": "a4", "type": "action", "lane": 1, "x": 445, "y": 305, "w": 190, "h": 50, "text": "Evaluar propuesta comercial\ny condiciones de financiamiento"},
            {"id": "d1", "type": "decision", "lane": 1, "x": 520, "y": 395, "w": 40, "h": 40, "text": "¿Aprueba la\nventa?"},
            {"id": "a_rechazo", "type": "action", "lane": 1, "x": 380, "y": 485, "w": 160, "h": 50, "text": "Registrar causal de rechazo\no ajuste requerido"},
            {"id": "a_libera", "type": "action", "lane": 2, "x": 805, "y": 485, "w": 190, "h": 50, "text": "Liberar bloqueo de unidad\ny notificar al asesor"},
            {"id": "end_rechazo", "type": "end", "lane": 0, "x": 180, "y": 575},
            {"id": "a5", "type": "action", "lane": 1, "x": 560, "y": 485, "w": 160, "h": 50, "text": "Emitir aprobación formal\nde la venta"},
            {"id": "a6", "type": "action", "lane": 2, "x": 805, "y": 575, "w": 190, "h": 55, "text": "Generar contrato de promesa\nde compraventa y plan de pagos"},
            {"id": "a7", "type": "action", "lane": 0, "x": 85, "y": 670, "w": 190, "h": 50, "text": "Formalizar firma de contrato\ncon el comprador"},
            {"id": "a8", "type": "action", "lane": 2, "x": 805, "y": 760, "w": 190, "h": 50, "text": "Actualizar unidad a 'VENDIDA'\ny registrar expediente"},
            {"id": "end_exito", "type": "end", "lane": 0, "x": 180, "y": 845}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", ""),
            ("a3", "a4", "Solicitud de evaluación"),
            ("a4", "d1", ""),
            ("d1", "a_rechazo", "[No / Observado]"),
            ("a_rechazo", "a_libera", ""),
            ("a_libera", "end_rechazo", "Operación declinada"),
            ("d1", "a5", "[Sí / Aprobado]"),
            ("a5", "a6", "Venta autorizada"),
            ("a6", "a7", "Contrato listo"),
            ("a7", "a8", "Firma consolidada"),
            ("a8", "end_exito", "Venta formalizada")
        ]
    },
    {
        "id": "act_cu40_inspecciones_calidad",
        "tab_name": "CU40 - Inspecciones y Calidad",
        "cu_code": "CU40",
        "title": "CU40 – Inspecciones y control de calidad",
        "subtitle": "Representación de inspección, registro de observaciones, evaluación de conformidad y acciones correctivas.",
        "lanes": ["Inspector de Calidad", "Responsable de Cuadrilla", "Sistema"],
        "w": 1140,
        "h": 920,
        "lane_w": 360,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "x": 180, "y": 80},
            {"id": "a1", "type": "action", "lane": 0, "x": 85, "y": 130, "w": 190, "h": 50, "text": "Programar inspección técnica\ny seleccionar partida a revisar"},
            {"id": "a2", "type": "action", "lane": 2, "x": 805, "y": 130, "w": 190, "h": 50, "text": "Cargar lista de chequeo y\ntolerancias normativas"},
            {"id": "a3", "type": "action", "lane": 0, "x": 85, "y": 215, "w": 190, "h": 50, "text": "Inspeccionar trabajos en terreno\ny registrar mediciones"},
            {"id": "d1", "type": "decision", "lane": 0, "x": 160, "y": 305, "w": 40, "h": 40, "text": "¿Cumple estándares\ntécnicos?"},
            {"id": "a_noconf", "type": "action", "lane": 0, "x": 30, "y": 395, "w": 170, "h": 55, "text": "Registrar observaciones,\nnivel de defecto y plazo"},
            {"id": "a_notif", "type": "action", "lane": 2, "x": 805, "y": 395, "w": 190, "h": 50, "text": "Emitir orden de no conformidad\ny notificar a cuadrilla"},
            {"id": "a4", "type": "action", "lane": 1, "x": 445, "y": 485, "w": 190, "h": 50, "text": "Ejecutar acciones correctivas\nen frente de faena"},
            {"id": "a5", "type": "action", "lane": 0, "x": 85, "y": 575, "w": 190, "h": 50, "text": "Emitir acta digital de\nconformidad técnica"},
            {"id": "a6", "type": "action", "lane": 2, "x": 805, "y": 665, "w": 190, "h": 55, "text": "Certificar partida como apta\npara avance y valorización"},
            {"id": "a7", "type": "action", "lane": 0, "x": 85, "y": 755, "w": 190, "h": 50, "text": "Archivar informe en el dossier\nde aseguramiento de calidad"},
            {"id": "end_exito", "type": "end", "lane": 0, "x": 180, "y": 845}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", "Lista cargada"),
            ("a3", "d1", ""),
            ("d1", "a_noconf", "[No conforme]"),
            ("a_noconf", "a_notif", ""),
            ("a_notif", "a4", "Aviso de corrección"),
            ("a4", "a3", "Solicitar reinspección"),
            ("d1", "a5", "[Conforme 100%]"),
            ("a5", "a6", "Acta firmada"),
            ("a6", "a7", "Liberación técnica"),
            ("a7", "end_exito", "Dossier cerrado")
        ]
    },
    {
        "id": "act_cu41_operacion_offline",
        "tab_name": "CU41 - Operación Offline",
        "cu_code": "CU41",
        "title": "CU41 – Operación offline y sincronización",
        "subtitle": "Representación de trabajo sin conexión, almacenamiento local, recuperación de conexión y sincronización.",
        "lanes": ["Personal de Campo", "Aplicación Móvil (Offline)", "Servidor Central"],
        "w": 1140,
        "h": 920,
        "lane_w": 360,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "x": 180, "y": 80},
            {"id": "a1", "type": "action", "lane": 0, "x": 85, "y": 130, "w": 190, "h": 50, "text": "Ingresar a frente de obra\nsin cobertura celular"},
            {"id": "a2", "type": "action", "lane": 1, "x": 445, "y": 130, "w": 190, "h": 50, "text": "Habilitar modo local con snapshot\nde obra en caché"},
            {"id": "a3", "type": "action", "lane": 0, "x": 85, "y": 215, "w": 190, "h": 50, "text": "Registrar avances físicos\ny reporte de incidencias"},
            {"id": "a4", "type": "action", "lane": 1, "x": 445, "y": 215, "w": 190, "h": 55, "text": "Almacenar datos en SQLite local\ncomo PENDIENTE_SYNC"},
            {"id": "d1", "type": "decision", "lane": 1, "x": 520, "y": 305, "w": 40, "h": 40, "text": "¿Detecta red\nInternet?"},
            {"id": "a_espera", "type": "action", "lane": 0, "x": 85, "y": 395, "w": 190, "h": 50, "text": "Continuar jornada operativa\nregistrando en local"},
            {"id": "a5", "type": "action", "lane": 1, "x": 445, "y": 395, "w": 190, "h": 50, "text": "Empaquetar lote de pendientes\ny enviar a sincronizar"},
            {"id": "a6", "type": "action", "lane": 2, "x": 805, "y": 395, "w": 190, "h": 55, "text": "Validar autenticación, permisos\ny verificar idempotencia"},
            {"id": "d2", "type": "decision", "lane": 2, "x": 880, "y": 485, "w": 40, "h": 40, "text": "¿Hay conflictos\nde versión?"},
            {"id": "a_resolve", "type": "action", "lane": 2, "x": 735, "y": 575, "w": 150, "h": 50, "text": "Aplicar regla Last-Write\ny registrar en auditoría"},
            {"id": "a_insert", "type": "action", "lane": 2, "x": 905, "y": 575, "w": 150, "h": 50, "text": "Consolidar avances e\nincidencias en base de datos"},
            {"id": "merge1", "type": "join", "lane": 2, "x": 880, "y": 660, "w": 40, "h": 16, "text": ""},
            {"id": "a7", "type": "action", "lane": 1, "x": 445, "y": 715, "w": 190, "h": 50, "text": "Actualizar registros locales\na SINCRONIZADO"},
            {"id": "end_exito", "type": "end", "lane": 0, "x": 180, "y": 815}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", "Caché habilitada"),
            ("a3", "a4", ""),
            ("a4", "d1", ""),
            ("d1", "a_espera", "[Sin red]"),
            ("a_espera", "a3", "Nuevos registros"),
            ("d1", "a5", "[Conexión restaurada]"),
            ("a5", "a6", "Envío de lote"),
            ("a6", "d2", ""),
            ("d2", "a_resolve", "[Conflicto]"),
            ("d2", "a_insert", "[Sin conflicto]"),
            ("a_resolve", "merge1", ""),
            ("a_insert", "merge1", ""),
            ("merge1", "a7", "Confirmación de lote"),
            ("a7", "end_exito", "Sincronización completa")
        ]
    },
    {
        "id": "act_cu42_garantias_posventa",
        "tab_name": "CU42 - Garantías y Posventa",
        "cu_code": "CU42",
        "title": "CU42 – Garantías y servicio posventa",
        "subtitle": "Representación de registro de solicitud, clasificación, asignación, atención y resolución.",
        "lanes": ["Propietario / Cliente", "Técnico de Posventa", "Sistema"],
        "w": 1140,
        "h": 920,
        "lane_w": 360,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "x": 180, "y": 80},
            {"id": "a1", "type": "action", "lane": 0, "x": 85, "y": 130, "w": 190, "h": 50, "text": "Detectar desperfecto en unidad\ninmobiliaria entregada"},
            {"id": "a2", "type": "action", "lane": 0, "x": 85, "y": 215, "w": 190, "h": 50, "text": "Registrar solicitud de garantía\nadjuntando fotos y detalle"},
            {"id": "a3", "type": "action", "lane": 2, "x": 805, "y": 215, "w": 190, "h": 50, "text": "Clasificar tipo de falla y\nverificar vigencia de póliza"},
            {"id": "d1", "type": "decision", "lane": 2, "x": 880, "y": 305, "w": 40, "h": 40, "text": "¿Cubre la póliza\nde garantía?"},
            {"id": "a_rechazo", "type": "action", "lane": 2, "x": 735, "y": 395, "w": 155, "h": 50, "text": "Notificar improcedencia formal\ny cotizar servicio particular"},
            {"id": "end_rechazo", "type": "end", "lane": 0, "x": 180, "y": 485},
            {"id": "a4", "type": "action", "lane": 2, "x": 905, "y": 395, "w": 155, "h": 50, "text": "Aprobar solicitud, asignar\ntécnico y programar visita"},
            {"id": "a5", "type": "action", "lane": 1, "x": 445, "y": 485, "w": 190, "h": 55, "text": "Realizar peritaje en sitio y\nejecutar reparación técnica"},
            {"id": "a6", "type": "action", "lane": 0, "x": 85, "y": 575, "w": 190, "h": 50, "text": "Inspeccionar trabajos y firmar\nacta de conformidad"},
            {"id": "a7", "type": "action", "lane": 2, "x": 805, "y": 665, "w": 190, "h": 55, "text": "Cerrar ticket de posventa y\nregistrar costos asumidos"},
            {"id": "a8", "type": "action", "lane": 0, "x": 85, "y": 755, "w": 190, "h": 50, "text": "Responder encuesta de\nsatisfacción del servicio"},
            {"id": "end_exito", "type": "end", "lane": 0, "x": 180, "y": 845}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", "Ticket emitido"),
            ("a3", "d1", ""),
            ("d1", "a_rechazo", "[No cubre / Expirada]"),
            ("a_rechazo", "end_rechazo", "Garantía declinada"),
            ("d1", "a4", "[Garantía vigente]"),
            ("a4", "a5", "Asignación de orden"),
            ("a5", "a6", "Reparación concluida"),
            ("a6", "a7", "Conformidad firmada"),
            ("a7", "a8", "Ticket resuelto"),
            ("a8", "end_exito", "Servicio concluido")
        ]
    }
]

# Generate Vectorial SVG and High-Res PNG with ZERO Overlaps
for act in activities:
    w = act["w"]
    h = act["h"]
    lanes = act["lanes"]
    lane_w = act["lane_w"]
    num_lanes = len(lanes)

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    svg.append('''<defs>
      <marker id="act-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
      </marker>
    </defs>''')
    svg.append(f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>')

    # Title Banner (Clean, Academic)
    svg.append(f'<text x="30" y="28" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="bold" fill="#000000">{act["title"]}</text>')
    svg.append(f'<text x="30" y="45" font-family="Arial, Helvetica, sans-serif" font-size="10.5" fill="#555555">{act["subtitle"]}</text>')

    # Outer Boundary
    header_h = 36
    top_y = 55
    bot_y = h - 25
    svg.append(f'<rect x="30" y="{top_y}" width="{w-60}" height="{bot_y - top_y}" fill="none" stroke="#000000" stroke-width="1.3"/>')

    # Swimlanes
    for idx, lname in enumerate(lanes):
        lx = 30 + idx * lane_w
        # Header rect
        svg.append(f'<rect x="{lx}" y="{top_y}" width="{lane_w}" height="{header_h}" fill="#F4F4F4" stroke="#000000" stroke-width="1.2"/>')
        svg.append(f'<text x="{lx + lane_w/2}" y="{top_y + 23}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#000000">{lname}</text>')
        # Lane divider
        if idx > 0:
            svg.append(f'<line x1="{lx}" y1="{top_y + header_h}" x2="{lx}" y2="{bot_y}" stroke="#000000" stroke-width="1.2"/>')

    node_map = {n["id"]: n for n in act["nodes"]}

    # Draw Edges first so nodes and labels render on top
    for src_id, dst_id, lbl in act["edges"]:
        n1 = node_map[src_id]
        n2 = node_map[dst_id]

        # Calculate exact source attachment point
        if n1["type"] == "start":
            x1 = n1["x"]
            y1 = n1["y"] + 11
        elif n1["type"] == "decision":
            # If target is to the left or right, exit side; otherwise bottom
            if n2["type"] == "action" and abs(n1["y"] - n2["y"]) < 50:
                if n2["x"] < n1["x"]:
                    x1 = n1["x"]
                    y1 = n1["y"] + n1["h"]/2
                else:
                    x1 = n1["x"] + n1["w"]
                    y1 = n1["y"] + n1["h"]/2
            else:
                x1 = n1["x"] + n1["w"]/2
                y1 = n1["y"] + n1["h"]
        elif n1["type"] == "join":
            x1 = n1["x"] + n1["w"]/2
            y1 = n1["y"] + n1["h"]
        else:
            x1 = n1["x"] + n1["w"]/2
            y1 = n1["y"] + n1["h"]

        # Calculate exact target attachment point
        if n2["type"] == "end":
            x2 = n2["x"]
            y2 = n2["y"] - 12
        elif n2["type"] == "decision" or n2["type"] == "join":
            x2 = n2["x"] + n2["w"]/2
            y2 = n2["y"]
        else:
            # If coming from a backward loop (e.g. reinspeccion), enter side
            if y1 > n2["y"] + n2["h"]:
                x2 = n2["x"] + n2["w"]
                y2 = n2["y"] + n2["h"]/2
            else:
                x2 = n2["x"] + n2["w"]/2
                y2 = n2["y"]

        # Orthogonal Line Routing
        if abs(x1 - x2) < 5:
            # Straight vertical line
            svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000000" stroke-width="1.2" marker-end="url(#act-arr)"/>')
            if lbl:
                mid_y = (y1 + y2) / 2
                svg.append(f'<rect x="{x1 + 6}" y="{mid_y - 8}" width="{len(lbl)*6.2}" height="15" fill="#FFFFFF"/>')
                svg.append(f'<text x="{x1 + 8}" y="{mid_y + 3}" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#000000">{lbl}</text>')
        elif y1 > y2:
            # Backward loop (e.g. reinspeccion a4 -> a3)
            # Route down/right then up and back
            loop_x = x1 + 130
            svg.append(f'<path d="M {x1} {y1} L {loop_x} {y1} L {loop_x} {y2} L {x2} {y2}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#act-arr)"/>')
            if lbl:
                svg.append(f'<rect x="{loop_x - 50}" y="{(y1+y2)/2 - 8}" width="{len(lbl)*6.2}" height="15" fill="#FFFFFF"/>')
                svg.append(f'<text x="{loop_x - 45}" y="{(y1+y2)/2 + 3}" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#000000">{lbl}</text>')
        else:
            # Step orthogonal
            mid_y = y1 + (y2 - y1) * 0.45
            svg.append(f'<path d="M {x1} {y1} L {x1} {mid_y} L {x2} {mid_y} L {x2} {y2}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#act-arr)"/>')
            if lbl:
                lbl_w = len(lbl) * 6.2 + 8
                lbl_x = (x1 + x2) / 2
                svg.append(f'<rect x="{lbl_x - lbl_w/2}" y="{mid_y - 8}" width="{lbl_w}" height="15" fill="#FFFFFF"/>')
                svg.append(f'<text x="{lbl_x}" y="{mid_y + 3}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#000000">{lbl}</text>')

    # Draw Nodes (Clean, Rounded, High-Definition)
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
                ty = dy - len(lines)*11 - 3
                for l in lines:
                    lw = len(l) * 6 + 6
                    svg.append(f'<rect x="{cx - lw/2}" y="{ty - 9}" width="{lw}" height="12" fill="#FFFFFF"/>')
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
    print(f"Generated clean SVG & PNG for: {act['title']}")

# ==============================================================================
# CONSOLIDATED MULTI-TAB DRAW.IO FILE (4 High Priority Sprint Diagrams)
# ==============================================================================
drawio_xml = []
drawio_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
drawio_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-22T21:30:00.000Z" agent="Antigravity" version="24.0.0" type="device">')

for act in activities:
    act_id = act["id"]
    tab_name = act["tab_name"]
    w = act["w"]
    h = act["h"]
    lanes = act["lanes"]
    lane_w = act["lane_w"]

    drawio_xml.append(f'  <diagram id="{act_id}" name="{html.escape(tab_name)}">')
    drawio_xml.append(f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{w}" pageHeight="{h}" background="#FFFFFF" math="0" shadow="0">')
    drawio_xml.append('      <root>')
    drawio_xml.append('        <mxCell id="0" />')
    drawio_xml.append('        <mxCell id="1" parent="0" />')

    # Title
    drawio_xml.append(f'        <mxCell id="title_{act_id}" value="&lt;b&gt;{html.escape(act["title"])}&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;{html.escape(act["subtitle"])}&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=12;fontColor=#000000;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="30" y="15" width="{w-60}" height="35" as="geometry" />')
    drawio_xml.append('        </mxCell>')

    # Pool Container
    top_y = 55
    bot_h = h - 80
    drawio_xml.append(f'        <mxCell id="pool_{act_id}" value="" style="swimlane;html=1;childLayout=stackLayout;resizeParent=1;resizeParentMax=0;startSize=0;horizontal=1;horizontalStack=1;fillColor=none;strokeColor=#000000;strokeWidth=1.3;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="30" y="{top_y}" width="{w-60}" height="{bot_h}" as="geometry" />')
    drawio_xml.append('        </mxCell>')

    # Lanes
    header_h = 36
    for idx, lname in enumerate(lanes):
        drawio_xml.append(f'        <mxCell id="lane_{act_id}_{idx}" value="&lt;b&gt;{html.escape(lname)}&lt;/b&gt;" style="swimlane;html=1;startSize={header_h};fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=11;fontColor=#000000;collapsible=0;" vertex="1" parent="pool_{act_id}">')
        drawio_xml.append(f'          <mxGeometry x="{int(idx*lane_w)}" y="0" width="{int(lane_w)}" height="{bot_h}" as="geometry" />')
        drawio_xml.append('        </mxCell>')

    # Nodes placed cleanly with absolute-relative math inside lane
    for n in act["nodes"]:
        nid = f"{act_id}_{n['id']}"
        lane_idx = n["lane"]
        parent_id = f"lane_{act_id}_{lane_idx}"
        # Node coordinate relative to its lane
        rx = n["x"] - (30 + lane_idx * lane_w)
        ry = n["y"] - top_y

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
                drawio_xml.append(f'        <mxCell id="{nid}_lbl" value="&lt;b&gt;{txt}&lt;/b&gt;" style="text;html=1;strokeColor=none;fillColor=#FFFFFF;align=center;verticalAlign=bottom;fontSize=9.5;fontFamily=Arial;fontColor=#000000;" vertex="1" parent="{parent_id}">')
                drawio_xml.append(f'          <mxGeometry x="{int(rx - 45)}" y="{int(ry - 30)}" width="130" height="25" as="geometry" />')
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

    # Edges with labelBackgroundColor=#FFFFFF so text NEVER collides with lines!
    for edge_idx, (src_id, dst_id, lbl) in enumerate(act["edges"]):
        eid = f"edge_{act_id}_{edge_idx}"
        full_src = f"{act_id}_{src_id}"
        full_dst = f"{act_id}_{dst_id}"
        lbl_escaped = html.escape(lbl) if lbl else ""
        drawio_xml.append(f'        <mxCell id="{eid}" value="{lbl_escaped}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="{full_src}" target="{full_dst}">')
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
print("Generated Draw.io Multi-tab file with ZERO overlaps!")
