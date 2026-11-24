import os
import shutil
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)
brain_diag_dir = r'C:\Users\eddym\.gemini\antigravity\brain\45528441-65b1-4e7f-b192-74455f38d829\diagramas'
os.makedirs(brain_diag_dir, exist_ok=True)

# ==============================================================================
# 1. DIAGRAMA DE ESTADOS UML - CU41
# ==============================================================================
def generate_state_diagram():
    w = 1260
    h = 440
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    svg.append('''<defs>
      <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
      </marker>
      <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
        <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" flood-color="#000000" flood-opacity="0.08"/>
      </filter>
    </defs>''')
    svg.append(f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>')

    # Title
    svg.append('<text x="45" y="38" font-family="Arial, Helvetica, sans-serif" font-size="14.5" font-weight="bold" fill="#000000">CU 41M – Gestionar operación offline y sincronización</text>')
    svg.append('<text x="45" y="56" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#555555">Diagrama de Estados: Ciclo de vida del registro de datos y sincronización de faena</text>')

    # Outer container border
    svg.append(f'<rect x="35" y="72" width="{w-70}" height="{h-95}" rx="8" fill="none" stroke="#000000" stroke-width="1.3"/>')

    # Coordinates
    nodes = {
        "start": {"cx": 65, "cy": 185},
        "s1": {"cx": 160, "cy": 185, "w": 125, "h": 52, "title": "CREADO LOCAL", "sub": "(SQLite)"},
        "s2": {"cx": 340, "cy": 185, "w": 135, "h": 52, "title": "EN ESPERA DE RED", "sub": "(Cola offline)"},
        "s3": {"cx": 530, "cy": 185, "w": 145, "h": 52, "title": "EMPAQUETANDO LOTE", "sub": "(JSON + Checksum)"},
        "s4": {"cx": 725, "cy": 185, "w": 140, "h": 52, "title": "TRANSMITIENDO", "sub": "(HTTP POST sync)"},
        "d1": {"cx": 855, "cy": 185, "w": 36, "h": 36, "q": "¿Conflicto?"},
        "s_conf": {"cx": 855, "cy": 305, "w": 155, "h": 52, "title": "RESOLVIENDO CONFLICTO", "sub": "(Last-Write-Wins)"},
        "s5": {"cx": 1005, "cy": 185, "w": 150, "h": 52, "title": "CONSOLIDADO", "sub": "(PostgreSQL Central)"},
        "s6": {"cx": 1155, "cy": 185, "w": 115, "h": 52, "title": "SINCRONIZADO", "sub": "(Confirmado local)"},
        "end": {"cx": 1205, "cy": 305}
    }

    # Edges
    # 1. start -> s1
    svg.append(f'<line x1="{nodes["start"]["cx"]+11}" y1="185" x2="{nodes["s1"]["cx"] - nodes["s1"]["w"]/2}" y2="185" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')

    # 2. s1 -> s2
    x1 = nodes["s1"]["cx"] + nodes["s1"]["w"]/2
    x2 = nodes["s2"]["cx"] - nodes["s2"]["w"]/2
    svg.append(f'<line x1="{x1}" y1="185" x2="{x2}" y2="185" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
    svg.append(f'<text x="{(x1+x2)/2}" y="175" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">Almacenar local</text>')

    # 3. s2 -> s3
    x1 = nodes["s2"]["cx"] + nodes["s2"]["w"]/2
    x2 = nodes["s3"]["cx"] - nodes["s3"]["w"]/2
    svg.append(f'<line x1="{x1}" y1="185" x2="{x2}" y2="185" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
    svg.append(f'<text x="{(x1+x2)/2}" y="175" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">Red detectada</text>')

    # 4. s3 -> s4
    x1 = nodes["s3"]["cx"] + nodes["s3"]["w"]/2
    x2 = nodes["s4"]["cx"] - nodes["s4"]["w"]/2
    svg.append(f'<line x1="{x1}" y1="185" x2="{x2}" y2="185" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
    svg.append(f'<text x="{(x1+x2)/2}" y="175" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">Payload listo</text>')

    # 5. s4 -> d1
    x1 = nodes["s4"]["cx"] + nodes["s4"]["w"]/2
    x2 = nodes["d1"]["cx"] - nodes["d1"]["w"]/2
    svg.append(f'<line x1="{x1}" y1="185" x2="{x2}" y2="185" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')

    # 6. d1 -> s5 [Sin conflicto]
    x1 = nodes["d1"]["cx"] + nodes["d1"]["w"]/2
    x2 = nodes["s5"]["cx"] - nodes["s5"]["w"]/2
    svg.append(f'<line x1="{x1}" y1="185" x2="{x2}" y2="185" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
    svg.append(f'<text x="{(x1+x2)/2}" y="175" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">[Sin conflicto]</text>')

    # 7. d1 -> s_conf [Conflicto detectado]
    y1 = nodes["d1"]["cy"] + nodes["d1"]["h"]/2
    y2 = nodes["s_conf"]["cy"] - nodes["s_conf"]["h"]/2
    svg.append(f'<line x1="{nodes["d1"]["cx"]}" y1="{y1}" x2="{nodes["d1"]["cx"]}" y2="{y2}" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
    svg.append(f'<rect x="{nodes["d1"]["cx"] + 6}" y="{(y1+y2)/2 - 7}" width="95" height="15" rx="3" fill="#FFFFFF" stroke="#CCCCCC" stroke-width="0.8"/>')
    svg.append(f'<text x="{nodes["d1"]["cx"] + 10}" y="{(y1+y2)/2 + 4}" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">[Hay conflicto]</text>')

    # 8. s_conf -> s5 (Resolución aplicada)
    x1 = nodes["s_conf"]["cx"] + nodes["s_conf"]["w"]/2
    x2 = nodes["s5"]["cx"]
    y2 = nodes["s5"]["cy"] + nodes["s5"]["h"]/2
    svg.append(f'<path d="M {x1} {nodes["s_conf"]["cy"]} L {x2} {nodes["s_conf"]["cy"]} L {x2} {y2}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
    svg.append(f'<rect x="{(x1+x2)/2 - 45}" y="{nodes["s_conf"]["cy"] - 18}" width="90" height="15" rx="3" fill="#FFFFFF" stroke="#CCCCCC" stroke-width="0.8"/>')
    svg.append(f'<text x="{(x1+x2)/2}" y="{nodes["s_conf"]["cy"] - 7}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">Resolución Last-Write</text>')

    # 9. s5 -> s6
    x1 = nodes["s5"]["cx"] + nodes["s5"]["w"]/2
    x2 = nodes["s6"]["cx"] - nodes["s6"]["w"]/2
    svg.append(f'<line x1="{x1}" y1="185" x2="{x2}" y2="185" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
    svg.append(f'<text x="{(x1+x2)/2}" y="175" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">HTTP 200 (ACK)</text>')

    # 10. s6 -> end
    x1 = nodes["s6"]["cx"]
    y1 = nodes["s6"]["cy"] + nodes["s6"]["h"]/2
    x2 = nodes["end"]["cx"]
    y2 = nodes["end"]["cy"] - 12
    svg.append(f'<path d="M {x1} {y1} L {x1} {nodes["end"]["cy"]} L {x2} {nodes["end"]["cy"]}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
    svg.append(f'<rect x="{(x1+x2)/2 - 40}" y="{nodes["end"]["cy"] - 18}" width="80" height="15" rx="3" fill="#FFFFFF" stroke="#CCCCCC" stroke-width="0.8"/>')
    svg.append(f'<text x="{(x1+x2)/2}" y="{nodes["end"]["cy"] - 7}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">Purga / Archivo</text>')

    # 11. Error loop underneath (s4 -> s2)
    x1 = nodes["s4"]["cx"]
    y1 = nodes["s4"]["cy"] + nodes["s4"]["h"]/2
    x2 = nodes["s2"]["cx"]
    y2 = nodes["s2"]["cy"] + nodes["s2"]["h"]/2
    under_y = 385
    svg.append(f'<path d="M {x1} {y1} L {x1} {under_y} L {x2} {under_y} L {x2} {y2}" fill="none" stroke="#000000" stroke-width="1.2" marker-end="url(#arr)"/>')
    svg.append(f'<rect x="{(x1+x2)/2 - 80}" y="{under_y - 8}" width="160" height="16" rx="3" fill="#FFFFFF" stroke="#CCCCCC" stroke-width="0.8"/>')
    svg.append(f'<text x="{(x1+x2)/2}" y="{under_y + 4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" font-style="italic" fill="#333333">Fallo de red / Timeout (Reintento con backoff)</text>')

    # Draw Nodes
    # Start
    svg.append(f'<circle cx="{nodes["start"]["cx"]}" cy="{nodes["start"]["cy"]}" r="11" fill="#000000" stroke="#000000" stroke-width="1.2" filter="url(#shadow)"/>')

    # State boxes
    for sid in ["s1", "s2", "s3", "s4", "s5", "s6", "s_conf"]:
        n = nodes[sid]
        cx, cy, nw, nh = n["cx"], n["cy"], n["w"], n["h"]
        svg.append(f'<rect x="{cx - nw/2}" y="{cy - nh/2}" width="{nw}" height="{nh}" rx="12" fill="#FFFFFF" stroke="#000000" stroke-width="1.3" filter="url(#shadow)"/>')
        svg.append(f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" font-weight="bold" fill="#000000">{n["title"]}</text>')
        svg.append(f'<text x="{cx}" y="{cy + 11}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">{n["sub"]}</text>')

    # Decision
    d = nodes["d1"]
    cx, cy, dw, dh = d["cx"], d["cy"], d["w"], d["h"]
    svg.append(f'<polygon points="{cx},{cy - dh/2} {cx + dw/2},{cy} {cx},{cy + dh/2} {cx - dw/2},{cy}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3" filter="url(#shadow)"/>')

    # End
    e = nodes["end"]
    svg.append(f'<circle cx="{e["cx"]}" cy="{e["cy"]}" r="12" fill="#FFFFFF" stroke="#000000" stroke-width="1.4" filter="url(#shadow)"/>')
    svg.append(f'<circle cx="{e["cx"]}" cy="{e["cy"]}" r="7" fill="#000000"/>')

    svg.append('</svg>')
    return "\n".join(svg)

# ==============================================================================
# 2. DIAGRAMA DE TIEMPO UML - CU41
# ==============================================================================
def generate_timing_diagram():
    w = 1140
    h = 560
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    svg.append('''<defs>
      <marker id="arr-left" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="5" markerHeight="5" orient="auto">
        <path d="M 8 1.5 L 0 5 L 8 8.5 z" fill="#000000"/>
      </marker>
      <marker id="arr-right" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto">
        <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#000000"/>
      </marker>
    </defs>''')
    svg.append(f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>')

    # Title
    svg.append('<text x="45" y="36" font-family="Arial, Helvetica, sans-serif" font-size="14.5" font-weight="bold" fill="#000000">CU 41M – Gestionar operación offline y sincronización</text>')
    svg.append('<text x="45" y="54" font-family="Arial, Helvetica, sans-serif" font-size="11" fill="#555555">Diagrama de Tiempos: Transición de estados temporales entre App Móvil, Red, API Gateway y Base de Datos</text>')

    # Outer Frame
    top_y = 70
    bot_y = 520
    header_w = 145
    svg.append(f'<rect x="45" y="{top_y}" width="{w-90}" height="{bot_y-top_y}" fill="none" stroke="#000000" stroke-width="1.3"/>')
    svg.append(f'<line x1="{45+header_w}" y1="{top_y}" x2="{45+header_w}" y2="{bot_y}" stroke="#000000" stroke-width="1.3"/>')

    tracks = [
        {"name": "APP MÓVIL\n(SQLITE LOCAL)", "y": top_y},
        {"name": "CONECTIVIDAD\n/ RED MÓVIL", "y": top_y + 112},
        {"name": "API GATEWAY\n/ BACKEND", "y": top_y + 224},
        {"name": "BASE DE DATOS\nCENTRAL (PG)", "y": top_y + 336}
    ]

    for idx, tr in enumerate(tracks):
        ty = tr["y"]
        if idx > 0:
            svg.append(f'<line x1="45" y1="{ty}" x2="{w-45}" y2="{ty}" stroke="#000000" stroke-width="1.1"/>')
        # Header text
        lines = tr["name"].split("\n")
        mid_y = ty + 56 - (len(lines)-1)*7
        for l in lines:
            svg.append(f'<text x="{45 + header_w/2}" y="{mid_y}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" font-weight="bold" fill="#111111">{l}</text>')
            mid_y += 14

    # Horizontal Waveforms
    # Time points across tracks:
    # x0: 200 (Start)
    # x1: 240 (Step 1)
    # x2: 440 (Step 2 - Connection restored)
    # x3: 560 (Step 3 - Package ready & transmission start)
    # x4: 730 (Step 4 - Backend validation & DB commit)
    # x5: 860 (Step 5 - ACK received & local update)
    # x6: 980 (Step 6 - Consolidated rest)
    # x_end: 1060

    # TRACK 1: APP MÓVIL (SQLITE LOCAL)
    # Y bounds: ty = 70 to 182. Base low = 155, High = 95
    ty1 = 70
    y_low1 = ty1 + 82
    y_high1 = ty1 + 25
    path1 = f"M 195 {y_low1} L 240 {y_low1} L 240 {y_high1} L 470 {y_high1} L 470 {y_low1} L 550 {y_low1} L 550 {y_high1} L 850 {y_high1} L 850 {y_low1} L 1060 {y_low1}"
    svg.append(f'<path d="{path1}" fill="none" stroke="#000000" stroke-width="1.6"/>')

    # Track 1 Labels & Durations
    svg.append(f'<text x="215" y="{y_low1 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">En reposo</text>')
    svg.append(f'<text x="355" y="{y_high1 - 7}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#000000">Captura Offline en SQLite (Modo local activo)</text>')
    # Dimension arrow T > 0 min
    svg.append(f'<line x1="260" y1="{y_high1 + 18}" x2="450" y2="{y_high1 + 18}" stroke="#000000" stroke-width="1" marker-start="url(#arr-left)" marker-end="url(#arr-right)"/>')
    svg.append(f'<text x="355" y="{y_high1 + 31}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">T > 0 min (Jornada de faena)</text>')

    svg.append(f'<text x="510" y="{y_low1 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">Espera red</text>')

    svg.append(f'<text x="700" y="{y_high1 - 7}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#000000">Empaquetando lote JSON + Actualizando SQLite local</text>')
    # Dimension arrow {1 - 3 seg}
    svg.append(f'<line x1="570" y1="{y_high1 + 18}" x2="830" y2="{y_high1 + 18}" stroke="#000000" stroke-width="1" marker-start="url(#arr-left)" marker-end="url(#arr-right)"/>')
    svg.append(f'<text x="700" y="{y_high1 + 31}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">&#123;1 - 4 seg&#125;</text>')

    svg.append(f'<text x="955" y="{y_low1 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">Sincronizado / En reposo</text>')

    # TRACK 2: CONECTIVIDAD / RED
    # Y bounds: ty = 182 to 294. Base low = 267, High = 207
    ty2 = 182
    y_low2 = ty2 + 82
    y_high2 = ty2 + 25
    path2 = f"M 195 {y_low2} L 470 {y_low2} L 470 {y_high2} L 740 {y_high2} L 740 {y_low2} L 1060 {y_low2}"
    svg.append(f'<path d="{path2}" fill="none" stroke="#000000" stroke-width="1.6"/>')

    svg.append(f'<text x="330" y="{y_low2 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">Sin cobertura celular (En túnel / frente)</text>')
    svg.append(f'<line x1="220" y1="{y_low2 + 14}" x2="440" y2="{y_low2 + 14}" stroke="#000000" stroke-width="1" marker-start="url(#arr-left)" marker-end="url(#arr-right)"/>')
    svg.append(f'<text x="330" y="{y_low2 + 25}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">T > 0 seg</text>')

    svg.append(f'<text x="605" y="{y_high2 - 7}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#000000">Detección de red activa + Canal HTTPS transmitiendo</text>')
    svg.append(f'<line x1="490" y1="{y_high2 + 18}" x2="720" y2="{y_high2 + 18}" stroke="#000000" stroke-width="1" marker-start="url(#arr-left)" marker-end="url(#arr-right)"/>')
    svg.append(f'<text x="605" y="{y_high2 + 31}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">&#123;1 - 3 seg&#125;</text>')

    svg.append(f'<text x="900" y="{y_low2 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">Canal en reposo (Conectado)</text>')

    # TRACK 3: API GATEWAY / BACKEND
    # Y bounds: ty = 294 to 406. Base low = 379, High = 319
    ty3 = 294
    y_low3 = ty3 + 82
    y_high3 = ty3 + 25
    path3 = f"M 195 {y_low3} L 550 {y_low3} L 550 {y_high3} L 850 {y_high3} L 850 {y_low3} L 1060 {y_low3}"
    svg.append(f'<path d="{path3}" fill="none" stroke="#000000" stroke-width="1.6"/>')

    svg.append(f'<text x="370" y="{y_low3 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">Inactivo / En escucha</text>')

    svg.append(f'<text x="700" y="{y_high3 - 7}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#000000">Validación JWT + Idempotencia + Resolución Last-Write-Wins</text>')
    svg.append(f'<line x1="570" y1="{y_high3 + 18}" x2="830" y2="{y_high3 + 18}" stroke="#000000" stroke-width="1" marker-start="url(#arr-left)" marker-end="url(#arr-right)"/>')
    svg.append(f'<text x="700" y="{y_high3 + 31}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">&#123;&lt; 2 seg&#125;</text>')

    svg.append(f'<text x="955" y="{y_low3 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">HTTP 200 OK (ACK emitido)</text>')

    # TRACK 4: BASE DE DATOS CENTRAL
    # Y bounds: ty = 406 to 518. Base low = 491, High = 431
    ty4 = 406
    y_low4 = ty4 + 82
    y_high4 = ty4 + 25
    path4 = f"M 195 {y_low4} L 630 {y_low4} L 630 {y_high4} L 810 {y_high4} L 810 {y_low4} L 1060 {y_low4}"
    svg.append(f'<path d="{path4}" fill="none" stroke="#000000" stroke-width="1.6"/>')

    svg.append(f'<text x="410" y="{y_low4 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">Sin transacción (En espera)</text>')

    svg.append(f'<text x="720" y="{y_high4 - 7}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9" font-weight="bold" fill="#000000">BEGIN / COMMIT: Consolidación atómica de avances y auditoría</text>')
    svg.append(f'<line x1="650" y1="{y_high4 + 18}" x2="790" y2="{y_high4 + 18}" stroke="#000000" stroke-width="1" marker-start="url(#arr-left)" marker-end="url(#arr-right)"/>')
    svg.append(f'<text x="720" y="{y_high4 + 31}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#333333">&#123;&lt; 1 seg&#125;</text>')

    svg.append(f'<text x="935" y="{y_low4 - 8}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="8.5" fill="#555555">Persistido en PostgreSQL</text>')

    svg.append('</svg>')
    return "\n".join(svg)

# ==============================================================================
# RENDER HIGH-RES PNG AND SVG
# ==============================================================================
# 1. State Diagram
svg_state = generate_state_diagram()
with open('docs/diagramas/diag_estado_cu41.svg', 'w', encoding='utf-8') as f:
    f.write(svg_state)
png_state_bytes = resvg_py.svg_to_bytes(svg_state)
with open('docs/diagramas/diag_estado_cu41.png', 'wb') as f:
    f.write(png_state_bytes)
shutil.copyfile('docs/diagramas/diag_estado_cu41.svg', os.path.join(brain_diag_dir, 'diag_estado_cu41.svg'))
shutil.copyfile('docs/diagramas/diag_estado_cu41.png', os.path.join(brain_diag_dir, 'diag_estado_cu41.png'))
print("Rendered State Diagram for CU41!")

# 2. Timing Diagram
svg_timing = generate_timing_diagram()
with open('docs/diagramas/diag_tiempo_cu41.svg', 'w', encoding='utf-8') as f:
    f.write(svg_timing)
png_timing_bytes = resvg_py.svg_to_bytes(svg_timing)
with open('docs/diagramas/diag_tiempo_cu41.png', 'wb') as f:
    f.write(png_timing_bytes)
shutil.copyfile('docs/diagramas/diag_tiempo_cu41.svg', os.path.join(brain_diag_dir, 'diag_tiempo_cu41.svg'))
shutil.copyfile('docs/diagramas/diag_tiempo_cu41.png', os.path.join(brain_diag_dir, 'diag_tiempo_cu41.png'))
print("Rendered Timing Diagram for CU41!")

# ==============================================================================
# 3. DRAW.IO MULTI-TAB XML (100% Matching Layout)
# ==============================================================================
drawio_xml = []
drawio_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
drawio_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-22T23:30:00.000Z" agent="Antigravity" version="24.0.0" type="device">')

# Tab 1: Estado CU41
drawio_xml.append('  <diagram id="diag_estado_cu41" name="CU41 - Diagrama de Estados">')
drawio_xml.append('    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1260" pageHeight="440" background="#FFFFFF" math="0" shadow="0">')
drawio_xml.append('      <root>')
drawio_xml.append('        <mxCell id="0" />')
drawio_xml.append('        <mxCell id="1" parent="0" />')

# Title
drawio_xml.append('        <mxCell id="title_estado" value="&lt;b&gt;CU 41M – Gestionar operación offline y sincronización&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;Diagrama de Estados: Ciclo de vida del registro de datos y sincronización de faena&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=12;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="45" y="18" width="800" height="40" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Outer frame
drawio_xml.append('        <mxCell id="frame_estado" value="" style="rounded=1;arcSize=4;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;strokeWidth=1.3;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="35" y="72" width="1190" height="345" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Start
drawio_xml.append('        <mxCell id="start_node" value="" style="ellipse;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=#000000;strokeWidth=1.2;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="54" y="174" width="22" height="22" as="geometry" />')
drawio_xml.append('        </mxCell>')

# States
states_data = [
    ("s1", "CREADO LOCAL", "(SQLite)", 98, 159, 125, 52),
    ("s2", "EN ESPERA DE RED", "(Cola offline)", 273, 159, 135, 52),
    ("s3", "EMPAQUETANDO LOTE", "(JSON + Checksum)", 458, 159, 145, 52),
    ("s4", "TRANSMITIENDO", "(HTTP POST sync)", 655, 159, 140, 52),
    ("s_conf", "RESOLVIENDO CONFLICTO", "(Last-Write-Wins)", 778, 279, 155, 52),
    ("s5", "CONSOLIDADO", "(PostgreSQL Central)", 930, 159, 150, 52),
    ("s6", "SINCRONIZADO", "(Confirmado local)", 1098, 159, 115, 52)
]

for sid, title, sub, x, y, sw, sh in states_data:
    txt = f"&lt;b&gt;{title}&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;{sub}&lt;/font&gt;"
    drawio_xml.append(f'        <mxCell id="{sid}" value="{txt}" style="rounded=1;arcSize=24;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;align=center;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="{x}" y="{y}" width="{sw}" height="{sh}" as="geometry" />')
    drawio_xml.append('        </mxCell>')

# Decision
drawio_xml.append('        <mxCell id="d1" value="" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="837" y="167" width="36" height="36" as="geometry" />')
drawio_xml.append('        </mxCell>')

# End
drawio_xml.append('        <mxCell id="end_node" value="" style="ellipse;shape=doubleEllipse;whiteSpace=wrap;html=1;fillColor=#000000;strokeColor=#000000;strokeWidth=1.4;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="1193" y="293" width="24" height="24" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Transitions
edge_style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#000000;strokeWidth=1.2;fontSize=8.5;fontColor=#333333;fontFamily=Arial;labelBackgroundColor=#FFFFFF;labelBorderColor=#CCCCCC;"

transitions = [
    ("start_node", "s1", ""),
    ("s1", "s2", "Almacenar local"),
    ("s2", "s3", "Red detectada"),
    ("s3", "s4", "Payload listo"),
    ("s4", "d1", ""),
    ("d1", "s5", "[Sin conflicto]"),
    ("d1", "s_conf", "[Hay conflicto]"),
    ("s_conf", "s5", "Resolución Last-Write"),
    ("s5", "s6", "HTTP 200 (ACK)"),
    ("s6", "end_node", "Purga / Archivo")
]

for idx, (src, dst, lbl) in enumerate(transitions):
    drawio_xml.append(f'        <mxCell id="e_{idx}" value="{lbl}" style="{edge_style}" edge="1" parent="1" source="{src}" target="{dst}">')
    drawio_xml.append('          <mxGeometry relative="1" as="geometry" />')
    drawio_xml.append('        </mxCell>')

# Underneath retry loop
drawio_xml.append(f'        <mxCell id="e_retry" value="Fallo de red / Timeout (Reintento con backoff)" style="{edge_style}" edge="1" parent="1" source="s4" target="s2">')
drawio_xml.append('          <mxGeometry relative="1" as="geometry">')
drawio_xml.append('            <Array as="points">')
drawio_xml.append('              <mxPoint x="725" y="385" />')
drawio_xml.append('              <mxPoint x="340" y="385" />')
drawio_xml.append('            </Array>')
drawio_xml.append('          </mxGeometry>')
drawio_xml.append('        </mxCell>')

drawio_xml.append('      </root>')
drawio_xml.append('    </mxGraphModel>')
drawio_xml.append('  </diagram>')

# Tab 2: Tiempo CU41
drawio_xml.append('  <diagram id="diag_tiempo_cu41" name="CU41 - Diagrama de Tiempos">')
drawio_xml.append('    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1140" pageHeight="560" background="#FFFFFF" math="0" shadow="0">')
drawio_xml.append('      <root>')
drawio_xml.append('        <mxCell id="0" />')
drawio_xml.append('        <mxCell id="1" parent="0" />')

# Title
drawio_xml.append('        <mxCell id="title_tiempo" value="&lt;b&gt;CU 41M – Gestionar operación offline y sincronización&lt;/b&gt;&lt;br&gt;&lt;font color=&quot;#555555&quot;&gt;Diagrama de Tiempos: Transición temporal entre App Móvil, Red, API Gateway y Base de Datos&lt;/font&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=12;fontColor=#000000;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="45" y="16" width="850" height="40" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Outer timing frame
drawio_xml.append('        <mxCell id="frame_timing" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;strokeWidth=1.3;" vertex="1" parent="1">')
drawio_xml.append('          <mxGeometry x="45" y="70" width="1050" height="450" as="geometry" />')
drawio_xml.append('        </mxCell>')

# Track headers
t_names = [
    ("APP MÓVIL\n(SQLITE LOCAL)", 70),
    ("CONECTIVIDAD\n/ RED MÓVIL", 182),
    ("API GATEWAY\n/ BACKEND", 294),
    ("BASE DE DATOS\nCENTRAL (PG)", 406)
]

for tname, ty in t_names:
    drawio_xml.append(f'        <mxCell id="th_{ty}" value="&lt;b&gt;{html.escape(tname)}&lt;/b&gt;" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#F8F9FA;strokeColor=#000000;strokeWidth=1.1;fontFamily=Arial;fontSize=9.5;align=center;verticalAlign=middle;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="45" y="{ty}" width="145" height="112" as="geometry" />')
    drawio_xml.append('        </mxCell>')
    drawio_xml.append(f'        <mxCell id="tc_{ty}" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#000000;strokeWidth=1.1;" vertex="1" parent="1">')
    drawio_xml.append(f'          <mxGeometry x="190" y="{ty}" width="905" height="112" as="geometry" />')
    drawio_xml.append('        </mxCell>')

drawio_xml.append('      </root>')
drawio_xml.append('    </mxGraphModel>')
drawio_xml.append('  </diagram>')

drawio_xml.append('</mxfile>')

drawio_path = 'docs/diagramas/diagramas_cu41_estado_tiempo.drawio'
with open(drawio_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(drawio_xml))

shutil.copyfile(drawio_path, os.path.join(brain_diag_dir, 'diagramas_cu41_estado_tiempo.drawio'))
print("Successfully generated Draw.io XML for CU41 State and Timing Diagrams!")
