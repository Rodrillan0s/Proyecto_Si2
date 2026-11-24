import html
import os

os.makedirs('docs/diagramas/c4', exist_ok=True)

# Define the 4 C4 Component diagrams for Draw.io
domains_c4 = [
    {
        "id": "c4_obras_costos",
        "tab": "Obras y Costos",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Obras y Control de Costos",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Interfaz web para administración técnica", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "App móvil operativa para supervisión", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"name": "API Backend [FastAPI + Uvicorn]", "x": 100, "y": 200, "w": 880, "h": 460},
        "components": [
            {"id": "c1", "name": "Obra Controller", "type": "FastAPI Router", "desc": "Rutas REST para proyectos y estructuras", "x": 150, "y": 260, "w": 210, "h": 80},
            {"id": "c2", "name": "Control Costos Controller", "type": "FastAPI Router", "desc": "Rutas para costos y estimaciones", "x": 430, "y": 260, "w": 220, "h": 80},
            {"id": "c3", "name": "Consulta Técnica Controller", "type": "FastAPI Router", "desc": "Rutas para ciclo de vida de RFIs", "x": 710, "y": 260, "w": 220, "h": 80},
            
            {"id": "s1", "name": "Obra Service", "type": "Python Service", "desc": "Lógica de obras y estructuras", "x": 150, "y": 390, "w": 210, "h": 80},
            {"id": "s2", "name": "Control Costos Service", "type": "Python Service", "desc": "Cálculo de desviaciones y costos", "x": 430, "y": 390, "w": 220, "h": 80},
            {"id": "s3", "name": "Consulta Técnica Service", "type": "Python Service", "desc": "Gestión de estados y trazabilidad RFI", "x": 710, "y": 390, "w": 220, "h": 80},

            {"id": "r1", "name": "Obras Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de proyectos y avances", "x": 150, "y": 520, "w": 210, "h": 80},
            {"id": "r2", "name": "Costos Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de costos y órdenes", "x": 430, "y": 520, "w": 220, "h": 80},
            {"id": "r3", "name": "Consulta Técnica Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de consultas y respuestas", "x": 710, "y": 520, "w": 220, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Almacena proyectos, costos y RFIs", "x": 390, "y": 720, "w": 290, "h": 90}
        ],
        "externals": [],
        "links": [
            ("web", "c1", "Gestiona obras [JSON/HTTPS]"),
            ("web", "c2", "Audita costos [JSON/HTTPS]"),
            ("web", "c3", "Gestiona RFIs [JSON/HTTPS]"),
            ("mobile", "c1", "Consulta proyectos [JSON/HTTPS]"),
            ("mobile", "c3", "Reporta RFIs [JSON/HTTPS]"),
            ("c1", "s1", "Delega lógica"),
            ("c2", "s2", "Delega cálculo"),
            ("c3", "s3", "Delega flujo RFI"),
            ("s1", "r1", "Persiste obras"),
            ("s2", "r2", "Persiste costos"),
            ("s3", "r3", "Persiste consultas"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP"),
            ("r3", "db", "SQL/TCP")
        ]
    },
    {
        "id": "c4_inventario_compras",
        "tab": "Inventario y Compras",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Inventario, Compras y Materiales",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Gestión de compras y catálogo", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Recepciones y salidas en obra", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"name": "API Backend [FastAPI + Uvicorn]", "x": 100, "y": 200, "w": 880, "h": 460},
        "components": [
            {"id": "c1", "name": "Inventario Controller", "type": "FastAPI Router", "desc": "Rutas para stock y ajustes (CU35/36)", "x": 150, "y": 260, "w": 210, "h": 80},
            {"id": "c2", "name": "Compras Controller", "type": "FastAPI Router", "desc": "Rutas para órdenes de compra", "x": 430, "y": 260, "w": 220, "h": 80},
            {"id": "c3", "name": "Material Controller", "type": "FastAPI Router", "desc": "Rutas para catálogo de materiales", "x": 710, "y": 260, "w": 220, "h": 80},
            
            {"id": "s1", "name": "Inventario Service", "type": "Python Service", "desc": "Kardex, validación de stock y auditoría", "x": 150, "y": 390, "w": 210, "h": 80},
            {"id": "s2", "name": "Compras Service", "type": "Python Service", "desc": "Aprobaciones y control de recepciones", "x": 430, "y": 390, "w": 220, "h": 80},
            {"id": "s3", "name": "Material Service", "type": "Python Service", "desc": "Precios y categorías de insumos", "x": 710, "y": 390, "w": 220, "h": 80},

            {"id": "r1", "name": "Inventario Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Kardex y t_movimiento_almacen", "x": 150, "y": 520, "w": 210, "h": 80},
            {"id": "r2", "name": "Compras Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Órdenes y recepciones de compra", "x": 430, "y": 520, "w": 220, "h": 80},
            {"id": "r3", "name": "Material Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Tablas de materiales y unidades", "x": 710, "y": 520, "w": 220, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Almacena materiales, compras y almacén", "x": 390, "y": 720, "w": 290, "h": 90}
        ],
        "externals": [],
        "links": [
            ("web", "c1", "Gestiona stock [JSON/HTTPS]"),
            ("web", "c2", "Emite órdenes [JSON/HTTPS]"),
            ("web", "c3", "Administra catálogo [JSON/HTTPS]"),
            ("mobile", "c1", "Entradas y salidas [JSON/HTTPS]"),
            ("mobile", "c2", "Recepciona insumos [JSON/HTTPS]"),
            ("c1", "s1", "Delega ajuste"),
            ("c2", "s2", "Delega compra"),
            ("c3", "s3", "Delega catálogo"),
            ("s1", "r1", "Persiste kardex"),
            ("s2", "r2", "Persiste orden"),
            ("s2", "r1", "Actualiza stock"),
            ("s3", "r3", "Actualiza insumo"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP"),
            ("r3", "db", "SQL/TCP")
        ]
    },
    {
        "id": "c4_seguridad_pagos",
        "tab": "Seguridad y Pagos SaaS",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Seguridad, Suscripciones y Pagos SaaS",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Portal SaaS y gestión de cuenta", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Login y control de acceso", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"name": "API Backend [FastAPI + Uvicorn]", "x": 70, "y": 200, "w": 960, "h": 460},
        "components": [
            {"id": "c1", "name": "Auth Controller", "type": "FastAPI Router", "desc": "Login, refresh token y perfil", "x": 100, "y": 260, "w": 200, "h": 80},
            {"id": "c2", "name": "Suscripción Controller", "type": "FastAPI Router", "desc": "Gestión de planes y cupos", "x": 350, "y": 260, "w": 200, "h": 80},
            {"id": "c3", "name": "Pagos Controller", "type": "FastAPI Router", "desc": "Checkout y webhooks Stripe", "x": 600, "y": 260, "w": 200, "h": 80},
            
            {"id": "s1", "name": "Auth Service", "type": "Python Service", "desc": "JWT, RBAC y barrera tenant", "x": 100, "y": 390, "w": 200, "h": 80},
            {"id": "s2", "name": "Suscripción Service", "type": "Python Service", "desc": "Límites SaaS y vigencias", "x": 350, "y": 390, "w": 200, "h": 80},
            {"id": "s3", "name": "Pagos Service", "type": "Python Service", "desc": "Cobros y renovación de planes", "x": 600, "y": 390, "w": 200, "h": 80},
            {"id": "a1", "name": "Stripe Gateway Adapter", "type": "Python Client", "desc": "Cliente SDK Stripe", "x": 820, "y": 390, "w": 180, "h": 80},

            {"id": "r1", "name": "Auth Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Usuarios, credenciales y roles", "x": 100, "y": 520, "w": 200, "h": 80},
            {"id": "r2", "name": "Suscripción Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Planes y suscripciones empresa", "x": 350, "y": 520, "w": 200, "h": 80},
            {"id": "r3", "name": "Pagos Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Transacciones y recibos", "x": 600, "y": 520, "w": 200, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste usuarios, empresas y pagos", "x": 270, "y": 720, "w": 290, "h": 90}
        ],
        "externals": [
            {"id": "stripe", "name": "Stripe API", "type": "Servicio Externo", "desc": "Pasarela de pagos en línea", "x": 750, "y": 720, "w": 230, "h": 90}
        ],
        "links": [
            ("web", "c1", "Login y usuarios [JSON/HTTPS]"),
            ("web", "c2", "Cambio de plan [JSON/HTTPS]"),
            ("web", "c3", "Pago checkout [JSON/HTTPS]"),
            ("mobile", "c1", "Login móvil [JSON/HTTPS]"),
            ("c1", "s1", "Valida JWT"),
            ("c2", "s2", "Verifica cuotas"),
            ("c3", "s3", "Procesa cobro"),
            ("s3", "a1", "Ejecuta cargo"),
            ("s3", "s2", "Renueva plan"),
            ("a1", "stripe", "HTTPS/REST"),
            ("s1", "r1", "Persiste usuario"),
            ("s2", "r2", "Persiste cupo"),
            ("s3", "r3", "Persiste pago"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP"),
            ("r3", "db", "SQL/TCP")
        ]
    },
    {
        "id": "c4_ia_crm_reportes",
        "tab": "IA, CRM y Reportes",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Inteligencia Artificial, CRM y Reportes",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Asistente web y reportería", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Consultas y alertas operativas", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"name": "API Backend [FastAPI + Uvicorn]", "x": 70, "y": 200, "w": 960, "h": 460},
        "components": [
            {"id": "c1", "name": "AI & CRM Controller", "type": "FastAPI Router", "desc": "Rutas de chat IA y prospectos", "x": 180, "y": 260, "w": 230, "h": 80},
            {"id": "c2", "name": "Reportes Controller", "type": "FastAPI Router", "desc": "Rutas de generación de reportes", "x": 580, "y": 260, "w": 230, "h": 80},
            
            {"id": "s1", "name": "AI Engine Service", "type": "Python Service", "desc": "Orquestación de prompts y contexto", "x": 100, "y": 390, "w": 200, "h": 80},
            {"id": "s2", "name": "CRM Service", "type": "Python Service", "desc": "Calificación e interacciones cliente", "x": 330, "y": 390, "w": 200, "h": 80},
            {"id": "s3", "name": "Reportes Service", "type": "Python Service", "desc": "Compilación PDF/Excel y métricas", "x": 580, "y": 390, "w": 200, "h": 80},
            {"id": "a1", "name": "Gemini Adapter", "type": "Python Client", "desc": "SDK LLM Google Gemini", "x": 800, "y": 390, "w": 180, "h": 80},

            {"id": "r1", "name": "AI Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Sesiones y mensajes de chat", "x": 100, "y": 520, "w": 200, "h": 80},
            {"id": "r2", "name": "CRM Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Clientes, interacciones y unidades", "x": 330, "y": 520, "w": 200, "h": 80},
            {"id": "r3", "name": "Reportes Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Ejecuciones y archivos generados", "x": 580, "y": 520, "w": 200, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste mensajes, CRM y reportes", "x": 270, "y": 720, "w": 290, "h": 90}
        ],
        "externals": [
            {"id": "gemini", "name": "Gemini API", "type": "Servicio Externo", "desc": "Modelo LLM de lenguaje natural", "x": 750, "y": 720, "w": 230, "h": 90}
        ],
        "links": [
            ("web", "c1", "Chat y CRM [JSON/HTTPS]"),
            ("web", "c2", "Descarga reportes [JSON/HTTPS]"),
            ("mobile", "c1", "Consulta IA [JSON/HTTPS]"),
            ("c1", "s1", "Delega consulta IA"),
            ("c1", "s2", "Delega prospectos"),
            ("c2", "s3", "Genera reporte"),
            ("s1", "a1", "Inferencia LLM"),
            ("a1", "gemini", "HTTPS/REST"),
            ("s1", "r1", "Persiste chat"),
            ("s2", "r2", "Persiste cliente"),
            ("s3", "r3", "Persiste log"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP"),
            ("r3", "db", "SQL/TCP")
        ]
    }
]

# Build Consolidated Draw.io XML
xml = []
xml.append('<?xml version="1.0" encoding="UTF-8"?>')
xml.append('<mxfile host="app.diagrams.net" modified="2026-11-22T12:00:00.000Z" agent="Antigravity" version="24.0.0" type="device">')

for dom in domains_c4:
    xml.append(f'  <diagram id="{dom["id"]}" name="{dom["tab"]}">')
    xml.append('    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="900" background="#FFFFFF" math="0" shadow="0">')
    xml.append('      <root>')
    xml.append('        <mxCell id="0" />')
    xml.append('        <mxCell id="1" parent="0" />')

    # Title
    t_val = f"&lt;b style=&quot;font-size:14px;&quot;&gt;{html.escape(dom['title'])}&lt;/b&gt;"
    xml.append(f'        <mxCell id="title_{dom["id"]}" value="{t_val}" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;" vertex="1" parent="1">')
    xml.append('          <mxGeometry x="50" y="20" width="700" height="30" as="geometry" />')
    xml.append('        </mxCell>')

    # Consumers (Top)
    for c in dom["consumers"]:
        val = f"&lt;b&gt;{html.escape(c['name'])}&lt;/b&gt;&lt;br/&gt;&lt;i style=&quot;font-size:10px;&quot;&gt;[{html.escape(c['tech'])}]&lt;/i&gt;&lt;br/&gt;&lt;span style=&quot;font-size:9.5px;&quot;&gt;{html.escape(c['desc'])}&lt;/span&gt;"
        xml.append(f'        <mxCell id="{c["id"]}" value="{val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2B6CB0;strokeColor=#1A365D;strokeWidth=1.3;fontFamily=Arial;fontColor=#FFFFFF;align=center;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{c["x"]}" y="{c["y"]}" width="{c["w"]}" height="{c["h"]}" as="geometry" />')
        xml.append('        </mxCell>')

    # Container Boundary
    b = dom["boundary"]
    b_val = f"&lt;b&gt;Container:&lt;/b&gt; {html.escape(b['name'])}"
    xml.append(f'        <mxCell id="boundary" value="{b_val}" style="swimlane;fontStyle=1;align=left;spacingLeft=10;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=0;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#4A5568;strokeWidth=1.5;strokeDasharray=4 4;fontFamily=Arial;fontSize=11;fontColor=#2D3748;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" as="geometry" />')
    xml.append('        </mxCell>')

    # Internal Components
    for comp in dom["components"]:
        c_val = f"&lt;b style=&quot;font-size:11px;&quot;&gt;{html.escape(comp['name'])}&lt;/b&gt;&lt;br/&gt;&lt;i style=&quot;font-size:9.5px;&quot;&gt;[Component: {html.escape(comp['type'])}]&lt;/i&gt;&lt;br/&gt;&lt;span style=&quot;font-size:9px;&quot;&gt;{html.escape(comp['desc'])}&lt;/span&gt;"
        xml.append(f'        <mxCell id="{comp["id"]}" value="{c_val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#4299E1;strokeColor=#2B6CB0;strokeWidth=1.2;fontFamily=Arial;fontColor=#FFFFFF;align=center;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{comp["x"]}" y="{comp["y"]}" width="{comp["w"]}" height="{comp["h"]}" as="geometry" />')
        xml.append('        </mxCell>')

    # Persistence (Bottom)
    for p in dom["persistence"]:
        p_val = f"&lt;b style=&quot;font-size:11px;&quot;&gt;{html.escape(p['name'])}&lt;/b&gt;&lt;br/&gt;&lt;i style=&quot;font-size:9.5px;&quot;&gt;[ContainerDb: {html.escape(p['type'])}]&lt;/i&gt;&lt;br/&gt;&lt;span style=&quot;font-size:9px;&quot;&gt;{html.escape(p['desc'])}&lt;/span&gt;"
        xml.append(f'        <mxCell id="{p["id"]}" value="{p_val}" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#2B6CB0;strokeColor=#1A365D;strokeWidth=1.2;fontFamily=Arial;fontColor=#FFFFFF;align=center;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{p["x"]}" y="{p["y"]}" width="{p["w"]}" height="{p["h"]}" as="geometry" />')
        xml.append('        </mxCell>')

    # External Systems (Bottom)
    for ext in dom["externals"]:
        e_val = f"&lt;b style=&quot;font-size:11px;&quot;&gt;{html.escape(ext['name'])}&lt;/b&gt;&lt;br/&gt;&lt;i style=&quot;font-size:9.5px;&quot;&gt;[System_Ext: {html.escape(ext['type'])}]&lt;/i&gt;&lt;br/&gt;&lt;span style=&quot;font-size:9px;&quot;&gt;{html.escape(ext['desc'])}&lt;/span&gt;"
        xml.append(f'        <mxCell id="{ext["id"]}" value="{e_val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#718096;strokeColor=#4A5568;strokeWidth=1.2;fontFamily=Arial;fontColor=#FFFFFF;align=center;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{ext["x"]}" y="{ext["y"]}" width="{ext["w"]}" height="{ext["h"]}" as="geometry" />')
        xml.append('        </mxCell>')

    # Links
    link_counter = 100
    for src, tgt, label in dom["links"]:
        link_counter += 1
        l_val = html.escape(label)
        xml.append(f'        <mxCell id="link_{link_counter}" value="{l_val}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=classic;strokeColor=#2D3748;strokeWidth=1.2;fontFamily=Arial;fontSize=9.5;fontColor=#1A202C;labelBackgroundColor=#FFFFFF;" edge="1" parent="1" source="{src}" target="{tgt}">')
        xml.append('          <mxGeometry relative="1" as="geometry" />')
        xml.append('        </mxCell>')

    xml.append('      </root>')
    xml.append('    </mxGraphModel>')
    xml.append('  </diagram>')

xml.append('</mxfile>')

drawio_c4_path = "docs/diagramas/c4/diagramas_componentes_c4.drawio"
with open(drawio_c4_path, "w", encoding="utf-8") as f:
    f.write("\n".join(xml))

print(f"Generated consolidated C4 Draw.io file: {drawio_c4_path}")
