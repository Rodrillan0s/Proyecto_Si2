import os
import html
from generate_analysis_diagrams import diagrams_data

def build_drawio_diagram_xml(d, diagram_id):
    xml = []
    xml.append(f'  <diagram id="{diagram_id}" name="{d["tab_name"]}">')
    xml.append('    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="800" background="#FFFFFF" math="0" shadow="0">')
    xml.append('      <root>')
    xml.append('        <mxCell id="0" />')
    xml.append('        <mxCell id="1" parent="0" />')

    # Helper to construct HTML for class card
    def format_box_value(title, attrs, methods):
        parts = [f'<p style="margin:0px;padding-top:4px;text-align:center;"><b>{html.escape(title)}</b></p>']
        if attrs:
            parts.append('<hr style="border:none;border-top:1px solid #000000;margin:4px 0px;"/>')
            attrs_html = "<br/>".join(html.escape(a) for a in attrs)
            parts.append(f'<div style="padding:2px 8px;text-align:left;font-family:Arial;font-size:11px;">{attrs_html}</div>')
        if methods:
            parts.append('<hr style="border:none;border-top:1px solid #000000;margin:4px 0px;"/>')
            methods_html = "<br/>".join(html.escape(m) for m in methods)
            parts.append(f'<div style="padding:2px 8px;text-align:left;font-family:Arial;font-size:11px;">{methods_html}</div>')
        return "".join(parts)

    def calc_h(attrs, methods):
        h = 32 + (len(attrs) * 18 + 10 if attrs else 20) + (len(methods) * 18 + 10 if methods else 0)
        return max(70, h)

    # 1. Cells
    # Form
    f_h = calc_h(d['form']['attrs'], d['form']['methods'])
    xml.append(f'        <mxCell id="cell_form" value="{html.escape(format_box_value(d["form"]["title"], d["form"]["attrs"], d["form"]["methods"]))}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="40" y="220" width="220" height="{f_h}" as="geometry" />')
    xml.append('        </mxCell>')

    # Control
    c_h = calc_h(d['control']['attrs'], d['control']['methods'])
    xml.append(f'        <mxCell id="cell_control" value="{html.escape(format_box_value(d["control"]["title"], d["control"]["attrs"], d["control"]["methods"]))}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="300" y="240" width="200" height="{c_h}" as="geometry" />')
    xml.append('        </mxCell>')

    # Main Entity
    m_h = calc_h(d['main_entity']['attrs'], d['main_entity']['methods'])
    xml.append(f'        <mxCell id="cell_main" value="{html.escape(format_box_value(d["main_entity"]["title"], d["main_entity"]["attrs"], d["main_entity"]["methods"]))}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="550" y="220" width="180" height="{m_h}" as="geometry" />')
    xml.append('        </mxCell>')

    # Top
    t_h = calc_h(d['related_top']['attrs'], d['related_top']['methods'])
    xml.append(f'        <mxCell id="cell_top" value="{html.escape(format_box_value(d["related_top"]["title"], d["related_top"]["attrs"], d["related_top"]["methods"]))}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="565" y="45" width="150" height="{t_h}" as="geometry" />')
    xml.append('        </mxCell>')

    # Right
    r_h = calc_h(d['related_right']['attrs'], d['related_right']['methods'])
    xml.append(f'        <mxCell id="cell_right" value="{html.escape(format_box_value(d["related_right"]["title"], d["related_right"]["attrs"], d["related_right"]["methods"]))}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="790" y="220" width="180" height="{r_h}" as="geometry" />')
    xml.append('        </mxCell>')

    # Bottom (Empresa)
    b_h = calc_h(d['related_bottom']['attrs'], d['related_bottom']['methods'])
    xml.append(f'        <mxCell id="cell_bottom" value="{html.escape(format_box_value(d["related_bottom"]["title"], d["related_bottom"]["attrs"], d["related_bottom"]["methods"]))}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="565" y="490" width="150" height="{b_h}" as="geometry" />')
    xml.append('        </mxCell>')

    # Extra
    e_h = calc_h(d['related_extra']['attrs'], d['related_extra']['methods'])
    xml.append(f'        <mxCell id="cell_extra" value="{html.escape(format_box_value(d["related_extra"]["title"], d["related_extra"]["attrs"], d["related_extra"]["methods"]))}" style="html=1;whiteSpace=wrap;overflow=hidden;rounded=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontColor=#000000;verticalAlign=top;align=center;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="790" y="440" width="190" height="{e_h}" as="geometry" />')
    xml.append('        </mxCell>')

    # 2. Edges
    # Edge Form -> Control
    xml.append('        <mxCell id="edge_fc" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.3;exitX=1;exitY=0.4;exitDx=0;exitDy=0;entryX=0;entryY=0.4;entryDx=0;entryDy=0;" edge="1" parent="1" source="cell_form" target="cell_control">')
    xml.append('          <mxGeometry relative="1" as="geometry" />')
    xml.append('        </mxCell>')

    # Edge Control -> Main Entity
    xml.append('        <mxCell id="edge_cm" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.3;exitX=1;exitY=0.4;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;" edge="1" parent="1" source="cell_control" target="cell_main">')
    xml.append('          <mxGeometry relative="1" as="geometry" />')
    xml.append('        </mxCell>')

    # Edge Main -> Top
    xml.append(f'        <mxCell id="edge_mt" value="{d["related_top"]["card_rel"]}" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.3;exitX=0.5;exitY=0;exitDx=0;exitDy=0;entryX=0.5;entryY=1;entryDx=0;entryDy=0;fontSize=11;fontColor=#000000;" edge="1" parent="1" source="cell_main" target="cell_top">')
    xml.append('          <mxGeometry relative="1" as="geometry">')
    xml.append('            <mxPoint as="offset" />')
    xml.append('          </mxGeometry>')
    xml.append('        </mxCell>')

    # Edge Main -> Right
    xml.append(f'        <mxCell id="edge_mr" value="{d["related_right"]["card_rel"]}" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.3;exitX=1;exitY=0.3;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;fontSize=11;fontColor=#000000;" edge="1" parent="1" source="cell_main" target="cell_right">')
    xml.append('          <mxGeometry relative="1" as="geometry">')
    xml.append('            <mxPoint as="offset" />')
    xml.append('          </mxGeometry>')
    xml.append('        </mxCell>')

    # Edge Main -> Bottom (Diamond Aggregation)
    xml.append(f'        <mxCell id="edge_mb" value="{d["related_bottom"]["card_rel"]}" style="endArrow=none;startArrow=diamond;startFill=0;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.3;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;fontSize=11;fontColor=#000000;" edge="1" parent="1" source="cell_main" target="cell_bottom">')
    xml.append('          <mxGeometry relative="1" as="geometry">')
    xml.append('            <mxPoint as="offset" />')
    xml.append('          </mxGeometry>')
    xml.append('        </mxCell>')

    # Edge Main -> Extra
    xml.append(f'        <mxCell id="edge_me" value="{d["related_extra"]["card_rel"]}" style="edgeStyle=orthogonalEdgeStyle;endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.3;exitX=1;exitY=0.7;exitDx=0;exitDy=0;entryX=0;entryY=0.3;entryDx=0;entryDy=0;fontSize=11;fontColor=#000000;" edge="1" parent="1" source="cell_main" target="cell_extra">')
    xml.append('          <mxGeometry relative="1" as="geometry">')
    xml.append('            <mxPoint as="offset" />')
    xml.append('          </mxGeometry>')
    xml.append('        </mxCell>')

    xml.append('      </root>')
    xml.append('    </mxGraphModel>')
    xml.append('  </diagram>')
    return "\n".join(xml)

# 1. Generate individual .drawio files
for cu_key, d in diagrams_data.items():
    file_xml = []
    file_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
    file_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-02T03:00:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
    file_xml.append(build_drawio_diagram_xml(d, d['id']))
    file_xml.append('</mxfile>')
    
    file_path = f"docs/diagramas/{d['id']}.drawio"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(file_xml))
    print(f"Generated Draw.io file: {file_path}")

# 2. Generate consolidated multi-tab .drawio file
consolidated_xml = []
consolidated_xml.append('<?xml version="1.0" encoding="UTF-8"?>')
consolidated_xml.append('<mxfile host="app.diagrams.net" modified="2026-11-02T03:00:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
for cu_key, d in diagrams_data.items():
    consolidated_xml.append(build_drawio_diagram_xml(d, d['id']))
consolidated_xml.append('</mxfile>')

multi_path = "docs/diagramas/analisis_clases_cu35_cu36_cu23_cu34.drawio"
with open(multi_path, "w", encoding="utf-8") as f:
    f.write("\n".join(consolidated_xml))
print(f"Generated multi-tab Draw.io file: {multi_path}")

