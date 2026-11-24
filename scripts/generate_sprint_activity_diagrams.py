import os
import shutil
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)
brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'
os.makedirs(brain_diag_dir, exist_ok=True)

# The 6 Official Use Cases of this Sprint (No "CUXX" codes in titles or nodes)
sprint_activities = [
    {
        "id": "act_comunicaciones_notificaciones",
        "tab_name": "Comunicaciones y Notificaciones",
        "title": "Gestionar Comunicaciones y Notificaciones",
        "subtitle": "Difusión de alertas operativas, avisos de seguridad y comunicados de obra con acuse de recibo.",
        "swimlanes": ["Emisor (Supervisor / Jefe de Obra)", "Sistema", "Receptor (Personal / Contratista)"],
        "w": 1100,
        "h": 820,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 190},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 95, "w": 190, "h": 50, "text": "Redactar comunicado u orden\nde seguridad para la obra"},
            {"id": "a2", "type": "action", "lane": 0, "y": 200, "x": 95, "w": 190, "h": 50, "text": "Seleccionar destinatarios,\nprioridad y canales de envío"},
            {"id": "a3", "type": "action", "lane": 1, "y": 200, "x": 455, "w": 190, "h": 50, "text": "Registrar notificación y despachar\nvía Web, Push móvil y correo"},
            {"id": "a4", "type": "action", "lane": 2, "y": 280, "x": 815, "w": 190, "h": 50, "text": "Recibir notificación en dispositivo\ny revisar contenido del aviso"},
            {"id": "d1", "type": "decision", "lane": 1, "y": 360, "x": 530, "w": 40, "h": 40, "text": "¿Requiere acuse\nde lectura?"},
            {"id": "a5", "type": "action", "lane": 2, "y": 440, "x": 815, "w": 190, "h": 50, "text": "Confirmar recepción y lectura\nde la instrucción recibida"},
            {"id": "a6", "type": "action", "lane": 1, "y": 520, "x": 455, "w": 190, "h": 50, "text": "Actualizar estado a 'Entregada'\ny computar estadísticas de lectura"},
            {"id": "a7", "type": "action", "lane": 0, "y": 600, "x": 95, "w": 190, "h": 50, "text": "Consultar panel de seguimiento\ny porcentaje de acuse en faena"},
            {"id": "end", "type": "end", "lane": 0, "y": 690, "x": 190}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", ""),
            ("a3", "a4", "Despacho a canales"),
            ("a4", "d1", ""),
            ("d1", "a5", "[Requiere confirmación]"),
            ("d1", "a6", "[Solo informativo]"),
            ("a5", "a6", "Acuse firmado"),
            ("a6", "a7", "Métricas actualizadas"),
            ("a7", "end", "")
        ]
    },
    {
        "id": "act_consulta_proyectos_cliente",
        "tab_name": "Consulta Proyectos como Cliente",
        "title": "Consultar Proyectos y Unidades como Cliente",
        "subtitle": "Búsqueda interactiva de proyectos, exploración de unidades en catálogo y simulación de planes de pago.",
        "swimlanes": ["Cliente Potencial", "Sistema"],
        "w": 860,
        "h": 800,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 210},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 115, "w": 190, "h": 50, "text": "Acceder al catálogo público\nde proyectos y desarrollo"},
            {"id": "a2", "type": "action", "lane": 0, "y": 200, "x": 115, "w": 190, "h": 50, "text": "Aplicar filtros de búsqueda\n(zona, precio, tipología)"},
            {"id": "a3", "type": "action", "lane": 1, "y": 200, "x": 545, "w": 190, "h": 50, "text": "Consultar inventario en vivo\ny disponibilidad de unidades"},
            {"id": "d1", "type": "decision", "lane": 1, "y": 285, "x": 620, "w": 40, "h": 40, "text": "¿Coinciden\nunidades?"},
            {"id": "a_alt", "type": "action", "lane": 1, "y": 365, "x": 440, "w": 170, "h": 50, "text": "Sugerir proyectos similares\ny solicitar ajuste de filtros"},
            {"id": "a4", "type": "action", "lane": 1, "y": 365, "x": 640, "w": 180, "h": 50, "text": "Mostrar catálogo con renders,\nplanos de planta y precios"},
            {"id": "merge1", "type": "join", "lane": 1, "y": 450, "x": 620, "w": 40, "h": 20, "text": ""},
            {"id": "a5", "type": "action", "lane": 0, "y": 500, "x": 115, "w": 190, "h": 50, "text": "Seleccionar unidad de interés\ny solicitar simulación de cuotas"},
            {"id": "a6", "type": "action", "lane": 1, "y": 580, "x": 545, "w": 190, "h": 50, "text": "Generar propuesta financiera\ny habilitar botón de contacto"},
            {"id": "a7", "type": "action", "lane": 0, "y": 660, "x": 115, "w": 190, "h": 50, "text": "Descargar ficha informativa\ny solicitar visita a sala de ventas"},
            {"id": "end", "type": "end", "lane": 0, "y": 740, "x": 210}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", ""),
            ("a3", "d1", ""),
            ("d1", "a_alt", "[Sin stock exacto]"),
            ("d1", "a4", "[Disponibles]"),
            ("a_alt", "merge1", ""),
            ("a4", "merge1", ""),
            ("merge1", "a5", "Visualizar resultados"),
            ("a5", "a6", ""),
            ("a6", "a7", "Plan financiero"),
            ("a7", "end", "")
        ]
    },
    {
        "id": "act_comercializacion_unidades",
        "tab_name": "Comercialización Inmobiliaria",
        "title": "Gestionar Comercialización de Unidades Inmobiliarias",
        "subtitle": "Reserva de unidades, verificación de solvencia, aprobación gerencial y formalización de venta.",
        "swimlanes": ["Asesor Comercial", "Gerencia Comercial", "Sistema"],
        "w": 1150,
        "h": 850,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 195},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 100, "w": 190, "h": 50, "text": "Registrar datos del cliente\ny unidad inmobiliaria elegida"},
            {"id": "a2", "type": "action", "lane": 0, "y": 200, "x": 100, "w": 190, "h": 50, "text": "Solicitar reserva temporal\ny adjuntar abono de separación"},
            {"id": "a3", "type": "action", "lane": 2, "y": 200, "x": 860, "w": 190, "h": 50, "text": "Bloquear unidad temporalmente\ny verificar comprobante bancario"},
            {"id": "a4", "type": "action", "lane": 1, "y": 290, "x": 480, "w": 190, "h": 50, "text": "Evaluar perfil crediticio\ny condiciones del financiamiento"},
            {"id": "d1", "type": "decision", "lane": 1, "y": 380, "x": 555, "w": 40, "h": 40, "text": "¿Aprueba\noperación?"},
            {"id": "a_rechazo", "type": "action", "lane": 1, "y": 460, "x": 420, "w": 160, "h": 50, "text": "Registrar causales de rechazo\ny solicitar subsanación"},
            {"id": "a_libera", "type": "action", "lane": 2, "y": 460, "x": 860, "w": 180, "h": 50, "text": "Liberar unidad al inventario\ny notificar al asesor comercial"},
            {"id": "end_rechazo", "type": "end", "lane": 0, "y": 550, "x": 195},
            {"id": "a5", "type": "action", "lane": 1, "y": 550, "x": 580, "w": 180, "h": 50, "text": "Aprobar contrato de preventa\ny esquema de pagos pactado"},
            {"id": "a6", "type": "action", "lane": 2, "y": 640, "x": 860, "w": 190, "h": 50, "text": "Generar contrato de promesa,\nplan de pagos y recibo oficial"},
            {"id": "a7", "type": "action", "lane": 0, "y": 720, "x": 100, "w": 190, "h": 50, "text": "Recabar firma del comprador\ny cerrar expediente comercial"},
            {"id": "end_exito", "type": "end", "lane": 0, "y": 800, "x": 195}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", ""),
            ("a3", "a4", "Expediente de reserva"),
            ("a4", "d1", ""),
            ("d1", "a_rechazo", "[Rechazado]"),
            ("a_rechazo", "a_libera", ""),
            ("a_libera", "end_rechazo", "Venta cancelada"),
            ("d1", "a5", "[Aprobado]"),
            ("a5", "a6", "Autorización gerencial"),
            ("a6", "a7", "Documentos listos"),
            ("a7", "end_exito", "Venta consolidada")
        ]
    },
    {
        "id": "act_inspecciones_calidad",
        "tab_name": "Inspecciones y Calidad",
        "title": "Gestionar Inspecciones y Control de Calidad",
        "subtitle": "Inspección técnica en terreno, aplicación de listas de chequeo normativo y resolución de no conformidades.",
        "swimlanes": ["Inspector de Calidad", "Responsable de Cuadrilla", "Sistema"],
        "w": 1150,
        "h": 850,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 195},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 100, "w": 190, "h": 50, "text": "Seleccionar frente de obra\ny partida a inspeccionar"},
            {"id": "a2", "type": "action", "lane": 2, "y": 120, "x": 860, "w": 190, "h": 50, "text": "Cargar lista de chequeo y\ntolerancias técnicas normadas"},
            {"id": "a3", "type": "action", "lane": 0, "y": 210, "x": 100, "w": 190, "h": 50, "text": "Evaluar parámetros en campo\ny tomar fotografías de control"},
            {"id": "d1", "type": "decision", "lane": 0, "y": 300, "x": 175, "w": 40, "h": 40, "text": "¿Cumple con\nla norma?"},
            {"id": "a_noconf", "type": "action", "lane": 0, "y": 380, "x": 40, "w": 170, "h": 55, "text": "Registrar 'No Conformidad',\nplazo y severidad del defecto"},
            {"id": "a_notif", "type": "action", "lane": 2, "y": 380, "x": 860, "w": 190, "h": 50, "text": "Generar orden de subsanación\ny notificar al responsable"},
            {"id": "a4", "type": "action", "lane": 1, "y": 470, "x": 480, "w": 190, "h": 55, "text": "Ejecutar corrección en obra\ny solicitar reinspección"},
            {"id": "a5", "type": "action", "lane": 0, "y": 550, "x": 100, "w": 190, "h": 50, "text": "Firmar digitalmente acta\nde aprobación de calidad"},
            {"id": "a6", "type": "action", "lane": 2, "y": 640, "x": 860, "w": 190, "h": 55, "text": "Certificar partida como apta\npara avance y valorización"},
            {"id": "a7", "type": "action", "lane": 0, "y": 720, "x": 100, "w": 190, "h": 50, "text": "Incorporar informe al dossier\nde aseguramiento de obra"},
            {"id": "end_exito", "type": "end", "lane": 0, "y": 800, "x": 195}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", "Checklist cargado"),
            ("a3", "d1", ""),
            ("d1", "a_noconf", "[Con observaciones]"),
            ("a_noconf", "a_notif", ""),
            ("a_notif", "a4", "Aviso de corrección"),
            ("a4", "a3", "Reinspeccionar"),
            ("d1", "a5", "[Conforme 100%]"),
            ("a5", "a6", "Acta firmada"),
            ("a6", "a7", "Partida liberada"),
            ("a7", "end_exito", "Dossier completo")
        ]
    },
    {
        "id": "act_operacion_offline_sync",
        "tab_name": "Operación Offline y Sync",
        "title": "Gestionar Operación Offline y Sincronización",
        "subtitle": "Captura continua de datos en terreno sin señal y sincronización atómica e idempotente con el servidor.",
        "swimlanes": ["Personal de Campo", "Aplicación Móvil (Offline)", "Servidor Central"],
        "w": 1150,
        "h": 860,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 195},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 100, "w": 190, "h": 50, "text": "Ingresar a frente de obra\nsin señal o conectividad"},
            {"id": "a2", "type": "action", "lane": 1, "y": 120, "x": 480, "w": 190, "h": 50, "text": "Cargar snapshot local de obra,\nfrentes y cronograma en caché"},
            {"id": "a3", "type": "action", "lane": 0, "y": 200, "x": 100, "w": 190, "h": 50, "text": "Registrar avances diarios o\nreportar incidencias con fotos"},
            {"id": "a4", "type": "action", "lane": 1, "y": 200, "x": 480, "w": 190, "h": 50, "text": "Encolar registro en SQLite local\ncon estado 'PENDIENTE_SYNC'"},
            {"id": "d1", "type": "decision", "lane": 1, "y": 290, "x": 555, "w": 40, "h": 40, "text": "¿Detecta red\nInternet?"},
            {"id": "a_espera", "type": "action", "lane": 0, "y": 370, "x": 100, "w": 190, "h": 50, "text": "Continuar jornada y registrar\nmás datos sobre base local"},
            {"id": "a5", "type": "action", "lane": 1, "y": 370, "x": 480, "w": 190, "h": 50, "text": "Empaquetar lote de pendientes\ny enviar petición HTTP batch"},
            {"id": "a6", "type": "action", "lane": 2, "y": 370, "x": 860, "w": 190, "h": 50, "text": "Validar autenticación,\npermisos e idempotencia"},
            {"id": "d2", "type": "decision", "lane": 2, "y": 460, "x": 935, "w": 40, "h": 40, "text": "¿Existen\nconflictos?"},
            {"id": "a_resolve", "type": "action", "lane": 2, "y": 550, "x": 780, "w": 160, "h": 50, "text": "Aplicar regla Last-Write\ny registrar en auditoría"},
            {"id": "a_insert", "type": "action", "lane": 2, "y": 550, "x": 960, "w": 160, "h": 50, "text": "Consolidar avances e\nincidencias en base de datos"},
            {"id": "merge1", "type": "join", "lane": 2, "y": 630, "x": 935, "w": 40, "h": 20, "text": ""},
            {"id": "a7", "type": "action", "lane": 1, "y": 690, "x": 480, "w": 190, "h": 50, "text": "Actualizar registros locales\na SINCRONIZADO y limpiar"},
            {"id": "end_exito", "type": "end", "lane": 0, "y": 780, "x": 195}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", "Caché lista"),
            ("a3", "a4", ""),
            ("a4", "d1", ""),
            ("d1", "a_espera", "[Sin red]"),
            ("a_espera", "a3", "Nuevos registros"),
            ("d1", "a5", "[Señal recuperada]"),
            ("a5", "a6", "Envío de lote"),
            ("a6", "d2", ""),
            ("d2", "a_resolve", "[Conflicto]"),
            ("d2", "a_insert", "[Sin conflicto]"),
            ("a_resolve", "merge1", ""),
            ("a_insert", "merge1", ""),
            ("merge1", "a7", "Confirmación de lote"),
            ("a7", "end_exito", "Notificar sincronización OK")
        ]
    },
    {
        "id": "act_garantias_posventa",
        "tab_name": "Garantías y Posventa",
        "title": "Gestionar Garantías y Servicio Posventa Inmobiliaria",
        "subtitle": "Atención de reclamos de propietarios, validación de pólizas de garantía y ejecución de reparaciones técnicas.",
        "swimlanes": ["Propietario / Cliente", "Técnico de Posventa", "Sistema"],
        "w": 1150,
        "h": 850,
        "nodes": [
            {"id": "start", "type": "start", "lane": 0, "y": 70, "x": 195},
            {"id": "a1", "type": "action", "lane": 0, "y": 120, "x": 100, "w": 190, "h": 50, "text": "Detectar desperfecto o falla\nen unidad entregada"},
            {"id": "a2", "type": "action", "lane": 0, "y": 200, "x": 100, "w": 190, "h": 50, "text": "Registrar ticket de garantía\ncon descripción y fotos"},
            {"id": "a3", "type": "action", "lane": 2, "y": 200, "x": 860, "w": 190, "h": 50, "text": "Verificar vigencia de póliza\ny tipo de daño contractual"},
            {"id": "d1", "type": "decision", "lane": 2, "y": 290, "x": 935, "w": 40, "h": 40, "text": "¿Cubre la\ngarantía?"},
            {"id": "a_rechazo", "type": "action", "lane": 2, "y": 380, "x": 780, "w": 160, "h": 50, "text": "Notificar improcedencia\ny cotizar servicio particular"},
            {"id": "end_rechazo", "type": "end", "lane": 0, "y": 460, "x": 195},
            {"id": "a4", "type": "action", "lane": 2, "y": 380, "x": 960, "w": 160, "h": 50, "text": "Aprobar garantía y agendar\nvisita de inspección técnica"},
            {"id": "a5", "type": "action", "lane": 1, "y": 480, "x": 480, "w": 190, "h": 50, "text": "Acudir a la unidad inmobiliaria\ny ejecutar reparación física"},
            {"id": "a6", "type": "action", "lane": 0, "y": 570, "x": 100, "w": 190, "h": 50, "text": "Inspeccionar trabajos y firmar\nacta digital de conformidad"},
            {"id": "a7", "type": "action", "lane": 2, "y": 660, "x": 860, "w": 190, "h": 50, "text": "Cerrar ticket de garantía,\nliquidar costos y enviar encuesta"},
            {"id": "end_exito", "type": "end", "lane": 0, "y": 750, "x": 195}
        ],
        "edges": [
            ("start", "a1", ""),
            ("a1", "a2", ""),
            ("a2", "a3", ""),
            ("a3", "d1", ""),
            ("d1", "a_rechazo", "[No cubre o expirada]"),
            ("a_rechazo", "end_rechazo", "Garantía declinada"),
            ("d1", "a4", "[Garantía vigente]"),
            ("a4", "a5", "Asignación de orden"),
            ("a5", "a6", "Reparación concluida"),
            ("a6", "a7", "Conformidad firmada"),
            ("a7", "end_exito", "Ticket resuelto")
        ]
    }
]

# Generate Vectorial SVG and High-Res PNG for all 6 Activities
for act in sprint_activities:
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
    svg.append(f'<text x="30" y="32" font-family="Arial, Helvetica, sans-serif" font-size="13.5" font-weight="bold" fill="#000000">Diagrama de Actividades: {act["title"]}</text>')
    svg.append(f'<text x="30" y="48" font-family="Arial, Helvetica, sans-serif" font-size="10.5" fill="#555555">{act["subtitle"]}</text>')

    # Outer border
    svg.append(f'<rect x="30" y="60" width="{w-60}" height="{h-80}" fill="none" stroke="#000000" stroke-width="1.3"/>')

    # Swimlanes
    for i, lname in enumerate(lanes):
        lx = 30 + i * lane_w
        svg.append(f'<rect x="{lx}" y="60" width="{lane_w}" height="32" fill="#F4F4F4" stroke="#000000" stroke-width="1.2"/>')
        svg.append(f'<text x="{lx + lane_w/2}" y="81" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#000000">{lname}</text>')
        if i > 0:
            svg.append(f'<line x1="{lx}" y1="92" x2="{lx}" y2="{h-20}" stroke="#000000" stroke-width="1.2"/>')

    # Lookup map
    node_map = {n["id"]: n for n in act["nodes"]}

    # Draw Edges
    for src_id, dst_id, lbl in act["edges"]:
        n1 = node_map[src_id]
        n2 = node_map[dst_id]

        if n1["type"] == "start":
            x1, y1 = n1["x"], n1["y"] + 11
        elif n1["type"] == "decision" or n1["type"] == "join":
            x1, y1 = n1["x"] + n1["w"]/2, n1["y"] + n1["h"]
        else:
            x1, y1 = n1["x"] + n1["w"]/2, n1["y"] + n1["h"]

        if n2["type"] == "end":
            x2, y2 = n2["x"], n2["y"] - 12
        elif n2["type"] == "decision" or n2["type"] == "join":
            x2, y2 = n2["x"] + n2["w"]/2, n2["y"]
        else:
            x2, y2 = n2["x"] + n2["w"]/2, n2["y"]

        if abs(x1 - x2) < 5:
            svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000000" stroke-width="1.2" marker-end="url(#act-arr)"/>')
            if lbl:
                svg.append(f'<text x="{x1 + 8}" y="{(y1+y2)/2}" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#000000">{lbl}</text>')
        else:
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
    print(f"Generated SVG & PNG for Sprint Activity: {act['title']}")

# ==============================================================================
# MULTI-TAB DRAW.IO FILE (All 6 Sprint Activities in Separate Tabs)
# ==============================================================================
drawio_xml = []
drawio_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
drawio_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-22T21:15:00.000Z" agent="Antigravity" version="24.0.0" type="device">')

for act in sprint_activities:
    act_id = act["id"]
    tab_name = act["tab_name"]
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
    drawio_xml.append(f'        <mxCell id="title_{act_id}" value="&lt;b&gt;Diagrama de Actividades: {html.escape(act["title"])}&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;{html.escape(act["subtitle"])}&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=12;fontColor=#000000;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="30" y="15" width="{w-60}" height="35" as="geometry" />')
    drawio_xml.append('        </mxCell>')

    # Pool Container
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
print("Generated Multi-tab Draw.io file for all 6 Sprint Activities!")
