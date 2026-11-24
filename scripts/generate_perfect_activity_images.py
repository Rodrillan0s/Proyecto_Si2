import os
import shutil
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)
brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'
os.makedirs(brain_diag_dir, exist_ok=True)

# 6 Complete Sprint Activities Specification
activities_spec = [
    {
        "id": "act_cu22_comunicaciones",
        "tab_name": "CU22 - Comunicaciones y Notificaciones",
        "cu_code": "CU22 (W/M)",
        "title": "CU22 (W/M) – Gestionar comunicaciones y notificaciones",
        "subtitle": "Representación de redacción de comunicados, selección de canales, despacho prioritario/asíncrono y confirmación de lectura.",
        "w": 1140,
        "h": 980,
        "lanes": [
            {"name": "Usuario Gestor / Emisor", "cx": 220},
            {"name": "Destinatario (Cliente / Equipo)", "cx": 570},
            {"name": "Sistema", "cx": 920}
        ],
        "nodes": [
            {"id": "start", "type": "start", "cx": 220, "cy": 135},
            {"id": "a1", "type": "action", "cx": 220, "cy": 205, "w": 220, "h": 50, "lines": ["Redactar comunicado técnico o", "seleccionar evento de obra"]},
            {"id": "a2", "type": "action", "cx": 220, "cy": 295, "w": 220, "h": 50, "lines": ["Definir destinatarios y seleccionar", "canales (Push, Email, In-App)"]},
            {"id": "a3", "type": "action", "cx": 920, "cy": 295, "w": 220, "h": 50, "lines": ["Validar permisos, destinatarios y", "preferencias de notificación"]},
            {"id": "d1", "type": "decision", "cx": 920, "cy": 385, "w": 40, "h": 40, "q": "¿Tipo de notificación?"},
            {"id": "a4", "type": "action", "cx": 820, "cy": 470, "w": 160, "h": 50, "lines": ["Priorizar despacho", "inmediato individual"]},
            {"id": "a5", "type": "action", "cx": 1020, "cy": 470, "w": 160, "h": 50, "lines": ["Encolar lote en broker", "para envío asíncrono"]},
            {"id": "m1", "type": "join", "cx": 920, "cy": 540, "w": 50, "h": 12},
            {"id": "a6", "type": "action", "cx": 920, "cy": 615, "w": 220, "h": 50, "lines": ["Despachar mensajes y registrar", "transacción en base de datos"]},
            {"id": "a7", "type": "action", "cx": 570, "cy": 700, "w": 220, "h": 50, "lines": ["Recibir notificación en móvil", "o web y abrir contenido"]},
            {"id": "a8", "type": "action", "cx": 920, "cy": 785, "w": 220, "h": 50, "lines": ["Registrar acuse de recibo y", "actualizar estado a 'LEÍDO'"]},
            {"id": "a9", "type": "action", "cx": 220, "cy": 865, "w": 220, "h": 50, "lines": ["Consultar métricas de entrega", "y confirmaciones de lectura"]},
            {"id": "end_exito", "type": "end", "cx": 220, "cy": 935}
        ],
        "edges": [
            {"from": "start", "to": "a1"},
            {"from": "a1", "to": "a2"},
            {"from": "a2", "to": "a3", "lbl": "Configuración lista"},
            {"from": "a3", "to": "d1"},
            {"from": "d1", "to": "a4", "dir": "left", "lbl": "[Individual]"},
            {"from": "d1", "to": "a5", "dir": "right", "lbl": "[Masiva / Lote]"},
            {"from": "a4", "to": "m1"},
            {"from": "a5", "to": "m1"},
            {"from": "m1", "to": "a6", "lbl": "Cola procesada"},
            {"from": "a6", "to": "a7", "lbl": "Mensaje emitido"},
            {"from": "a7", "to": "a8", "lbl": "Apertura / Lectura"},
            {"from": "a8", "to": "a9", "lbl": "Trazabilidad OK"},
            {"from": "a9", "to": "end_exito", "lbl": "Proceso concluido"}
        ]
    },
    {
        "id": "act_cu30_consulta_proyectos",
        "tab_name": "CU30 - Consulta de Proyectos",
        "cu_code": "CU30 (W/M)",
        "title": "CU30 (W/M) – Consultar proyectos y unidades como cliente",
        "subtitle": "Representación de navegación de catálogo, consulta de disponibilidad, simulación de cotización y solicitud de atención comercial.",
        "w": 1140,
        "h": 980,
        "lanes": [
            {"name": "Cliente / Propietario", "cx": 220},
            {"name": "Asesor Comercial", "cx": 570},
            {"name": "Sistema", "cx": 920}
        ],
        "nodes": [
            {"id": "start", "type": "start", "cx": 220, "cy": 135},
            {"id": "a1", "type": "action", "cx": 220, "cy": 205, "w": 220, "h": 50, "lines": ["Acceder al portal de clientes", "y aplicar filtros de búsqueda"]},
            {"id": "a2", "type": "action", "cx": 920, "cy": 205, "w": 220, "h": 50, "lines": ["Consultar inventario activo y", "filtrar proyectos y tipologías"]},
            {"id": "a3", "type": "action", "cx": 220, "cy": 295, "w": 220, "h": 50, "lines": ["Seleccionar unidad y consultar", "planos, acabados y avance"]},
            {"id": "a4", "type": "action", "cx": 920, "cy": 295, "w": 220, "h": 50, "lines": ["Verificar disponibilidad en tiempo", "real (DISPONIBLE / RESERVADA)"]},
            {"id": "d1", "type": "decision", "cx": 220, "cy": 385, "w": 40, "h": 40, "q": "¿Solicita cotización personalizada?"},
            {"id": "a_view", "type": "action", "cx": 110, "cy": 475, "w": 150, "h": 50, "lines": ["Descargar brochure digital", "y galería de avance"]},
            {"id": "end_view", "type": "end", "cx": 110, "cy": 555},
            {"id": "a5", "type": "action", "cx": 220, "cy": 475, "w": 200, "h": 50, "lines": ["Simular plan de pagos y", "solicitar propuesta formal"]},
            {"id": "a6", "type": "action", "cx": 920, "cy": 565, "w": 220, "h": 50, "lines": ["Generar cotización proforma", "y registrar lead comercial"]},
            {"id": "a7", "type": "action", "cx": 570, "cy": 655, "w": 220, "h": 50, "lines": ["Revisar requerimiento del cliente", "y coordinar visita técnica / sala"]},
            {"id": "a8", "type": "action", "cx": 220, "cy": 745, "w": 220, "h": 50, "lines": ["Confirmar fecha de visita y", "recibir propuesta detallada"]},
            {"id": "a9", "type": "action", "cx": 920, "cy": 830, "w": 220, "h": 50, "lines": ["Actualizar estado de oportunidad", "a 'EN_SEGUIMIENTO' en CRM"]},
            {"id": "end_exito", "type": "end", "cx": 220, "cy": 915}
        ],
        "edges": [
            {"from": "start", "to": "a1"},
            {"from": "a1", "to": "a2", "lbl": "Criterios de búsqueda"},
            {"from": "a2", "to": "a3", "lbl": "Catálogo filtrado"},
            {"from": "a3", "to": "a4", "lbl": "Consulta de unidad"},
            {"from": "a4", "to": "d1", "lbl": "Ficha y estado válidos"},
            {"from": "d1", "to": "a_view", "dir": "left", "lbl": "[Solo consulta]"},
            {"from": "a_view", "to": "end_view", "lbl": "Descarga completa"},
            {"from": "d1", "to": "a5", "dir": "down", "lbl": "[Solicita cotización]"},
            {"from": "a5", "to": "a6", "lbl": "Simulación enviada"},
            {"from": "a6", "to": "a7", "lbl": "Lead asignado"},
            {"from": "a7", "to": "a8", "lbl": "Contacto y agenda"},
            {"from": "a8", "to": "a9", "lbl": "Cita concertada"},
            {"from": "a9", "to": "end_exito", "lbl": "Seguimiento activo"}
        ]
    },
    {
        "id": "act_cu31_comercializacion",
        "tab_name": "CU31W - Comercialización",
        "cu_code": "CU31W",
        "title": "CU31W – Gestionar comercialización de unidades inmobiliarias",
        "subtitle": "Representación de reserva, validación de solvencia, aprobación gerencial y formalización de la venta.",
        "w": 1140,
        "h": 950,
        "lanes": [
            {"name": "Asesor Comercial", "cx": 220},
            {"name": "Gerencia Comercial", "cx": 570},
            {"name": "Sistema", "cx": 920}
        ],
        "nodes": [
            {"id": "start", "type": "start", "cx": 220, "cy": 135},
            {"id": "a1", "type": "action", "cx": 220, "cy": 205, "w": 220, "h": 50, "lines": ["Registrar solicitud de reserva", "y datos del cliente"]},
            {"id": "a2", "type": "action", "cx": 220, "cy": 295, "w": 220, "h": 50, "lines": ["Cargar comprobante de abono", "inicial de separación"]},
            {"id": "a3", "type": "action", "cx": 920, "cy": 295, "w": 220, "h": 50, "lines": ["Validar disponibilidad de unidad", "y aplicar bloqueo temporal"]},
            {"id": "a4", "type": "action", "cx": 570, "cy": 390, "w": 220, "h": 50, "lines": ["Evaluar propuesta comercial", "y condiciones de financiamiento"]},
            {"id": "d1", "type": "decision", "cx": 570, "cy": 475, "w": 40, "h": 40, "q": "¿Aprueba la venta?"},
            {"id": "a_rech", "type": "action", "cx": 470, "cy": 560, "w": 170, "h": 50, "lines": ["Registrar causal", "de rechazo o ajuste"]},
            {"id": "a_libera", "type": "action", "cx": 920, "cy": 560, "w": 210, "h": 50, "lines": ["Liberar bloqueo de unidad", "y notificar al asesor"]},
            {"id": "end_rech", "type": "end", "cx": 220, "cy": 645},
            {"id": "a5", "type": "action", "cx": 670, "cy": 560, "w": 170, "h": 50, "lines": ["Emitir aprobación formal", "de la venta"]},
            {"id": "a6", "type": "action", "cx": 920, "cy": 645, "w": 220, "h": 55, "lines": ["Generar contrato de promesa", "de compraventa y plan de pagos"]},
            {"id": "a7", "type": "action", "cx": 220, "cy": 735, "w": 220, "h": 50, "lines": ["Formalizar firma de contrato", "con el comprador"]},
            {"id": "a8", "type": "action", "cx": 920, "cy": 825, "w": 220, "h": 50, "lines": ["Actualizar unidad a 'VENDIDA'", "y registrar expediente"]},
            {"id": "end_exito", "type": "end", "cx": 220, "cy": 905}
        ],
        "edges": [
            {"from": "start", "to": "a1"},
            {"from": "a1", "to": "a2"},
            {"from": "a2", "to": "a3"},
            {"from": "a3", "to": "a4", "lbl": "Solicitud de evaluación"},
            {"from": "a4", "to": "d1"},
            {"from": "d1", "to": "a_rech", "dir": "left", "lbl": "[No / Observado]"},
            {"from": "a_rech", "to": "a_libera"},
            {"from": "a_libera", "to": "end_rech", "lbl": "Operación cancelada"},
            {"from": "d1", "to": "a5", "dir": "right", "lbl": "[Sí / Aprobado]"},
            {"from": "a5", "to": "a6", "lbl": "Venta autorizada"},
            {"from": "a6", "to": "a7", "lbl": "Contrato listo"},
            {"from": "a7", "to": "a8", "lbl": "Firma confirmada"},
            {"from": "a8", "to": "end_exito", "lbl": "Venta formalizada"}
        ]
    },
    {
        "id": "act_cu40_inspecciones_calidad",
        "tab_name": "CU40 - Inspecciones y Calidad",
        "cu_code": "CU40 (W/M)",
        "title": "CU40 (W/M) – Gestionar inspecciones y control de calidad",
        "subtitle": "Representación de inspección técnica, registro de observaciones, evaluación de conformidad y bucle de acciones correctivas.",
        "w": 1140,
        "h": 960,
        "lanes": [
            {"name": "Inspector de Calidad", "cx": 220},
            {"name": "Responsable de Cuadrilla", "cx": 570},
            {"name": "Sistema", "cx": 920}
        ],
        "nodes": [
            {"id": "start", "type": "start", "cx": 220, "cy": 135},
            {"id": "a1", "type": "action", "cx": 220, "cy": 205, "w": 220, "h": 50, "lines": ["Programar inspección técnica", "y seleccionar partida a revisar"]},
            {"id": "a2", "type": "action", "cx": 920, "cy": 205, "w": 220, "h": 50, "lines": ["Cargar lista de chequeo y", "tolerancias normativas"]},
            {"id": "a3", "type": "action", "cx": 220, "cy": 295, "w": 220, "h": 50, "lines": ["Inspeccionar trabajos en terreno", "y registrar mediciones"]},
            {"id": "d1", "type": "decision", "cx": 220, "cy": 385, "w": 40, "h": 40, "q": "¿Cumple estándares técnicos?"},
            {"id": "a_noconf", "type": "action", "cx": 130, "cy": 475, "w": 160, "h": 55, "lines": ["Registrar observaciones,", "nivel de defecto y plazo"]},
            {"id": "a_notif", "type": "action", "cx": 920, "cy": 475, "w": 220, "h": 50, "lines": ["Emitir orden de no conformidad", "y notificar a cuadrilla"]},
            {"id": "a4", "type": "action", "cx": 570, "cy": 560, "w": 210, "h": 50, "lines": ["Ejecutar acciones correctivas", "en frente de faena"]},
            {"id": "a5", "type": "action", "cx": 220, "cy": 645, "w": 220, "h": 50, "lines": ["Emitir acta digital de", "conformidad técnica"]},
            {"id": "a6", "type": "action", "cx": 920, "cy": 735, "w": 220, "h": 55, "lines": ["Certificar partida como apta", "para avance y valorización"]},
            {"id": "a7", "type": "action", "cx": 220, "cy": 825, "w": 220, "h": 50, "lines": ["Archivar informe en el dossier", "de aseguramiento de calidad"]},
            {"id": "end_exito", "type": "end", "cx": 220, "cy": 905}
        ],
        "edges": [
            {"from": "start", "to": "a1"},
            {"from": "a1", "to": "a2"},
            {"from": "a2", "to": "a3", "lbl": "Checklist cargado"},
            {"from": "a3", "to": "d1"},
            {"from": "d1", "to": "a_noconf", "dir": "left", "lbl": "[No conforme]"},
            {"from": "a_noconf", "to": "a_notif"},
            {"from": "a_notif", "to": "a4", "lbl": "Orden emitida"},
            {"from": "a4", "to": "a3", "type": "loop_gutter", "lbl": "Solicitar reinspección"},
            {"from": "d1", "to": "a5", "dir": "down", "lbl": "[Conforme 100%]"},
            {"from": "a5", "to": "a6", "lbl": "Acta firmada"},
            {"from": "a6", "to": "a7", "lbl": "Partida liberada"},
            {"from": "a7", "to": "end_exito", "lbl": "Dossier cerrado"}
        ]
    },
    {
        "id": "act_cu41_operacion_offline",
        "tab_name": "CU41M - Operación Offline",
        "cu_code": "CU41M",
        "title": "CU41M – Gestionar operación offline y sincronización",
        "subtitle": "Representación de trabajo sin conexión en faena, almacenamiento SQLite, recuperación de red y sincronización atómica.",
        "w": 1140,
        "h": 960,
        "lanes": [
            {"name": "Personal de Campo", "cx": 220},
            {"name": "Aplicación Móvil (Offline)", "cx": 570},
            {"name": "Servidor Central", "cx": 920}
        ],
        "nodes": [
            {"id": "start", "type": "start", "cx": 220, "cy": 135},
            {"id": "a1", "type": "action", "cx": 220, "cy": 205, "w": 220, "h": 50, "lines": ["Ingresar a frente de obra", "sin cobertura celular"]},
            {"id": "a2", "type": "action", "cx": 570, "cy": 205, "w": 220, "h": 50, "lines": ["Habilitar modo local con snapshot", "de obra en caché"]},
            {"id": "a3", "type": "action", "cx": 220, "cy": 295, "w": 220, "h": 50, "lines": ["Registrar avances físicos", "y reporte de incidencias"]},
            {"id": "a4", "type": "action", "cx": 570, "cy": 295, "w": 220, "h": 50, "lines": ["Almacenar datos en SQLite local", "como PENDIENTE_SYNC"]},
            {"id": "d1", "type": "decision", "cx": 570, "cy": 385, "w": 40, "h": 40, "q": "¿Detecta conexión Internet?"},
            {"id": "a_espera", "type": "action", "cx": 220, "cy": 475, "w": 210, "h": 50, "lines": ["Continuar jornada operativa", "registrando en local"]},
            {"id": "a5", "type": "action", "cx": 570, "cy": 540, "w": 220, "h": 50, "lines": ["Empaquetar lote de pendientes", "y enviar a sincronizar"]},
            {"id": "a6", "type": "action", "cx": 920, "cy": 540, "w": 220, "h": 50, "lines": ["Validar autenticación, permisos", "y verificar idempotencia"]},
            {"id": "d2", "type": "decision", "cx": 920, "cy": 625, "w": 40, "h": 40, "q": "¿Hay conflictos de versión?"},
            {"id": "a_resolve", "type": "action", "cx": 830, "cy": 710, "w": 150, "h": 50, "lines": ["Aplicar regla Last-Write", "y registrar en auditoría"]},
            {"id": "a_insert", "type": "action", "cx": 1010, "cy": 710, "w": 150, "h": 50, "lines": ["Consolidar avances e", "incidencias en base datos"]},
            {"id": "m1", "type": "join", "cx": 920, "cy": 775, "w": 50, "h": 12},
            {"id": "a7", "type": "action", "cx": 570, "cy": 830, "w": 220, "h": 50, "lines": ["Actualizar registros locales", "a SINCRONIZADO"]},
            {"id": "end_exito", "type": "end", "cx": 220, "cy": 910}
        ],
        "edges": [
            {"from": "start", "to": "a1"},
            {"from": "a1", "to": "a2"},
            {"from": "a2", "to": "a3", "lbl": "Caché lista"},
            {"from": "a3", "to": "a4"},
            {"from": "a4", "to": "d1"},
            {"from": "d1", "to": "a_espera", "dir": "left", "lbl": "[Sin conexión]"},
            {"from": "a_espera", "to": "a3", "type": "loop_gutter", "lbl": "Nuevos registros"},
            {"from": "d1", "to": "a5", "dir": "down", "lbl": "[Conexión restaurada]"},
            {"from": "a5", "to": "a6", "lbl": "Envío de lote"},
            {"from": "a6", "to": "d2"},
            {"from": "d2", "to": "a_resolve", "dir": "left", "lbl": "[Conflicto]"},
            {"from": "d2", "to": "a_insert", "dir": "right", "lbl": "[Sin conflicto]"},
            {"from": "a_resolve", "to": "m1"},
            {"from": "a_insert", "to": "m1"},
            {"from": "m1", "to": "a7", "lbl": "Lote confirmado"},
            {"from": "a7", "to": "end_exito", "lbl": "Sincronización OK"}
        ]
    },
    {
        "id": "act_cu42_garantias_posventa",
        "tab_name": "CU42 - Garantías y Posventa",
        "cu_code": "CU42 (W/M)",
        "title": "CU42 (W/M) – Gestionar garantías y servicio posventa inmobiliaria",
        "subtitle": "Representación de registro de solicitud, clasificación, validación de póliza, atención en sitio y resolución formal.",
        "w": 1140,
        "h": 960,
        "lanes": [
            {"name": "Propietario / Cliente", "cx": 220},
            {"name": "Técnico de Posventa", "cx": 570},
            {"name": "Sistema", "cx": 920}
        ],
        "nodes": [
            {"id": "start", "type": "start", "cx": 220, "cy": 135},
            {"id": "a1", "type": "action", "cx": 220, "cy": 205, "w": 220, "h": 50, "lines": ["Detectar desperfecto en unidad", "inmobiliaria entregada"]},
            {"id": "a2", "type": "action", "cx": 220, "cy": 295, "w": 220, "h": 50, "lines": ["Registrar solicitud de garantía", "adjuntando fotos y detalle"]},
            {"id": "a3", "type": "action", "cx": 920, "cy": 295, "w": 220, "h": 50, "lines": ["Clasificar tipo de falla y", "verificar vigencia de póliza"]},
            {"id": "d1", "type": "decision", "cx": 920, "cy": 385, "w": 40, "h": 40, "q": "¿Cubre la póliza de garantía?"},
            {"id": "a_rech", "type": "action", "cx": 820, "cy": 475, "w": 160, "h": 50, "lines": ["Notificar improcedencia", "y cotizar servicio particular"]},
            {"id": "end_rech", "type": "end", "cx": 220, "cy": 475},
            {"id": "a4", "type": "action", "cx": 920, "cy": 555, "w": 210, "h": 50, "lines": ["Aprobar solicitud, asignar", "técnico y programar visita"]},
            {"id": "a5", "type": "action", "cx": 570, "cy": 645, "w": 220, "h": 50, "lines": ["Realizar peritaje en sitio y", "ejecutar reparación técnica"]},
            {"id": "a6", "type": "action", "cx": 220, "cy": 735, "w": 220, "h": 50, "lines": ["Inspeccionar trabajos y firmar", "acta de conformidad"]},
            {"id": "a7", "type": "action", "cx": 920, "cy": 820, "w": 220, "h": 50, "lines": ["Cerrar ticket de posventa y", "registrar costos asumidos"]},
            {"id": "a8", "type": "action", "cx": 220, "cy": 820, "w": 210, "h": 50, "lines": ["Responder encuesta de", "satisfacción del servicio"]},
            {"id": "end_exito", "type": "end", "cx": 220, "cy": 905}
        ],
        "edges": [
            {"from": "start", "to": "a1"},
            {"from": "a1", "to": "a2"},
            {"from": "a2", "to": "a3", "lbl": "Ticket emitido"},
            {"from": "a3", "to": "d1"},
            {"from": "d1", "to": "a_rech", "dir": "left", "lbl": "[No cubre / Expirada]"},
            {"from": "a_rech", "to": "end_rech", "lbl": "Garantía declinada"},
            {"from": "d1", "to": "a4", "dir": "down", "lbl": "[Garantía vigente]"},
            {"from": "a4", "to": "a5", "lbl": "Asignación de orden"},
            {"from": "a5", "to": "a6", "lbl": "Reparación concluida"},
            {"from": "a6", "to": "a7", "lbl": "Conformidad firmada"},
            {"from": "a7", "to": "a8", "lbl": "Ticket resuelto"},
            {"from": "a8", "to": "end_exito", "lbl": "Servicio concluido"}
        ]
    }
]

# Helper to render SVG & High-Res PNG
for act in activities_spec:
    w = act["w"]
    h = act["h"]
    lanes = act["lanes"]
    num_lanes = len(lanes)
    lane_w = (w - 90) / num_lanes

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    svg.append('''<defs>
      <marker id="act-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
      </marker>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" flood-color="#000000" flood-opacity="0.08"/>
      </filter>
    </defs>''')
    svg.append(f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>')

    # Title Banner (Academic, Premium)
    svg.append(f'<text x="45" y="30" font-family="Arial, Helvetica, sans-serif" font-size="14.5" font-weight="bold" fill="#000000">{act["title"]}</text>')
    svg.append(f'<text x="45" y="47" font-family="Arial, Helvetica, sans-serif" font-size="10.5" fill="#555555">{act["subtitle"]}</text>')

    # Outer Swimlane Frame
    top_y = 58
    bot_y = h - 25
    header_h = 38
    svg.append(f'<rect x="45" y="{top_y}" width="{w-90}" height="{bot_y - top_y}" fill="none" stroke="#000000" stroke-width="1.3"/>')

    for idx, lane in enumerate(lanes):
        lx = 45 + idx * lane_w
        # Header Box with clean styling
        svg.append(f'<rect x="{lx}" y="{top_y}" width="{lane_w}" height="{header_h}" fill="#F0F2F5" stroke="#000000" stroke-width="1.2"/>')
        svg.append(f'<text x="{lx + lane_w/2}" y="{top_y + 24}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="11.5" font-weight="bold" fill="#111111">{lane["name"]}</text>')
        # Vertical Lane Divider
        if idx > 0:
            svg.append(f'<line x1="{lx}" y1="{top_y + header_h}" x2="{lx}" y2="{bot_y}" stroke="#000000" stroke-width="1.2"/>')

    node_map = {n["id"]: n for n in act["nodes"]}

    # Draw Edges (Clean Manhattan Routing with Zero Intersections)
    for edge in act["edges"]:
        n1 = node_map[edge["from"]]
        n2 = node_map[edge["to"]]
        lbl = edge.get("lbl", "")
        direction = edge.get("dir", "")
        edge_type = edge.get("type", "normal")

        if edge_type == "loop_gutter":
            # Backward loop routed through the left gutter (x=25) so it touches NO nodes!
            x1 = n1["cx"] - n1["w"]/2
            y1 = n1["cy"]
            x2 = n2["cx"] - n2["w"]/2
            y2 = n2["cy"]
            gutter_x = 22
            svg.append(f'<path d="M {x1} {y1} L {gutter_x} {y1} L {gutter_x} {y2} L {x2} {y2}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#act-arr)"/>')
            if lbl:
                mid_y = (y1 + y2) / 2
                svg.append(f'<rect x="{gutter_x + 5}" y="{mid_y - 8}" width="{len(lbl)*6.5 + 10}" height="16" rx="3" fill="#FFFFFF" stroke="#CCCCCC" stroke-width="1"/>')
                svg.append(f'<text x="{gutter_x + 10}" y="{mid_y + 4}" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#000000">{lbl}</text>')
            continue

        # Normal Attachments
        if n1["type"] == "start":
            x1 = n1["cx"]
            y1 = n1["cy"] + 11
        elif n1["type"] == "decision":
            if direction == "left":
                x1 = n1["cx"] - n1["w"]/2
                y1 = n1["cy"]
            elif direction == "right":
                x1 = n1["cx"] + n1["w"]/2
                y1 = n1["cy"]
            else:
                x1 = n1["cx"]
                y1 = n1["cy"] + n1["h"]/2
        elif n1["type"] == "join":
            x1 = n1["cx"]
            y1 = n1["cy"] + n1["h"]/2
        else:
            x1 = n1["cx"]
            y1 = n1["cy"] + n1["h"]/2

        if n2["type"] == "end":
            x2 = n2["cx"]
            y2 = n2["cy"] - 12
        elif n2["type"] == "decision":
            x2 = n2["cx"]
            y2 = n2["cy"] - n2["h"]/2
        elif n2["type"] == "join":
            x2 = n2["cx"]
            y2 = n2["cy"] - n2["h"]/2
        else:
            x2 = n2["cx"]
            y2 = n2["cy"] - n2["h"]/2

        # Route lines
        if abs(x1 - x2) < 5:
            # Straight vertical line
            svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000000" stroke-width="1.2" marker-end="url(#act-arr)"/>')
            if lbl:
                mid_y = (y1 + y2) / 2
                lw = len(lbl) * 6.3 + 12
                svg.append(f'<rect x="{x1 - lw/2}" y="{mid_y - 8}" width="{lw}" height="16" rx="3" fill="#FFFFFF" stroke="#BBBBBB" stroke-width="1"/>')
                svg.append(f'<text x="{x1}" y="{mid_y + 4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#000000">{lbl}</text>')
        else:
            # Orthogonal step line
            mid_y = y1 + (y2 - y1) * 0.5
            svg.append(f'<path d="M {x1} {y1} L {x1} {mid_y} L {x2} {mid_y} L {x2} {y2}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#act-arr)"/>')
            if lbl:
                mid_x = (x1 + x2) / 2
                lw = len(lbl) * 6.3 + 12
                svg.append(f'<rect x="{mid_x - lw/2}" y="{mid_y - 8}" width="{lw}" height="16" rx="3" fill="#FFFFFF" stroke="#BBBBBB" stroke-width="1"/>')
                svg.append(f'<text x="{mid_x}" y="{mid_y + 4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#000000">{lbl}</text>')

    # Draw Nodes
    for n in act["nodes"]:
        nt = n["type"]
        cx = n["cx"]
        cy = n["cy"]

        if nt == "start":
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="11" fill="#000000" stroke="#000000" stroke-width="1.2" filter="url(#shadow)"/>')
        elif nt == "end":
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="#FFFFFF" stroke="#000000" stroke-width="1.4" filter="url(#shadow)"/>')
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="#000000"/>')
        elif nt == "decision":
            w_d = n["w"]
            h_d = n["h"]
            svg.append(f'<polygon points="{cx},{cy - h_d/2} {cx + w_d/2},{cy} {cx},{cy + h_d/2} {cx - w_d/2},{cy}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3" filter="url(#shadow)"/>')
            if "q" in n and n["q"]:
                q_text = n["q"]
                qw = len(q_text) * 6.2 + 10
                svg.append(f'<rect x="{cx - qw/2}" y="{cy - h_d/2 - 20}" width="{qw}" height="16" rx="3" fill="#FFFFFF" stroke="#AAAAAA" stroke-width="0.8"/>')
                svg.append(f'<text x="{cx}" y="{cy - h_d/2 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#000000">{q_text}</text>')
        elif nt == "join":
            w_j = n["w"]
            h_j = n["h"]
            svg.append(f'<rect x="{cx - w_j/2}" y="{cy - h_j/2}" width="{w_j}" height="{h_j}" rx="3" fill="#000000"/>')
        elif nt == "action":
            aw = n["w"]
            ah = n["h"]
            svg.append(f'<rect x="{cx - aw/2}" y="{cy - ah/2}" width="{aw}" height="{ah}" rx="12" fill="#FFFFFF" stroke="#000000" stroke-width="1.3" filter="url(#shadow)"/>')
            lines = n["lines"]
            start_ty = cy - (len(lines)-1)*7 + 4
            for l in lines:
                svg.append(f'<text x="{cx}" y="{start_ty}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">{l}</text>')
                start_ty += 14

    svg.append('</svg>')
    svg_content = "\n".join(svg)
    svg_path = f'docs/diagramas/{act["id"]}.svg'
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    png_path = f'docs/diagramas/{act["id"]}.png'
    # Render at 2x resolution for razor-sharp quality
    png_bytes = resvg_py.svg_to_bytes(svg_content)
    with open(png_path, 'wb') as f:
        f.write(png_bytes)

    shutil.copyfile(svg_path, os.path.join(brain_diag_dir, f'{act["id"]}.svg'))
    shutil.copyfile(png_path, os.path.join(brain_diag_dir, f'{act["id"]}.png'))
    print(f"Generated High-Res PNG & SVG for: {act['title']}")

# ==============================================================================
# DRAW.IO MULTI-TAB XML (100% Matching Layout)
# ==============================================================================
drawio_xml = []
drawio_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
drawio_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-22T21:50:00.000Z" agent="Antigravity" version="24.0.0" type="device">')

for act in activities_spec:
    act_id = act["id"]
    tab_name = act["tab_name"]
    w = act["w"]
    h = act["h"]
    lanes = act["lanes"]
    lane_w = (w - 90) / len(lanes)

    drawio_xml.append(f'  <diagram id="{act_id}" name="{html.escape(tab_name)}">')
    drawio_xml.append(f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{w}" pageHeight="{h}" background="#FFFFFF" math="0" shadow="0">')
    drawio_xml.append('      <root>')
    drawio_xml.append('        <mxCell id="0" />')
    drawio_xml.append('        <mxCell id="1" parent="0" />')

    # Title
    drawio_xml.append(f'        <mxCell id="title_{act_id}" value="&lt;b&gt;{html.escape(act["title"])}&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;{html.escape(act["subtitle"])}&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=12;fontColor=#000000;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="45" y="15" width="{w-90}" height="35" as="geometry" />')
    drawio_xml.append('        </mxCell>')

    # Pool Container
    top_y = 58
    bot_h = h - 85
    drawio_xml.append(f'        <mxCell id="pool_{act_id}" value="" style="swimlane;html=1;childLayout=stackLayout;resizeParent=1;resizeParentMax=0;startSize=0;horizontal=1;horizontalStack=1;fillColor=none;strokeColor=#000000;strokeWidth=1.3;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="45" y="{top_y}" width="{w-90}" height="{bot_h}" as="geometry" />')
    drawio_xml.append('        </mxCell>')

    header_h = 38
    for idx, lane in enumerate(lanes):
        drawio_xml.append(f'        <mxCell id="lane_{act_id}_{idx}" value="&lt;b&gt;{html.escape(lane["name"])}&lt;/b&gt;" style="swimlane;html=1;startSize={header_h};fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=11;fontColor=#000000;collapsible=0;" vertex="1" parent="pool_{act_id}">')
        drawio_xml.append(f'          <mxGeometry x="{int(idx*lane_w)}" y="0" width="{int(lane_w)}" height="{bot_h}" as="geometry" />')
        drawio_xml.append('        </mxCell>')

    node_map = {n["id"]: n for n in act["nodes"]}

    # Place Nodes (Absolute inside parent="1" for seamless cross-lane connections)
    for n in act["nodes"]:
        nid = f"{act_id}_{n['id']}"
        nt = n["type"]
        cx = n["cx"]
        cy = n["cy"]

        if nt == "start":
            drawio_xml.append(f'        <mxCell id="{nid}" value="" style="ellipse;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=#000000;strokeWidth=1.2;" vertex="1" parent="1">')
            drawio_xml.append(f'          <mxGeometry x="{cx-11}" y="{cy-11}" width="22" height="22" as="geometry" />')
            drawio_xml.append('        </mxCell>')
        elif nt == "end":
            drawio_xml.append(f'        <mxCell id="{nid}" value="" style="ellipse;shape=doubleEllipse;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=#000000;strokeWidth=1.4;" vertex="1" parent="1">')
            drawio_xml.append(f'          <mxGeometry x="{cx-12}" y="{cy-12}" width="24" height="24" as="geometry" />')
            drawio_xml.append('        </mxCell>')
        elif nt == "decision":
            w_d = n["w"]
            h_d = n["h"]
            drawio_xml.append(f'        <mxCell id="{nid}" value="" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;" vertex="1" parent="1">')
            drawio_xml.append(f'          <mxGeometry x="{cx - w_d/2}" y="{cy - h_d/2}" width="{w_d}" height="{h_d}" as="geometry" />')
            drawio_xml.append('        </mxCell>')
            if "q" in n and n["q"]:
                q_txt = html.escape(n["q"])
                drawio_xml.append(f'        <mxCell id="{nid}_lbl" value="&lt;b&gt;{q_txt}&lt;/b&gt;" style="text;html=1;strokeColor=#AAAAAA;strokeWidth=1;fillColor=#FFFFFF;rounded=1;align=center;verticalAlign=middle;fontSize=9;fontFamily=Arial;fontColor=#000000;" vertex="1" parent="1">')
                drawio_xml.append(f'          <mxGeometry x="{cx - 75}" y="{cy - h_d/2 - 22}" width="150" height="18" as="geometry" />')
                drawio_xml.append('        </mxCell>')
        elif nt == "join":
            w_j = n["w"]
            h_j = n["h"]
            drawio_xml.append(f'        <mxCell id="{nid}" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=#000000;strokeWidth=1.2;" vertex="1" parent="1">')
            drawio_xml.append(f'          <mxGeometry x="{cx - w_j/2}" y="{cy - h_j/2}" width="{w_j}" height="{h_j}" as="geometry" />')
            drawio_xml.append('        </mxCell>')
        elif nt == "action":
            aw = n["w"]
            ah = n["h"]
            txt = "&lt;br&gt;".join(html.escape(l) for l in n["lines"])
            drawio_xml.append(f'        <mxCell id="{nid}" value="{txt}" style="rounded=1;arcSize=24;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontColor=#000000;align=center;" vertex="1" parent="1">')
            drawio_xml.append(f'          <mxGeometry x="{cx - aw/2}" y="{cy - ah/2}" width="{aw}" height="{ah}" as="geometry" />')
            drawio_xml.append('        </mxCell>')

    # Edges
    for edge_idx, edge in enumerate(act["edges"]):
        eid = f"edge_{act_id}_{edge_idx}"
        full_src = f"{act_id}_{edge['from']}"
        full_dst = f"{act_id}_{edge['to']}"
        lbl = html.escape(edge.get("lbl", ""))
        edge_type = edge.get("type", "normal")

        edge_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelBackgroundColor=#FFFFFF;labelBorderColor=#CCCCCC;"
        if edge_type == "loop_gutter":
            # Add routing points for the loop around the left margin
            drawio_xml.append(f'        <mxCell id="{eid}" value="{lbl}" style="{edge_style}" edge="1" parent="1" source="{full_src}" target="{full_dst}">')
            drawio_xml.append(f'          <mxGeometry relative="1" as="geometry">')
            drawio_xml.append(f'            <Array as="points">')
            drawio_xml.append(f'              <mxPoint x="22" y="{node_map[edge["from"]]["cy"]}" />')
            drawio_xml.append(f'              <mxPoint x="22" y="{node_map[edge["to"]]["cy"]}" />')
            drawio_xml.append(f'            </Array>')
            drawio_xml.append(f'          </mxGeometry>')
            drawio_xml.append('        </mxCell>')
        else:
            drawio_xml.append(f'        <mxCell id="{eid}" value="{lbl}" style="{edge_style}" edge="1" parent="1" source="{full_src}" target="{full_dst}">')
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
print("Successfully generated all 6 high-end activity diagrams and Draw.io file!")
