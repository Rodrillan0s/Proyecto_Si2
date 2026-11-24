import os
import shutil
import html
import resvg_py

brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'
os.makedirs('docs/diagramas', exist_ok=True)
os.makedirs(brain_diag_dir, exist_ok=True)

# Helper for Class Card HTML
def format_class_card(title, attrs, methods):
    parts = [f'<p style="margin:0px;padding-top:4px;text-align:center;"><b>{html.escape(title)}</b></p>']
    if attrs:
        parts.append('<hr style="border:none;border-top:1px solid #000000;margin:4px 0px;"/>')
        attrs_html = "<br/>".join(html.escape(a) for a in attrs)
        parts.append(f'<div style="padding:2px 8px;text-align:left;font-family:Arial;font-size:10px;">{attrs_html}</div>')
    if methods:
        parts.append('<hr style="border:none;border-top:1px solid #000000;margin:4px 0px;"/>')
        methods_html = "<br/>".join(html.escape(m) for m in methods)
        parts.append(f'<div style="padding:2px 8px;text-align:left;font-family:Arial;font-size:10px;">{methods_html}</div>')
    return "".join(parts)

# ==============================================================================
# 1. GENERATE DRAW.IO CLASS ANALYSIS DIAGRAM (CU41 - COMPLETE BCE WITH AVANCE & INCIDENCIA)
# ==============================================================================
cls_xml = []
cls_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
cls_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-22T15:00:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
cls_xml.append('  <diagram id="cu41_analisis_clases_completo" name="CU41 - Analisis de Clases BCE">')
cls_xml.append('    <mxGraphModel dx="1400" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1550" pageHeight="1000" background="#FFFFFF" math="0" shadow="0">')
cls_xml.append('      <root>')
cls_xml.append('        <mxCell id="0" />')
cls_xml.append('        <mxCell id="1" parent="0" />')

# Title
cls_xml.append('        <mxCell id="title" value="&lt;b&gt;Diagrama de Análisis de Clases (BCE) — CU41: Gestionar Operación Offline y Sincronización&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;Historias de Usuario: HU90 (Consulta Offline), HU91 (Avances Offline), HU92 (Incidencias Offline), HU93 (Sync Automático), HU94 (Estado Sync)&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=12;fontColor=#000000;" vertex="1" parent="1">')
cls_xml.append('          <mxGeometry x="40" y="20" width="950" height="40" as="geometry" />')
cls_xml.append('        </mxCell>')

# 1. Form (Boundary Móvil)
form_val = format_class_card(
    "Form_Operacion_Offline",
    [
        "+ id_obra: int",
        "+ id_unidad: int",
        "+ porcentaje_avance: numeric",
        "+ observacion_avance: text",
        "+ titulo_incidencia: text",
        "+ descripcion_incidencia: text",
        "+ prioridad_incidencia: text",
        "+ estado_red: bool",
        "+ total_pendientes: int"
    ],
    [
        "+ registrar_avance_offline_ui()",
        "+ registrar_incidencia_offline_ui()",
        "+ consultar_obra_offline_ui()",
        "+ consultar_estado_sync_ui()",
        "+ forzar_sincronizacion_ui()"
    ]
)
cls_xml.append(f'        <mxCell id="cell_form" value="{html.escape(form_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_xml.append('          <mxGeometry x="40" y="320" width="240" height="290" as="geometry" />')
cls_xml.append('        </mxCell>')

# 2. Control (Registro / Coordinador de Sincronización)
ctrl_val = format_class_card(
    "Sync_Manager_Control",
    [
        "- red_activa: bool",
        "- temporizador_sync: Timer",
        "- url_backend_sync: text",
        "- max_reintentos: int"
    ],
    [
        "- consultar_info_obra_cache()",
        "- guardar_avance_offline()",
        "- guardar_incidencia_offline()",
        "- obtener_pendientes_sincronizacion()",
        "- despachar_lote_sync_api()",
        "- procesar_lote_batch_db()",
        "- actualizar_estado_sync_db()",
        "- registrar_log_sincronizacion()"
    ]
)
cls_xml.append(f'        <mxCell id="cell_control" value="{html.escape(ctrl_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_xml.append('          <mxGeometry x="340" y="320" width="250" height="290" as="geometry" />')
cls_xml.append('        </mxCell>')

# 3. Main Central Entity: COLA_SINCRONIZACION (SQLite Móvil)
cola_val = format_class_card(
    "COLA_SINCRONIZACION",
    [
        "+ id_local: str (UUID)",
        "+ tipo_registro: str ('AVANCE'|'INCIDENCIA')",
        "+ payload_json: text",
        "+ estado: str ('PENDIENTE'|'SINCRONIZADO')",
        "+ fecha_registro_local: datetime",
        "+ reintentos: int",
        "+ id_obra: int",
        "+ id_usuario: int"
    ],
    [
        "+ encolar_registro_local()",
        "+ listar_pendientes_sync()",
        "+ marcar_sincronizado()",
        "+ contar_por_estado()"
    ]
)
cls_xml.append(f'        <mxCell id="cell_cola" value="{html.escape(cola_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_xml.append('          <mxGeometry x="660" y="320" width="240" height="290" as="geometry" />')
cls_xml.append('        </mxCell>')

# 4. Top Entity: OBRA (t_obra)
obra_val = format_class_card(
    "OBRA",
    [
        "+ id_obra: int",
        "+ nombre_obra: text",
        "+ id_empresa: int",
        "+ estado: text",
        "+ fecha_inicio: date",
        "+ fecha_fin_prevista: date"
    ],
    [
        "+ consultar_obra_db()",
        "+ generar_snapshot_cache_obra()"
    ]
)
cls_xml.append(f'        <mxCell id="cell_obra" value="{html.escape(obra_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_xml.append('          <mxGeometry x="660" y="90" width="240" height="170" as="geometry" />')
cls_xml.append('        </mxCell>')

# 5. Entity: AVANCE_OBRA (obras.t_avance_obra) -> REQUERIDA
avance_val = format_class_card(
    "AVANCE_OBRA",
    [
        "+ id_avance: int",
        "+ id_obra: int",
        "+ id_unidad: int",
        "+ porcentaje_avance: numeric(5,2)",
        "+ fecha_registro: date",
        "+ observacion: text",
        "+ id_usuario: int",
        "+ created_at: timestamptz"
    ],
    [
        "+ registrar_avance_db()",
        "+ consultar_historial_avances()",
        "+ validar_porcentaje_unidad()"
    ]
)
cls_xml.append(f'        <mxCell id="cell_avance" value="{html.escape(avance_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_xml.append('          <mxGeometry x="980" y="200" width="240" height="240" as="geometry" />')
cls_xml.append('        </mxCell>')

# 6. Entity: INCIDENCIA (obras.t_incidencia)
incidencia_val = format_class_card(
    "INCIDENCIA",
    [
        "+ id_incidencia: int",
        "+ id_obra: int",
        "+ id_unidad: int",
        "+ id_usuario_registro: int",
        "+ titulo: text",
        "+ descripcion: text",
        "+ prioridad: text ('BAJA'|'MEDIA'|'ALTA'|'CRITICA')",
        "+ estado: text ('ABIERTA'|'RESUELTA')",
        "+ created_at: timestamptz"
    ],
    [
        "+ registrar_incidencia_db()",
        "+ consultar_incidencias_obra()",
        "+ cambiar_estado_incidencia()"
    ]
)
cls_xml.append(f'        <mxCell id="cell_incidencia" value="{html.escape(incidencia_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_xml.append('          <mxGeometry x="980" y="490" width="240" height="260" as="geometry" />')
cls_xml.append('        </mxCell>')

# 7. Entity: SINCRONIZACION_LOG (obras.t_sincronizacion_log)
log_val = format_class_card(
    "SINCRONIZACION_LOG",
    [
        "+ id_log: int",
        "+ id_empresa: int",
        "+ id_usuario: int",
        "+ id_dispositivo: text",
        "+ total_recibidos: int",
        "+ total_sincronizados: int",
        "+ total_errores: int",
        "+ fecha_sincronizacion: timestamptz"
    ],
    [
        "+ insertar_log_sincronizacion()",
        "+ consultar_auditoria_sync()"
    ]
)
cls_xml.append(f'        <mxCell id="cell_log" value="{html.escape(log_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_xml.append('          <mxGeometry x="660" y="670" width="240" height="220" as="geometry" />')
cls_xml.append('        </mxCell>')

# Relationships with multiplicity (Exact style of user sample: Form - Control - Entity)
# 1. Form -> Control
cls_xml.append('        <mxCell id="edge_form_ctrl" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="cell_form" target="cell_control"><mxGeometry relative="1" as="geometry" /></mxCell>')

# 2. Control -> Cola
cls_xml.append('        <mxCell id="edge_ctrl_cola" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="cell_control" target="cell_cola"><mxGeometry relative="1" as="geometry" /></mxCell>')

# 3. Obra -> Cola (1 a 1..*)
cls_xml.append('        <mxCell id="edge_obra_cola" value="1&#xa;&#xa;&#xa;1..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;" edge="1" parent="1" source="cell_obra" target="cell_cola"><mxGeometry relative="1" as="geometry" /></mxCell>')

# 4. Cola -> Avance (1 a 0..*)
cls_xml.append('        <mxCell id="edge_cola_avance" value="1                  0..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;" edge="1" parent="1" source="cell_cola" target="cell_avance"><mxGeometry relative="1" as="geometry" /></mxCell>')

# 5. Cola -> Incidencia (1 a 0..*)
cls_xml.append('        <mxCell id="edge_cola_incidencia" value="1                  0..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;" edge="1" parent="1" source="cell_cola" target="cell_incidencia"><mxGeometry relative="1" as="geometry" /></mxCell>')

# 6. Cola -> Sincronizacion_Log (1 a 1)
cls_xml.append('        <mxCell id="edge_cola_log" value="1&#xa;&#xa;&#xa;1" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;" edge="1" parent="1" source="cell_cola" target="cell_log"><mxGeometry relative="1" as="geometry" /></mxCell>')

# 7. Obra -> Avance (1 a 1..*)
cls_xml.append('        <mxCell id="edge_obra_avance" value="1&#xa;&#xa;&#xa;1..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;exitX=1;exitY=0.5;entryX=0.5;entryY=0;" edge="1" parent="1" source="cell_obra" target="cell_avance"><mxGeometry relative="1" as="geometry" /></mxCell>')

# 8. Obra -> Incidencia (1 a 0..*)
cls_xml.append('        <mxCell id="edge_obra_incidencia" value="1&#xa;&#xa;&#xa;0..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;exitX=0.9;exitY=1;entryX=0.25;entryY=0;" edge="1" parent="1" source="cell_obra" target="cell_incidencia"><mxGeometry relative="1" as="geometry" /></mxCell>')

cls_xml.append('      </root>')
cls_xml.append('    </mxGraphModel>')
cls_xml.append('  </diagram>')
cls_xml.append('</mxfile>')

cls_drawio_path = 'docs/diagramas/analisis_clases_cu41_offline_sync.drawio'
with open(cls_drawio_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(cls_xml))

shutil.copyfile(cls_drawio_path, os.path.join(brain_diag_dir, 'analisis_clases_cu41_offline_sync.drawio'))
print("Regenerated complete Class Analysis diagram with AVANCE_OBRA, INCIDENCIA, OBRA, and LOG!")

# ==============================================================================
# 2. UPDATE SEQUENCE DIAGRAM (CU41 - WITH BOTH AVANCE & INCIDENCIA LIFELINES)
# ==============================================================================
seq_drawio = []
seq_drawio.append('<?xml version="1.0" encoding="UTF-8"?>')
seq_drawio.append('<mxfile host="app.diagrams.net" modified="2026-11-22T15:00:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
seq_drawio.append('  <diagram id="cu41_secuencia_offline_sync" name="CU41 - Secuencia Offline Sync">')
seq_drawio.append('    <mxGraphModel dx="1600" dy="1100" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1650" pageHeight="1150" background="#FFFFFF" math="0" shadow="0">')
seq_drawio.append('      <root>')
seq_drawio.append('        <mxCell id="0" />')
seq_drawio.append('        <mxCell id="1" parent="0" />')

# Frame
seq_drawio.append('        <mxCell id="frame_sd" value="sd CU41 - Gestionar Operacion Offline y Sincronizacion (HU90-HU94)" style="shape=umlFrame;whiteSpace=wrap;html=1;width=420;height=22;fillColor=none;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=11;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
seq_drawio.append('          <mxGeometry x="20" y="20" width="1580" height="1060" as="geometry" />')
seq_drawio.append('        </mxCell>')

# Lifelines
seq_drawio.append('        <mxCell id="ll_actor" value="user : PersonalCampo" style="shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=10;fontColor=#000000;" vertex="1" parent="1">')
seq_drawio.append('          <mxGeometry x="50" y="60" width="40" height="1000" as="geometry" />')
seq_drawio.append('        </mxCell>')

lifelines = [
    ("ll_ui", "ui : OperacionOfflineUI", 160, 150),
    ("ll_sync", "sync_mgr : SyncManager", 340, 150),
    ("ll_sqlite", "sqlite : LocalDbService", 520, 150),
    ("ll_router", "router : sync_routes", 700, 140),
    ("ll_service", "service : sync_services", 870, 140),
    ("ll_t_avance", "t_avance_obra", 1040, 130),
    ("ll_t_inc", "t_incidencia", 1200, 130),
    ("ll_t_log", "t_sincronizacion_log", 1360, 140)
]

for lid, lname, lx, lw in lifelines:
    seq_drawio.append(f'        <mxCell id="{lid}" value="{html.escape(lname)}" style="shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=11;fontColor=#000000;rounded=1;" vertex="1" parent="1">')
    seq_drawio.append(f'          <mxGeometry x="{lx}" y="60" width="{lw}" height="1000" as="geometry" />')
    seq_drawio.append('        </mxCell>')

def add_msg(mid, val, x1, x2, y, is_ret=False, is_dashed=False):
    style = f"endArrow={'open' if is_ret else 'classic'};html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9.5;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;"
    if is_dashed or is_ret:
        style += "dashed=1;"
    return f'''        <mxCell id="edge_{mid}" value="{html.escape(val)}" style="{style}" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="{x1}" y="{y}" as="sourcePoint" />
            <mxPoint x="{x2}" y="{y}" as="targetPoint" />
          </mxGeometry>
        </mxCell>'''

def add_box(bid, val, x, y, w, h):
    return f'''        <mxCell id="{bid}" value="{html.escape(val)}" style="shape=umlFrame;whiteSpace=wrap;html=1;width=180;height=20;fillColor=none;strokeColor=#333333;strokeWidth=1;strokeDasharray=3 3;fontFamily=Arial;fontSize=10;fontStyle=2;fontColor=#333333;" vertex="1" parent="1">
          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />
        </mxCell>'''

# Centers:
# Actor: 70
# UI: 235
# SyncMgr: 415
# SQLite: 595
# Router: 770
# Service: 940
# TAvance: 1105
# TInc: 1265
# TLog: 1430

# Section 1: HU90 - Consultar obra offline
seq_drawio.append(add_box("box_hu90", "alt [HU90 - Consultar Obra sin Conexión]", 40, 130, 620, 170))
seq_drawio.append(add_msg("1", "1: consultar_obra_offline(id_obra)", 70, 235, 160))
seq_drawio.append(add_msg("2", "2: obtener_datos_cache(id_obra)", 235, 415, 185))
seq_drawio.append(add_msg("3", "3: SELECT datos_obra FROM cache_obra WHERE id_obra=?", 415, 595, 210))
seq_drawio.append(add_msg("4", "4: return datos_cache_offline()", 595, 415, 235, is_ret=True))
seq_drawio.append(add_msg("5", "5: return datos_obra_offline()", 415, 235, 260, is_ret=True))
seq_drawio.append(add_msg("6", "6: mostrar_informacion_offline(datos)", 235, 70, 285, is_ret=True))

# Section 2: HU91 / HU92 - Registrar Avance o Incidencia sin Conexión
seq_drawio.append(add_box("box_hu91", "alt [HU91 / HU92 - Registrar Avance o Incidencia sin Conexión]", 40, 320, 620, 200))
seq_drawio.append(add_msg("7", "7: registrar_avance_o_incidencia(datos)", 70, 235, 350))
seq_drawio.append(add_msg("8", "8: guardar_registro_offline(tipo, payload)", 235, 415, 380))
seq_drawio.append(add_msg("9", "9: INSERT INTO cola_pendientes(tipo, payload, 'PENDIENTE')", 415, 595, 410))
seq_drawio.append(add_msg("10", "10: return id_local_pendiente", 595, 415, 440, is_ret=True))
seq_drawio.append(add_msg("11", "11: return confirmacion_guardado_local()", 415, 235, 470, is_ret=True))
seq_drawio.append(add_msg("12", "12: mostrar_notificacion('Guardado localmente - Pendiente de Sync')", 235, 70, 500, is_ret=True))

# Section 3: HU93 - Sincronizar Automáticamente Datos Pendientes
seq_drawio.append(add_box("box_hu93", "alt [HU93 - Sincronizar Automáticamente al Recuperar Conexión]", 40, 540, 1530, 340))
seq_drawio.append(add_msg("13", "13: evento_red(conexion_restablecida)", 70, 415, 570))
seq_drawio.append(add_msg("14", "14: SELECT * FROM cola_pendientes WHERE estado='PENDIENTE'", 415, 595, 600))
seq_drawio.append(add_msg("15", "15: return lista_pendientes[avances, incidencias]", 595, 415, 630, is_ret=True))
seq_drawio.append(add_msg("16", "16: POST /api/v1/sync/batch (lote_datos, token_jwt)", 415, 770, 665))
seq_drawio.append(add_msg("17", "17: procesar_lote_sync(id_empresa, lote_datos)", 770, 940, 695))
seq_drawio.append(add_msg("18a", "18a: INSERT INTO obras.t_avance_obra (id_obra, porcentaje, ...)", 940, 1105, 720))
seq_drawio.append(add_msg("18b", "18b: INSERT INTO obras.t_incidencia (id_obra, titulo, ...)", 940, 1265, 745))
seq_drawio.append(add_msg("19", "19: INSERT INTO obras.t_sincronizacion_log (lote_id, total_ok)", 940, 1430, 770))
seq_drawio.append(add_msg("20", "20: return 200 OK (procesados: 5, ids_confirmados: [...])", 770, 415, 800, is_ret=True))
seq_drawio.append(add_msg("21", "21: UPDATE cola_pendientes SET estado='SINCRONIZADO'", 415, 595, 825))
seq_drawio.append(add_msg("22", "22: notificar_sync_completado(total: 5)", 415, 235, 850, is_ret=True))
seq_drawio.append(add_msg("23", "23: actualizar_badge('Todo sincronizado')", 235, 70, 875, is_ret=True))

# Section 4: HU94 - Consultar Estado de Sincronización
seq_drawio.append(add_box("box_hu94", "alt [HU94 - Consultar Estado de Sincronización]", 40, 900, 620, 160))
seq_drawio.append(add_msg("24", "24: consultar_estado_sincronizacion()", 70, 235, 930))
seq_drawio.append(add_msg("25", "25: obtener_resumen_cola()", 235, 415, 955))
seq_drawio.append(add_msg("26", "26: SELECT COUNT(*) GROUP BY estado", 415, 595, 980))
seq_drawio.append(add_msg("27", "27: return resumen { pendientes: 0, sincronizados: 12 }", 595, 235, 1010, is_ret=True))
seq_drawio.append(add_msg("28", "28: renderizar_panel_sync(estado_actual)", 235, 70, 1035, is_ret=True))

seq_drawio.append('      </root>')
seq_drawio.append('    </mxGraphModel>')
seq_drawio.append('  </diagram>')
seq_drawio.append('</mxfile>')

seq_drawio_path = 'docs/diagramas/secuencia_cu41_offline_sync.drawio'
with open(seq_drawio_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(seq_drawio))

shutil.copyfile(seq_drawio_path, os.path.join(brain_diag_dir, 'secuencia_cu41_offline_sync.drawio'))
print("Regenerated Sequence diagram with both t_avance_obra and t_incidencia lifelines!")
