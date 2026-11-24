import os
import html
from generate_sequence_diagrams import sequence_data

def build_drawio_sequence_xml(d, diagram_id):
    xml = []
    xml.append(f'  <diagram id="{diagram_id}" name="{d["tab_name"]}">')
    xml.append('    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="800" background="#FFFFFF" math="0" shadow="0">')
    xml.append('      <root>')
    xml.append('        <mxCell id="0" />')
    xml.append('        <mxCell id="1" parent="0" />')

    # Lifelines layout
    ll_w = 150
    gap = 25
    margin_l = 45
    header_box_h = 36
    
    col_x = []
    col_x.append(margin_l + 35) # actor center
    curr_x = margin_l + 70 + gap
    for ll in d["lifelines"]:
        col_x.append(curr_x + ll_w / 2.0)
        curr_x += ll_w + gap

    total_w = curr_x + 30
    row_h = 28
    events = d["events"]
    content_top = 40 + 65
    total_h = content_top + len(events) * row_h + 80

    # 1. Outer Frame
    sd_title = html.escape(d["sd_tag"])
    tag_w = len(d["sd_tag"]) * 7.5 + 24
    xml.append(f'        <mxCell id="frame_sd" value="{sd_title}" style="shape=umlFrame;whiteSpace=wrap;html=1;width={int(tag_w)};height=22;fillColor=none;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=11;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="15" y="15" width="{int(total_w-30)}" height="{int(total_h-30)}" as="geometry" />')
    xml.append('        </mxCell>')

    # 2. Actor Lifeline
    act_cx = col_x[0]
    act_name = html.escape(d["actor"])
    xml.append(f'        <mxCell id="ll_actor" value="{act_name}" style="shape=umlLifeline;participant=umlActor;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=10;fontColor=#000000;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="{int(act_cx-20)}" y="50" width="40" height="{int(total_h-100)}" as="geometry" />')
    xml.append('        </mxCell>')

    # 3. Object Lifelines
    for idx, ll in enumerate(d["lifelines"]):
        cx = col_x[idx+1]
        bx = cx - ll_w / 2.0
        ll_name = html.escape(ll["name"])
        xml.append(f'        <mxCell id="ll_{ll["id"]}" value="{ll_name}" style="shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=11;fontColor=#000000;rounded=1;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{int(bx)}" y="60" width="{ll_w}" height="{int(total_h-110)}" as="geometry" />')
        xml.append('        </mxCell>')

    # 4. Events / Messages
    curr_y = content_top + 20
    edge_id = 100
    alt_start_y = None
    alt_else_y = None
    alt_cond_text = ""
    alt_else_text = ""

    for ev in events:
        ev_type = ev["type"]
        if ev_type == "alt_start":
            alt_start_y = curr_y - 12
            alt_cond_text = ev["cond"]
            curr_y += 10
            continue
        elif ev_type == "alt_else":
            alt_else_y = curr_y - 10
            alt_else_text = ev["cond"]
            curr_y += 15
            continue
        elif ev_type == "alt_end":
            alt_end_y = curr_y + 10
            ab_x = col_x[2] - 40
            ab_w = (col_x[5] if len(col_x) > 5 else col_x[-1]) - ab_x + 40
            ab_h = alt_end_y - alt_start_y
            xml.append(f'        <mxCell id="alt_box" value="alt {html.escape(alt_cond_text)}" style="shape=umlFrame;whiteSpace=wrap;html=1;width=140;height=20;fillColor=none;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
            xml.append(f'          <mxGeometry x="{int(ab_x)}" y="{int(alt_start_y)}" width="{int(ab_w)}" height="{int(ab_h)}" as="geometry" />')
            xml.append('        </mxCell>')
            if alt_else_y:
                xml.append(f'        <mxCell id="alt_else_line" value="{html.escape(alt_else_text)}" style="strokeColor=#000000;strokeWidth=1.2;dashed=1;endArrow=none;html=1;fontFamily=Arial;fontSize=10;fontStyle=1;align=left;spacingLeft=8;" edge="1" parent="1">')
                xml.append(f'          <mxGeometry relative="1" as="geometry"><mxPoint x="{int(ab_x)}" y="{int(alt_else_y)}" as="sourcePoint"/><mxPoint x="{int(ab_x+ab_w)}" y="{int(alt_else_y)}" as="targetPoint"/></mxGeometry>')
                xml.append('        </mxCell>')
            curr_y += 15
            continue

        edge_id += 1
        msg_text = html.escape(ev["text"])

        if ev_type == "msg":
            x1 = col_x[ev["from"]]
            x2 = col_x[ev["to"]]
            xml.append(f'        <mxCell id="edge_{edge_id}" value="{msg_text}" style="html=1;verticalAlign=bottom;endArrow=block;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=10;fontColor=#000000;" edge="1" parent="1">')
            xml.append(f'          <mxGeometry relative="1" as="geometry"><mxPoint x="{int(x1)}" y="{int(curr_y)}" as="sourcePoint"/><mxPoint x="{int(x2)}" y="{int(curr_y)}" as="targetPoint"/></mxGeometry>')
            xml.append('        </mxCell>')
            curr_y += row_h

        elif ev_type == "ret":
            x1 = col_x[ev["from"]]
            x2 = col_x[ev["to"]]
            xml.append(f'        <mxCell id="edge_{edge_id}" value="{msg_text}" style="html=1;verticalAlign=bottom;endArrow=open;dashed=1;endSize=8;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=10;fontStyle=2;fontColor=#000000;" edge="1" parent="1">')
            xml.append(f'          <mxGeometry relative="1" as="geometry"><mxPoint x="{int(x1)}" y="{int(curr_y)}" as="sourcePoint"/><mxPoint x="{int(x2)}" y="{int(curr_y)}" as="targetPoint"/></mxGeometry>')
            xml.append('        </mxCell>')
            curr_y += row_h

        elif ev_type == "self":
            cx = col_x[ev["at"]]
            xml.append(f'        <mxCell id="edge_{edge_id}" value="{msg_text}" style="html=1;align=left;spacingLeft=5;verticalAlign=bottom;endArrow=block;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontFamily=Arial;fontSize=10;fontColor=#000000;edgeStyle=orthogonalEdgeStyle;" edge="1" parent="1">')
            xml.append(f'          <mxGeometry relative="1" as="geometry"><mxPoint x="{int(cx)}" y="{int(curr_y)}" as="sourcePoint"/><mxPoint x="{int(cx)}" y="{int(curr_y+14)}" as="targetPoint"/><Array as="points"><mxPoint x="{int(cx+20)}" y="{int(curr_y)}"/><mxPoint x="{int(cx+20)}" y="{int(curr_y+14)}"/></Array></mxGeometry>')
            xml.append('        </mxCell>')
            curr_y += row_h

    xml.append('      </root>')
    xml.append('    </mxGraphModel>')
    xml.append('  </diagram>')
    return "\n".join(xml)

# 1. Generate individual .drawio files
for cu_key, d in sequence_data.items():
    file_xml = []
    file_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
    file_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-02T03:08:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
    file_xml.append(build_drawio_sequence_xml(d, d['id']))
    file_xml.append('</mxfile>')
    
    file_path = f"docs/diagramas/{d['id']}.drawio"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(file_xml))
    print(f"Generated Draw.io sequence file: {file_path}")

# 2. Generate consolidated multi-tab .drawio file
consolidated_xml = []
consolidated_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
consolidated_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-02T03:08:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
for cu_key, d in sequence_data.items():
    consolidated_xml.append(build_drawio_sequence_xml(d, d['id']))
consolidated_xml.append('</mxfile>')

multi_path = "docs/diagramas/secuencia_clases_cu35_cu36_cu23_cu34.drawio"
with open(multi_path, "w", encoding="utf-8") as f:
    f.write("\n".join(consolidated_xml))
print(f"Generated multi-tab Draw.io sequence file: {multi_path}")

