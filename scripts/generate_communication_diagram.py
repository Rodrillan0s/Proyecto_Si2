import os
import html
import resvg_py

os.makedirs('docs/diagramas', exist_ok=True)

# Layout definition for CU34 Communication Diagram
svg_w = 1350
svg_h = 750

# Objects / Nodes
nodes = {
    "user": {
        "label": "user : Cliente_Potencial",
        "type": "actor",
        "x": 60,
        "y": 280,
        "w": 150,
        "h": 50
    },
    "ui": {
        "label": "ui : Form_Asistente_Comercial",
        "x": 280,
        "y": 280,
        "w": 200,
        "h": 50
    },
    "router": {
        "label": "router : ai_routes",
        "x": 550,
        "y": 280,
        "w": 170,
        "h": 50
    },
    "service": {
        "label": "service : Control_Asistente_Comercial",
        "x": 790,
        "y": 280,
        "w": 230,
        "h": 50
    },
    "t_asist": {
        "label": "t_asistente_conversacion",
        "x": 1090,
        "y": 100,
        "w": 190,
        "h": 50
    },
    "t_unid": {
        "label": "t_unidad_construccion",
        "x": 1090,
        "y": 280,
        "w": 190,
        "h": 50
    },
    "t_crm": {
        "label": "t_crm_cliente",
        "x": 1090,
        "y": 460,
        "w": 190,
        "h": 50
    }
}

# Links and Message annotations along links
links = [
    {
        "n1": "user",
        "n2": "ui",
        "msgs": [
            ("1: ingresar_consulta('Busco depto 2 dorms', presupuesto)", "->", -15),
            ("14: visualizar_recomendaciones_comerciales()", "<-", 15)
        ]
    },
    {
        "n1": "ui",
        "n2": "router",
        "msgs": [
            ("2: POST /api/ai/crm/consulta", "->", -15),
            ("12: 200 OK (Mensaje IA y tarjetas)", "<-", 15)
        ]
    },
    {
        "n1": "router",
        "n2": "service",
        "msgs": [
            ("3: consultar_crm_ia(pregunta, pres, token, ip)", "->", -15),
            ("11: return {respuesta_ia, unidades, sugerencias}", "<-", 15)
        ]
    },
    {
        "n1": "service",
        "n2": "t_asist",
        "msgs": [
            ("4: SELECT / INSERT sesion_conversacion() ->", "top_branch", -25),
            ("5: return id_conversacion <-", "top_branch", -10),
            ("9: INSERT INTO t_asistente_mensaje(...) ->", "top_branch", 5)
        ]
    },
    {
        "n1": "service",
        "n2": "t_unid",
        "msgs": [
            ("6: SELECT * FROM t_unidad WHERE estado='DISPONIBLE'", "->", -15),
            ("7: return lista_unidades_compatibles", "<-", 15)
        ]
    },
    {
        "n1": "service",
        "n2": "t_crm",
        "msgs": [
            ("10: UPDATE t_crm_cliente SET clasificacion='INTERESADO' ->", "bot_branch", 15)
        ]
    }
]

# Build SVG (strictly Black and White)
svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">')

# Background
svg.append(f'<rect width="{svg_w}" height="{svg_h}" fill="#FFFFFF"/>')

# Outer UML frame
frame_x = 20
frame_y = 20
frame_w = svg_w - 40
frame_h = svg_h - 40
svg.append(f'<rect x="{frame_x}" y="{frame_y}" width="{frame_w}" height="{frame_h}" fill="none" stroke="#000000" stroke-width="1.3"/>')

# Top-left folded frame tab: cd CU34 - Consultar asistente comercial y recomendaciones
tag_text = "cd CU34 - Consultar asistente comercial y recomendaciones"
tag_w = len(tag_text) * 7.2 + 25
tag_h = 24
svg.append(f'<polygon points="{frame_x},{frame_y} {frame_x+tag_w},{frame_y} {frame_x+tag_w+8},{frame_y+tag_h/2} {frame_x+tag_w},{frame_y+tag_h} {frame_x},{frame_y+tag_h}" fill="#FFFFFF" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<text x="{frame_x+8}" y="{frame_y+16}" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" fill="#000000">{tag_text}</text>')

# Draw Links (connecting lines)
for l in links:
    n1 = nodes[l["n1"]]
    n2 = nodes[l["n2"]]

    # Horizontal connection
    if n1["y"] == n2["y"]:
        x1 = n1["x"] + n1["w"]
        y1 = n1["y"] + n1["h"] / 2.0
        x2 = n2["x"]
        y2 = n2["y"] + n2["h"] / 2.0
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000000" stroke-width="1.3"/>')

        # Messages along line
        mid_x = (x1 + x2) / 2.0
        for msg, direction, y_offset in l["msgs"]:
            arrow_symbol = " →" if direction == "->" else " ←"
            text_str = html.escape(msg + arrow_symbol)
            svg.append(f'<text x="{mid_x}" y="{y1 + y_offset}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">{text_str}</text>')

    # Diagonal connection to top-right
    elif n2["y"] < n1["y"]:
        x1 = n1["x"] + n1["w"]
        y1 = n1["y"] + 15
        x2 = n2["x"]
        y2 = n2["y"] + n2["h"] - 15
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000000" stroke-width="1.3"/>')
        
        # Messages
        mid_x = (x1 + x2) / 2.0 - 15
        mid_y = (y1 + y2) / 2.0
        for msg, _, y_offset in l["msgs"]:
            text_str = html.escape(msg)
            svg.append(f'<text x="{mid_x}" y="{mid_y + y_offset}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">{text_str}</text>')

    # Diagonal connection to bottom-right
    elif n2["y"] > n1["y"]:
        x1 = n1["x"] + n1["w"]
        y1 = n1["y"] + n1["h"] - 15
        x2 = n2["x"]
        y2 = n2["y"] + 15
        svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000000" stroke-width="1.3"/>')
        
        # Messages
        mid_x = (x1 + x2) / 2.0 - 10
        mid_y = (y1 + y2) / 2.0
        for msg, _, y_offset in l["msgs"]:
            text_str = html.escape(msg)
            svg.append(f'<text x="{mid_x}" y="{mid_y + y_offset}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">{text_str}</text>')

# Self-loops
# On ui: 13: renderizar_mensajes_y_tarjetas_inmuebles()
ui_n = nodes["ui"]
ui_cx = ui_n["x"] + ui_n["w"] / 2.0
ui_top = ui_n["y"]
svg.append(f'<path d="M {ui_cx-25} {ui_top} C {ui_cx-25} {ui_top-40}, {ui_cx+25} {ui_top-40}, {ui_cx+25} {ui_top}" fill="none" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<text x="{ui_cx}" y="{ui_top-44}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">13: renderizar_mensajes_y_tarjetas() ↺</text>')

# On service: 8: generar_analisis_recomendaciones_ia()
srv_n = nodes["service"]
srv_cx = srv_n["x"] + srv_n["w"] / 2.0
srv_top = srv_n["y"]
svg.append(f'<path d="M {srv_cx-25} {srv_top} C {srv_cx-25} {srv_top-40}, {srv_cx+25} {srv_top-40}, {srv_cx+25} {srv_top}" fill="none" stroke="#000000" stroke-width="1.3"/>')
svg.append(f'<text x="{srv_cx}" y="{srv_top-44}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="9.5" fill="#000000">8: generar_analisis_recomendaciones_ia() ↺</text>')

# Draw Nodes (Boxes)
for k, n in nodes.items():
    x, y, w, h = n["x"], n["y"], n["w"], n["h"]

    # White box with black border
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#FFFFFF" stroke="#000000" stroke-width="1.4"/>')
    # Text (underlined for UML object standard)
    label_txt = html.escape(n["label"])
    svg.append(f'<text x="{x + w/2.0}" y="{y + h/2.0 + 4}" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="11" font-weight="bold" text-decoration="underline" fill="#000000">{label_txt}</text>')

svg.append('</svg>')
svg_content = "\n".join(svg)

# Save SVG
out_svg = "docs/diagramas/comunicacion_cu34_asistente_comercial.svg"
with open(out_svg, "w", encoding="utf-8") as f:
    f.write(svg_content)
print(f"Generated {out_svg}")

# Render PNG
out_png = "docs/diagramas/comunicacion_cu34_asistente_comercial.png"
png_bytes = resvg_py.svg_to_bytes(svg_content)
with open(out_png, "wb") as f:
    f.write(png_bytes)
print(f"Generated {out_png} ({len(png_bytes)} bytes)")

