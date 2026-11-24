import os
import shutil
import resvg_py

brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'

# Dimensions
w = 1380
h = 920

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
svg.append(f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>')

# Title
svg.append('<text x="40" y="45" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="bold" fill="#000000">Diagrama de Análisis de Clases (BCE) — CU41: Gestionar Operación Offline y Sincronización</text>')
svg.append('<text x="40" y="65" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#555555">Mapeo Completo con t_avance_obra, t_incidencia, t_obra y cola_sincronizacion (HU90 - HU94)</text>')

# Helper to draw a class box in SVG
def draw_class_svg(x, y, bw, bh, title, attrs, methods):
    s = []
    # Outer rect
    s.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    # Title
    s.append(f'<text x="{x + bw/2}" y="{y + 20}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="11.5" font-weight="bold" fill="#000000">{title}</text>')
    
    curr_y = y + 28
    if attrs:
        s.append(f'<line x1="{x}" y1="{curr_y}" x2="{x+bw}" y2="{curr_y}" stroke="#000000" stroke-width="1"/>')
        curr_y += 15
        for a in attrs:
            s.append(f'<text x="{x + 10}" y="{curr_y}" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">{a}</text>')
            curr_y += 16
        curr_y += 2

    if methods:
        s.append(f'<line x1="{x}" y1="{curr_y}" x2="{x+bw}" y2="{curr_y}" stroke="#000000" stroke-width="1"/>')
        curr_y += 15
        for m in methods:
            s.append(f'<text x="{x + 10}" y="{curr_y}" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">{m}</text>')
            curr_y += 16

    return "".join(s)

# Connectors
# 1. Form -> Control
svg.append('<line x1="260" y1="450" x2="330" y2="450" stroke="#000000" stroke-width="1.2"/>')
# 2. Control -> Cola
svg.append('<line x1="560" y1="450" x2="640" y2="450" stroke="#000000" stroke-width="1.2"/>')
# 3. Obra -> Cola
svg.append('<line x1="755" y1="240" x2="755" y2="330" stroke="#000000" stroke-width="1.2"/>')
svg.append('<text x="765" y="260" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1</text>')
svg.append('<text x="765" y="320" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1..*</text>')
# 4. Cola -> Avance_Obra
svg.append('<line x1="870" y1="400" x2="960" y2="330" stroke="#000000" stroke-width="1.2"/>')
svg.append('<text x="880" y="390" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1</text>')
svg.append('<text x="945" y="345" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">0..*</text>')
# 5. Cola -> Incidencia
svg.append('<line x1="870" y1="500" x2="960" y2="570" stroke="#000000" stroke-width="1.2"/>')
svg.append('<text x="880" y="515" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1</text>')
svg.append('<text x="945" y="560" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">0..*</text>')
# 6. Cola -> Sincronizacion_Log
svg.append('<line x1="755" y1="600" x2="755" y2="670" stroke="#000000" stroke-width="1.2"/>')
svg.append('<text x="765" y="620" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1</text>')
svg.append('<text x="765" y="660" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1</text>')
# 7. Obra -> Avance_Obra
svg.append('<line x1="870" y1="165" x2="1075" y2="165" stroke="#000000" stroke-width="1.2"/>')
svg.append('<line x1="1075" y1="165" x2="1075" y2="230" stroke="#000000" stroke-width="1.2"/>')
svg.append('<text x="880" y="155" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1</text>')
svg.append('<text x="1085" y="220" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1..*</text>')

# Draw Class Boxes
# 1. Form_Operacion_Offline
svg.append(draw_class_svg(
    40, 330, 220, 275,
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
))

# 2. Sync_Manager_Control
svg.append(draw_class_svg(
    330, 330, 230, 275,
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
        "- obtener_pendientes_sync()",
        "- despachar_lote_sync_api()",
        "- procesar_lote_batch_db()",
        "- actualizar_estado_sync_db()",
        "- registrar_log_sincronizacion()"
    ]
))

# 3. COLA_SINCRONIZACION
svg.append(draw_class_svg(
    640, 330, 230, 270,
    "COLA_SINCRONIZACION",
    [
        "+ id_local: str (UUID)",
        "+ tipo_registro: str ('AVANCE'|'INC')",
        "+ payload_json: text",
        "+ estado: str ('PEND'|'SYNC')",
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
))

# 4. OBRA (t_obra)
svg.append(draw_class_svg(
    640, 95, 230, 145,
    "OBRA (t_obra)",
    [
        "+ id_obra: int",
        "+ nombre_obra: text",
        "+ id_empresa: int",
        "+ estado: text",
        "+ fecha_inicio: date"
    ],
    [
        "+ consultar_obra_db()",
        "+ generar_snapshot_cache()"
    ]
))

# 5. AVANCE_OBRA (t_avance_obra)
svg.append(draw_class_svg(
    960, 230, 240, 230,
    "AVANCE_OBRA (t_avance_obra)",
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
))

# 6. INCIDENCIA (t_incidencia)
svg.append(draw_class_svg(
    960, 480, 240, 240,
    "INCIDENCIA (t_incidencia)",
    [
        "+ id_incidencia: int",
        "+ id_obra: int",
        "+ id_unidad: int",
        "+ id_usuario_registro: int",
        "+ titulo: text",
        "+ descripcion: text",
        "+ prioridad: text",
        "+ estado: text ('ABIERTA'|'RESUELTA')",
        "+ created_at: timestamptz"
    ],
    [
        "+ registrar_incidencia_db()",
        "+ consultar_incidencias_obra()",
        "+ cambiar_estado_incidencia()"
    ]
))

# 7. SINCRONIZACION_LOG (t_sincronizacion_log)
svg.append(draw_class_svg(
    640, 670, 230, 200,
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
))

svg.append('</svg>')

svg_str = "\n".join(svg)
svg_path = 'docs/diagramas/analisis_clases_cu41_offline_sync.svg'
with open(svg_path, 'w', encoding='utf-8') as f:
    f.write(svg_str)

png_path = 'docs/diagramas/analisis_clases_cu41_offline_sync.png'
png_bytes = resvg_py.svg_to_bytes(svg_str)
with open(png_path, 'wb') as f:
    f.write(png_bytes)

shutil.copyfile(svg_path, os.path.join(brain_diag_dir, 'analisis_clases_cu41_offline_sync.svg'))
shutil.copyfile(png_path, os.path.join(brain_diag_dir, 'analisis_clases_cu41_offline_sync.png'))
print(f"Generated SVG and PNG for Class Analysis diagram! ({len(png_bytes)} bytes)")
