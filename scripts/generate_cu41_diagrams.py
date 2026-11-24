import os
import shutil
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)
brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'
os.makedirs(brain_diag_dir, exist_ok=True)

# ==============================================================================
# 1. GENERATE COMMUNICATION / ROBUSTNESS DIAGRAM (SVG & PNG)
# ==============================================================================
svg_w = 1750
svg_h = 560

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">')

# Definitions: Markers
svg.append('''<defs>
  <marker id="arr-fwd" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
  </marker>
  <marker id="arr-back" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 8 1.5 L 0 5 L 8 8.5 z" fill="#000000"/>
  </marker>
  <marker id="arr-down" viewBox="0 0 10 10" refX="5" refY="8" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 1.5 0 L 5 8 L 8.5 0 z" fill="#000000"/>
  </marker>
  <marker id="arr-up" viewBox="0 0 10 10" refX="5" refY="2" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 1.5 8 L 5 0 L 8.5 8 z" fill="#000000"/>
  </marker>
</defs>''')

# White background
svg.append(f'<rect width="{svg_w}" height="{svg_h}" fill="#FFFFFF"/>')

# Title
svg.append('<text x="50" y="45" font-family="Arial, Helvetica, sans-serif" font-size="14" font-weight="bold" fill="#000000">Diagrama de Comunicación: Gestionar Operación Offline y Sincronización (CU41 - HU90 a HU94)</text>')
svg.append('<text x="50" y="65" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#444444">Arquitectura Robusta BCE: Cliente Móvil Flutter (SQLite Offline) ⟷ Backend FastAPI (PostgreSQL Obras Central)</text>')

# Node Coordinates (Horizontal Centerline cy = 200)
cy = 200
r = 38

# Positions:
# Actor: x=75, y=cy
# IU_operacion_offline (Boundary): x=240, y=cy
# sync_manager (Control Móvil): x=460, y=cy
# local_sqlite_db (Entity Móvil): x=460, y=420
# t_cache_obra_local (Entity Móvil Sub): x=290, y=420
# t_cola_sync_local (Entity Móvil Sub): x=630, y=420
# sync_routes (Control Backend): x=780, y=cy
# sync_services (Control Backend): x=1030, y=cy
# sync_repos (Control Backend): x=1270, y=cy
# database obras (Entity Backend): x=1500, y=cy
# Branching Backend Entities:
# t_avance_obra: x=1670, y=110
# t_incidencia: x=1670, y=200
# t_sincronizacion_log: x=1670, y=290

# Zona background boxes (dashed subtle boundaries)
svg.append(f'<rect x="160" y="90" width="530" height="420" rx="10" fill="none" stroke="#666666" stroke-width="1" stroke-dasharray="4 4"/>')
svg.append(f'<text x="180" y="115" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#333333">ZONA CLIENTE MÓVIL (FLUTTER / SQLITE)</text>')

svg.append(f'<rect x="710" y="90" width="1010" height="420" rx="10" fill="none" stroke="#666666" stroke-width="1" stroke-dasharray="4 4"/>')
svg.append(f'<text x="730" y="115" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#333333">ZONA SERVIDOR CENTRAL (FASTAPI / POSTGRESQL)</text>')

# Connecting lines
# Actor to IU
svg.append(f'<line x1="75" y1="{cy}" x2="{240-r-12}" y2="{cy}" stroke="#000000" stroke-width="1.2"/>')

# IU to sync_manager
svg.append(f'<line x1="{240+r}" y1="{cy}" x2="{460-r}" y2="{cy}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')

# sync_manager to local_sqlite_db (vertical)
svg.append(f'<line x1="460" y1="{cy+r}" x2="460" y2="{420-r}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-down)"/>')

# local_sqlite_db to local entities
svg.append(f'<line x1="{460-r}" y1="420" x2="{290+r}" y2="420" stroke="#000000" stroke-width="1.2"/>')
svg.append(f'<line x1="{460+r}" y1="420" x2="{630-r}" y2="420" stroke="#000000" stroke-width="1.2"/>')

# sync_manager to sync_routes (Network jump HTTPS)
svg.append(f'<line x1="{460+r}" y1="{cy}" x2="{780-r}" y2="{cy}" stroke="#000000" stroke-width="1.5" stroke-dasharray="5 3" marker-end="url(#arr-fwd)"/>')

# sync_routes to sync_services
svg.append(f'<line x1="{780+r}" y1="{cy}" x2="{1030-r}" y2="{cy}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')

# sync_services to sync_repos
svg.append(f'<line x1="{1030+r}" y1="{cy}" x2="{1270-r}" y2="{cy}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')

# sync_repos to database obras
svg.append(f'<line x1="{1270+r}" y1="{cy}" x2="{1500-r}" y2="{cy}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')

# Database obras to central entities
svg.append(f'<line x1="{1500+r*0.7}" y1="{cy-r*0.7}" x2="{1670-r*0.7}" y2="{110+r*0.7}" stroke="#000000" stroke-width="1.2"/>')
svg.append(f'<line x1="{1500+r}" y1="{cy}" x2="{1670-r}" y2="{200}" stroke="#000000" stroke-width="1.2"/>')
svg.append(f'<line x1="{1500+r*0.7}" y1="{cy+r*0.7}" x2="{1670-r*0.7}" y2="{290-r*0.7}" stroke="#000000" stroke-width="1.2"/>')

# ================= MESSAGES =================

# 1. Actor -> IU
svg.append(f'<text x="145" y="{cy-30}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">1. consultarInfoObra() [HU90] →</text>')
svg.append(f'<text x="145" y="{cy-16}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">5. registrarAvance/Incidencia() [HU91/92] →</text>')
svg.append(f'<text x="145" y="{cy-2}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">8. consultarEstadoSync() [HU94] →</text>')
svg.append(f'<text x="145" y="{cy+22}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">← 9. mostrarEstadoLocal()</text>')
svg.append(f'<text x="145" y="{cy+36}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">← 18. notificarSincronizacion()</text>')

# 2. IU -> sync_manager
svg.append(f'<text x="350" y="{cy-24}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">2. leerCacheObra() →</text>')
svg.append(f'<text x="350" y="{cy-10}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">6. guardarOffline(PENDIENTE) →</text>')
svg.append(f'<text x="350" y="{cy+24}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">← 4. returnInfoObraCache()</text>')
svg.append(f'<text x="350" y="{cy+38}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">← 18a. callbackSyncCompletado()</text>')

# 3. sync_manager -> local_sqlite_db (vertical)
svg.append(f'<text x="475" y="275" text-anchor="start" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#000000">3. SELECT cache_obra</text>')
svg.append(f'<text x="475" y="295" text-anchor="start" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#000000">7. INSERT cola_sync (PENDIENTE)</text>')
svg.append(f'<text x="475" y="315" text-anchor="start" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#000000">11. SELECT WHERE estado="PENDIENTE"</text>')
svg.append(f'<text x="475" y="335" text-anchor="start" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#000000">17. UPDATE estado="SINCRONIZADO"</text>')

# 4. sync_manager -> sync_routes (Online HTTP sync)
svg.append(f'<text x="620" y="{cy-28}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#000000">10. [Conexión Recuperada / HU93]</text>')
svg.append(f'<text x="620" y="{cy-14}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">12. POST /api/v1/sync/batch (lote_json) →</text>')
svg.append(f'<text x="620" y="{cy+24}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">← 16. 200 OK (ids_confirmados, timestamp)</text>')

# 5. sync_routes -> sync_services
svg.append(f'<text x="905" y="{cy-20}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">13. validarYAplicarLote() →</text>')
svg.append(f'<text x="905" y="{cy-6}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">(idempotencia y permisos tenant)</text>')

# 6. sync_services -> sync_repos
svg.append(f'<text x="1150" y="{cy-20}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">14. transaccionLote() →</text>')
svg.append(f'<text x="1150" y="{cy-6}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">(inserción atómica &amp; auditoría)</text>')

# 7. sync_repos -> database obras
svg.append(f'<text x="1385" y="{cy-20}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">15. INSERT / UPDATE →</text>')
svg.append(f'<text x="1385" y="{cy-6}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">SQL multi-tenant (obras)</text>')

# ================= NODES =================

# 1. Actor: Supervisor / Personal de Campo
act_x = 55
act_y = cy - 25
svg.append(f'<circle cx="{act_x}" cy="{act_y}" r="8" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{act_x}" y1="{act_y+8}" x2="{act_x}" y2="{act_y+24}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{act_x-12}" y1="{act_y+14}" x2="{act_x+12}" y2="{act_y+14}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{act_x}" y1="{act_y+24}" x2="{act_x-10}" y2="{act_y+40}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{act_x}" y1="{act_y+24}" x2="{act_x+10}" y2="{act_y+40}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<text x="{act_x}" y="{act_y+53}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" font-weight="bold" fill="#000000">Supervisor /</text>')
svg.append(f'<text x="{act_x}" y="{act_y+65}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" font-weight="bold" fill="#000000">Personal Campo</text>')

# Helper to draw Boundary: ┫◯
def draw_boundary(cx, cy, label1, label2=""):
    s = []
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    s.append(f'<line x1="{cx-r}" y1="{cy-22}" x2="{cx-r}" y2="{cy+22}" stroke="#000000" stroke-width="1.4"/>')
    s.append(f'<line x1="{cx-r-12}" y1="{cy-22}" x2="{cx-r-12}" y2="{cy+22}" stroke="#000000" stroke-width="1.4"/>')
    s.append(f'<line x1="{cx-r-12}" y1="{cy}" x2="{cx-r}" y2="{cy}" stroke="#000000" stroke-width="1.4"/>')
    s.append(f'<text x="{cx}" y="{cy-3 if label2 else cy+4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" font-weight="bold" fill="#000000">{label1}</text>')
    if label2:
        s.append(f'<text x="{cx}" y="{cy+11}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">{label2}</text>')
    return "".join(s)

# Helper to draw Control: ↻◯
def draw_control(cx, cy, label1, label2=""):
    s = []
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    s.append(f'<path d="M {cx-14} {cy-r+2} A 16 16 0 0 1 {cx+12} {cy-r-3}" fill="none" stroke="#000000" stroke-width="1.3"/>')
    s.append(f'<polygon points="{cx+12},{cy-r-8} {cx+19},{cy-r-2} {cx+11},{cy-r+3}" fill="#000000"/>')
    s.append(f'<text x="{cx}" y="{cy-3 if label2 else cy+4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" font-weight="bold" fill="#000000">{label1}</text>')
    if label2:
        s.append(f'<text x="{cx}" y="{cy+11}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" fill="#000000">{label2}</text>')
    return "".join(s)

# Helper to draw Entity: ◯_
def draw_entity(cx, cy, label1, label2="", label3=""):
    s = []
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    s.append(f'<line x1="{cx-r+8}" y1="{cy+r}" x2="{cx+r-8}" y2="{cy+r}" stroke="#000000" stroke-width="1.4"/>')
    y_off = cy - 8 if label3 else (cy - 3 if label2 else cy + 4)
    s.append(f'<text x="{cx}" y="{y_off}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#000000">{label1}</text>')
    if label2:
        s.append(f'<text x="{cx}" y="{y_off+12}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#000000">{label2}</text>')
    if label3:
        s.append(f'<text x="{cx}" y="{y_off+23}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#000000">{label3}</text>')
    return "".join(s)

# Draw Node 1: IU_operacion_offline (Boundary)
svg.append(draw_boundary(240, cy, "IU_operacion", "offline"))

# Draw Node 2: sync_manager (Control Móvil)
svg.append(draw_control(460, cy, "sync_manager", "(Móvil)"))

# Draw Node 3: local_sqlite_db (Entity Móvil)
svg.append(draw_entity(460, 420, "sqlite_local", "database", "(Móvil)"))

# Draw Sub-Entities Móvil:
svg.append(draw_entity(290, 420, "cache_obra", "local", "(HU90)"))
svg.append(draw_entity(630, 420, "cola_pendientes", "sync", "(HU91/92/94)"))

# Draw Backend Control Nodes:
svg.append(draw_control(780, cy, "sync_routes", "(FastAPI)"))
svg.append(draw_control(1030, cy, "sync_services", "(Business)"))
svg.append(draw_control(1270, cy, "sync_repos", "(Data Layer)"))

# Draw Backend Central DB:
svg.append(draw_entity(1500, cy, "database", "obras", "(PostgreSQL)"))

# Draw Backend Central Entities:
svg.append(draw_entity(1670, 110, "t_avance", "obra"))
svg.append(draw_entity(1670, 200, "t_incidencia", ""))
svg.append(draw_entity(1670, 290, "t_sincronizacion", "log"))

svg.append('</svg>')

svg_str = "\n".join(svg)
svg_path = 'docs/diagramas/comunicacion_cu41_offline_sync.svg'
with open(svg_path, 'w', encoding='utf-8') as f:
    f.write(svg_str)

# Convert to PNG via resvg_py
png_path = 'docs/diagramas/comunicacion_cu41_offline_sync.png'
png_bytes = resvg_py.svg_to_bytes(svg_str)
with open(png_path, "wb") as f:
    f.write(png_bytes)
print(f"Generated SVG & PNG for CU41 communication diagram! ({len(png_bytes)} bytes)")

# Copy to brain
shutil.copyfile(svg_path, os.path.join(brain_diag_dir, 'comunicacion_cu41_offline_sync.svg'))
shutil.copyfile(png_path, os.path.join(brain_diag_dir, 'comunicacion_cu41_offline_sync.png'))

# ==============================================================================
# 2. GENERATE DRAW.IO EDITABLE XML FOR COMMUNICATION DIAGRAM
# ==============================================================================
drawio_xml = []
drawio_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
drawio_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-22T14:35:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
drawio_xml.append('  <diagram id="cu41_comunicacion_offline_sync" name="CU41 - Comunicacion Offline Sync">')
drawio_xml.append('    <mxGraphModel dx="1600" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1800" pageHeight="600" background="#FFFFFF" math="0" shadow="0">')
drawio_xml.append('      <root>')
drawio_xml.append('        <mxCell id="0" />')
drawio_xml.append('        <mxCell id="1" parent="0" />')

# Title
drawio_xml.append('        <mxCell id="title" value="&lt;b&gt;Gestionar Operación Offline y Sincronización (CU41 - HU90 a HU94)&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;Diagrama de Comunicación con Análisis de Robustez BCE (Móvil Flutter + Backend FastAPI)&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=13;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="50" y="25" width="800" height="40" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Containers / Boundaries for Mobile Zone and Backend Zone
drawio_xml.append('        <mxCell id="zone_mobile" value="ZONA CLIENTE MÓVIL (FLUTTER / SQLITE)" style="swimlane;whiteSpace=wrap;html=1;dashed=1;dashPattern=5 5;fillColor=none;strokeColor=#666666;fontFamily=Arial;fontSize=11;fontStyle=1;align=left;spacingLeft=15;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="150" y="80" width="530" height="430" as="geometry" />')
drawio_xml.append('        </mxCell>')

drawio_xml.append('        <mxCell id="zone_backend" value="ZONA SERVIDOR CENTRAL (FASTAPI / POSTGRESQL OBRAS)" style="swimlane;whiteSpace=wrap;html=1;dashed=1;dashPattern=5 5;fillColor=none;strokeColor=#666666;fontFamily=Arial;fontSize=11;fontStyle=1;align=left;spacingLeft=15;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="710" y="80" width="1030" height="430" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Actor
drawio_xml.append('        <mxCell id="actor_user" value="Supervisor /&lt;br&gt;Personal de Campo" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="55" y="170" width="30" height="60" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Boundary: IU_operacion_offline
drawio_xml.append('        <mxCell id="b_iu" value="IU_operacion_&lt;br&gt;offline" style="shape=umlBoundary;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="210" y="165" width="85" height="70" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Control: sync_manager (Móvil)
drawio_xml.append('        <mxCell id="c_sync_mgr" value="sync_manager&lt;br&gt;&lt;font style=&quot;font-size: 8.5px; font-weight: normal;&quot;&gt;(Móvil)&lt;/font&gt;" style="shape=umlControl;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="425" y="165" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Entity: sqlite_local_db
drawio_xml.append('        <mxCell id="e_sqlite" value="sqlite_local_db&lt;br&gt;&lt;font style=&quot;font-size: 8.5px; font-weight: normal;&quot;&gt;(Móvil)&lt;/font&gt;" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="425" y="380" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Sub-Entities Móvil
drawio_xml.append('        <mxCell id="e_cache_obra" value="cache_obra_&lt;br&gt;local&lt;br&gt;&lt;font style=&quot;font-size: 8.5px; font-weight: normal;&quot;&gt;(HU90)&lt;/font&gt;" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="250" y="380" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

drawio_xml.append('        <mxCell id="e_cola_sync" value="cola_pendientes_&lt;br&gt;sync&lt;br&gt;&lt;font style=&quot;font-size: 8.5px; font-weight: normal;&quot;&gt;(HU91/92/94)&lt;/font&gt;" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="590" y="380" width="80" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Control Backend: sync_routes
drawio_xml.append('        <mxCell id="c_sync_routes" value="sync_routes&lt;br&gt;&lt;font style=&quot;font-size: 8.5px; font-weight: normal;&quot;&gt;(FastAPI)&lt;/font&gt;" style="shape=umlControl;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="750" y="165" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Control Backend: sync_services
drawio_xml.append('        <mxCell id="c_sync_services" value="sync_services&lt;br&gt;&lt;font style=&quot;font-size: 8.5px; font-weight: normal;&quot;&gt;(Lógica / Resolve)&lt;/font&gt;" style="shape=umlControl;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="990" y="165" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Control Backend: sync_repos
drawio_xml.append('        <mxCell id="c_sync_repos" value="sync_repos&lt;br&gt;&lt;font style=&quot;font-size: 8.5px; font-weight: normal;&quot;&gt;(PostgreSQL)&lt;/font&gt;" style="shape=umlControl;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="1230" y="165" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Entity Backend: database obras
drawio_xml.append('        <mxCell id="e_db_obras" value="database&lt;br&gt;obras&lt;br&gt;&lt;font style=&quot;font-size: 8.5px; font-weight: normal;&quot;&gt;(PostgreSQL)&lt;/font&gt;" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="1460" y="165" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Sub-Entities Backend Central
drawio_xml.append('        <mxCell id="e_t_avance" value="t_avance_&lt;br&gt;obra" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="1630" y="80" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

drawio_xml.append('        <mxCell id="e_t_incidencia" value="t_incidencia" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="1630" y="165" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

drawio_xml.append('        <mxCell id="e_t_sync_log" value="t_sincronizacion_&lt;br&gt;log" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="1630" y="250" width="75" height="75" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Edges & Messages
# Edge 1: Actor -> IU
drawio_xml.append('        <mxCell id="edge_user_iu" value="1. consultarInfoObra() [HU90] →&lt;br&gt;5. registrarAvance/Incidencia() [HU91/92] →&lt;br&gt;8. consultarEstadoSync() [HU94] →&lt;br&gt;← 9. mostrarEstadoLocal()&lt;br&gt;← 18. notificarSincronizacion()" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="actor_user" target="b_iu">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Edge 2: IU -> sync_manager
drawio_xml.append('        <mxCell id="edge_iu_mgr" value="2. leerCacheObra() →&lt;br&gt;6. guardarOffline(PENDIENTE) →&lt;br&gt;← 4. returnInfoObraCache()&lt;br&gt;← 18a. callbackSyncCompletado()" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="b_iu" target="c_sync_mgr">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Edge 3: sync_manager -> sqlite_local_db
drawio_xml.append('        <mxCell id="edge_mgr_sqlite" value="3. SELECT cache_obra ↓&lt;br&gt;7. INSERT cola_sync (PENDIENTE) ↓&lt;br&gt;11. SELECT WHERE estado=PENDIENTE ↓&lt;br&gt;17. UPDATE estado=SINCRONIZADO ↓" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=8.5;fontColor=#000000;fontFamily=Arial;labelPosition=right;verticalLabelPosition=middle;align=left;spacingLeft=10;" edge="1" parent="1" source="c_sync_mgr" target="e_sqlite">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Edge 4: sqlite_local_db -> sub-entities
drawio_xml.append('        <mxCell id="edge_sqlite_cache" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="e_sqlite" target="e_cache_obra">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

drawio_xml.append('        <mxCell id="edge_sqlite_cola" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="e_sqlite" target="e_cola_sync">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Edge 5: sync_manager -> sync_routes (Online HTTP)
drawio_xml.append('        <mxCell id="edge_mgr_routes" value="10. [Conexión Recuperada / HU93]&lt;br&gt;12. POST /api/v1/sync/batch (lote_json) →&lt;br&gt;← 16. 200 OK (ids_confirmados, timestamp)" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.5;strokeDasharray=4 3;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_sync_mgr" target="c_sync_routes">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Edge 6: sync_routes -> sync_services
drawio_xml.append('        <mxCell id="edge_routes_services" value="13. validarYAplicarLote() →&lt;br&gt;(idempotencia y permisos tenant)" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_sync_routes" target="c_sync_services">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Edge 7: sync_services -> sync_repos
drawio_xml.append('        <mxCell id="edge_services_repos" value="14. transaccionLote() →&lt;br&gt;(inserción atómica &amp; auditoría)" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_sync_services" target="c_sync_repos">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Edge 8: sync_repos -> database obras
drawio_xml.append('        <mxCell id="edge_repos_db" value="15. INSERT / UPDATE →&lt;br&gt;SQL multi-tenant (obras)" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=9;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_sync_repos" target="e_db_obras">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Edge 9: database obras -> sub-entities
drawio_xml.append('        <mxCell id="edge_db_avance" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="e_db_obras" target="e_t_avance">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

drawio_xml.append('        <mxCell id="edge_db_incidencia" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="e_db_obras" target="e_t_incidencia">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

drawio_xml.append('        <mxCell id="edge_db_sync_log" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="e_db_obras" target="e_t_sync_log">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
drawio_xml.append('        </mxCell>')

drawio_xml.append('      </root>')
drawio_xml.append('    </mxGraphModel>')
drawio_xml.append('  </diagram>')
drawio_xml.append('</mxfile>')

drawio_path = 'docs/diagramas/comunicacion_cu41_offline_sync.drawio'
with open(drawio_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(drawio_xml))

shutil.copyfile(drawio_path, os.path.join(brain_diag_dir, 'comunicacion_cu41_offline_sync.drawio'))
print("Generated Draw.io for CU41 communication diagram!")
