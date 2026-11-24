"""
Script de generación para los diagramas de análisis y diseño de CU33:
'Gestionar Garantías y Servicio Posventa Inmobiliario'
Produce PUML y Draw.io nativo editable para:
- Robustez ICONIX (BCE)
- Secuencia UML 2.5.1 MVC
- Comunicación UML 2.5.1
- Clases de Análisis UML 2.5.1
- Tiempo UML 2.5.1
"""
import os
import sys
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

WORKSPACE = Path(r"D:\Sistemas de informacion 2\Proyecto2\Proyecto_Si2")
DOCS_DIAG = WORKSPACE / "docs" / "diagramas"
DOCS_DIAG.mkdir(parents=True, exist_ok=True)

def sub_geo(parent, x="0", y="0", width="0", height="0", relative="0", attribs=None):
    d = {"x": str(x), "y": str(y), "width": str(width), "height": str(height), "as": "geometry", "relative": str(relative)}
    if attribs:
        d.update(attribs)
    return ET.SubElement(parent, "mxGeometry", attrib=d)

# ─────────────────────────────────────────────────────────────────────────────
# 1. GENERAR MATRIZ CANÓNICA CSV
# ─────────────────────────────────────────────────────────────────────────────
def generate_matrix():
    csv_path = DOCS_DIAG / "CU33-matriz.csv"
    rows = [
        {"id_op": "HU161", "operacion": "Registrar Garantía Inmobiliaria", "actor": "Administrador_empresa", "boundary": "UIPosventa", "control": "GestorPosventa", "entidades": "UnidadGarantia, UnidadConstruccion, ClienteCRM", "metodo_control": "registrarGarantia(dto)", "metodo_entidad": "crearGarantia()", "estado": "CONFIRMADO"},
        {"id_op": "HU162", "operacion": "Consultar Garantías Inmobiliarias", "actor": "Cliente / Administrador_empresa", "boundary": "UIPosventa", "control": "GestorPosventa", "entidades": "UnidadGarantia", "metodo_control": "consultarGarantias(filtros)", "metodo_entidad": "obtenerGarantiasConVigencia()", "estado": "CONFIRMADO"},
        {"id_op": "HU163", "operacion": "Registrar Solicitud de Posventa", "actor": "Cliente", "boundary": "UIPosventa", "control": "GestorPosventa", "entidades": "SolicitudPosventa, EvidenciaPosventa, BitacoraPosventa", "metodo_control": "registrarSolicitud(dto)", "metodo_entidad": "crearSolicitud(), adjuntarEvidencia(), registrarBitacora()", "estado": "CONFIRMADO"},
        {"id_op": "HU164", "operacion": "Clasificar Solicitud y Validar Garantía", "actor": "Administrador_empresa", "boundary": "UIPosventa", "control": "GestorPosventa", "entidades": "SolicitudPosventa, UnidadGarantia, BitacoraPosventa", "metodo_control": "clasificarSolicitud(idSolicitud, dto)", "metodo_entidad": "actualizarClasificacion(), verificarCobertura()", "estado": "CONFIRMADO"},
        {"id_op": "HU165", "operacion": "Asignar Responsables de Atención", "actor": "Jefe de Obra", "boundary": "UIPosventa", "control": "GestorPosventa", "entidades": "SolicitudPosventa, Usuario, BitacoraPosventa", "metodo_control": "asignarResponsable(idSolicitud, dto)", "metodo_entidad": "actualizarAsignacion(), registrarBitacora()", "estado": "CONFIRMADO"},
        {"id_op": "HU166", "operacion": "Gestionar Atención Técnica y Bitácora", "actor": "Supervisor", "boundary": "UIPosventa", "control": "GestorPosventa", "entidades": "SolicitudPosventa, BitacoraPosventa, EvidenciaPosventa", "metodo_control": "gestionarAtencion(idSolicitud, dto)", "metodo_entidad": "actualizarEstado(), registrarBitacora(), adjuntarEvidencia()", "estado": "CONFIRMADO"},
        {"id_op": "HU167", "operacion": "Consultar Seguimiento y Línea de Tiempo", "actor": "Cliente", "boundary": "UIPosventa", "control": "GestorPosventa", "entidades": "SolicitudPosventa, BitacoraPosventa, EvidenciaPosventa", "metodo_control": "consultarDetalleSolicitud(idSolicitud)", "metodo_entidad": "obtenerDetalleTicket(), listarBitacoras()", "estado": "CONFIRMADO"},
        {"id_op": "HU168", "operacion": "Consultar Historial y Trazabilidad", "actor": "Administrador_empresa", "boundary": "UIPosventa", "control": "GestorPosventa", "entidades": "SolicitudPosventa, UnidadGarantia", "metodo_control": "consultarMetricasHistorial(filtros)", "metodo_entidad": "consolidarTrazabilidad(), contarPorEstado()", "estado": "CONFIRMADO"},
    ]
    with open(csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generado {csv_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. GENERAR DIAGRAMA DE ROBUSTEZ ICONIX (PUML & DRAWIO)
# ─────────────────────────────────────────────────────────────────────────────
def generate_robustness():
    puml_path = DOCS_DIAG / "CU33-robustez.puml"
    drawio_path = DOCS_DIAG / "CU33-robustez.drawio"

    puml_content = """@startuml
title Diagrama de Robustez ICONIX — CU33: Gestionar Garantías y Servicio Posventa Inmobiliario
left to right direction
skinparam shadowing false
skinparam defaultFontName Arial
skinparam packageStyle rectangle

actor "Administrador_empresa" as Admin
actor "Cliente" as Cliente
actor "Jefe de Obra" as JefeObra
actor "Supervisor" as Supervisor

package "Límites («boundary»)" {
  boundary "UIPosventa\\n(Web / Móvil)" as UI
}

package "Controles («control»)" {
  control "GestorPosventa" as Ctrl
}

package "Entidades («entity»)" {
  entity "UnidadGarantia" as E_Garantia
  entity "SolicitudPosventa" as E_Solicitud
  entity "BitacoraPosventa" as E_Bitacora
  entity "EvidenciaPosventa" as E_Evidencia
  entity "UnidadConstruccion" as E_Unidad
  entity "ClienteCRM" as E_Cliente
  entity "Usuario" as E_Usuario
}

Admin --> UI : HU161: registrarGarantia(datos)\\nHU164: clasificarSolicitud(categoria, prioridad)\\nHU168: consultarHistorialYMetricas()
Cliente --> UI : HU162: consultarGarantias()\\nHU163: registrarSolicitud(defecto, fotos)\\nHU167: consultarSeguimiento()
JefeObra --> UI : HU165: asignarResponsable(supervisor, fecha)
Supervisor --> UI : HU166: gestionarAtencion(estado, bitacora, materiales)

UI --> Ctrl : invoca operaciones CU33

Ctrl --> Ctrl : validarFechasYTipo()\\nvalidarTransicionEstado()\\ngenerarCodigoTicket()

Ctrl --> E_Garantia : registrar_garantia()\\nconsultar_garantias()\\nverificar_cobertura()
Ctrl --> E_Solicitud : registrar_solicitud()\\nactualizar_clasificacion()\\nasignar_supervisor()\\nactualizar_estado()\\nconsultar_detalle()
Ctrl --> E_Bitacora : registrar_bitacora()\\nlistar_linea_tiempo()
Ctrl --> E_Evidencia : adjuntar_evidencia()\\nlistar_evidencias()
Ctrl --> E_Unidad : verificar_unidad_empresa()
Ctrl --> E_Cliente : verificar_propietario()
Ctrl --> E_Usuario : obtener_supervisores_empresa()

@enduml
"""
    puml_path.write_text(puml_content, encoding="utf-8")
    print(f"Generado {puml_path}")

    # Drawio XML
    root = ET.Element("mxfile", host="app.diagrams.net", type="device")
    diagram = ET.SubElement(root, "diagram", id="robustness_cu33", name="CU33 - Robustez ICONIX")
    model = ET.SubElement(diagram, "mxGraphModel", dx="1400", dy="950", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1400", pageHeight="950", math="0", shadow="0")
    root_cell = ET.SubElement(model, "root")
    ET.SubElement(root_cell, "mxCell", id="0")
    ET.SubElement(root_cell, "mxCell", id="1", parent="0")

    # Frame
    frame = ET.SubElement(root_cell, "mxCell", id="frame", value="rd CU33 - Gestionar Garantías y Servicio Posventa Inmobiliario (Robustez ICONIX)", style="swimlane;html=1;startSize=32;horizontal=1;fillColor=none;swimlaneFillColor=none;strokeColor=#0284c7;fontSize=14;fontStyle=1;align=left;spacingLeft=12;", vertex="1", parent="1")
    sub_geo(frame, x=20, y=20, width=1360, height=900)

    # Actores (Columna 1: X=60)
    actors = [
        ("act_admin", "Administrador_empresa", 60, 100),
        ("act_cliente", "Cliente", 60, 300),
        ("act_jefe", "Jefe de Obra", 60, 500),
        ("act_supervisor", "Supervisor", 60, 700),
    ]
    for aid, aname, ax, ay in actors:
        c = ET.SubElement(root_cell, "mxCell", id=aid, value=aname, style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", vertex="1", parent="1")
        sub_geo(c, x=ax, y=ay, width=50, height=90)

    # Boundary (Columna 2: X=300)
    ui_cell = ET.SubElement(root_cell, "mxCell", id="b_ui", value="«boundary»&#xa;UIPosventa&#xa;(Web / Móvil)", style="shape=umlBoundary;whiteSpace=wrap;html=1;verticalAlign=top;fillColor=#e0f2fe;strokeColor=#0284c7;fontSize=11;fontStyle=1;", vertex="1", parent="1")
    sub_geo(ui_cell, x=280, y=360, width=100, height=80)

    # Control (Columna 3: X=580)
    ctrl_cell = ET.SubElement(root_cell, "mxCell", id="c_ctrl", value="«control»&#xa;GestorPosventa", style="shape=umlControl;whiteSpace=wrap;html=1;verticalAlign=top;fillColor=#fef08a;strokeColor=#ca8a04;fontSize=11;fontStyle=1;", vertex="1", parent="1")
    sub_geo(ctrl_cell, x=560, y=360, width=90, height=80)

    # Entidades (Columna 4: X=960)
    entities = [
        ("e_garantia", "«entity»&#xa;UnidadGarantia", 960, 80),
        ("e_solicitud", "«entity»&#xa;SolicitudPosventa", 960, 200),
        ("e_bitacora", "«entity»&#xa;BitacoraPosventa", 960, 320),
        ("e_evidencia", "«entity»&#xa;EvidenciaPosventa", 960, 440),
        ("e_unidad", "«entity»&#xa;UnidadConstruccion", 960, 560),
        ("e_cliente", "«entity»&#xa;ClienteCRM", 960, 680),
        ("e_usuario", "«entity»&#xa;Usuario", 960, 800),
    ]
    for eid, ename, ex, ey in entities:
        c = ET.SubElement(root_cell, "mxCell", id=eid, value=ename, style="shape=umlEntity;whiteSpace=wrap;html=1;verticalAlign=top;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", vertex="1", parent="1")
        sub_geo(c, x=ex, y=ey, width=90, height=80)

    # Edges: Actores -> Boundary
    actor_edges = [
        ("e_a1", "act_admin", "b_ui", "HU161: registrarGarantia()&#xa;HU164: clasificarSolicitud()&#xa;HU168: consultarHistorial()"),
        ("e_a2", "act_cliente", "b_ui", "HU162: consultarGarantias()&#xa;HU163: registrarSolicitud()&#xa;HU167: consultarSeguimiento()"),
        ("e_a3", "act_jefe", "b_ui", "HU165: asignarResponsable()"),
        ("e_a4", "act_supervisor", "b_ui", "HU166: gestionarAtencion()"),
    ]
    for eid, s, t, lbl in actor_edges:
        edge = ET.SubElement(root_cell, "mxCell", id=eid, value=lbl, style="endArrow=none;html=1;rounded=0;strokeColor=#334155;strokeWidth=1.5;fontSize=10;labelBackgroundColor=#ffffff;", edge="1", parent="1", source=s, target=t)
        sub_geo(edge, width=0, height=0, relative=1)

    # Edge: Boundary -> Control
    edge_bc = ET.SubElement(root_cell, "mxCell", id="e_bc", value="solicitarAccion(dto)", style="endArrow=classic;html=1;rounded=0;strokeColor=#0284c7;strokeWidth=2;fontSize=11;labelBackgroundColor=#ffffff;", edge="1", parent="1", source="b_ui", target="c_ctrl")
    sub_geo(edge_bc, width=0, height=0, relative=1)

    # Edges: Control -> Entidades
    ctrl_edges = [
        ("e_ce1", "c_ctrl", "e_garantia", "registrar_garantia()&#xa;verificar_cobertura()"),
        ("e_ce2", "c_ctrl", "e_solicitud", "registrar_solicitud()&#xa;actualizar_estado()"),
        ("e_ce3", "c_ctrl", "e_bitacora", "registrar_bitacora()&#xa;listar_linea_tiempo()"),
        ("e_ce4", "c_ctrl", "e_evidencia", "adjuntar_evidencia()"),
        ("e_ce5", "c_ctrl", "e_unidad", "verificar_unidad_empresa()"),
        ("e_ce6", "c_ctrl", "e_cliente", "verificar_propietario()"),
        ("e_ce7", "c_ctrl", "e_usuario", "obtener_supervisores()"),
    ]
    for eid, s, t, lbl in ctrl_edges:
        edge = ET.SubElement(root_cell, "mxCell", id=eid, value=lbl, style="endArrow=classic;html=1;rounded=0;strokeColor=#16a34a;strokeWidth=1.5;fontSize=10;labelBackgroundColor=#ffffff;", edge="1", parent="1", source=s, target=t)
        sub_geo(edge, width=0, height=0, relative=1)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(drawio_path, encoding="utf-8", xml_declaration=True)
    print(f"Generado {drawio_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. GENERAR DIAGRAMA DE SECUENCIA UML 2.5.1 MVC (PUML & DRAWIO)
# ─────────────────────────────────────────────────────────────────────────────
def generate_sequence():
    puml_path = DOCS_DIAG / "CU33-secuencia.puml"
    drawio_path = DOCS_DIAG / "CU33-secuencia.drawio"

    puml_content = """@startuml
title Diagrama de Secuencia UML 2.5.1 (MVC) — CU33: Gestionar Garantías y Servicio Posventa Inmobiliario
autonumber
skinparam shadowing false
skinparam defaultFontName Arial
skinparam sequenceMessageAlign center
skinparam roundcorner 4

actor "Administrador_empresa" as Admin
actor "Cliente" as Cliente
actor "Jefe de Obra" as JefeObra
actor "Supervisor" as Supervisor

participant "ui: UIPosventa" as UI <<boundary>>
participant "ctrl: GestorPosventa" as Ctrl <<control>>
participant "garantia: UnidadGarantia" as E_Garantia <<entity>>
participant "solicitud: SolicitudPosventa" as E_Solicitud <<entity>>
participant "bitacora: BitacoraPosventa" as E_Bitacora <<entity>>
participant "evidencia: EvidenciaPosventa" as E_Evidencia <<entity>>
participant "clienteCRM: ClienteCRM" as E_Cliente <<entity>>
participant "unidad: UnidadConstruccion" as E_Unidad <<entity>>

== HU161: Registrar Garantía Inmobiliaria ==
Admin -> UI: registrarGarantia(idUnidad, idCliente, tipo, vigencia, cobertura)
activate UI
UI -> Ctrl: registrar_garantia_inmobiliaria(dto)
activate Ctrl
Ctrl -> Ctrl: validarFechasYTipo()
Ctrl -> E_Unidad: verificar_unidad_pertenece_empresa(idUnidad, idEmpresa)
activate E_Unidad
E_Unidad --> Ctrl: unidadValida
deactivate E_Unidad
Ctrl -> E_Cliente: verificar_cliente_propietario(idCliente, idUnidad)
activate E_Cliente
E_Cliente --> Ctrl: esPropietario
deactivate E_Cliente
Ctrl -> E_Garantia: crear_garantia(datosGarantia)
activate E_Garantia
E_Garantia --> Ctrl: garantiaCreada
deactivate E_Garantia
Ctrl --> UI: 201 Created (Garantía registrada)
deactivate Ctrl
UI --> Admin: Mostrar confirmación y póliza activa
deactivate UI

== HU162: Consultar Garantías Inmobiliarias ==
Cliente -> UI: solicitarMisGarantias(idUnidad)
activate UI
UI -> Ctrl: consultar_garantias(idEmpresa, idCliente)
activate Ctrl
Ctrl -> E_Garantia: obtener_garantias_con_vigencia(idEmpresa, idCliente)
activate E_Garantia
E_Garantia --> Ctrl: listaGarantiasVigencia
deactivate E_Garantia
Ctrl --> UI: 200 OK (Garantías con estado Vigente/Vencida)
deactivate Ctrl
UI --> Cliente: Mostrar garantías y coberturas
deactivate UI

== HU163: Registrar Solicitud de Posventa y Evidencia ==
Cliente -> UI: registrarSolicitud(idUnidad, defecto, idGarantia, evidencia)
activate UI
UI -> Ctrl: registrar_solicitud_posventa(dto)
activate Ctrl
Ctrl -> Ctrl: generarCodigoTicket()
Ctrl -> E_Solicitud: crear_solicitud(codigo, PENDIENTE)
activate E_Solicitud
E_Solicitud --> Ctrl: idSolicitud
deactivate E_Solicitud
Ctrl -> E_Bitacora: registrar_bitacora(CREACION, PENDIENTE)
activate E_Bitacora
E_Bitacora --> Ctrl: bitacoraOk
deactivate E_Bitacora
Ctrl -> E_Evidencia: adjuntar_evidencia(idSolicitud, archivo, CLIENTE_REPORTE)
activate E_Evidencia
E_Evidencia --> Ctrl: evidenciaOk
deactivate E_Evidencia
Ctrl --> UI: 201 Created (Ticket generado)
deactivate Ctrl
UI --> Cliente: Mostrar código de ticket y confirmación
deactivate UI

== HU164: Clasificar Solicitud y Validar Cobertura ==
Admin -> UI: clasificarSolicitud(idSolicitud, categoria, prioridad, aplicaGarantia)
activate UI
UI -> Ctrl: clasificar_solicitud_posventa(idSolicitud, dto)
activate Ctrl
alt Aplica Garantía
  Ctrl -> E_Garantia: verificar_cobertura(idGarantia, idUnidad)
  activate E_Garantia
  E_Garantia --> Ctrl: garantiaVigente
  deactivate E_Garantia
end
Ctrl -> E_Solicitud: actualizar_clasificacion(categoria, prioridad, CLASIFICADA)
activate E_Solicitud
E_Solicitud --> Ctrl: solicitudClasificada
deactivate E_Solicitud
Ctrl -> E_Bitacora: registrar_bitacora(CLASIFICACION, CLASIFICADA)
activate E_Bitacora
E_Bitacora --> Ctrl: bitacoraOk
deactivate E_Bitacora
Ctrl --> UI: 200 OK (Solicitud clasificada)
deactivate Ctrl
UI --> Admin: Notificar clasificación habilitada para Jefe de Obra
deactivate UI

== HU165: Asignar Responsables de Atención ==
JefeObra -> UI: asignarResponsable(idSolicitud, idSupervisor, fechaEstimada, notas)
activate UI
UI -> Ctrl: asignar_responsable_atencion(idSolicitud, dto)
activate Ctrl
Ctrl -> E_Solicitud: actualizar_asignacion(idSupervisor, fechaEstimada, ASIGNADA)
activate E_Solicitud
E_Solicitud --> Ctrl: solicitudAsignada
deactivate E_Solicitud
Ctrl -> E_Bitacora: registrar_bitacora(ASIGNACION, ASIGNADA)
activate E_Bitacora
E_Bitacora --> Ctrl: bitacoraOk
deactivate E_Bitacora
Ctrl --> UI: 200 OK (Supervisor asignado)
deactivate Ctrl
UI --> JefeObra: Confirmar asignación técnica
deactivate UI

== HU166: Gestionar Atención Técnica y Bitácora ==
Supervisor -> UI: registrarAtencion(idSolicitud, nuevoEstado, acciones, materiales)
activate UI
UI -> Ctrl: gestionar_atencion_solicitud(idSolicitud, dto)
activate Ctrl
Ctrl -> Ctrl: validarTransicionEstado(estadoActual, nuevoEstado)
Ctrl -> E_Solicitud: actualizar_estado(nuevoEstado, fechaCierre)
activate E_Solicitud
E_Solicitud --> Ctrl: estadoActualizado
deactivate E_Solicitud
Ctrl -> E_Bitacora: registrar_bitacora(ATENCION, nuevoEstado, materiales)
activate E_Bitacora
E_Bitacora --> Ctrl: bitacoraOk
deactivate E_Bitacora
Ctrl --> UI: 200 OK (Atención registrada)
deactivate Ctrl
UI --> Supervisor: Mostrar estado actualizado del caso
deactivate UI

== HU167: Consultar Seguimiento y Línea de Tiempo ==
Cliente -> UI: consultarProgresoTicket(idSolicitud)
activate UI
UI -> Ctrl: consultar_detalle_solicitud_posventa(idSolicitud)
activate Ctrl
Ctrl -> E_Solicitud: obtener_detalle_ticket(idSolicitud)
activate E_Solicitud
E_Solicitud --> Ctrl: datosTicket
deactivate E_Solicitud
Ctrl -> E_Bitacora: listar_linea_tiempo(idSolicitud)
activate E_Bitacora
E_Bitacora --> Ctrl: historialEventos
deactivate E_Bitacora
Ctrl -> E_Evidencia: listar_evidencias(idSolicitud)
activate E_Evidencia
E_Evidencia --> Ctrl: listaEvidencias
deactivate E_Evidencia
Ctrl --> UI: 200 OK (Línea de tiempo completa)
deactivate Ctrl
UI --> Cliente: Desplegar timeline y fecha programada
deactivate UI

== HU168: Consultar Historial y Trazabilidad Consolidada ==
Admin -> UI: consultarHistorialYMetricas()
activate UI
UI -> Ctrl: consultar_historial_y_metricas()
activate Ctrl
Ctrl -> E_Solicitud: consolidar_trazabilidad(idEmpresa)
activate E_Solicitud
E_Solicitud --> Ctrl: metricasSolicitudes
deactivate E_Solicitud
Ctrl -> E_Garantia: contar_por_estado(idEmpresa)
activate E_Garantia
E_Garantia --> Ctrl: metricasGarantias
deactivate E_Garantia
Ctrl --> UI: 200 OK (Dashboard consolidado)
deactivate Ctrl
UI --> Admin: Visualizar indicadores y trazabilidad
deactivate UI

@enduml
"""
    puml_path.write_text(puml_content, encoding="utf-8")
    print(f"Generado {puml_path}")

    # Drawio XML nativo
    lifelines = [
        ("Admin", "Administrador_empresa", "shape=umlActor;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", 60),
        ("Cliente", "Cliente", "shape=umlActor;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", 180),
        ("Jefe", "Jefe de Obra", "shape=umlActor;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", 300),
        ("Sup", "Supervisor", "shape=umlActor;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", 420),
        ("UI", "«boundary»&#xa;UIPosventa", "ellipse;fillColor=#c7eef4;strokeColor=#0e7490;fontSize=11;fontStyle=1;", 550),
        ("Ctrl", "«control»&#xa;GestorPosventa", "ellipse;fillColor=#fef08a;strokeColor=#ca8a04;fontSize=11;fontStyle=1;", 700),
        ("Garantia", "«entity»&#xa;UnidadGarantia", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 860),
        ("Solicitud", "«entity»&#xa;SolicitudPosventa", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 1020),
        ("Bitacora", "«entity»&#xa;BitacoraPosventa", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 1180),
        ("Evidencia", "«entity»&#xa;EvidenciaPosventa", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 1340),
    ]

    total_width = 1480
    total_height = 2300

    root = ET.Element("mxfile", host="app.diagrams.net", type="device")
    diagram = ET.SubElement(root, "diagram", id="sequence_cu33", name="CU33 - Secuencia MVC")
    model = ET.SubElement(diagram, "mxGraphModel", dx="1600", dy="1200", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth=str(total_width), pageHeight=str(total_height), math="0", shadow="0")
    root_cell = ET.SubElement(model, "root")
    ET.SubElement(root_cell, "mxCell", id="0")
    ET.SubElement(root_cell, "mxCell", id="1", parent="0")

    # Frame
    frame = ET.SubElement(root_cell, "mxCell", id="frame", value="sd CU33 - Gestionar Garantías y Servicio Posventa Inmobiliario (UML 2.5.1 MVC)", style="swimlane;html=1;startSize=32;horizontal=1;fillColor=none;swimlaneFillColor=none;strokeColor=#475569;fontSize=14;fontStyle=1;align=left;spacingLeft=12;", vertex="1", parent="1")
    sub_geo(frame, x=15, y=15, width=total_width - 30, height=total_height - 30)

    # Header & Lifelines
    coords = {}
    for lid, lname, lstyle, lx in lifelines:
        coords[lid] = lx
        head_w = 90
        head_h = 50 if "ellipse" in lstyle else 70
        head_y = 60 if "ellipse" in lstyle else 45
        c_head = ET.SubElement(root_cell, "mxCell", id=f"head_{lid}", value=lname, style=lstyle, vertex="1", parent="1")
        sub_geo(c_head, x=lx - head_w//2, y=head_y, width=head_w, height=head_h)

        # Lifeline vertical dashed
        life_y = 120
        life_h = total_height - 180
        c_life = ET.SubElement(root_cell, "mxCell", id=f"life_{lid}", value="", style="shape=line;direction=south;strokeColor=#64748b;dashed=1;dashPattern=5 5;", vertex="1", parent="1")
        sub_geo(c_life, x=lx, y=life_y, width=1, height=life_h)

    # Mensajes
    messages = [
        # HU161
        ("HU161: Registrar Garantía", None, None, None, True),
        ("Admin", "UI", "1: registrarGarantia(datos)", False),
        ("UI", "Ctrl", "1.1: registrar_garantia_inmobiliaria(dto)", False),
        ("Ctrl", "Ctrl", "1.1.1: validarFechasYTipo()", False),
        ("Ctrl", "Garantia", "1.1.2: crear_garantia(datos)", False),
        ("Garantia", "Ctrl", "garantiaCreada", True),
        ("Ctrl", "UI", "201 Created", True),
        ("UI", "Admin", "póliza registrada", True),

        # HU162
        ("HU162: Consultar Garantías", None, None, None, True),
        ("Cliente", "UI", "2: solicitarMisGarantias(idUnidad)", False),
        ("UI", "Ctrl", "2.1: consultar_garantias(idEmpresa, idCliente)", False),
        ("Ctrl", "Garantia", "2.1.1: obtener_garantias_con_vigencia()", False),
        ("Garantia", "Ctrl", "listaGarantias", True),
        ("Ctrl", "UI", "200 OK (garantías vigentes/vencidas)", True),
        ("UI", "Cliente", "desplegar garantías", True),

        # HU163
        ("HU163: Registrar Solicitud de Posventa", None, None, None, True),
        ("Cliente", "UI", "3: registrarSolicitud(defecto, evidencia)", False),
        ("UI", "Ctrl", "3.1: registrar_solicitud_posventa(dto)", False),
        ("Ctrl", "Ctrl", "3.1.1: generarCodigoTicket()", False),
        ("Ctrl", "Solicitud", "3.1.2: crear_solicitud(PENDIENTE)", False),
        ("Solicitud", "Ctrl", "idSolicitud", True),
        ("Ctrl", "Bitacora", "3.1.3: registrar_bitacora(CREACION)", False),
        ("Ctrl", "Evidencia", "3.1.4: adjuntar_evidencia(fotos)", False),
        ("Ctrl", "UI", "201 Created (ticket asignado)", True),
        ("UI", "Cliente", "confirmación ticket", True),

        # HU164
        ("HU164: Clasificar Solicitud y Validar Cobertura", None, None, None, True),
        ("Admin", "UI", "4: clasificarSolicitud(categoria, prioridad)", False),
        ("UI", "Ctrl", "4.1: clasificar_solicitud_posventa(dto)", False),
        ("Ctrl", "Garantia", "4.1.1: verificar_cobertura(idGarantia)", False),
        ("Ctrl", "Solicitud", "4.1.2: actualizar_clasificacion(CLASIFICADA)", False),
        ("Ctrl", "Bitacora", "4.1.3: registrar_bitacora(CLASIFICACION)", False),
        ("Ctrl", "UI", "200 OK", True),
        ("UI", "Admin", "notificar solicitud lista para asignación", True),

        # HU165
        ("HU165: Asignar Responsable de Atención", None, None, None, True),
        ("Jefe", "UI", "5: asignarResponsable(supervisor, fechaVisita)", False),
        ("UI", "Ctrl", "5.1: asignar_responsable_atencion(dto)", False),
        ("Ctrl", "Solicitud", "5.1.1: actualizar_asignacion(ASIGNADA)", False),
        ("Ctrl", "Bitacora", "5.1.2: registrar_bitacora(ASIGNACION)", False),
        ("Ctrl", "UI", "200 OK", True),
        ("UI", "Jefe", "confirmar asignación técnica", True),

        # HU166
        ("HU166: Gestionar Atención Técnica y Cierre", None, None, None, True),
        ("Sup", "UI", "6: registrarAtencion(nuevoEstado, bitacora)", False),
        ("UI", "Ctrl", "6.1: gestionar_atencion_solicitud(dto)", False),
        ("Ctrl", "Ctrl", "6.1.1: validarTransicionEstado()", False),
        ("Ctrl", "Solicitud", "6.1.2: actualizar_estado(RESUELTA)", False),
        ("Ctrl", "Bitacora", "6.1.3: registrar_bitacora(materiales, tareas)", False),
        ("Ctrl", "UI", "200 OK", True),
        ("UI", "Sup", "estado actualizado", True),

        # HU167
        ("HU167: Consultar Seguimiento y Línea de Tiempo", None, None, None, True),
        ("Cliente", "UI", "7: consultarProgresoTicket(idSolicitud)", False),
        ("UI", "Ctrl", "7.1: consultar_detalle_solicitud(idSolicitud)", False),
        ("Ctrl", "Solicitud", "7.1.1: obtener_detalle_ticket()", False),
        ("Ctrl", "Bitacora", "7.1.2: listar_linea_tiempo()", False),
        ("Ctrl", "Evidencia", "7.1.3: listar_evidencias()", False),
        ("Ctrl", "UI", "200 OK", True),
        ("UI", "Cliente", "desplegar timeline de atención", True),

        # HU168
        ("HU168: Historial y Métricas Consolidadas", None, None, None, True),
        ("Admin", "UI", "8: consultarHistorialYMetricas()", False),
        ("UI", "Ctrl", "8.1: consultar_historial_y_metricas()", False),
        ("Ctrl", "Solicitud", "8.1.1: consolidar_trazabilidad()", False),
        ("Ctrl", "Garantia", "8.1.2: contar_por_estado()", False),
        ("Ctrl", "UI", "200 OK", True),
        ("UI", "Admin", "visualizar métricas y auditoría", True),
    ]

    current_y = 150
    msg_idx = 0
    for item in messages:
        if len(item) == 5:
            title = item[0]
            # Divider / Section Frame
            div = ET.SubElement(root_cell, "mxCell", id=f"sec_{msg_idx}", value=title, style="shape=note;whiteSpace=wrap;html=1;size=14;verticalAlign=middle;align=left;spacingLeft=10;fillColor=#f1f5f9;strokeColor=#64748b;fontSize=12;fontStyle=1;", vertex="1", parent="1")
            sub_geo(div, x=40, y=current_y, width=350, height=30)
            current_y += 45
            msg_idx += 1
            continue

        s_id, t_id, lbl, is_ret = item
        sx = coords[s_id]
        tx = coords[t_id]

        if s_id == t_id:
            # Self call
            anc_s = ET.SubElement(root_cell, "mxCell", id=f"anc_{msg_idx}_s", value="", style="ellipse;opacity=0;strokeColor=none;fillColor=none;", vertex="1", parent="1")
            sub_geo(anc_s, x=sx, y=current_y, width=2, height=2)
            anc_t = ET.SubElement(root_cell, "mxCell", id=f"anc_{msg_idx}_t", value="", style="ellipse;opacity=0;strokeColor=none;fillColor=none;", vertex="1", parent="1")
            sub_geo(anc_t, x=sx, y=current_y + 20, width=2, height=2)

            edge = ET.SubElement(root_cell, "mxCell", id=f"msg_{msg_idx}", value=lbl, style="endArrow=block;dashed=0;html=1;rounded=0;strokeColor=#ca8a04;strokeWidth=1.5;fontSize=10;labelBackgroundColor=#ffffff;", edge="1", parent="1", source=f"anc_{msg_idx}_s", target=f"anc_{msg_idx}_t")
            geo = sub_geo(edge, width=0, height=0, relative=1)
            arr = ET.SubElement(geo, "Array", attrib={"as": "points"})
            ET.SubElement(arr, "mxPoint", attrib={"x": str(sx + 35), "y": str(current_y)})
            ET.SubElement(arr, "mxPoint", attrib={"x": str(sx + 35), "y": str(current_y + 20)})
            current_y += 35
        else:
            anc_s = ET.SubElement(root_cell, "mxCell", id=f"anc_{msg_idx}_s", value="", style="ellipse;opacity=0;strokeColor=none;fillColor=none;", vertex="1", parent="1")
            sub_geo(anc_s, x=sx, y=current_y, width=2, height=2)
            anc_t = ET.SubElement(root_cell, "mxCell", id=f"anc_{msg_idx}_t", value="", style="ellipse;opacity=0;strokeColor=none;fillColor=none;", vertex="1", parent="1")
            sub_geo(anc_t, x=tx, y=current_y, width=2, height=2)

            style_arrow = "endArrow=open;dashed=1;strokeColor=#64748b;strokeWidth=1.2;fontSize=10;labelBackgroundColor=#ffffff;" if is_ret else "endArrow=block;dashed=0;strokeColor=#1e293b;strokeWidth=1.5;fontSize=10;labelBackgroundColor=#ffffff;"
            edge = ET.SubElement(root_cell, "mxCell", id=f"msg_{msg_idx}", value=lbl, style=style_arrow, edge="1", parent="1", source=f"anc_{msg_idx}_s", target=f"anc_{msg_idx}_t")
            sub_geo(edge, width=0, height=0, relative=1)
            current_y += 38
        msg_idx += 1

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(drawio_path, encoding="utf-8", xml_declaration=True)
    print(f"Generado {drawio_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. GENERAR DIAGRAMA DE COMUNICACIÓN UML 2.5.1 (PUML & DRAWIO)
# ─────────────────────────────────────────────────────────────────────────────
def generate_communication():
    puml_path = DOCS_DIAG / "CU33-comunicacion.puml"
    drawio_path = DOCS_DIAG / "CU33-comunicacion.drawio"

    puml_content = """@startuml
title Diagrama de Comunicación UML 2.5.1 — CU33: Gestionar Garantías y Servicio Posventa Inmobiliario
left to right direction
skinparam shadowing false
skinparam defaultFontName Arial
skinparam packageStyle rectangle

actor "Administrador_empresa" as Admin
actor "Cliente" as Cliente
actor "Jefe de Obra" as JefeObra
actor "Supervisor" as Supervisor

package "Colaboración MVC" {
  circle "UI: UIPosventa\\n<<boundary>>" as UI
  circle "ctrl: GestorPosventa\\n<<control>>" as Ctrl
  circle "garantia: UnidadGarantia\\n<<entity>>" as Garantia
  circle "solicitud: SolicitudPosventa\\n<<entity>>" as Solicitud
  circle "bitacora: BitacoraPosventa\\n<<entity>>" as Bitacora
  circle "evidencia: EvidenciaPosventa\\n<<entity>>" as Evidencia
  circle "clienteCRM: ClienteCRM\\n<<entity>>" as ClienteCRM
  circle "unidad: UnidadConstruccion\\n<<entity>>" as Unidad
}

Admin -- UI : 1: registrarGarantia()\\n4: clasificarSolicitud()\\n8: consultarHistorial()
Cliente -- UI : 2: consultarGarantias()\\n3: registrarSolicitud()\\n7: consultarSeguimiento()
JefeObra -- UI : 5: asignarResponsable()
Supervisor -- UI : 6: registrarAtencion()

UI -- Ctrl : 1.1: registrar_garantia_inmobiliaria()\\n2.1: consultar_garantias()\\n3.1: registrar_solicitud_posventa()\\n4.1: clasificar_solicitud_posventa()\\n5.1: asignar_responsable_atencion()\\n6.1: gestionar_atencion_solicitud()\\n7.1: consultar_detalle_solicitud()\\n8.1: consultar_historial_y_metricas()

Ctrl -- Garantia : 1.1.2: crear_garantia()\\n2.1.1: obtener_garantias()\\n4.1.1: verificar_cobertura()\\n8.1.2: contar_por_estado()
Ctrl -- Solicitud : 3.1.2: crear_solicitud()\\n4.1.2: actualizar_clasificacion()\\n5.1.1: actualizar_asignacion()\\n6.1.2: actualizar_estado()\\n7.1.1: obtener_detalle()\\n8.1.1: consolidar_trazabilidad()
Ctrl -- Bitacora : 3.1.3: registrar_bitacora(CREACION)\\n4.1.3: registrar_bitacora(CLASIFICACION)\\n5.1.2: registrar_bitacora(ASIGNACION)\\n6.1.3: registrar_bitacora(ATENCION)\\n7.1.2: listar_linea_tiempo()
Ctrl -- Evidencia : 3.1.4: adjuntar_evidencia()\\n7.1.3: listar_evidencias()
Ctrl -- Unidad : 1.1.1a: verificar_unidad_empresa()
Ctrl -- ClienteCRM : 1.1.1b: verificar_propietario()

@enduml
"""
    puml_path.write_text(puml_content, encoding="utf-8")
    print(f"Generado {puml_path}")

    # Drawio XML
    root = ET.Element("mxfile", host="app.diagrams.net", type="device")
    diagram = ET.SubElement(root, "diagram", id="comm_cu33", name="CU33 - Comunicación")
    model = ET.SubElement(diagram, "mxGraphModel", dx="1400", dy="950", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1400", pageHeight="950", math="0", shadow="0")
    root_cell = ET.SubElement(model, "root")
    ET.SubElement(root_cell, "mxCell", id="0")
    ET.SubElement(root_cell, "mxCell", id="1", parent="0")

    # Frame
    frame = ET.SubElement(root_cell, "mxCell", id="frame", value="sd CU33 - Gestionar Garantías y Servicio Posventa Inmobiliario (UML 2.5.1 Comunicación)", style="swimlane;html=1;startSize=32;horizontal=1;fillColor=none;swimlaneFillColor=none;strokeColor=#475569;fontSize=14;fontStyle=1;align=left;spacingLeft=12;", vertex="1", parent="1")
    sub_geo(frame, x=20, y=20, width=1360, height=900)

    # Nodes
    nodes = [
        ("act_admin", "Administrador_empresa", "shape=umlActor;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", 60, 100, 50, 80),
        ("act_cliente", "Cliente", "shape=umlActor;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", 60, 320, 50, 80),
        ("act_jefe", "Jefe de Obra", "shape=umlActor;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", 60, 520, 50, 80),
        ("act_sup", "Supervisor", "shape=umlActor;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", 60, 720, 50, 80),

        ("node_ui", "«boundary»&#xa;UIPosventa", "ellipse;fillColor=#c7eef4;strokeColor=#0e7490;fontSize=11;fontStyle=1;", 320, 420, 100, 70),
        ("node_ctrl", "«control»&#xa;GestorPosventa", "ellipse;fillColor=#fef08a;strokeColor=#ca8a04;fontSize=11;fontStyle=1;", 620, 420, 110, 70),

        ("node_garantia", "«entity»&#xa;UnidadGarantia", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 980, 80, 110, 70),
        ("node_solicitud", "«entity»&#xa;SolicitudPosventa", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 980, 220, 110, 70),
        ("node_bitacora", "«entity»&#xa;BitacoraPosventa", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 980, 360, 110, 70),
        ("node_evidencia", "«entity»&#xa;EvidenciaPosventa", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 980, 500, 110, 70),
        ("node_unidad", "«entity»&#xa;UnidadConstruccion", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 980, 640, 110, 70),
        ("node_cliente", "«entity»&#xa;ClienteCRM", "ellipse;fillColor=#dcfce7;strokeColor=#16a34a;fontSize=11;fontStyle=1;", 980, 780, 110, 70),
    ]

    for nid, nname, nstyle, nx, ny, nw, nh in nodes:
        c = ET.SubElement(root_cell, "mxCell", id=nid, value=nname, style=nstyle, vertex="1", parent="1")
        sub_geo(c, x=nx, y=ny, width=nw, height=nh)

    # Edges with numbered messages
    links = [
        ("l_a1", "act_admin", "node_ui", "1: registrarGarantia()&#xa;4: clasificarSolicitud()&#xa;8: consultarHistorial()"),
        ("l_a2", "act_cliente", "node_ui", "2: consultarGarantias()&#xa;3: registrarSolicitud()&#xa;7: consultarSeguimiento()"),
        ("l_a3", "act_jefe", "node_ui", "5: asignarResponsable()"),
        ("l_a4", "act_sup", "node_ui", "6: registrarAtencion()"),

        ("l_ui_ctrl", "node_ui", "node_ctrl", "1.1: registrar_garantia_inmobiliaria()&#xa;2.1: consultar_garantias()&#xa;3.1: registrar_solicitud()&#xa;4.1: clasificar_solicitud()&#xa;5.1: asignar_responsable()&#xa;6.1: gestionar_atencion()&#xa;7.1: consultar_detalle()&#xa;8.1: consultar_metricas()"),

        ("l_c_garantia", "node_ctrl", "node_garantia", "1.1.2: crear_garantia()&#xa;2.1.1: obtener_garantias()&#xa;4.1.1: verificar_cobertura()&#xa;8.1.2: contar_por_estado()"),
        ("l_c_solicitud", "node_ctrl", "node_solicitud", "3.1.2: crear_solicitud()&#xa;4.1.2: actualizar_clasificacion()&#xa;5.1.1: actualizar_asignacion()&#xa;6.1.2: actualizar_estado()&#xa;7.1.1: obtener_detalle()&#xa;8.1.1: consolidar_trazabilidad()"),
        ("l_c_bitacora", "node_ctrl", "node_bitacora", "3.1.3: registrar_bitacora(CREACION)&#xa;4.1.3: registrar_bitacora(CLASIFICACION)&#xa;5.1.2: registrar_bitacora(ASIGNACION)&#xa;6.1.3: registrar_bitacora(ATENCION)&#xa;7.1.2: listar_linea_tiempo()"),
        ("l_c_evidencia", "node_ctrl", "node_evidencia", "3.1.4: adjuntar_evidencia()&#xa;7.1.3: listar_evidencias()"),
        ("l_c_unidad", "node_ctrl", "node_unidad", "1.1.1a: verificar_unidad_empresa()"),
        ("l_c_cliente", "node_ctrl", "node_cliente", "1.1.1b: verificar_propietario()"),
    ]

    for lid, s, t, lbl in links:
        edge = ET.SubElement(root_cell, "mxCell", id=lid, value=lbl, style="endArrow=none;html=1;rounded=0;strokeColor=#334155;strokeWidth=1.5;fontSize=10;labelBackgroundColor=#ffffff;", edge="1", parent="1", source=s, target=t)
        sub_geo(edge, width=0, height=0, relative=1)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(drawio_path, encoding="utf-8", xml_declaration=True)
    print(f"Generado {drawio_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. GENERAR DIAGRAMA DE CLASES DE ANÁLISIS UML 2.5.1 (PUML & DRAWIO)
# ─────────────────────────────────────────────────────────────────────────────
def generate_classes():
    puml_path = DOCS_DIAG / "CU33-clases-analisis.puml"
    drawio_path = DOCS_DIAG / "CU33-clases-analisis.drawio"

    puml_content = """@startuml
title Diagrama de Clases de Análisis UML 2.5.1 — CU33: Gestionar Garantías y Servicio Posventa Inmobiliario
left to right direction
skinparam classAttributeIconSize 0
skinparam shadowing false
skinparam defaultFontName Arial
hide empty members

class "Actores del CU33\\n(Admin, Cliente, Jefe, Supervisor)" as Actores <<actor>>

class "UIPosventa" as UI <<boundary>> {
  + mostrarFormularioGarantia(): void
  + mostrarListadoGarantias(): void
  + capturarSolicitudPosventa(): void
  + mostrarBandejaClasificacion(): void
  + capturarAsignacionResponsable(): void
  + registrarBitacoraAtencion(): void
  + desplegarTimelineSeguimiento(): void
  + mostrarDashboardHistorial(): void
}

class "GestorPosventa" as Ctrl <<control>> {
  + registrarGarantia(dto: RegistrarGarantiaDTO): GarantiaVO
  + consultarGarantias(filtros: FiltrosGarantiaDTO): List~GarantiaVO~
  + registrarSolicitud(dto: RegistrarSolicitudDTO): SolicitudVO
  + clasificarSolicitud(id: int, dto: ClasificarDTO): SolicitudVO
  + asignarResponsable(id: int, dto: AsignarDTO): SolicitudVO
  + gestionarAtencion(id: int, dto: AtenderDTO): SolicitudVO
  + consultarDetalleSolicitud(id: int): DetalleSolicitudVO
  + consultarMetricasHistorial(filtros: FiltrosDTO): MetricasVO
}

class "UnidadGarantia" as Garantia <<entity>> {
  - id_garantia: int
  - id_empresa: int
  - id_unidad: int
  - id_cliente: int
  - tipo_garantia: String
  - descripcion_cobertura: String
  - condiciones: String
  - fecha_inicio: date
  - fecha_fin: date
  - estado_vigencia: String
  + esVigente(): boolean
  + cubreDefecto(tipo: String): boolean
}

class "SolicitudPosventa" as Solicitud <<entity>> {
  - id_solicitud: int
  - id_empresa: int
  - codigo_ticket: String
  - id_unidad: int
  - id_cliente: int
  - id_garantia: int
  - id_supervisor: int
  - titulo: String
  - descripcion_defecto: String
  - categoria: String
  - prioridad: String
  - estado: String
  - aplica_garantia: boolean
  - fecha_creacion: timestamp
  - fecha_estimada_visita: date
  - fecha_cierre: timestamp
  + cambiarEstado(nuevoEstado: String): void
  + asignarTecnico(idSupervisor: int, fecha: date): void
}

class "BitacoraPosventa" as Bitacora <<entity>> {
  - id_bitacora: int
  - id_solicitud: int
  - id_usuario: int
  - tipo_evento: String
  - estado_resultante: String
  - detalle_acciones: String
  - materiales_utilizados: String
  - fecha_registro: timestamp
  + registrarEntrada(): void
}

class "EvidenciaPosventa" as Evidencia <<entity>> {
  - id_evidencia: int
  - id_solicitud: int
  - id_bitacora: int
  - id_usuario: int
  - tipo_evidencia: String
  - ruta_archivo: String
  - nombre_archivo: String
  - tipo_mime: String
  - fecha_subida: timestamp
  + obtenerUrlDescarga(): String
}

class "UnidadConstruccion" as Unidad <<entity>> {
  - id_unidad: int
  - codigo: String
  - id_obra: int
  + perteneceAEmpresa(idEmpresa: int): boolean
}

class "ClienteCRM" as Cliente <<entity>> {
  - id_cliente: int
  - id_persona: int
  - id_empresa: int
  - email: String
  + esPropietarioDe(idUnidad: int): boolean
}

Actores ..> UI : interactúa con
UI ..> Ctrl : solicita operaciones

Ctrl ..> Garantia : gestiona
Ctrl ..> Solicitud : gestiona
Ctrl ..> Bitacora : registra
Ctrl ..> Evidencia : adjunta
Ctrl ..> Unidad : valida
Ctrl ..> Cliente : valida

Solicitud "1" *-- "0..*" Bitacora : contiene
Solicitud "1" *-- "0..*" Evidencia : documenta
Solicitud "0..*" --> "0..1" Garantia : amparada por
Solicitud "0..*" --> "1" Unidad : reportada en
Solicitud "0..*" --> "1" Cliente : solicitada por
Garantia "0..*" --> "1" Unidad : cubre
Garantia "0..*" --> "1" Cliente : emitida a

@enduml
"""
    puml_path.write_text(puml_content, encoding="utf-8")
    print(f"Generado {puml_path}")

    # Drawio XML
    root = ET.Element("mxfile", host="app.diagrams.net", type="device")
    diagram = ET.SubElement(root, "diagram", id="class_cu33", name="CU33 - Clases de Análisis")
    model = ET.SubElement(diagram, "mxGraphModel", dx="1600", dy="1200", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1600", pageHeight="1200", math="0", shadow="0")
    root_cell = ET.SubElement(model, "root")
    ET.SubElement(root_cell, "mxCell", id="0")
    ET.SubElement(root_cell, "mxCell", id="1", parent="0")

    # Frame
    frame = ET.SubElement(root_cell, "mxCell", id="frame", value="class CU33 - Gestionar Garantías y Servicio Posventa Inmobiliario (Clases de Análisis UML 2.5.1)", style="swimlane;html=1;startSize=32;horizontal=1;fillColor=none;swimlaneFillColor=none;strokeColor=#475569;fontSize=14;fontStyle=1;align=left;spacingLeft=12;", vertex="1", parent="1")
    sub_geo(frame, x=20, y=20, width=1560, height=1150)

    # Actor
    act = ET.SubElement(root_cell, "mxCell", id="act_context", value="Actores del CU33&#xa;(Admin, Cliente,&#xa;Jefe, Supervisor)", style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;outlineConnect=0;fillColor=#e0f2fe;strokeColor=#0369a1;fontSize=11;fontStyle=1;", vertex="1", parent="1")
    sub_geo(act, x=50, y=180, width=50, height=80)

    # Classes definitions (x, y, w, h, header, attrs, methods, bg, stroke)
    classes_def = [
        ("c_ui", "«boundary»&#xa;<b>UIPosventa</b>", "", "+ mostrarFormularioGarantia(): void&#xa;+ mostrarListadoGarantias(): void&#xa;+ capturarSolicitudPosventa(): void&#xa;+ mostrarBandejaClasificacion(): void&#xa;+ capturarAsignacionResponsable(): void&#xa;+ registrarBitacoraAtencion(): void&#xa;+ desplegarTimelineSeguimiento(): void&#xa;+ mostrarDashboardHistorial(): void", 160, 100, 240, 210, "#c7eef4", "#0e7490"),
        ("c_ctrl", "«control»&#xa;<b>GestorPosventa</b>", "", "+ registrarGarantia(dto): GarantiaVO&#xa;+ consultarGarantias(filtros): List&#xa;+ registrarSolicitud(dto): SolicitudVO&#xa;+ clasificarSolicitud(id, dto): SolicitudVO&#xa;+ asignarResponsable(id, dto): SolicitudVO&#xa;+ gestionarAtencion(id, dto): SolicitudVO&#xa;+ consultarDetalleSolicitud(id): DetalleVO&#xa;+ consultarMetricasHistorial(): MetricasVO", 460, 100, 260, 210, "#fef08a", "#ca8a04"),
        ("c_garantia", "«entity»&#xa;<b>UnidadGarantia</b>", "- id_garantia: int&#xa;- id_empresa: int&#xa;- id_unidad: int&#xa;- id_cliente: int&#xa;- tipo_garantia: String&#xa;- descripcion_cobertura: String&#xa;- condiciones: String&#xa;- fecha_inicio: date&#xa;- fecha_fin: date&#xa;- estado_vigencia: String", "+ esVigente(): boolean&#xa;+ cubreDefecto(tipo): boolean", 790, 80, 220, 250, "#dcfce7", "#16a34a"),
        ("c_solicitud", "«entity»&#xa;<b>SolicitudPosventa</b>", "- id_solicitud: int&#xa;- id_empresa: int&#xa;- codigo_ticket: String&#xa;- id_unidad: int&#xa;- id_cliente: int&#xa;- id_garantia: int&#xa;- id_supervisor: int&#xa;- titulo: String&#xa;- descripcion_defecto: String&#xa;- categoria: String&#xa;- prioridad: String&#xa;- estado: String&#xa;- aplica_garantia: boolean&#xa;- fecha_creacion: timestamp&#xa;- fecha_estimada_visita: date&#xa;- fecha_cierre: timestamp", "+ cambiarEstado(nuevoEstado): void&#xa;+ asignarTecnico(idSupervisor, fecha): void", 1080, 80, 250, 320, "#dcfce7", "#16a34a"),
        ("c_bitacora", "«entity»&#xa;<b>BitacoraPosventa</b>", "- id_bitacora: int&#xa;- id_solicitud: int&#xa;- id_usuario: int&#xa;- tipo_evento: String&#xa;- estado_resultante: String&#xa;- detalle_acciones: String&#xa;- materiales_utilizados: String&#xa;- fecha_registro: timestamp", "+ registrarEntrada(): void", 1080, 480, 250, 200, "#dcfce7", "#16a34a"),
        ("c_evidencia", "«entity»&#xa;<b>EvidenciaPosventa</b>", "- id_evidencia: int&#xa;- id_solicitud: int&#xa;- id_bitacora: int&#xa;- id_usuario: int&#xa;- tipo_evidencia: String&#xa;- ruta_archivo: String&#xa;- nombre_archivo: String&#xa;- tipo_mime: String&#xa;- fecha_subida: timestamp", "+ obtenerUrlDescarga(): String", 1080, 740, 250, 210, "#dcfce7", "#16a34a"),
        ("c_unidad", "«entity»&#xa;<b>UnidadConstruccion</b>", "- id_unidad: int&#xa;- codigo: String&#xa;- id_obra: int", "+ perteneceAEmpresa(idEmpresa): boolean", 460, 450, 240, 120, "#dcfce7", "#16a34a"),
        ("c_cliente", "«entity»&#xa;<b>ClienteCRM</b>", "- id_cliente: int&#xa;- id_persona: int&#xa;- id_empresa: int&#xa;- email: String", "+ esPropietarioDe(idUnidad): boolean", 460, 640, 240, 130, "#dcfce7", "#16a34a"),
    ]

    for cid, ctitle, cattrs, cmeths, cx, cy, cw, ch, cbg, cstroke in classes_def:
        val = f"{ctitle}"
        if cattrs:
            val += f"<hr/>{cattrs}"
        if cmeths:
            val += f"<hr/>{cmeths}"
        c = ET.SubElement(root_cell, "mxCell", id=cid, value=val, style=f"swimlane;fontStyle=0;childLayout=stackLayout;horizontal=1;startSize=40;fillColor={cbg};strokeColor={cstroke};horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;html=1;fontSize=10;align=left;spacingLeft=6;", vertex="1", parent="1")
        sub_geo(c, x=cx, y=cy, width=cw, height=ch)

    # Relationships
    edges = [
        ("rel_act_ui", "act_context", "c_ui", "interactúa", "endArrow=open;dashed=1;strokeColor=#0284c7;"),
        ("rel_ui_ctrl", "c_ui", "c_ctrl", "solicita", "endArrow=open;dashed=1;strokeColor=#0e7490;"),
        ("rel_ctrl_g", "c_ctrl", "c_garantia", "gestiona", "endArrow=open;dashed=1;strokeColor=#ca8a04;"),
        ("rel_ctrl_s", "c_ctrl", "c_solicitud", "coordina", "endArrow=open;dashed=1;strokeColor=#ca8a04;"),
        ("rel_ctrl_u", "c_ctrl", "c_unidad", "valida", "endArrow=open;dashed=1;strokeColor=#ca8a04;"),
        ("rel_ctrl_c", "c_ctrl", "c_cliente", "valida", "endArrow=open;dashed=1;strokeColor=#ca8a04;"),

        ("rel_s_b", "c_solicitud", "c_bitacora", "1   contiene   0..*", "endArrow=diamond;endFill=1;strokeColor=#16a34a;strokeWidth=1.5;"),
        ("rel_s_e", "c_solicitud", "c_evidencia", "1   documenta  0..*", "endArrow=diamond;endFill=1;strokeColor=#16a34a;strokeWidth=1.5;"),
        ("rel_s_g", "c_solicitud", "c_garantia", "0..*  amparada por  0..1", "endArrow=classic;strokeColor=#16a34a;"),
        ("rel_g_u", "c_garantia", "c_unidad", "0..*  asociada a  1", "endArrow=classic;strokeColor=#16a34a;"),
        ("rel_g_c", "c_garantia", "c_cliente", "0..*  emitida a  1", "endArrow=classic;strokeColor=#16a34a;"),
    ]

    for eid, s, t, lbl, style in edges:
        edge = ET.SubElement(root_cell, "mxCell", id=eid, value=lbl, style=f"{style}html=1;fontSize=10;labelBackgroundColor=#ffffff;", edge="1", parent="1", source=s, target=t)
        sub_geo(edge, width=0, height=0, relative=1)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(drawio_path, encoding="utf-8", xml_declaration=True)
    print(f"Generado {drawio_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. GENERAR DIAGRAMA DE TIEMPO UML 2.5.1 (DRAWIO)
# ─────────────────────────────────────────────────────────────────────────────
def generate_timing():
    drawio_path = DOCS_DIAG / "CU33-tiempo.drawio"

    root = ET.Element("mxfile", host="app.diagrams.net", type="device")
    diagram = ET.SubElement(root, "diagram", id="timing_cu33", name="CU33 - Diagrama de Tiempo")
    model = ET.SubElement(diagram, "mxGraphModel", dx="1400", dy="950", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1400", pageHeight="950", math="0", shadow="0")
    root_cell = ET.SubElement(model, "root")
    ET.SubElement(root_cell, "mxCell", id="0")
    ET.SubElement(root_cell, "mxCell", id="1", parent="0")

    # Frame
    frame = ET.SubElement(root_cell, "mxCell", id="frame", value="timing CU33 - Diagrama de Tiempo de Estados de Solicitud de Posventa", style="swimlane;html=1;startSize=32;horizontal=1;fillColor=none;swimlaneFillColor=none;strokeColor=#475569;fontSize=14;fontStyle=1;align=left;spacingLeft=12;", vertex="1", parent="1")
    sub_geo(frame, x=20, y=20, width=1360, height=880)

    # Estados en el eje vertical
    states = [
        ("st_cerrada", "CERRADA", 100),
        ("st_resuelta", "RESUELTA", 180),
        ("st_atencion", "EN_ATENCION", 260),
        ("st_asignada", "ASIGNADA", 340),
        ("st_clasificada", "CLASIFICADA", 420),
        ("st_pendiente", "PENDIENTE", 500),
        ("st_rechazada", "RECHAZADA", 580),
    ]

    for sid, sname, sy in states:
        # State label box
        c_lbl = ET.SubElement(root_cell, "mxCell", id=f"lbl_{sid}", value=sname, style="rounded=1;whiteSpace=wrap;html=1;fontSize=11;fontStyle=1;fillColor=#f8fafc;strokeColor=#64748b;align=center;", vertex="1", parent="1")
        sub_geo(c_lbl, x=50, y=sy - 15, width=110, height=30)

        # Grid guideline
        c_line = ET.SubElement(root_cell, "mxCell", id=f"line_{sid}", value="", style="shape=line;strokeColor=#e2e8f0;dashed=1;dashPattern=3 3;", vertex="1", parent="1")
        sub_geo(c_line, x=170, y=sy, width=1150, height=1)

    # Time milestones / Events on X axis (X from 250 to 1250)
    milestones = [
        ("m1", "t0: Reporte Cliente&#xa;(HU163)", 260, 500),
        ("m2", "t1: Clasificación Admin&#xa;(HU164)", 450, 420),
        ("m3", "t2: Asignación Jefe Obra&#xa;(HU165)", 640, 340),
        ("m4", "t3: Visita / Bitácora Sup&#xa;(HU166)", 830, 260),
        ("m5", "t4: Solución / Reparación&#xa;(HU166)", 1020, 180),
        ("m6", "t5: Cierre / Conformidad&#xa;(HU167/HU168)", 1220, 100),
    ]

    # Create milestone points and waveform
    prev_id = None
    for idx, (mid, mlbl, mx, my) in enumerate(milestones):
        pt = ET.SubElement(root_cell, "mxCell", id=mid, value="", style="ellipse;whiteSpace=wrap;html=1;fillColor=#0284c7;strokeColor=#0369a1;", vertex="1", parent="1")
        sub_geo(pt, x=mx - 5, y=my - 5, width=10, height=10)

        # Annotation above milestone
        ann = ET.SubElement(root_cell, "mxCell", id=f"ann_{mid}", value=mlbl, style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=bottom;fontSize=10;fontStyle=1;fontColor=#0f172a;", vertex="1", parent="1")
        sub_geo(ann, x=mx - 65, y=my - 45, width=130, height=35)

        # Connect with staircase line
        if prev_id:
            edge = ET.SubElement(root_cell, "mxCell", id=f"edge_step_{idx}", value="", style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0284c7;strokeWidth=2.5;", edge="1", parent="1", source=prev_id, target=mid)
            sub_geo(edge, width=0, height=0, relative=1)
        prev_id = mid

    # Alternative rejection branch
    pt_rechazo = ET.SubElement(root_cell, "mxCell", id="m_rechazo", value="", style="ellipse;whiteSpace=wrap;html=1;fillColor=#ef4444;strokeColor=#b91c1c;", vertex="1", parent="1")
    sub_geo(pt_rechazo, x=480, y=575, width=10, height=10)

    ann_r = ET.SubElement(root_cell, "mxCell", id="ann_rechazo", value="[alt: No aplica garantía / Improcedente]&#xa;Rechazo motivado", style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=top;fontSize=10;fontColor=#b91c1c;fontStyle=1;", vertex="1", parent="1")
    sub_geo(ann_r, x=410, y=595, width=150, height=35)

    edge_r = ET.SubElement(root_cell, "mxCell", id="edge_rechazo", value="", style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#ef4444;strokeWidth=2;dashed=1;", edge="1", parent="1", source="m2", target="m_rechazo")
    sub_geo(edge_r, width=0, height=0, relative=1)

    # Time ruler on bottom
    pt_r_start = ET.SubElement(root_cell, "mxCell", id="ruler_start", value="", style="ellipse;opacity=0;strokeColor=none;fillColor=none;", vertex="1", parent="1")
    sub_geo(pt_r_start, x=170, y=680, width=2, height=2)
    pt_r_end = ET.SubElement(root_cell, "mxCell", id="ruler_end", value="", style="ellipse;opacity=0;strokeColor=none;fillColor=none;", vertex="1", parent="1")
    sub_geo(pt_r_end, x=1320, y=680, width=2, height=2)

    ruler = ET.SubElement(root_cell, "mxCell", id="time_ruler", value="Eje Temporal / Progresión de Ciclo de Vida del Ticket de Posventa", style="endArrow=classic;html=1;strokeColor=#475569;strokeWidth=1.5;fontSize=11;fontStyle=1;align=center;", edge="1", parent="1", source="ruler_start", target="ruler_end")
    sub_geo(ruler, width=0, height=0, relative=1)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(drawio_path, encoding="utf-8", xml_declaration=True)
    print(f"Generado {drawio_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("Iniciando generación de diagramas para CU33...")
    generate_matrix()
    generate_robustness()
    generate_sequence()
    generate_communication()
    generate_classes()
    generate_timing()
    print("Todos los diagramas para CU33 fueron generados exitosamente.")

if __name__ == "__main__":
    main()
