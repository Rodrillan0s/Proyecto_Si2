import xml.etree.ElementTree as ET

xml = []
xml.append('<?xml version="1.0" encoding="UTF-8"?>')
xml.append('<mxfile host="app.diagrams.net" modified="2026-11-02T03:37:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
xml.append('  <diagram id="cu34_comunicacion_robustness" name="CU34 - Comunicacion">')
xml.append('    <mxGraphModel dx="1200" dy="600" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="400" background="#FFFFFF" math="0" shadow="0">')
xml.append('      <root>')
xml.append('        <mxCell id="0" />')
xml.append('        <mxCell id="1" parent="0" />')

# Title
xml.append('        <mxCell id="title" value="&lt;b&gt;Consultar Asistente Comercial y Recomendaciones (CU34)&lt;/b&gt;" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;fontSize=13;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="50" y="30" width="450" height="30" as="geometry" />')
xml.append('        </mxCell>')

# 1. Actor: Cliente Potencial
xml.append('        <mxCell id="actor_user" value="Cliente Potencial" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="60" y="150" width="30" height="60" as="geometry" />')
xml.append('        </mxCell>')

# 2. Boundary: IU_asistente
xml.append('        <mxCell id="b_iu" value="IU_asistente" style="shape=umlBoundary;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="220" y="145" width="90" height="70" as="geometry" />')
xml.append('        </mxCell>')

# 3. Control: ai_routes
xml.append('        <mxCell id="c_routes" value="ai_routes" style="shape=umlControl;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="410" y="145" width="75" height="75" as="geometry" />')
xml.append('        </mxCell>')

# 4. Control: crm_services
xml.append('        <mxCell id="c_services" value="crm_services" style="shape=umlControl;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="620" y="145" width="75" height="75" as="geometry" />')
xml.append('        </mxCell>')

# 5. Control: assistant_repos
xml.append('        <mxCell id="c_repos" value="assistant_repos" style="shape=umlControl;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="830" y="145" width="75" height="75" as="geometry" />')
xml.append('        </mxCell>')

# 6. Entity: database obras
xml.append('        <mxCell id="e_db" value="database&lt;br&gt;obras" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=10;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="1040" y="145" width="75" height="75" as="geometry" />')
xml.append('        </mxCell>')

# 7. Entity: t_asistente_conversacion (Up)
xml.append('        <mxCell id="e_asist" value="t_asistente_&lt;br&gt;conversacion" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="1230" y="55" width="75" height="75" as="geometry" />')
xml.append('        </mxCell>')

# 8. Entity: t_unidad_construccion (Middle)
xml.append('        <mxCell id="e_unid" value="t_unidad_&lt;br&gt;construccion" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="1230" y="145" width="75" height="75" as="geometry" />')
xml.append('        </mxCell>')

# 9. Entity: t_crm_cliente (Down)
xml.append('        <mxCell id="e_crm" value="t_crm_&lt;br&gt;cliente" style="shape=umlEntity;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.3;fontFamily=Arial;fontSize=9.5;fontStyle=1;fontColor=#000000;" vertex="1" parent="1">')
xml.append('          <mxGeometry x="1230" y="235" width="75" height="75" as="geometry" />')
xml.append('        </mxCell>')

# Edges with messages
# 1. Actor -> IU
xml.append('        <mxCell id="edge_user_iu" value="1. ingresarConsulta() →" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="actor_user" target="b_iu">')
xml.append('          <mxGeometry relative="1" as="geometry" />')
xml.append('        </mxCell>')

# 2. IU -> ai_routes
xml.append('        <mxCell id="edge_iu_routes" value="2. enviarConsulta(datos) →&lt;br&gt;← 6. mostrarResultados()" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="b_iu" target="c_routes">')
xml.append('          <mxGeometry relative="1" as="geometry" />')
xml.append('        </mxCell>')

# 3. ai_routes -> crm_services
xml.append('        <mxCell id="edge_routes_services" value="3. consultarCrmIa() →" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_routes" target="c_services">')
xml.append('          <mxGeometry relative="1" as="geometry" />')
xml.append('        </mxCell>')

# 4. crm_services -> assistant_repos
xml.append('        <mxCell id="edge_services_repos" value="4: validar y buscar inmuebles() →" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_services" target="c_repos">')
xml.append('          <mxGeometry relative="1" as="geometry" />')
xml.append('        </mxCell>')

# 5. assistant_repos -> database obras
xml.append('        <mxCell id="edge_repos_db" value="5: consultar unidades y guardar mensaje() →" style="endArrow=classic;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;fontSize=10;fontColor=#000000;fontFamily=Arial;labelPosition=center;verticalLabelPosition=top;verticalAlign=bottom;" edge="1" parent="1" source="c_repos" target="e_db">')
xml.append('          <mxGeometry relative="1" as="geometry" />')
xml.append('        </mxCell>')

# Database -> Entities
xml.append('        <mxCell id="edge_db_asist" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="e_db" target="e_asist">')
xml.append('          <mxGeometry relative="1" as="geometry" />')
xml.append('        </mxCell>')

xml.append('        <mxCell id="edge_db_unid" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="e_db" target="e_unid">')
xml.append('          <mxGeometry relative="1" as="geometry" />')
xml.append('        </mxCell>')

xml.append('        <mxCell id="edge_db_crm" value="" style="endArrow=none;html=1;rounded=0;strokeColor=#000000;strokeWidth=1.2;" edge="1" parent="1" source="e_db" target="e_crm">')
xml.append('          <mxGeometry relative="1" as="geometry" />')
xml.append('        </mxCell>')

xml.append('      </root>')
xml.append('    </mxGraphModel>')
xml.append('  </diagram>')
xml.append('</mxfile>')

drawio_path = "docs/diagramas/comunicacion_cu34_asistente_comercial.drawio"
with open(drawio_path, "w", encoding="utf-8") as f:
    f.write("\n".join(xml))
print(f"Generated {drawio_path}")

