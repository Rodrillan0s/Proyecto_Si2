import html
import xml.etree.ElementTree as ET
from collections import defaultdict
import csv

# Load Schema
tables = {}
fks = []

with open('docs/diagramas/schema_dump.tsv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        if not row or len(row) < 4:
            continue
        table = row[1].strip('"')
        if table in ('tabla', '<USER_REQUEST>'):
            continue
        attr = row[3].strip('"') if len(row) > 3 else ''
        tipo = row[4].strip('"') if len(row) > 4 else ''
        pk = (row[8].strip('"') if len(row) > 8 else '') == 'PK'
        fk = (row[9].strip('"') if len(row) > 9 else '') == 'FK'
        ref_table = row[10].strip('"') if len(row) > 10 else ''
        ref_attr = row[11].strip('"') if len(row) > 11 else ''

        if table not in tables:
            tables[table] = []
        tables[table].append({
            'attr': attr,
            'tipo': tipo,
            'pk': pk,
            'fk': fk,
            'ref_table': ref_table,
            'ref_attr': ref_attr
        })
        if fk and ref_table and ref_table != table:
            fks.append({
                'from_table': table,
                'from_col': attr,
                'to_table': ref_table,
                'to_col': ref_attr
            })

# Grid Layout (8 columns)
layout_grid = [
    # ROW 0
    ["t_plan_suscripcion", "t_plan_precio_saas", "t_plan_suscripcion_historial", "t_suscripcion_empresa", "t_empresa", "t_usuario", "t_seguridad_usuario", "t_persona"],
    # ROW 1
    ["t_suscripcion_cupo", "t_suscripcion_ia_uso", "t_suscripcion_historial", "t_pago_suscripcion", "t_rol", "t_rol_permiso", "t_permiso", "t_bitacora"],
    # ROW 2
    ["t_modulo", "t_tipo_obra", "t_obra", "t_detalle_obra", "t_estructura_obra", "t_obra_usuario", "t_avance_obra", "t_unidad_construccion"],
    # ROW 3
    ["t_consulta_tecnica", "t_consulta_tecnica_respuesta", "t_consulta_tecnica_historial", "t_incidencia", "t_incidencia_evidencia", "t_incidencia_seguimiento", "t_incidencia_orden_trabajo", "t_modelo_unidad"],
    # ROW 4
    ["t_cronograma", "t_cronograma_actividad", "t_cronograma_dependencia", "t_orden_trabajo", "t_orden_trabajo_usuario", "t_orden_trabajo_permiso", "t_usuario_orden_trabajo_permiso", "t_modelo_caracteristica"],
    # ROW 5
    ["t_control_costo_obra", "t_costo_ejecutado", "t_costo_ejecutado_legacy", "t_orden_cambio", "t_orden_cambio_detalle", "t_orden_cambio_historial", "t_unidad_ambiente", "t_unidad_caracteristica"],
    # ROW 6
    ["t_mano_obra", "t_salario_trabajador", "t_jornada_trabajador_obra", "t_cu32_mano_obra_cierre", "t_presupuesto", "t_partida_presupuesto", "t_unidad_medida", "t_unidad_material"],
    # ROW 7
    ["t_analisis_precio_unitario", "t_analisi_precio_unitario_insumo", "t_estimacion", "t_estimacion_analisis_precio_unitario", "t_parametro_estimacion", "t_obra_estimacion", "t_unidad_personalizacion", "t_unidad_seguimiento"],
    # ROW 8
    ["t_apu_detalle_mano_obra_archivo", "t_apu_legacy_archive", "t_categoria_material", "t_material_base", "t_material", "t_material_caracteristica", "t_crm_cliente", "t_crm_cliente_unidad"],
    # ROW 9
    ["t_materiales_almacen", "t_movimiento_almacen", "t_proveedor", "t_proveedor_material", "t_orden_compra", "t_orden_compra_detalle", "t_crm_interaccion", "notificacion"],
    # ROW 10
    ["t_recepcion_compra", "t_recepcion_compra_detalle", "t_equipo", "t_equipo_maquinaria", "t_equipo_maquinaria_obra", "t_asistente_conversacion", "t_asistente_mensaje", "t_reporte_ejecucion"],
    # ROW 11
    ["t_reporte_archivo", "t_reporte_envio", "t_reporte_programacion", "t_reporte_programacion_destinatario"]
]

card_w = 260
line_h = 24
header_h = 32
gap_x = 80
gap_y = 70
margin_x = 80
margin_y = 80
n_cols = 8

row_heights = defaultdict(int)
table_positions = {}

for r_idx, row in enumerate(layout_grid):
    for c_idx, t_name in enumerate(row):
        cols = tables.get(t_name, [])
        h = header_h + len(cols) * line_h + 8
        table_positions[t_name] = {
            'row': r_idx,
            'col': c_idx,
            'w': card_w,
            'h': h,
            'cols': cols
        }
        if h > row_heights[r_idx]:
            row_heights[r_idx] = h

total_w = margin_x * 2 + n_cols * card_w + (n_cols - 1) * gap_x
curr_y = margin_y

for r_idx in range(len(layout_grid)):
    for t_name, pos in table_positions.items():
        if pos['row'] == r_idx:
            pos['x'] = margin_x + pos['col'] * (card_w + gap_x)
            pos['y'] = curr_y
    curr_y += row_heights[r_idx] + gap_y

total_h = curr_y + 60

# Build Draw.io XML
xml_lines = []
xml_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
xml_lines.append('<mxfile host="app.diagrams.net" modified="2026-11-02T02:20:00.000Z" agent="Antigravity" version="24.0.0" type="device">')
xml_lines.append('  <diagram id="obratec_uml_db" name="Diagrama General de Clases (OBRATEC)">')
xml_lines.append(f'    <mxGraphModel dx="2000" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{int(total_w + 100)}" pageHeight="{int(total_h + 100)}" background="#F8FAFC" math="0" shadow="1">')
xml_lines.append('      <root>')
xml_lines.append('        <mxCell id="0" />')
xml_lines.append('        <mxCell id="1" parent="0" />')

cell_id_counter = 100

# 1. Create table cells
table_cell_ids = {}

for t_name, pos in table_positions.items():
    cell_id_counter += 1
    t_cell_id = f"cell_{t_name}"
    table_cell_ids[t_name] = t_cell_id
    
    x = int(pos['x'])
    y = int(pos['y'])
    w = int(pos['w'])
    h = int(pos['h'])
    
    # Table header container (UML Class swimlane style)
    title_escaped = html.escape(t_name.upper())
    swimlane_style = "swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=30;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E293B;strokeWidth=1.2;fontColor=#0F172A;fontFamily=Arial;fontSize=12;shadow=1;"
    
    xml_lines.append(f'        <mxCell id="{t_cell_id}" value="{title_escaped}" style="{swimlane_style}" vertex="1" parent="1">')
    xml_lines.append(f'          <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />')
    xml_lines.append('        </mxCell>')

    # Table columns (rows inside swimlane)
    curr_row_y = 30
    for c_idx, c in enumerate(pos['cols']):
        cell_id_counter += 1
        col_cell_id = f"col_{t_name}_{c_idx}"
        attr_name = c['attr']
        
        pk_str = " &lt;b style=&quot;color:#003366;&quot;&gt;[PK]&lt;/b&gt;" if c['pk'] else ""
        fk_str = " &lt;b style=&quot;color:#475569;&quot;&gt;[FK]&lt;/b&gt;" if c['fk'] else ""
        row_val = f"+ {attr_name}{pk_str}{fk_str}"
        
        row_style = "text;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;spacingLeft=8;spacingRight=6;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=11;fontColor=#1E293B;"
        if c['pk']:
            row_style += "fontStyle=1;"
            
        xml_lines.append(f'        <mxCell id="{col_cell_id}" value="{row_val}" style="{row_style}" vertex="1" parent="{t_cell_id}">')
        xml_lines.append(f'          <mxGeometry y="{curr_row_y}" width="{w}" height="{line_h}" as="geometry" />')
        xml_lines.append('        </mxCell>')
        curr_row_y += line_h

# 2. Create relationship edges
edge_counter = 0
for fk in fks:
    t_from = fk['from_table']
    t_to = fk['to_table']
    
    # Filter global tenant id_empresa and pervasive audit creator connections to keep diagram clean
    if t_to == 't_empresa' or (fk['from_col'] in ('creado_por', 'asignado_por', 'id_usuario') and t_to == 't_usuario' and t_from not in ('t_seguridad_usuario', 't_persona', 't_obra_usuario', 't_orden_trabajo_usuario')):
        continue
        
    if t_from in table_cell_ids and t_to in table_cell_ids:
        b1 = table_positions[t_from]
        b2 = table_positions[t_to]
        
        dr = abs(b1['row'] - b2['row'])
        dc = abs(b1['col'] - b2['col'])
        if dr + dc <= 4:
            edge_counter += 1
            e_id = f"edge_{edge_counter}"
            source_id = table_cell_ids[t_from]
            target_id = table_cell_ids[t_to]
            
            # Determine ports
            if b1['col'] < b2['col']:
                exit_port = "exitX=1;exitY=0.3;exitDx=0;exitDy=0;"
                entry_port = "entryX=0;entryY=0.3;entryDx=0;entryDy=0;"
            elif b1['col'] > b2['col']:
                exit_port = "exitX=0;exitY=0.3;exitDx=0;exitDy=0;"
                entry_port = "entryX=1;entryY=0.3;entryDx=0;entryDy=0;"
            else:
                if b1['row'] < b2['row']:
                    exit_port = "exitX=0.5;exitY=1;exitDx=0;exitDy=0;"
                    entry_port = "entryX=0.5;entryY=0;entryDx=0;entryDy=0;"
                else:
                    exit_port = "exitX=0.5;exitY=0;exitDx=0;entryDy=0;"
                    entry_port = "entryX=0.5;entryY=1;entryDx=0;entryDy=0;"
                    
            edge_style = f"edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#475569;strokeWidth=1.3;{exit_port}{entry_port}"
            
            xml_lines.append(f'        <mxCell id="{e_id}" value="" style="{edge_style}" edge="1" parent="1" source="{source_id}" target="{target_id}">')
            xml_lines.append('          <mxGeometry relative="1" as="geometry" />')
            xml_lines.append('        </mxCell>')
            
            # Cardinality labels at source (0..*) and target (1)
            xml_lines.append(f'        <mxCell id="{e_id}_src" value="0..*" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;fontStyle=1;fontColor=#1E293B;labelBackgroundColor=#FFFFFF;" vertex="1" connectable="0" parent="{e_id}">')
            xml_lines.append('          <mxGeometry x="-0.8" relative="1" as="geometry">')
            xml_lines.append('            <mxPoint as="offset" />')
            xml_lines.append('          </mxGeometry>')
            xml_lines.append('        </mxCell>')
            
            xml_lines.append(f'        <mxCell id="{e_id}_tgt" value="1" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];fontSize=10;fontStyle=1;fontColor=#1E293B;labelBackgroundColor=#FFFFFF;" vertex="1" connectable="0" parent="{e_id}">')
            xml_lines.append('          <mxGeometry x="0.8" relative="1" as="geometry">')
            xml_lines.append('            <mxPoint as="offset" />')
            xml_lines.append('          </mxGeometry>')
            xml_lines.append('        </mxCell>')

xml_lines.append('      </root>')
xml_lines.append('    </mxGraphModel>')
xml_lines.append('  </diagram>')
xml_lines.append('</mxfile>')

drawio_content = "\n".join(xml_lines)

# Write .drawio file
out_drawio = "docs/diagramas/diagrama_clases_completo.drawio"
with open(out_drawio, "w", encoding="utf-8") as f:
    f.write(drawio_content)

print(f"Draw.io file generated: {out_drawio} ({len(drawio_content)} bytes)")

