import os
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)

# Dimensions
svg_w = 1400
svg_h = 360

# Positions along the horizontal line
# Actor: x=80
# IU_asistente (Boundary): x=250, cy=180, r=40
# ai_routes (Control): x=450, cy=180, r=40
# crm_services (Control): x=660, cy=180, r=40
# crm_repos (Control): x=870, cy=180, r=40
# database obras (Entity): x=1080, cy=180, r=40
# Branching Entities:
# t_asistente: x=1270, cy=90, r=38
# t_unidad: x=1270, cy=180, r=38
# t_crm_cliente: x=1270, cy=270, r=38

cy = 180
r = 38

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">')

# Definitions: Arrow markers (B&W)
svg.append('''<defs>
  <marker id="arr-fwd" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
  </marker>
  <marker id="arr-back" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6" markerHeight="6" orient="auto">
    <path d="M 8 1.5 L 0 5 L 8 8.5 z" fill="#000000"/>
  </marker>
</defs>''')

# Background: Clean White
svg.append(f'<rect width="{svg_w}" height="{svg_h}" fill="#FFFFFF"/>')

# Title at top-left
svg.append('<text x="50" y="45" font-family="Arial, Helvetica, sans-serif" font-size="13" font-weight="bold" fill="#000000">Consultar Asistente Comercial y Recomendaciones (CU34)</text>')

# 1. Connecting Lines between nodes
# Actor to IU
svg.append(f'<line x1="80" y1="{cy}" x2="{250-r-12}" y2="{cy}" stroke="#000000" stroke-width="1.2"/>')
# IU to ai_routes
svg.append(f'<line x1="{250+r}" y1="{cy}" x2="{450-r}" y2="{cy}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')
# ai_routes to crm_services
svg.append(f'<line x1="{450+r}" y1="{cy}" x2="{660-r}" y2="{cy}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')
# crm_services to crm_repos
svg.append(f'<line x1="{660+r}" y1="{cy}" x2="{870-r}" y2="{cy}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')
# crm_repos to database obras
svg.append(f'<line x1="{870+r}" y1="{cy}" x2="{1080-r}" y2="{cy}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')

# Database obras to branching entities
# Branch to t_asistente (up)
svg.append(f'<line x1="{1080+r*0.7}" y1="{cy-r*0.7}" x2="{1270-r*0.7}" y2="{90+r*0.7}" stroke="#000000" stroke-width="1.2"/>')
# Branch to t_unidad (middle)
svg.append(f'<line x1="{1080+r}" y1="{cy}" x2="{1270-r}" y2="{cy}" stroke="#000000" stroke-width="1.2"/>')
# Branch to t_crm_cliente (down)
svg.append(f'<line x1="{1080+r*0.7}" y1="{cy+r*0.7}" x2="{1270-r*0.7}" y2="{270-r*0.7}" stroke="#000000" stroke-width="1.2"/>')

# 2. Messages above and below lines
# Above line Actor -> IU
svg.append(f'<text x="145" y="{cy-18}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">1. ingresarConsulta()</text>')
svg.append(f'<line x1="185" y1="{cy-21}" x2="200" y2="{cy-21}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')

# Above line IU -> ai_routes
svg.append(f'<text x="350" y="{cy-18}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">2. enviarConsulta(datos)</text>')
# Below line IU <- ai_routes (return)
svg.append(f'<line x1="330" y1="{cy+24}" x2="310" y2="{cy+24}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr-fwd)"/>')
svg.append(f'<text x="375" y="{cy+28}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">6. mostrarResultados()</text>')

# Above line ai_routes -> crm_services
svg.append(f'<text x="555" y="{cy-18}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">3. consultarCrmIa()</text>')

# Above line crm_services -> crm_repos
svg.append(f'<text x="765" y="{cy-25}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">4: validar y buscar</text>')
svg.append(f'<text x="765" y="{cy-12}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">inmuebles()</text>')

# Above line crm_repos -> database obras
svg.append(f'<text x="975" y="{cy-25}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">5: consultar unidades y</text>')
svg.append(f'<text x="975" y="{cy-12}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">guardar mensaje()</text>')

# 3. Draw Nodes (Robustness UML Icons matching user sample)

# Node 0: Actor (Stick figure)
act_x = 60
act_y = cy - 25
svg.append(f'<circle cx="{act_x}" cy="{act_y}" r="8" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{act_x}" y1="{act_y+8}" x2="{act_x}" y2="{act_y+24}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{act_x-12}" y1="{act_y+14}" x2="{act_x+12}" y2="{act_y+14}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{act_x}" y1="{act_y+24}" x2="{act_x-10}" y2="{act_y+40}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{act_x}" y1="{act_y+24}" x2="{act_x+10}" y2="{act_y+40}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<text x="{act_x}" y="{act_y+55}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" fill="#000000">Cliente Potencial</text>')

# Node 1: Boundary (Circle with T-bar on left: ┫◯)
b_cx = 250
svg.append(f'<circle cx="{b_cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{b_cx-r-12}" y1="{cy-22}" x2="{b_cx-r-12}" y2="{cy+22}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<line x1="{b_cx-r-12}" y1="{cy}" x2="{b_cx-r}" y2="{cy}" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<text x="{b_cx}" y="{cy+4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10.5" font-weight="bold" fill="#000000">IU_asistente</text>')

# Helper for Control Icon: Circle with curled arrow on top (↻◯)
def draw_control(cx, cy, r, name):
    res = []
    # Circle
    res.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    # Curl arrow at top
    arrow_path = f"M {cx-15} {cy-r+5} C {cx-8} {cy-r-12}, {cx+12} {cy-r-12}, {cx+16} {cy-r+4}"
    res.append(f'<path d="{arrow_path}" fill="none" stroke="#000000" stroke-width="1.3"/>')
    res.append(f'<polygon points="{cx-18},{cy-r+1} {cx-11},{cy-r+8} {cx-20},{cy-r+11}" fill="#000000"/>')
    # Text
    res.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10.5" font-weight="bold" fill="#000000">{name}</text>')
    return "".join(res)

# Node 2: Control ai_routes
svg.append(draw_control(450, cy, r, "ai_routes"))

# Node 3: Control crm_services
svg.append(draw_control(660, cy, r, "crm_services"))

# Node 4: Control assistant_repos
svg.append(draw_control(870, cy, r, "assistant_repos"))

# Helper for Entity Icon: Circle with horizontal line at bottom (◯_)
def draw_entity(cx, cy, r, name_lines):
    res = []
    res.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
    # Underline
    res.append(f'<line x1="{cx-r*0.75}" y1="{cy+r+6}" x2="{cx+r*0.75}" y2="{cy+r+6}" stroke="#000000" stroke-width="1.3"/>')
    # Text lines
    start_y = cy - (len(name_lines)-1)*7 + 4
    for idx, nl in enumerate(name_lines):
        res.append(f'<text x="{cx}" y="{start_y + idx*13}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="10" font-weight="bold" fill="#000000">{nl}</text>')
    return "".join(res)

# Node 5: Entity database obras
svg.append(draw_entity(1080, cy, r, ["database", "obras"]))

# Node 6: Entity t_asistente (Branch Up)
svg.append(draw_entity(1270, 90, r, ["t_asistente_", "conversacion"]))

# Node 7: Entity t_unidad (Branch Middle)
svg.append(draw_entity(1270, 180, r, ["t_unidad_", "construccion"]))

# Node 8: Entity t_crm_cliente (Branch Down)
svg.append(draw_entity(1270, 270, r, ["t_crm_", "cliente"]))

svg.append('</svg>')
svg_content = "\n".join(svg)

# Save SVG
svg_path = "docs/diagramas/comunicacion_cu34_asistente_comercial.svg"
with open(svg_path, "w", encoding="utf-8") as f:
    f.write(svg_content)
print(f"Generated {svg_path}")

# Render PNG with resvg_py
png_bytes = resvg_py.svg_to_bytes(svg_content)
png_path = "docs/diagramas/comunicacion_cu34_asistente_comercial.png"
with open(png_path, "wb") as f:
    f.write(png_bytes)
print(f"Generated {png_path} ({len(png_bytes)} bytes)")

