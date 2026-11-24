import os
import shutil
import html
import resvg_py

brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'
os.makedirs('docs/diagramas', exist_ok=True)
os.makedirs(brain_diag_dir, exist_ok=True)

# ==============================================================================
# 1. GENERATE DRAW.IO SEQUENCE DIAGRAM (CU41 - HU90 a HU94)
# ==============================================================================
seq_drawio = []
seq_drawio.append('<?xml version="1.0" encoding="UTF-8"?>')
seq_drawio.append('<mxfile host="app.diagrams.net" modified="2026-11-22T14:40:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
seq_drawio.append('  <diagram id="cu41_secuencia_offline_sync" name="CU41 - Secuencia Offline Sync">')
seq_drawio.append('    <mxGraphModel dx="1400" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1500" pageHeight="1150" background="#FFFFFF" math="0" shadow="0">')
seq_drawio.append('      <root>')
seq_drawio.append('        <mxCell id="0" />')
seq_drawio.append('        <mxCell id="1" parent="0" />')

# Frame
seq_drawio.append('        <mxCell id="frame_sd" value="sd CU41 - Gestionar Operacion Offline y Sincronizacion (HU90-HU94)" style="shape=umlFrame;whiteSpace=wrap;html=1;width=420;height=22;fillColor=none;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=11;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
seq_drawio.append('          <mxGeometry x="20" y="20" width="1440" height="1060" as="geometry" />')
seq_drawio.append('        </mxCell>')

# Lifelines
# Lifeline 1: Actor
seq_drawio.append('        <mxCell id="ll_actor" value="user : PersonalCampo" style="shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=10;fontColor=#000000;" vertex="1" parent="1">')
seq_drawio.append('          <mxGeometry x="50" y="60" width="40" height="1000" as="geometry" />')
seq_drawio.append('        </mxCell>')

lifelines = [
    ("ll_ui", "ui : OperacionOfflineUI", 170, 160),
    ("ll_sync", "sync_mgr : SyncManager", 370, 160),
    ("ll_sqlite", "sqlite : LocalDbService", 570, 160),
    ("ll_router", "router : sync_routes", 770, 150),
    ("ll_service", "service : sync_services", 960, 150),
    ("ll_t_avance", "t_avance_obra", 1140, 130),
    ("ll_t_log", "t_sincronizacion_log", 1300, 140)
]

for lid, lname, lx, lw in lifelines:
    seq_drawio.append(f'        <mxCell id="{lid}" value="{html.escape(lname)}" style="shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=11;fontColor=#000000;rounded=1;" vertex="1" parent="1">')
    seq_drawio.append(f'          <mxGeometry x="{lx}" y="60" width="{lw}" height="1000" as="geometry" />')
    seq_drawio.append('        </mxCell>')

# Helper for messages
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

# Helper for alt box
def add_box(bid, val, x, y, w, h):
    return f'''        <mxCell id="{bid}" value="{html.escape(val)}" style="shape=umlFrame;whiteSpace=wrap;html=1;width=180;height=20;fillColor=none;strokeColor=#333333;strokeWidth=1;strokeDasharray=3 3;fontFamily=Arial;fontSize=10;fontStyle=2;fontColor=#333333;" vertex="1" parent="1">
          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />
        </mxCell>'''

# Centers:
# Actor: 70
# UI: 250
# SyncMgr: 450
# SQLite: 650
# Router: 845
# Service: 1035
# TAvance: 1205
# TLog: 1370

# Section 1: HU90 - Consultar obra offline
seq_drawio.append(add_box("box_hu90", "alt [HU90 - Consultar Obra sin Conexión]", 40, 130, 680, 170))
seq_drawio.append(add_msg("1", "1: consultar_obra_offline(id_obra)", 70, 250, 160))
seq_drawio.append(add_msg("2", "2: obtener_datos_cache(id_obra)", 250, 450, 185))
seq_drawio.append(add_msg("3", "3: SELECT datos_obra FROM cache_obra WHERE id_obra=?", 450, 650, 210))
seq_drawio.append(add_msg("4", "4: return datos_cache_offline()", 650, 450, 235, is_ret=True))
seq_drawio.append(add_msg("5", "5: return datos_obra_offline()", 450, 250, 260, is_ret=True))
seq_drawio.append(add_msg("6", "6: mostrar_informacion_offline(datos)", 250, 70, 285, is_ret=True))

# Section 2: HU91 / HU92 - Registrar Avance o Incidencia sin Conexión
seq_drawio.append(add_box("box_hu91", "alt [HU91 / HU92 - Registrar Avance o Incidencia sin Conexión]", 40, 320, 680, 200))
seq_drawio.append(add_msg("7", "7: registrar_avance_offline(id_actividad, porcentaje, obs)", 70, 250, 350))
seq_drawio.append(add_msg("8", "8: guardar_registro_offline('AVANCE', payload)", 250, 450, 380))
seq_drawio.append(add_msg("9", "9: INSERT INTO cola_pendientes(tipo, payload, 'PENDIENTE')", 450, 650, 410))
seq_drawio.append(add_msg("10", "10: return id_local_pendiente", 650, 450, 440, is_ret=True))
seq_drawio.append(add_msg("11", "11: return confirmacion_guardado_local()", 450, 250, 470, is_ret=True))
seq_drawio.append(add_msg("12", "12: mostrar_notificacion('Guardado localmente - Pendiente de Sync')", 250, 70, 500, is_ret=True))

# Section 3: HU93 - Sincronizar Automáticamente Datos Pendientes
seq_drawio.append(add_box("box_hu93", "alt [HU93 - Sincronizar Automáticamente al Recuperar Conexión]", 40, 540, 1390, 340))
seq_drawio.append(add_msg("13", "13: evento_red(conexion_restablecida)", 70, 450, 570))
seq_drawio.append(add_msg("14", "14: SELECT * FROM cola_pendientes WHERE estado='PENDIENTE'", 450, 650, 600))
seq_drawio.append(add_msg("15", "15: return lista_pendientes[avances, incidencias]", 650, 450, 630, is_ret=True))
seq_drawio.append(add_msg("16", "16: POST /api/v1/sync/batch (lote_datos, token_jwt)", 450, 845, 665))
seq_drawio.append(add_msg("17", "17: procesar_lote_sync(id_empresa, lote_datos)", 845, 1035, 695))
seq_drawio.append(add_msg("18", "18: INSERT INTO obras.t_avance_obra (id_obra, porcentaje, ...)", 1035, 1205, 725))
seq_drawio.append(add_msg("19", "19: INSERT INTO obras.t_sincronizacion_log (lote_id, total_ok)", 1035, 1370, 755))
seq_drawio.append(add_msg("20", "20: return 200 OK (procesados: 5, ids_confirmados: [...])", 845, 450, 790, is_ret=True))
seq_drawio.append(add_msg("21", "21: UPDATE cola_pendientes SET estado='SINCRONIZADO'", 450, 650, 820))
seq_drawio.append(add_msg("22", "22: notificar_sync_completado(total: 5)", 450, 250, 845, is_ret=True))
seq_drawio.append(add_msg("23", "23: actualizar_badge('Todo sincronizado')", 250, 70, 870, is_ret=True))

# Section 4: HU94 - Consultar Estado de Sincronización
seq_drawio.append(add_box("box_hu94", "alt [HU94 - Consultar Estado de Sincronización]", 40, 900, 680, 160))
seq_drawio.append(add_msg("24", "24: consultar_estado_sincronizacion()", 70, 250, 930))
seq_drawio.append(add_msg("25", "25: obtener_resumen_cola()", 250, 450, 955))
seq_drawio.append(add_msg("26", "26: SELECT COUNT(*) GROUP BY estado", 450, 650, 980))
seq_drawio.append(add_msg("27", "27: return resumen { pendientes: 0, sincronizados: 12 }", 650, 250, 1010, is_ret=True))
seq_drawio.append(add_msg("28", "28: renderizar_panel_sync(estado_actual)", 250, 70, 1035, is_ret=True))

seq_drawio.append('      </root>')
seq_drawio.append('    </mxGraphModel>')
seq_drawio.append('  </diagram>')
seq_drawio.append('</mxfile>')

seq_drawio_path = 'docs/diagramas/secuencia_cu41_offline_sync.drawio'
with open(seq_drawio_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(seq_drawio))

shutil.copyfile(seq_drawio_path, os.path.join(brain_diag_dir, 'secuencia_cu41_offline_sync.drawio'))
print("Generated Draw.io Sequence diagram for CU41!")

# ==============================================================================
# 2. GENERATE DRAW.IO CLASS ANALYSIS DIAGRAM (CU41 - BCE)
# ==============================================================================
cls_drawio = []
cls_drawio.append('<?xml version="1.0" encoding="UTF-8"?>')
cls_drawio.append('<mxfile host="app.diagrams.net" modified="2026-11-22T14:40:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
cls_drawio.append('  <diagram id="cu41_analisis_clases" name="CU41 - Analisis de Clases BCE">')
cls_drawio.append('    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1350" pageHeight="850" background="#FFFFFF" math="0" shadow="0">')
cls_drawio.append('      <root>')
cls_drawio.append('        <mxCell id="0" />')
cls_drawio.append('        <mxCell id="1" parent="0" />')

# Helper for class card
def format_class_card(title, attrs, methods):
    parts = [f'<p style="margin:0px;padding-top:4px;text-align:center;"><b>{html.escape(title)}</b></p>']
    if attrs:
        parts.append('<hr style="border:none;border-top:1px solid #000000;margin:4px 0px;"/>')
        attrs_html = "<br/>".join(html.escape(a) for a in attrs)
        parts.append(f'<div style="padding:2px 8px;text-align:left;font-family:Arial;font-size:10.5px;">{attrs_html}</div>')
    if methods:
        parts.append('<hr style="border:none;border-top:1px solid #000000;margin:4px 0px;"/>')
        methods_html = "<br/>".join(html.escape(m) for m in methods)
        parts.append(f'<div style="padding:2px 8px;text-align:left;font-family:Arial;font-size:10.5px;">{methods_html}</div>')
    return "".join(parts)

# 1. Form (Boundary Móvil)
form_val = format_class_card(
    "Form_Operacion_Offline",
    ["+ id_obra: int", "+ estado_red: bool", "+ total_pendientes: int", "+ registro_actual: Map"],
    ["+ capturar_avance_offline()", "+ capturar_incidencia_offline()", "+ ver_informacion_obra()", "+ consultar_estado_sync()", "+ forzar_sincronizacion()"]
)
cls_drawio.append(f'        <mxCell id="cell_form" value="{html.escape(form_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_drawio.append('          <mxGeometry x="40" y="220" width="230" height="230" as="geometry" />')
cls_drawio.append('        </mxCell>')

# 2. Control Móvil (SyncManager)
ctrl_val = format_class_card(
    "Sync_Manager_Control",
    ["- red_activa: bool", "- temporizador_sync: Timer", "- reintentos: int"],
    ["- verificar_conectividad()", "- encolar_operacion_local()", "- despachar_lote_pendientes()", "- procesar_respuesta_sync()", "- refrescar_cache_local()"]
)
cls_drawio.append(f'        <mxCell id="cell_control" value="{html.escape(ctrl_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_drawio.append('          <mxGeometry x="320" y="220" width="220" height="230" as="geometry" />')
cls_drawio.append('        </mxCell>')

# 3. Main Entity (Cola_Sincronizacion_Local en SQLite)
main_val = format_class_card(
    "Cola_Sincronizacion_Local",
    ["+ id_local: str (UUID)", "+ tipo_registro: str", "+ payload_json: text", "+ estado: str (PEND/SYNC)", "+ fecha_creacion: datetime", "+ intento_count: int"],
    ["+ insertar_pendiente()", "+ listar_pendientes()", "+ marcar_sincronizado()", "+ registrar_fallo()"]
)
cls_drawio.append(f'        <mxCell id="cell_main" value="{html.escape(main_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_drawio.append('          <mxGeometry x="590" y="210" width="210" height="250" as="geometry" />')
cls_drawio.append('        </mxCell>')

# 4. Top Entity: Cache_Obra_Local (SQLite)
top_val = format_class_card(
    "Cache_Obra_Local",
    ["+ id_obra: int", "+ snapshot_json: text", "+ fecha_descarga: datetime", "+ version_schema: int"],
    ["+ guardar_snapshot()", "+ leer_snapshot()"]
)
cls_drawio.append(f'        <mxCell id="cell_top" value="{html.escape(top_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_drawio.append('          <mxGeometry x="590" y="30" width="210" height="150" as="geometry" />')
cls_drawio.append('        </mxCell>')

# 5. Right Entity: T_Sincronizacion_Log (PostgreSQL Backend)
right_val = format_class_card(
    "T_Sincronizacion_Log",
    ["+ id_log: int", "+ id_empresa: int", "+ id_usuario: int", "+ total_recibidos: int", "+ total_procesados: int", "+ fecha_sync: timestamp"],
    ["+ registrar_lote_sync()", "+ consultar_historial_sync()"]
)
cls_drawio.append(f'        <mxCell id="cell_right" value="{html.escape(right_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_drawio.append('          <mxGeometry x="850" y="220" width="210" height="230" as="geometry" />')
cls_drawio.append('        </mxCell>')

# 6. Bottom Entity: Backend Sync Controller & Service
bot_val = format_class_card(
    "Sync_Backend_Service",
    ["+ api_router: sync_routes", "+ db_session: Session", "+ repo: sync_repos"],
    ["+ POST_procesar_lote_batch()", "+ GET_estado_sincronizacion()", "+ resolver_conflictos_obra()"]
)
cls_drawio.append(f'        <mxCell id="cell_bot" value="{html.escape(bot_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_drawio.append('          <mxGeometry x="590" y="500" width="210" height="160" as="geometry" />')
cls_drawio.append('        </mxCell>')

# Edges with multiplicity
cls_drawio.append('        <mxCell id="edge_f_c" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="cell_form" target="cell_control"><mxGeometry relative="1" as="geometry" /></mxCell>')
cls_drawio.append('        <mxCell id="edge_c_m" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="cell_control" target="cell_main"><mxGeometry relative="1" as="geometry" /></mxCell>')
cls_drawio.append('        <mxCell id="edge_m_t" value="1\n\n\n1..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;" edge="1" parent="1" source="cell_main" target="cell_top"><mxGeometry relative="1" as="geometry" /></mxCell>')
cls_drawio.append('        <mxCell id="edge_m_r" value="1                          1..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;" edge="1" parent="1" source="cell_main" target="cell_right"><mxGeometry relative="1" as="geometry" /></mxCell>')
cls_drawio.append('        <mxCell id="edge_m_b" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="cell_main" target="cell_bot"><mxGeometry relative="1" as="geometry" /></mxCell>')

cls_drawio.append('      </root>')
cls_drawio.append('    </mxGraphModel>')
cls_drawio.append('  </diagram>')
cls_drawio.append('</mxfile>')

cls_drawio_path = 'docs/diagramas/analisis_clases_cu41_offline_sync.drawio'
with open(cls_drawio_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(cls_drawio))

shutil.copyfile(cls_drawio_path, os.path.join(brain_diag_dir, 'analisis_clases_cu41_offline_sync.drawio'))
print("Generated Draw.io Class Analysis diagram for CU41!")
