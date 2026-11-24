import os
import shutil
import resvg_py

brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'

# ==============================================================================
# 1. RENDER CLASS ANALYSIS BCE TO SVG & PNG
# ==============================================================================
w = 1200
h = 750

svg_cls = []
svg_cls.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
svg_cls.append(f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>')

# Title
svg_cls.append('<text x="40" y="40" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="bold" fill="#000000">Diagrama de Análisis de Clases (BCE Puro) — CU41: Operación Offline y Sincronización</text>')
svg_cls.append('<text x="40" y="60" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#555555">Solo Form (Boundary) — Control — Entidades de Dominio (Avance_Obra, Incidencia, Obra, Cola)</text>')

def draw_cls(x, y, bw, bh, title, attrs, methods):
    s = []
    s.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
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
svg_cls.append('<line x1="250" y1="420" x2="310" y2="420" stroke="#000000" stroke-width="1.2"/>')
svg_cls.append('<line x1="530" y1="420" x2="590" y2="420" stroke="#000000" stroke-width="1.2"/>')
svg_cls.append('<line x1="700" y1="230" x2="700" y2="300" stroke="#000000" stroke-width="1.2"/>')
svg_cls.append('<text x="710" y="250" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1</text>')
svg_cls.append('<text x="710" y="290" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1..*</text>')

svg_cls.append('<line x1="810" y1="380" x2="880" y2="310" stroke="#000000" stroke-width="1.2"/>')
svg_cls.append('<text x="815" y="370" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1</text>')
svg_cls.append('<text x="865" y="325" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">0..*</text>')

svg_cls.append('<line x1="810" y1="480" x2="880" y2="550" stroke="#000000" stroke-width="1.2"/>')
svg_cls.append('<text x="815" y="495" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1</text>')
svg_cls.append('<text x="865" y="540" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">0..*</text>')

# Form
svg_cls.append(draw_cls(
    40, 290, 210, 275,
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

# Control
svg_cls.append(draw_cls(
    310, 305, 220, 245,
    "Control_Operacion_Offline",
    [
        "- red_activa: bool",
        "- reintentos: int"
    ],
    [
        "- consultar_datos_obra()",
        "- procesar_avance_offline()",
        "- procesar_incidencia_offline()",
        "- encolar_registro_pendiente()",
        "- sincronizar_pendientes()",
        "- consultar_estado_sync()"
    ]
))

# Cola
svg_cls.append(draw_cls(
    590, 300, 220, 255,
    "COLA_SINCRONIZACION",
    [
        "+ id_local: str (UUID)",
        "+ tipo_registro: str ('AVANCE'|'INC')",
        "+ payload_json: text",
        "+ estado: str ('PEND'|'SYNC')",
        "+ fecha_registro: datetime",
        "+ id_obra: int",
        "+ id_usuario: int"
    ],
    [
        "+ encolar_pendiente()",
        "+ obtener_pendientes()",
        "+ marcar_sincronizado()",
        "+ contar_por_estado()"
    ]
))

# Obra
svg_cls.append(draw_cls(
    590, 85, 220, 145,
    "OBRA",
    [
        "+ id_obra: int",
        "+ nombre_obra: text",
        "+ id_empresa: int",
        "+ estado: text",
        "+ fecha_inicio: date"
    ],
    [
        "+ consultar_obra()",
        "+ obtener_snapshot_cache()"
    ]
))

# Avance_Obra
svg_cls.append(draw_cls(
    880, 200, 230, 225,
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
        "+ registrar_avance()",
        "+ consultar_historial_avances()",
        "+ validar_porcentaje()"
    ]
))

# Incidencia
svg_cls.append(draw_cls(
    880, 450, 230, 235,
    "INCIDENCIA",
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
        "+ registrar_incidencia()",
        "+ consultar_incidencias()",
        "+ cambiar_estado()"
    ]
))

svg_cls.append('</svg>')
svg_cls_str = "\n".join(svg_cls)
with open('docs/diagramas/analisis_clases_cu41_bce.svg', 'w', encoding='utf-8') as f:
    f.write(svg_cls_str)

png_cls_bytes = resvg_py.svg_to_bytes(svg_cls_str)
with open('docs/diagramas/analisis_clases_cu41_bce.png', 'wb') as f:
    f.write(png_cls_bytes)

shutil.copyfile('docs/diagramas/analisis_clases_cu41_bce.svg', os.path.join(brain_diag_dir, 'analisis_clases_cu41_bce.svg'))
shutil.copyfile('docs/diagramas/analisis_clases_cu41_bce.png', os.path.join(brain_diag_dir, 'analisis_clases_cu41_bce.png'))
print("Rendered Class Analysis BCE to SVG & PNG!")

# ==============================================================================
# 2. RENDER SEQUENCE BCE TO SVG & PNG
# ==============================================================================
w_seq = 1350
h_seq = 1120

svg_seq = []
svg_seq.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_seq}" height="{h_seq}" viewBox="0 0 {w_seq} {h_seq}">')
svg_seq.append('''<defs>
  <marker id="seq-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
  </marker>
  <marker id="seq-ret" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 0 1.5 L 8 5 L 0 8.5" fill="none" stroke="#000000" stroke-width="1.3"/>
  </marker>
</defs>''')
svg_seq.append(f'<rect width="{w_seq}" height="{h_seq}" fill="#FFFFFF"/>')

# Title
svg_seq.append('<text x="30" y="35" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="bold" fill="#000000">sd CU41 - Operacion Offline y Sincronizacion (Analisis BCE Puro)</text>')

# Outer Frame
svg_seq.append(f'<rect x="20" y="15" width="{w_seq-40}" height="{h_seq-30}" fill="none" stroke="#000000" stroke-width="1.3"/>')

# Lifelines columns:
# Actor: 70
# UI: 230
# Control: 420
# Obra: 630
# Avance: 810
# Incidencia: 990
# Cola: 1180
ll_cols = [
    (70, "user : PersonalCampo", True),
    (230, "ui : IU_operacion_offline", False),
    (420, "control : Control_Operacion_Offline", False),
    (630, "obra : Obra", False),
    (810, "avance : Avance_Obra", False),
    (990, "incidencia : Incidencia", False),
    (1180, "cola : Cola_Sincronizacion", False)
]

for cx, name, is_act in ll_cols:
    if is_act:
        svg_seq.append(f'<circle cx="{cx}" cy="60" r="7" fill="#FFFFFF" stroke="#000000" stroke-width="1.2"/>')
        svg_seq.append(f'<line x1="{cx}" y1="67" x2="{cx}" y2="80" stroke="#000000" stroke-width="1.2"/>')
        svg_seq.append(f'<line x1="{cx-10}" y1="72" x2="{cx+10}" y2="72" stroke="#000000" stroke-width="1.2"/>')
        svg_seq.append(f'<line x1="{cx}" y1="80" x2="{cx-8}" y2="95" stroke="#000000" stroke-width="1.2"/>')
        svg_seq.append(f'<line x1="{cx}" y1="80" x2="{cx+8}" y2="95" stroke="#000000" stroke-width="1.2"/>')
        svg_seq.append(f'<text x="{cx}" y="110" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">{name}</text>')
        svg_seq.append(f'<line x1="{cx}" y1="115" x2="{cx}" y2="{h_seq-40}" stroke="#000000" stroke-width="1" stroke-dasharray="4 4"/>')
    else:
        bw = 140 if len(name) < 22 else 170
        svg_seq.append(f'<rect x="{cx-bw/2}" y="55" width="{bw}" height="32" rx="4" fill="#FFFFFF" stroke="#000000" stroke-width="1.2"/>')
        svg_seq.append(f'<text x="{cx}" y="75" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#000000">{name}</text>')
        svg_seq.append(f'<line x1="{cx}" y1="87" x2="{cx}" y2="{h_seq-40}" stroke="#000000" stroke-width="1" stroke-dasharray="4 4"/>')

# Helper for SVG message line
def draw_svg_msg(x1, x2, y, txt, is_ret=False):
    marker = "url(#seq-ret)" if is_ret else "url(#seq-arr)"
    dash = 'stroke-dasharray="4 4"' if is_ret else ''
    s = []
    s.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="#000000" stroke-width="1.2" {dash} marker-end="{marker}"/>')
    tx = (x1 + x2) / 2
    s.append(f'<text x="{tx}" y="{y-5}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">{txt}</text>')
    return "".join(s)

# Helper for SVG alt/opt/loop frame
def draw_svg_frame(x, y, w, h, label):
    s = []
    s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#444444" stroke-width="1" stroke-dasharray="3 3"/>')
    tw = max(110, len(label)*6.5 + 15)
    s.append(f'<rect x="{x}" y="{y}" width="{tw}" height="18" fill="#F0F0F0" stroke="#444444" stroke-width="1"/>')
    s.append(f'<text x="{x+8}" y="{y+13}" font-family="Arial, Helvetica, sans-serif" font-size="9" font-style="italic" fill="#222222">{label}</text>')
    return "".join(s)

# Section 1: HU90 - Consultar obra sin conexión
svg_seq.append(draw_svg_msg(70, 230, 140, "1: consultarInfoObra(id_obra)"))
# Alt starts at UI (x=160) towards entities
svg_seq.append(draw_svg_frame(160, 155, 540, 145, "alt [HU90 - Consultar Obra sin Conexión]"))
svg_seq.append(draw_svg_msg(230, 420, 185, "2: solicitarDatosObra(id_obra)"))
svg_seq.append(draw_svg_msg(420, 630, 215, "3: consultarDatosObra(id_obra)"))
svg_seq.append(draw_svg_msg(630, 420, 245, "4: return datos_obra", is_ret=True))
svg_seq.append(draw_svg_msg(420, 230, 270, "5: return datos_obra", is_ret=True))
svg_seq.append(draw_svg_msg(230, 70, 290, "6: mostrarInformacionObra(datos)", is_ret=True))

# Section 2: HU91 - Registrar Avance sin Conexión
svg_seq.append(draw_svg_msg(70, 230, 325, "7: registrarAvance(id_actividad, porcentaje)"))
svg_seq.append(draw_svg_frame(160, 340, 1100, 180, "alt [HU91 - Registrar Avance sin Conexión]"))
svg_seq.append(draw_svg_msg(230, 420, 370, "8: procesarRegistroAvance(datos)"))
svg_seq.append(draw_svg_msg(420, 810, 400, "9: crearAvance(datos)"))
svg_seq.append(draw_svg_msg(810, 420, 430, "10: return id_avance", is_ret=True))
svg_seq.append(draw_svg_msg(420, 1180, 455, "11: encolarPendiente('AVANCE', datos)"))
svg_seq.append(draw_svg_msg(1180, 420, 480, "12: return ok", is_ret=True))
svg_seq.append(draw_svg_msg(230, 70, 505, "13: mostrarConfirmacion('Guardado localmente')", is_ret=True))

# Section 3: HU92 - Registrar Incidencia sin Conexión
svg_seq.append(draw_svg_msg(70, 230, 540, "14: registrarIncidencia(titulo, desc, prioridad)"))
svg_seq.append(draw_svg_frame(160, 555, 1100, 180, "alt [HU92 - Registrar Incidencia sin Conexión]"))
svg_seq.append(draw_svg_msg(230, 420, 585, "15: procesarRegistroIncidencia(datos)"))
svg_seq.append(draw_svg_msg(420, 990, 615, "16: crearIncidencia(datos)"))
svg_seq.append(draw_svg_msg(990, 420, 645, "17: return id_incidencia", is_ret=True))
svg_seq.append(draw_svg_msg(420, 1180, 670, "18: encolarPendiente('INCIDENCIA', datos)"))
svg_seq.append(draw_svg_msg(1180, 420, 695, "19: return ok", is_ret=True))
svg_seq.append(draw_svg_msg(230, 70, 720, "20: mostrarConfirmacion('Guardado localmente')", is_ret=True))

# Section 4: HU93 - Sincronizar Automáticamente Datos Pendientes
svg_seq.append(draw_svg_msg(70, 230, 755, "21: conectarRed() [Evento]"))
# Opt starts at UI towards entities
svg_seq.append(draw_svg_frame(160, 770, 1100, 215, "opt [HU93 - Conexión Restablecida y Sincronización Automática]"))
svg_seq.append(draw_svg_msg(230, 420, 800, "22: ejecutarSincronizacion()"))
svg_seq.append(draw_svg_msg(420, 1180, 825, "23: obtenerPendientes()"))
svg_seq.append(draw_svg_msg(1180, 420, 850, "24: return lista_pendientes[]", is_ret=True))
# Loop starts at CONTROLLER towards entities
svg_seq.append(draw_svg_frame(350, 865, 910, 85, "loop [Por cada registro pendiente]"))
svg_seq.append(draw_svg_msg(420, 810, 895, "25: consolidarRegistro(item)"))
svg_seq.append(draw_svg_msg(420, 1180, 925, "26: marcarSincronizado(id_item)"))
svg_seq.append(draw_svg_msg(420, 230, 960, "27: notificarSincronizacionCompleta()", is_ret=True))
svg_seq.append(draw_svg_msg(230, 70, 978, "28: actualizarEstado('Sincronizado')", is_ret=True))

# Section 5: HU94 - Consultar Estado de Sincronización
svg_seq.append(draw_svg_msg(70, 230, 1005, "29: consultarEstadoSync()"))
# Opt starts at UI towards entities
svg_seq.append(draw_svg_frame(160, 1018, 1100, 75, "opt [HU94 - Consultar Estado de Sincronización]"))
svg_seq.append(draw_svg_msg(230, 420, 1040, "30: consultarEstado()"))
svg_seq.append(draw_svg_msg(420, 1180, 1060, "31: contarPorEstado()"))
svg_seq.append(draw_svg_msg(1180, 230, 1078, "32: return resumen_sync", is_ret=True))

svg_seq.append('</svg>')
svg_seq_str = "\n".join(svg_seq)
with open('docs/diagramas/secuencia_cu41_bce.svg', 'w', encoding='utf-8') as f:
    f.write(svg_seq_str)

png_seq_bytes = resvg_py.svg_to_bytes(svg_seq_str)
with open('docs/diagramas/secuencia_cu41_bce.png', 'wb') as f:
    f.write(png_seq_bytes)

shutil.copyfile('docs/diagramas/secuencia_cu41_bce.svg', os.path.join(brain_diag_dir, 'secuencia_cu41_bce.svg'))
shutil.copyfile('docs/diagramas/secuencia_cu41_bce.png', os.path.join(brain_diag_dir, 'secuencia_cu41_bce.png'))
print("Rendered Sequence BCE to SVG & PNG!")
