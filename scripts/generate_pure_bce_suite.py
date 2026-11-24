import os
import shutil
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)
brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'
os.makedirs(brain_diag_dir, exist_ok=True)

# ==============================================================================
# 1. DIAGRAMA DE COMUNICACIÓN (ANÁLISIS BCE PURO)
#    Regla: Usuario -> UI -> Controller -> Entities. Ninguna otra relación.
# ==============================================================================
w_com = 1350
h_com = 520

svg_com = []
svg_com.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_com}" height="{h_com}" viewBox="0 0 {w_com} {h_com}">')
svg_com.append('''<defs>
  <marker id="arr-fwd" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
  </marker>
  <marker id="arr-back" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 8 1.5 L 0 5 L 8 8.5 z" fill="#000000"/>
  </marker>
</defs>''')
svg_com.append(f'<rect width="{w_com}" height="{h_com}" fill="#FFFFFF"/>')

# Title
svg_com.append('<text x="40" y="40" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="bold" fill="#000000">Diagrama de Comunicación (Análisis BCE Puro) — CU41: Gestionar Operación Offline y Sincronización</text>')
svg_com.append('<text x="40" y="60" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#555555">Flujo Estricto: Usuario → UI → Controller → Entidades (HU90 a HU94)</text>')

# Coordinates
# Actor: x=70, y=260
# IU_operacion_offline (Boundary): x=280, y=260, r=40
# Control_Operacion_Offline (Control): x=580, y=260, r=40
# Entities branching from Controller:
# Obra: x=980, y=100, r=40
# Avance_Obra: x=980, y=210, r=40
# Incidencia: x=980, y=320, r=40
# Cola_Sincronizacion: x=980, y=430, r=40

cy = 260
r = 40

# Helper to draw Boundary: ┫◯
def draw_boundary_svg(cx, cy, label1, label2=""):
    s = []
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    s.append(f'<line x1="{cx-r}" y1="{cy-24}" x2="{cx-r}" y2="{cy+24}" stroke="#000000" stroke-width="1.4"/>')
    s.append(f'<line x1="{cx-r-12}" y1="{cy-24}" x2="{cx-r-12}" y2="{cy+24}" stroke="#000000" stroke-width="1.4"/>')
    s.append(f'<line x1="{cx-r-12}" y1="{cy}" x2="{cx-r}" y2="{cy}" stroke="#000000" stroke-width="1.4"/>')
    s.append(f'<text x="{cx}" y="{cy-3 if label2 else cy+4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#000000">{label1}</text>')
    if label2:
        s.append(f'<text x="{cx}" y="{cy+12}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">{label2}</text>')
    return "".join(s)

# Helper to draw Control: ↻◯
def draw_control_svg(cx, cy, label1, label2=""):
    s = []
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    s.append(f'<path d="M {cx-14} {cy-r+2} A 16 16 0 0 1 {cx+12} {cy-r-3}" fill="none" stroke="#000000" stroke-width="1.3"/>')
    s.append(f'<polygon points="{cx+12},{cy-r-8} {cx+19},{cy-r-2} {cx+11},{cy-r+3}" fill="#000000"/>')
    s.append(f'<text x="{cx}" y="{cy-3 if label2 else cy+4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#000000">{label1}</text>')
    if label2:
        s.append(f'<text x="{cx}" y="{cy+12}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">{label2}</text>')
    return "".join(s)

# Helper to draw Entity: ◯_
def draw_entity_svg(cx, cy, label1, label2=""):
    s = []
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    s.append(f'<line x1="{cx-r+8}" y1="{cy+r}" x2="{cx+r-8}" y2="{cy+r}" stroke="#000000" stroke-width="1.4"/>')
    s.append(f'<text x="{cx}" y="{cy-3 if label2 else cy+4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#000000">{label1}</text>')
    if label2:
        s.append(f'<text x="{cx}" y="{cy+12}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">{label2}</text>')
    return "".join(s)

# Connecting lines: ONLY Usuario -> UI -> Controller -> Entities
# Line 1: Usuario to UI
svg_com.append(f'<line x1="75" y1="{cy}" x2="{280-r-12}" y2="{cy}" stroke="#000000" stroke-width="1.3"/>')

# Line 2: UI to Controller
svg_com.append(f'<line x1="{280+r}" y1="{cy}" x2="{580-r}" y2="{cy}" stroke="#000000" stroke-width="1.3" marker-end="url(#arr-fwd)"/>')

# Line 3: Controller to Obra (Branch 1 - Up)
svg_com.append(f'<line x1="{580+r*0.7}" y1="{cy-r*0.7}" x2="{980-r*0.7}" y2="{100+r*0.7}" stroke="#000000" stroke-width="1.3" marker-end="url(#arr-fwd)"/>')

# Line 4: Controller to Avance_Obra (Branch 2)
svg_com.append(f'<line x1="{580+r*0.9}" y1="{cy-r*0.3}" x2="{980-r*0.9}" y2="{210+r*0.3}" stroke="#000000" stroke-width="1.3" marker-end="url(#arr-fwd)"/>')

# Line 5: Controller to Incidencia (Branch 3)
svg_com.append(f'<line x1="{580+r*0.9}" y1="{cy+r*0.3}" x2="{980-r*0.9}" y2="{320-r*0.3}" stroke="#000000" stroke-width="1.3" marker-end="url(#arr-fwd)"/>')

# Line 6: Controller to Cola_Sincronizacion (Branch 4 - Down)
svg_com.append(f'<line x1="{580+r*0.7}" y1="{cy+r*0.7}" x2="{980-r*0.7}" y2="{430-r*0.7}" stroke="#000000" stroke-width="1.3" marker-end="url(#arr-fwd)"/>')

# Messages
# Above line Usuario -> UI
svg_com.append(f'<text x="160" y="{cy-35}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">1: consultarObra() [HU90] →</text>')
svg_com.append(f'<text x="160" y="{cy-20}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">4: registrarAvance() [HU91] →</text>')
svg_com.append(f'<text x="160" y="{cy-5}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">7: registrarIncidencia() [HU92] →</text>')
svg_com.append(f'<text x="160" y="{cy+18}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">10: sincronizarDatos() [HU93] →</text>')
svg_com.append(f'<text x="160" y="{cy+33}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">13: consultarEstadoSync() [HU94] →</text>')

# Above line UI -> Controller
svg_com.append(f'<text x="430" y="{cy-28}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">2: solicitarDatosObra() →</text>')
svg_com.append(f'<text x="430" y="{cy-14}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">5: procesarRegistroAvance() →</text>')
svg_com.append(f'<text x="430" y="{cy}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">8: procesarRegistroIncidencia() →</text>')
svg_com.append(f'<text x="430" y="{cy+20}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">11: ejecutarSincronizacion() →</text>')
svg_com.append(f'<text x="430" y="{cy+35}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">14: consultarEstado() →</text>')

# Controller -> Obra
svg_com.append(f'<text x="770" y="145" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">3: consultarDatosObra() →</text>')

# Controller -> Avance_Obra
svg_com.append(f'<text x="770" y="215" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">6: crearAvance() [HU91] →</text>')

# Controller -> Incidencia
svg_com.append(f'<text x="770" y="305" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">9: crearIncidencia() [HU92] →</text>')

# Controller -> Cola_Sincronizacion
svg_com.append(f'<text x="770" y="380" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">6b/9b: encolarPendiente() →</text>')
svg_com.append(f'<text x="770" y="395" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">12: procesarPendientes() [HU93] →</text>')
svg_com.append(f'<text x="770" y="410" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">15: contarPorEstado() [HU94] →</text>')

# Nodes
# 1. Actor
act_x = 55
act_y = cy - 25
svg_com.append(f'<circle cx="{act_x}" cy="{act_y}" r="8" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
svg_com.append(f'<line x1="{act_x}" y1="{act_y+8}" x2="{act_x}" y2="{act_y+24}" stroke="#000000" stroke-width="1.3"/>')
svg_com.append(f'<line x1="{act_x-12}" y1="{act_y+14}" x2="{act_x+12}" y2="{act_y+14}" stroke="#000000" stroke-width="1.3"/>')
svg_com.append(f'<line x1="{act_x}" y1="{act_y+24}" x2="{act_x-10}" y2="{act_y+40}" stroke="#000000" stroke-width="1.3"/>')
svg_com.append(f'<line x1="{act_x}" y1="{act_y+24}" x2="{act_x+10}" y2="{act_y+40}" stroke="#000000" stroke-width="1.3"/>')
svg_com.append(f'<text x="{act_x}" y="{act_y+53}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" font-weight="bold" fill="#000000">Personal de</text>')
svg_com.append(f'<text x="{act_x}" y="{act_y+65}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" font-weight="bold" fill="#000000">Campo</text>')

# 2. Boundary
svg_com.append(draw_boundary_svg(280, cy, "IU_operacion", "offline"))

# 3. Controller
svg_com.append(draw_control_svg(580, cy, "Control_Operacion", "Offline"))

# 4. Entities
svg_com.append(draw_entity_svg(980, 100, "Obra", ""))
svg_com.append(draw_entity_svg(980, 210, "Avance_Obra", ""))
svg_com.append(draw_entity_svg(980, 320, "Incidencia", ""))
svg_com.append(draw_entity_svg(980, 430, "Cola_", "Sincronizacion"))

svg_com.append('</svg>')

svg_com_str = "\n".join(svg_com)
with open('docs/diagramas/comunicacion_cu41_bce.svg', 'w', encoding='utf-8') as f:
    f.write(svg_com_str)

png_com_bytes = resvg_py.svg_to_bytes(svg_com_str)
with open('docs/diagramas/comunicacion_cu41_bce.png', 'wb') as f:
    f.write(png_com_bytes)

shutil.copyfile('docs/diagramas/comunicacion_cu41_bce.svg', os.path.join(brain_diag_dir, 'comunicacion_cu41_bce.svg'))
shutil.copyfile('docs/diagramas/comunicacion_cu41_bce.png', os.path.join(brain_diag_dir, 'comunicacion_cu41_bce.png'))

# DRAW.IO XML for Communication Diagram (BCE Puro)
drawio_com = []
drawio_com.append('<?xml version="1.0" encoding="UTF-8"?>')
drawio_com.append('<mxfile host="app.diagrams.net" modified="2026-11-22T18:45:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
drawio_com.append('  <diagram id="cu41_comunicacion_bce_puro" name="CU41 - Comunicacion BCE Puro">')
drawio_com.append('    <mxGraphModel dx="1200" dy="700" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="600" background="#FFFFFF" math="0" shadow="0">')
drawio_com.append('      <root>')
drawio_com.append('        <mxCell id="0" />')
drawio_com.append('        <mxCell id="1" parent="0" />')

drawio_com.append('        <mxCell id="title" value="&lt;b&gt;Diagrama de Comunicación (Análisis BCE Puro) — CU41: Operación Offline y Sincronización&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;Solo Usuario — Boundary — Controller — Entidades (Sin servicios ni componentes de implementación)&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=12;fontColor=#000000;" vertex="1" parent="1">')
drawio_com.append('          <mxGeometry x="40" y="25" width="850" height="35" as="geometry" />')
drawio_com.append('        </mxCell>')

# Actor
drawio_com.append('        <mxCell id="actor_user" value="Personal de Campo" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontColor=#000000;" vertex="1" parent="1">')
drawio_com.append('          <mxGeometry x="50" y="230" width="30" height="60" as="geometry" />')
drawio_com.append('        </mxCell>')

# Boundary
drawio_com.append('        <mxCell id="b_iu" value="IU_operacion_&lt;br&gt;offline" style="shape=umlBoundary;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_com.append('          <mxGeometry x="240" y="225" width="85" height="70" as="geometry" />')
drawio_com.append('        </mxCell>')

# Controller
drawio_com.append('        <mxCell id="c_ctrl" value="Control_Operacion_&lt;br&gt;Offline" style="shape=umlControl;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_com.append('          <mxGeometry x="540" y="225" width="85" height="75" as="geometry" />')
drawio_com.append('        </mxCell>')

# Entities
drawio_com.append('        <mxCell id="e_obra" value="Obra" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_com.append('          <mxGeometry x="940" y="65" width="75" height="75" as="geometry" />')
drawio_com.append('        </mxCell>')

drawio_com.append('        <mxCell id="e_avance" value="Avance_Obra" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_com.append('          <mxGeometry x="940" y="175" width="75" height="75" as="geometry" />')
drawio_com.append('        </mxCell>')

drawio_com.append('        <mxCell id="e_incidencia" value="Incidencia" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_com.append('          <mxGeometry x="940" y="285" width="75" height="75" as="geometry" />')
drawio_com.append('        </mxCell>')

drawio_com.append('        <mxCell id="e_cola" value="Cola_&lt;br&gt;Sincronizacion" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_com.append('          <mxGeometry x="940" y="395" width="75" height="75" as="geometry" />')
drawio_com.append('        </mxCell>')

# Edges: ONLY Usuario -> UI -> Controller -> Entities
drawio_com.append('        <mxCell id="edge_user_iu" value="1: consultarObra() [HU90] →&lt;br&gt;4: registrarAvance() [HU91] →&lt;br&gt;7: registrarIncidencia() [HU92] →&lt;br&gt;10: sincronizarDatos() [HU93] →&lt;br&gt;13: consultarEstadoSync() [HU94] →" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="actor_user" target="b_iu">')
drawio_com.append('          <mxGeometry relative="1" as="geometry" />')
drawio_com.append('        </mxCell>')

drawio_com.append('        <mxCell id="edge_iu_ctrl" value="2: solicitarDatosObra() →&lt;br&gt;5: procesarRegistroAvance() →&lt;br&gt;8: procesarRegistroIncidencia() →&lt;br&gt;11: ejecutarSincronizacion() →&lt;br&gt;14: consultarEstado() →" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="b_iu" target="c_ctrl">')
drawio_com.append('          <mxGeometry relative="1" as="geometry" />')
drawio_com.append('        </mxCell>')

drawio_com.append('        <mxCell id="edge_ctrl_obra" value="3: consultarDatosObra() →" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_ctrl" target="e_obra">')
drawio_com.append('          <mxGeometry relative="1" as="geometry" />')
drawio_com.append('        </mxCell>')

drawio_com.append('        <mxCell id="edge_ctrl_avance" value="6: crearAvance() [HU91] →" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_ctrl" target="e_avance">')
drawio_com.append('          <mxGeometry relative="1" as="geometry" />')
drawio_com.append('        </mxCell>')

drawio_com.append('        <mxCell id="edge_ctrl_incidencia" value="9: crearIncidencia() [HU92] →" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_ctrl" target="e_incidencia">')
drawio_com.append('          <mxGeometry relative="1" as="geometry" />')
drawio_com.append('        </mxCell>')

drawio_com.append('        <mxCell id="edge_ctrl_cola" value="6b/9b: encolarPendiente() →&lt;br&gt;12: procesarPendientes() [HU93] →&lt;br&gt;15: contarPorEstado() [HU94] →" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_ctrl" target="e_cola">')
drawio_com.append('          <mxGeometry relative="1" as="geometry" />')
drawio_com.append('        </mxCell>')

drawio_com.append('      </root>')
drawio_com.append('    </mxGraphModel>')
drawio_com.append('  </diagram>')
drawio_com.append('</mxfile>')

with open('docs/diagramas/comunicacion_cu41_bce.drawio', 'w', encoding='utf-8') as f:
    f.write("\n".join(drawio_com))
shutil.copyfile('docs/diagramas/comunicacion_cu41_bce.drawio', os.path.join(brain_diag_dir, 'comunicacion_cu41_bce.drawio'))
print("Generated Pure BCE Communication Diagram!")


# ==============================================================================
# 2. DIAGRAMA DE SECUENCIA (ANÁLISIS BCE PURO)
#    Regla 1: Mismos participantes que comunicación: Usuario, UI, Controller, Entidades.
#    Regla 2: Alt y Opt inician en UI hacia las entidades (NO incluyen al usuario).
#    Regla 3: Loop inicia en Controller hacia las entidades (NO va desde usuario ni desde UI).
# ==============================================================================
seq_bce = []
seq_bce.append('<?xml version="1.0" encoding="UTF-8"?>')
seq_bce.append('<mxfile host="app.diagrams.net" modified="2026-11-22T18:45:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
seq_bce.append('  <diagram id="cu41_secuencia_bce_puro" name="CU41 - Secuencia BCE Puro">')
seq_bce.append('    <mxGraphModel dx="1400" dy="1100" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1350" pageHeight="1150" background="#FFFFFF" math="0" shadow="0">')
seq_bce.append('      <root>')
seq_bce.append('        <mxCell id="0" />')
seq_bce.append('        <mxCell id="1" parent="0" />')

# Frame outer
seq_bce.append('        <mxCell id="frame_sd" value="sd CU41 - Operacion Offline y Sincronizacion (Analisis BCE Puro)" style="shape=umlFrame;whiteSpace=wrap;html=1;width=390;height=22;fillColor=none;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=11;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
seq_bce.append('          <mxGeometry x="20" y="20" width="1280" height="1060" as="geometry" />')
seq_bce.append('        </mxCell>')

# Lifelines: Usuario, UI, Controller, Obra, Avance_Obra, Incidencia, Cola_Sincronizacion
# Positions:
# Actor: 70
# UI: 230
# Controller: 420
# Obra: 630
# Avance_Obra: 810
# Incidencia: 990
# Cola_Sincronizacion: 1180

seq_bce.append('        <mxCell id="ll_actor" value="user : PersonalCampo" style="shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=10;fontColor=#000000;" vertex="1" parent="1">')
seq_bce.append('          <mxGeometry x="50" y="60" width="40" height="1000" as="geometry" />')
seq_bce.append('        </mxCell>')

lifelines_bce = [
    ("ll_ui", "ui : IU_operacion_offline", 150, 160),
    ("ll_ctrl", "control : Control_Operacion_Offline", 330, 180),
    ("ll_obra", "obra : Obra", 555, 150),
    ("ll_avance", "avance : Avance_Obra", 735, 150),
    ("ll_inc", "incidencia : Incidencia", 915, 150),
    ("ll_cola", "cola : Cola_Sincronizacion", 1095, 170)
]

for lid, lname, lx, lw in lifelines_bce:
    seq_bce.append(f'        <mxCell id="{lid}" value="{html.escape(lname)}" style="shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=11;fontColor=#000000;rounded=1;" vertex="1" parent="1">')
    seq_bce.append(f'          <mxGeometry x="{lx}" y="60" width="{lw}" height="1000" as="geometry" />')
    seq_bce.append('        </mxCell>')

def add_msg_bce(mid, val, x1, x2, y, is_ret=False):
    style = f"endArrow={'open' if is_ret else 'classic'};html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9.5;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;"
    if is_ret:
        style += "dashed=1;"
    return f'''        <mxCell id="edge_{mid}" value="{html.escape(val)}" style="{style}" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="{x1}" y="{y}" as="sourcePoint" />
            <mxPoint x="{x2}" y="{y}" as="targetPoint" />
          </mxGeometry>
        </mxCell>'''

def add_frame_bce(fid, label, x, y, w, h):
    tag_w = min(w-20, max(140, len(label)*7 + 20))
    return f'''        <mxCell id="{fid}" value="{html.escape(label)}" style="shape=umlFrame;whiteSpace=wrap;html=1;width={int(tag_w)};height=20;fillColor=none;strokeColor=#333333;strokeWidth=1;strokeDasharray=3 3;fontFamily=Arial;fontSize=9.5;fontStyle=2;fontColor=#333333;" vertex="1" parent="1">
          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />
        </mxCell>'''

# Centers:
# Actor: 70
# UI: 230
# Control: 420
# Obra: 630
# Avance: 810
# Incidencia: 990
# Cola: 1180

# Section 1: HU90 - Consultar obra sin conexión
# Message from user to UI is outside alt (at y=140)
seq_bce.append(add_msg_bce("1", "1: consultarInfoObra(id_obra)", 70, 230, 140))
# Alt starts at UI (x=160) towards entities (w=550): covers UI to Obra
seq_bce.append(add_frame_bce("alt_hu90", "alt [HU90 - Consultar Obra sin Conexión]", 160, 155, 540, 140))
seq_bce.append(add_msg_bce("2", "2: solicitarDatosObra(id_obra)", 230, 420, 185))
seq_bce.append(add_msg_bce("3", "3: consultarDatosObra(id_obra)", 420, 630, 215))
seq_bce.append(add_msg_bce("4", "4: return datos_obra", 630, 420, 245, is_ret=True))
seq_bce.append(add_msg_bce("5", "5: return datos_obra", 420, 230, 270, is_ret=True))
seq_bce.append(add_msg_bce("6", "6: mostrarInformacionObra(datos)", 230, 70, 290, is_ret=True))

# Section 2: HU91 - Registrar Avance sin Conexión
seq_bce.append(add_msg_bce("7", "7: registrarAvance(id_actividad, porcentaje)", 70, 230, 320))
# Alt starts at UI (x=160) towards entities (w=1110): covers UI to Cola
seq_bce.append(add_frame_bce("alt_hu91", "alt [HU91 - Registrar Avance sin Conexión]", 160, 335, 1110, 175))
seq_bce.append(add_msg_bce("8", "8: procesarRegistroAvance(datos)", 230, 420, 365))
seq_bce.append(add_msg_bce("9", "9: crearAvance(datos)", 420, 810, 395))
seq_bce.append(add_msg_bce("10", "10: return id_avance", 810, 420, 425, is_ret=True))
seq_bce.append(add_msg_bce("11", "11: encolarPendiente('AVANCE', datos)", 420, 1180, 450))
seq_bce.append(add_msg_bce("12", "12: return ok", 1180, 420, 475, is_ret=True))
seq_bce.append(add_msg_bce("13", "13: mostrarConfirmacion('Guardado localmente')", 230, 70, 500, is_ret=True))

# Section 3: HU92 - Registrar Incidencia sin Conexión
seq_bce.append(add_msg_bce("14", "14: registrarIncidencia(titulo, desc, prioridad)", 70, 230, 530))
# Alt starts at UI (x=160) towards entities (w=1110)
seq_bce.append(add_frame_bce("alt_hu92", "alt [HU92 - Registrar Incidencia sin Conexión]", 160, 545, 1110, 175))
seq_bce.append(add_msg_bce("15", "15: procesarRegistroIncidencia(datos)", 230, 420, 575))
seq_bce.append(add_msg_bce("16", "16: crearIncidencia(datos)", 420, 990, 605))
seq_bce.append(add_msg_bce("17", "17: return id_incidencia", 990, 420, 635, is_ret=True))
seq_bce.append(add_msg_bce("18", "18: encolarPendiente('INCIDENCIA', datos)", 420, 1180, 660))
seq_bce.append(add_msg_bce("19", "19: return ok", 1180, 420, 685, is_ret=True))
seq_bce.append(add_msg_bce("20", "20: mostrarConfirmacion('Guardado localmente')", 230, 70, 710, is_ret=True))

# Section 4: HU93 - Sincronizar Automáticamente Datos Pendientes
# Event triggered in UI
seq_bce.append(add_msg_bce("21", "21: conectarRed() [Evento]", 70, 230, 740))
# Opt starts at UI (x=160) towards entities (w=1110)
seq_bce.append(add_frame_bce("opt_hu93", "opt [HU93 - Conexión Restablecida y Sincronización Automática]", 160, 755, 1110, 215))
seq_bce.append(add_msg_bce("22", "22: ejecutarSincronizacion()", 230, 420, 785))
seq_bce.append(add_msg_bce("23", "23: obtenerPendientes()", 420, 1180, 810))
seq_bce.append(add_msg_bce("24", "24: return lista_pendientes[]", 1180, 420, 835, is_ret=True))
# Loop starts at CONTROLLER (x=350) towards entities (w=920): DOES NOT start from user or UI!
seq_bce.append(add_frame_bce("loop_sync", "loop [Por cada registro pendiente]", 350, 850, 920, 85))
seq_bce.append(add_msg_bce("25", "25: consolidarRegistro(item)", 420, 810, 880))
seq_bce.append(add_msg_bce("26", "26: marcarSincronizado(id_item)", 420, 1180, 910))
seq_bce.append(add_msg_bce("27", "27: notificarSincronizacionCompleta()", 420, 230, 945, is_ret=True))
seq_bce.append(add_msg_bce("28", "28: actualizarEstado('Sincronizado')", 230, 70, 965, is_ret=True))

# Section 5: HU94 - Consultar Estado de Sincronización
seq_bce.append(add_msg_bce("29", "29: consultarEstadoSync()", 70, 230, 995))
# Opt starts at UI (x=160) towards entities (w=1110)
seq_bce.append(add_frame_bce("opt_hu94", "opt [HU94 - Consultar Estado de Sincronización]", 160, 1005, 1110, 65))
seq_bce.append(add_msg_bce("30", "30: consultarEstado()", 230, 420, 1025))
seq_bce.append(add_msg_bce("31", "31: contarPorEstado()", 420, 1180, 1045))
seq_bce.append(add_msg_bce("32", "32: return resumen_sync", 1180, 230, 1060, is_ret=True))

seq_bce.append('      </root>')
seq_bce.append('    </mxGraphModel>')
seq_bce.append('  </diagram>')
seq_bce.append('</mxfile>')

with open('docs/diagramas/secuencia_cu41_bce.drawio', 'w', encoding='utf-8') as f:
    f.write("\n".join(seq_bce))
shutil.copyfile('docs/diagramas/secuencia_cu41_bce.drawio', os.path.join(brain_diag_dir, 'secuencia_cu41_bce.drawio'))
print("Generated Pure BCE Sequence Diagram!")

# ==============================================================================
# 3. DIAGRAMA DE ANÁLISIS DE CLASES (ANÁLISIS BCE PURO)
#    Regla: Boundary (Form) -> Control -> Entities (Avance_Obra, Incidencia, Obra, Cola)
#    Sin clases de implementación (sin services, sin repos, sin router)
# ==============================================================================
def format_class_card_bce(title, attrs, methods):
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

cls_bce = []
cls_bce.append('<?xml version="1.0" encoding="UTF-8"?>')
cls_bce.append('<mxfile host="app.diagrams.net" modified="2026-11-22T18:45:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
cls_bce.append('  <diagram id="cu41_analisis_clases_bce_puro" name="CU41 - Analisis Clases BCE Puro">')
cls_bce.append('    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1350" pageHeight="900" background="#FFFFFF" math="0" shadow="0">')
cls_bce.append('      <root>')
cls_bce.append('        <mxCell id="0" />')
cls_bce.append('        <mxCell id="1" parent="0" />')

# Title
cls_bce.append('        <mxCell id="title" value="&lt;b&gt;Diagrama de Análisis de Clases (BCE Puro) — CU41: Gestionar Operación Offline y Sincronización&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;Estructura: Form (Boundary) — Control — Entidades de Dominio (Avance_Obra, Incidencia, Obra, Cola_Sincronizacion)&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=12;fontColor=#000000;" vertex="1" parent="1">')
cls_bce.append('          <mxGeometry x="40" y="20" width="950" height="40" as="geometry" />')
cls_bce.append('        </mxCell>')

# 1. Form_Operacion_Offline (Boundary)
form_val = format_class_card_bce(
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
cls_bce.append(f'        <mxCell id="cell_form" value="{html.escape(form_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_bce.append('          <mxGeometry x="40" y="270" width="230" height="280" as="geometry" />')
cls_bce.append('        </mxCell>')

# 2. Control_Operacion_Offline (Control)
ctrl_val = format_class_card_bce(
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
)
cls_bce.append(f'        <mxCell id="cell_ctrl" value="{html.escape(ctrl_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_bce.append('          <mxGeometry x="320" y="290" width="220" height="240" as="geometry" />')
cls_bce.append('        </mxCell>')

# 3. COLA_SINCRONIZACION (Main Entity)
cola_val = format_class_card_bce(
    "COLA_SINCRONIZACION",
    [
        "+ id_local: str (UUID)",
        "+ tipo_registro: str ('AVANCE'|'INC')",
        "+ payload_json: text",
        "+ estado: str ('PENDIENTE'|'SINCRONIZADO')",
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
)
cls_bce.append(f'        <mxCell id="cell_cola" value="{html.escape(cola_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_bce.append('          <mxGeometry x="590" y="280" width="230" height="260" as="geometry" />')
cls_bce.append('        </mxCell>')

# 4. OBRA (Top Entity)
obra_val = format_class_card_bce(
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
)
cls_bce.append(f'        <mxCell id="cell_obra" value="{html.escape(obra_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_bce.append('          <mxGeometry x="590" y="80" width="230" height="150" as="geometry" />')
cls_bce.append('        </mxCell>')

# 5. AVANCE_OBRA (Right-Top Entity) -> REQUERIDA
avance_val = format_class_card_bce(
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
)
cls_bce.append(f'        <mxCell id="cell_avance" value="{html.escape(avance_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_bce.append('          <mxGeometry x="880" y="180" width="230" height="230" as="geometry" />')
cls_bce.append('        </mxCell>')

# 6. INCIDENCIA (Right-Bottom Entity)
inc_val = format_class_card_bce(
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
)
cls_bce.append(f'        <mxCell id="cell_inc" value="{html.escape(inc_val)}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
cls_bce.append('          <mxGeometry x="880" y="440" width="230" height="240" as="geometry" />')
cls_bce.append('        </mxCell>')

# Relationships: Form - Control - Entity (Strict BCE)
cls_bce.append('        <mxCell id="edge_f_c" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="cell_form" target="cell_ctrl"><mxGeometry relative="1" as="geometry" /></mxCell>')
cls_bce.append('        <mxCell id="edge_c_m" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="cell_ctrl" target="cell_cola"><mxGeometry relative="1" as="geometry" /></mxCell>')
cls_bce.append('        <mxCell id="edge_m_t" value="1&#xa;&#xa;&#xa;1..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;" edge="1" parent="1" source="cell_cola" target="cell_obra"><mxGeometry relative="1" as="geometry" /></mxCell>')
cls_bce.append('        <mxCell id="edge_m_av" value="1                  0..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;" edge="1" parent="1" source="cell_cola" target="cell_avance"><mxGeometry relative="1" as="geometry" /></mxCell>')
cls_bce.append('        <mxCell id="edge_m_in" value="1                  0..*" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;" edge="1" parent="1" source="cell_cola" target="cell_inc"><mxGeometry relative="1" as="geometry" /></mxCell>')

cls_bce.append('      </root>')
cls_bce.append('    </mxGraphModel>')
cls_bce.append('  </diagram>')
cls_bce.append('</mxfile>')

with open('docs/diagramas/analisis_clases_cu41_bce.drawio', 'w', encoding='utf-8') as f:
    f.write("\n".join(cls_bce))
shutil.copyfile('docs/diagramas/analisis_clases_cu41_bce.drawio', os.path.join(brain_diag_dir, 'analisis_clases_cu41_bce.drawio'))
print("Generated Pure BCE Class Analysis Diagram!")
