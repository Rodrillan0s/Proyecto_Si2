import html
import xml.etree.ElementTree as ET
from generate_communication_diagram import nodes, links, svg_w, svg_h

xml = []
xml.append('<?xml version="1.0" encoding="UTF-8"?>')
xml.append('<mxfile host="app.diagrams.net" modified="2026-11-02T03:30:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
xml.append('  <diagram id="cu34_comunicacion" name="CU34 - Comunicacion">')
xml.append(f'    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{svg_w}" pageHeight="{svg_h}" background="#FFFFFF" math="0" shadow="0">')
xml.append('      <root>')
xml.append('        <mxCell id="0" />')
xml.append('        <mxCell id="1" parent="0" />')

# Outer Frame
xml.append('        <mxCell id="frame_cd" value="cd CU34 - Consultar asistente comercial y recomendaciones" style="shape=umlFrame;whiteSpace=wrap;html=1;width=360;height=22;fillColor=none;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=11;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
xml.append(f'          <mxGeometry x="20" y="20" width="{svg_w-40}" height="{svg_h-40}" as="geometry" />')
xml.append('        </mxCell>')

# Nodes
for k, n in nodes.items():
    lbl = f"&lt;u&gt;{html.escape(n['label'])}&lt;/u&gt;"
    xml.append(f'        <mxCell id="node_{k}" value="{lbl}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.4;fontFamily=Arial;fontSize=11;fontColor=#000000;fontStyle=1;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" as="geometry" />')
    xml.append('        </mxCell>')

# Links
link_id = 100
for l in links:
    link_id += 1
    src = f"node_{l['n1']}"
    tgt = f"node_{l['n2']}"
    
    xml.append(f'        <mxCell id="link_{link_id}" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.3;" edge="1" parent="1" source="{src}" target="{tgt}">')
    xml.append('          <mxGeometry relative="1" as="geometry" />')
    xml.append('        </mxCell>')
    
    # Message label
    msg_lines = []
    for msg, direction, _ in l["msgs"]:
        arrow = " →" if direction in ("->", "top_branch", "bot_branch") else " ←"
        msg_lines.append(html.escape(msg + arrow))
    msg_html = "&lt;br/&gt;".join(msg_lines)
    
    xml.append(f'        <mxCell id="lbl_{link_id}" value="{msg_html}" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;fontColor=#000000;labelBackgroundColor=#FFFFFF;spacing=2;" vertex="1" connectable="0" parent="link_{link_id}">')
    xml.append('          <mxGeometry relative="1" as="geometry"><mxPoint as="offset" /></mxGeometry>')
    xml.append('        </mxCell>')

# Self-loops
# On ui: 13: renderizar_mensajes_y_tarjetas_inmuebles()
xml.append('        <mxCell id="loop_ui" value="13: renderizar_mensajes_y_tarjetas() ↺" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=none;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontColor=#000000;exitX=0.3;exitY=0;exitDx=0;exitDy=0;entryX=0.7;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="node_ui" target="node_ui">')
xml.append('          <mxGeometry x="0" y="25" relative="1" as="geometry"><Array as="points"><mxPoint x="340" y="240"/><mxPoint x="420" y="240"/></Array><mxPoint as="offset"/></mxGeometry>')
xml.append('        </mxCell>')

# On service: 8: generar_analisis_recomendaciones_ia()
xml.append('        <mxCell id="loop_service" value="8: generar_analisis_recomendaciones_ia() ↺" style="edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;endArrow=none;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontColor=#000000;exitX=0.3;exitY=0;exitDx=0;exitDy=0;entryX=0.7;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="node_service" target="node_service">')
xml.append('          <mxGeometry x="0" y="25" relative="1" as="geometry"><Array as="points"><mxPoint x="860" y="240"/><mxPoint x="950" y="240"/></Array><mxPoint as="offset"/></mxGeometry>')
xml.append('        </mxCell>')

xml.append('      </root>')
xml.append('    </mxGraphModel>')
xml.append('  </diagram>')
xml.append('</mxfile>')

drawio_file = "docs/diagramas/comunicacion_cu34_asistente_comercial.drawio"
with open(drawio_file, "w", encoding="utf-8") as f:
    f.write("\n".join(xml))
print(f"Generated {drawio_file}")

