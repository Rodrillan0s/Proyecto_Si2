import os
import html

os.makedirs('docs/diagramas/c4', exist_ok=True)

# Specification of the 8 Real Modules
modules_c4 = [
    {
        "id": "01_gestion_usuarios",
        "tab": "1. Usuarios",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Gestión de Usuarios",
        "mmd_filename": "c4_component_01_gestion_usuarios.mmd",
        "boundary_name": "API Backend [FastAPI + Uvicorn]",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Interfaz web para administración de usuarios y roles", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "App móvil para inicio de sesión de operadores", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"x": 80, "y": 200, "w": 940, "h": 460},
        "components": [
            {"id": "c1", "name": "Auth & Recovery Controller", "type": "FastAPI Router", "desc": "Login, refresh token y recuperación (auth_routes.py)", "x": 120, "y": 260, "w": 250, "h": 80},
            {"id": "c2", "name": "Users & Roles Controller", "type": "FastAPI Router", "desc": "Gestión de usuarios, roles y empresas (users_routes.py)", "x": 580, "y": 260, "w": 250, "h": 80},
            
            {"id": "s1", "name": "Auth & Security Service", "type": "Python Service", "desc": "Validación JWT, hash contraseñas y RBAC (auth_services.py)", "x": 120, "y": 390, "w": 250, "h": 80},
            {"id": "s2", "name": "Users & Tenant Service", "type": "Python Service", "desc": "Lógica multi-inquilino y perfiles (users_services.py)", "x": 480, "y": 390, "w": 250, "h": 80},
            {"id": "a1", "name": "Email Brevo Adapter", "type": "Python Client", "desc": "Envío de correos de recuperación (email_service.py)", "x": 780, "y": 390, "w": 200, "h": 80},

            {"id": "r1", "name": "Auth & Users Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de usuarios, roles y seguridad (auth_repos.py)", "x": 300, "y": 520, "w": 280, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste t_usuario, t_rol, t_empresa, t_persona", "x": 280, "y": 720, "w": 320, "h": 90}
        ],
        "externals": [
            {"id": "brevo", "name": "Brevo API", "type": "Servicio Externo", "desc": "Servicio de correos transaccionales", "x": 770, "y": 720, "w": 220, "h": 90}
        ],
        "links": [
            ("web", "c1", "Login y recuperación [JSON/HTTPS]"),
            ("web", "c2", "Administra usuarios y roles [JSON/HTTPS]"),
            ("mobile", "c1", "Autenticación móvil [JSON/HTTPS]"),
            ("c1", "s1", "Delega autenticación"),
            ("c2", "s2", "Delega perfiles"),
            ("s1", "a1", "Solicita envío de correo"),
            ("a1", "brevo", "HTTPS/REST"),
            ("s1", "r1", "Consulta credenciales"),
            ("s2", "r1", "Persiste usuario"),
            ("r1", "db", "SQL/TCP")
        ]
    },
    {
        "id": "02_gestion_proyectos",
        "tab": "2. Proyectos",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Gestión de Proyectos",
        "mmd_filename": "c4_component_02_gestion_proyectos.mmd",
        "boundary_name": "API Backend [FastAPI + Uvicorn]",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Administración de obras y estructuras", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Supervisión en terreno y avance", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"x": 80, "y": 200, "w": 940, "h": 460},
        "components": [
            {"id": "c1", "name": "Obra & Estructura Controller", "type": "FastAPI Router", "desc": "Rutas de proyectos y estructuras (obra_routes.py)", "x": 100, "y": 260, "w": 240, "h": 80},
            {"id": "c2", "name": "Avance de Obra Controller", "type": "FastAPI Router", "desc": "Registro de avances físicos (avance_routes.py)", "x": 420, "y": 260, "w": 230, "h": 80},
            {"id": "c3", "name": "Consulta Técnica Controller", "type": "FastAPI Router", "desc": "Ciclo de vida de RFIs (consulta_tecnica_routes.py)", "x": 720, "y": 260, "w": 240, "h": 80},
            
            {"id": "s1", "name": "Obra Service", "type": "Python Service", "desc": "Lógica de proyectos y jerarquías (obra_services.py)", "x": 100, "y": 390, "w": 240, "h": 80},
            {"id": "s2", "name": "Avance Service", "type": "Python Service", "desc": "Cálculo de avances acumulados (avance_services.py)", "x": 420, "y": 390, "w": 230, "h": 80},
            {"id": "s3", "name": "Consulta Técnica Service", "type": "Python Service", "desc": "Flujo de estados y respuestas RFI (consulta_tecnica_services.py)", "x": 720, "y": 390, "w": 240, "h": 80},

            {"id": "r1", "name": "Proyectos Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de obras, frentes y avances (obra_repos.py)", "x": 240, "y": 520, "w": 260, "h": 80},
            {"id": "r2", "name": "Consulta Técnica Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Trazabilidad e historial de RFIs (consulta_tecnica_repos.py)", "x": 600, "y": 520, "w": 260, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste t_obra, t_estructura, t_avance, t_consulta_tecnica", "x": 390, "y": 720, "w": 320, "h": 90}
        ],
        "externals": [],
        "links": [
            ("web", "c1", "Gestiona proyectos [JSON/HTTPS]"),
            ("web", "c2", "Consulta avances [JSON/HTTPS]"),
            ("web", "c3", "Gestiona consultas RFI [JSON/HTTPS]"),
            ("mobile", "c1", "Consulta asignación [JSON/HTTPS]"),
            ("mobile", "c2", "Registra avance [JSON/HTTPS]"),
            ("mobile", "c3", "Reporta RFI [JSON/HTTPS]"),
            ("c1", "s1", "Delega proyecto"),
            ("c2", "s2", "Delega avance"),
            ("c3", "s3", "Delega RFI"),
            ("s1", "r1", "Persiste obra"),
            ("s2", "r1", "Persiste avance"),
            ("s3", "r2", "Persiste consulta"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP")
        ]
    },
    {
        "id": "03_inventario_materiales",
        "tab": "3. Inventario",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Inventario y Materiales",
        "mmd_filename": "c4_component_03_inventario_materiales.mmd",
        "boundary_name": "API Backend [FastAPI + Uvicorn]",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Control de almacén y compras", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Entradas, salidas y recepciones físicas", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"x": 80, "y": 200, "w": 940, "h": 460},
        "components": [
            {"id": "c1", "name": "Inventario Controller", "type": "FastAPI Router", "desc": "Rutas para kardex y ajustes CU35/36 (inventario_routes.py)", "x": 100, "y": 260, "w": 240, "h": 80},
            {"id": "c2", "name": "Compras Controller", "type": "FastAPI Router", "desc": "Órdenes de compra y recepciones (compras_routes.py)", "x": 420, "y": 260, "w": 230, "h": 80},
            {"id": "c3", "name": "Material Controller", "type": "FastAPI Router", "desc": "Catálogo de insumos y precios (material_routes.py)", "x": 720, "y": 260, "w": 240, "h": 80},
            
            {"id": "s1", "name": "Inventario Service", "type": "Python Service", "desc": "Movimientos de almacén y control de saldos (inventario_services.py)", "x": 100, "y": 390, "w": 240, "h": 80},
            {"id": "s2", "name": "Compras Service", "type": "Python Service", "desc": "Validación de órdenes y compras (compras_services.py)", "x": 420, "y": 390, "w": 230, "h": 80},
            {"id": "s3", "name": "Material Service", "type": "Python Service", "desc": "Mantenimiento del catálogo base (material_services.py)", "x": 720, "y": 390, "w": 240, "h": 80},

            {"id": "r1", "name": "Inventario Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Kardex y t_movimiento_almacen (inventario_repos.py)", "x": 100, "y": 520, "w": 240, "h": 80},
            {"id": "r2", "name": "Compras Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Órdenes y recepciones de compra (compras_repos.py)", "x": 420, "y": 520, "w": 230, "h": 80},
            {"id": "r3", "name": "Material Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Tablas de materiales y categorías (material_repos.py)", "x": 720, "y": 520, "w": 240, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste t_material, t_movimiento_almacen, t_orden_compra", "x": 390, "y": 720, "w": 320, "h": 90}
        ],
        "externals": [],
        "links": [
            ("web", "c1", "Kardex y ajustes [JSON/HTTPS]"),
            ("web", "c2", "Órdenes de compra [JSON/HTTPS]"),
            ("web", "c3", "Catálogo [JSON/HTTPS]"),
            ("mobile", "c1", "Entradas y salidas [JSON/HTTPS]"),
            ("mobile", "c2", "Recepciona insumos [JSON/HTTPS]"),
            ("c1", "s1", "Delega ajuste"),
            ("c2", "s2", "Delega compra"),
            ("c3", "s3", "Delega catálogo"),
            ("s1", "r1", "Persiste movimiento"),
            ("s2", "r2", "Persiste compra"),
            ("s2", "r1", "Actualiza stock"),
            ("s3", "r3", "Actualiza material"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP"),
            ("r3", "db", "SQL/TCP")
        ]
    },
    {
        "id": "04_presupuesto_costos",
        "tab": "4. Costos",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Presupuesto y Costos",
        "mmd_filename": "c4_component_04_presupuesto_costos.mmd",
        "boundary_name": "API Backend [FastAPI + Uvicorn]",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Gestión financiera, APU y costos", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Consulta de costos y estimaciones", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"x": 80, "y": 200, "w": 940, "h": 460},
        "components": [
            {"id": "c1", "name": "Presupuesto & APU Controller", "type": "FastAPI Router", "desc": "Rutas de partidas, APU e insumos (presupuesto_routes.py)", "x": 150, "y": 260, "w": 260, "h": 80},
            {"id": "c2", "name": "Control Costos Controller", "type": "FastAPI Router", "desc": "Costos ejecutados y estimaciones (control_costos_routes.py)", "x": 560, "y": 260, "w": 260, "h": 80},
            
            {"id": "s1", "name": "Presupuesto & APU Service", "type": "Python Service", "desc": "Cálculo de precios unitarios y partidas (presupuesto_services.py)", "x": 150, "y": 390, "w": 260, "h": 80},
            {"id": "s2", "name": "Control Costos Service", "type": "Python Service", "desc": "Desviaciones de costo y afectaciones (control_costos_services.py)", "x": 560, "y": 390, "w": 260, "h": 80},

            {"id": "r1", "name": "Presupuesto Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de partidas y APUs (presupuesto_repos.py)", "x": 150, "y": 520, "w": 260, "h": 80},
            {"id": "r2", "name": "Costos Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de costos y órdenes de cambio (control_costos_repos.py)", "x": 560, "y": 520, "w": 260, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste t_presupuesto, t_partida, t_apu, t_control_costo", "x": 360, "y": 720, "w": 320, "h": 90}
        ],
        "externals": [],
        "links": [
            ("web", "c1", "Administra presupuestos [JSON/HTTPS]"),
            ("web", "c2", "Audita costos finales [JSON/HTTPS]"),
            ("mobile", "c2", "Consulta costos en obra [JSON/HTTPS]"),
            ("c1", "s1", "Delega presupuesto"),
            ("c2", "s2", "Delega liquidación"),
            ("s1", "r1", "Persiste partida"),
            ("s2", "r2", "Persiste costo ejecutado"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP")
        ]
    },
    {
        "id": "05_actividades_ordenes",
        "tab": "5. Actividades",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Actividades y Órdenes de Trabajo",
        "mmd_filename": "c4_component_05_actividades_ordenes.mmd",
        "boundary_name": "API Backend [FastAPI + Uvicorn]",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Planificación y asignación operativa", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Ejecución de órdenes e incidencias", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"x": 70, "y": 200, "w": 960, "h": 460},
        "components": [
            {"id": "c1", "name": "Cronograma Controller", "type": "FastAPI Router", "desc": "Rutas de planificación CU39 (cronograma_routes.py)", "x": 90, "y": 260, "w": 220, "h": 80},
            {"id": "c2", "name": "Orden Trabajo Controller", "type": "FastAPI Router", "desc": "Asignación de cuadrillas y tareas (orden_Trabajo_routes.py)", "x": 350, "y": 260, "w": 220, "h": 80},
            {"id": "c3", "name": "Incidencias Controller", "type": "FastAPI Router", "desc": "Registro de eventos e incidencias (incidencia_routes.py)", "x": 610, "y": 260, "w": 220, "h": 80},
            
            {"id": "s1", "name": "Cronograma Service", "type": "Python Service", "desc": "Diagrama de Gantt y dependencias (cronograma_services.py)", "x": 90, "y": 390, "w": 220, "h": 80},
            {"id": "s2", "name": "Orden Trabajo Service", "type": "Python Service", "desc": "Control de cuadrillas y ejecución (orden_Trabajo_services.py)", "x": 350, "y": 390, "w": 220, "h": 80},
            {"id": "s3", "name": "Incidencias Service", "type": "Python Service", "desc": "Resolución y evidencias multimedia (incidencia_services.py)", "x": 610, "y": 390, "w": 220, "h": 80},
            {"id": "a1", "name": "Cloudinary Adapter", "type": "Python Client", "desc": "Subida segura de fotos y planos (incidencia_services.py)", "x": 840, "y": 390, "w": 180, "h": 80},

            {"id": "r1", "name": "Cronograma Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de hitos y tareas (cronograma_repos.py)", "x": 90, "y": 520, "w": 220, "h": 80},
            {"id": "r2", "name": "Orden Trabajo Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de asignaciones de cuadrilla (orden_Trabajo_repos.py)", "x": 350, "y": 520, "w": 220, "h": 80},
            {"id": "r3", "name": "Incidencias Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de incidencias y evidencias (incidencia_repos.py)", "x": 610, "y": 520, "w": 220, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste t_cronograma, t_orden_trabajo, t_incidencia", "x": 280, "y": 720, "w": 320, "h": 90}
        ],
        "externals": [
            {"id": "cloudinary", "name": "Cloudinary API", "type": "Servicio Externo", "desc": "Almacenamiento multimedia en la nube", "x": 780, "y": 720, "w": 220, "h": 90}
        ],
        "links": [
            ("web", "c1", "Planifica cronograma [JSON/HTTPS]"),
            ("web", "c2", "Emite órdenes [JSON/HTTPS]"),
            ("web", "c3", "Monitorea incidencias [JSON/HTTPS]"),
            ("mobile", "c2", "Ejecuta órdenes [JSON/HTTPS]"),
            ("mobile", "c3", "Reporta incidencias [JSON/HTTPS]"),
            ("c1", "s1", "Delega cronograma"),
            ("c2", "s2", "Delega orden"),
            ("c3", "s3", "Delega incidencia"),
            ("s3", "a1", "Sube evidencias multimedia"),
            ("a1", "cloudinary", "HTTPS/REST"),
            ("s1", "r1", "Persiste tarea"),
            ("s2", "r2", "Persiste asignación"),
            ("s3", "r3", "Persiste incidencia"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP"),
            ("r3", "db", "SQL/TCP")
        ]
    },
    {
        "id": "06_reportes_analisis",
        "tab": "6. Reportes",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Reportes y Análisis",
        "mmd_filename": "c4_component_06_reportes_analisis.mmd",
        "boundary_name": "API Backend [FastAPI + Uvicorn]",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Generación y visualización de reportes", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Descarga de reportes operativos", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"x": 80, "y": 200, "w": 940, "h": 460},
        "components": [
            {"id": "c1", "name": "Reportes Controller", "type": "FastAPI Router", "desc": "Rutas de generación y descarga PDF/Excel (reportes_routes.py)", "x": 120, "y": 260, "w": 250, "h": 80},
            {"id": "c2", "name": "Notificaciones Controller", "type": "FastAPI Router", "desc": "Alertas y auditoría del sistema (notificaciones_routes.py)", "x": 580, "y": 260, "w": 250, "h": 80},
            
            {"id": "s1", "name": "Reportes Service", "type": "Python Service", "desc": "Motor de reportes PDF/Excel (reportes_services.py)", "x": 120, "y": 390, "w": 250, "h": 80},
            {"id": "s2", "name": "Notificaciones Service", "type": "Python Service", "desc": "Gestión de eventos y bitácora (notificaciones_services.py)", "x": 480, "y": 390, "w": 250, "h": 80},
            {"id": "a1", "name": "Brevo Dispatch Adapter", "type": "Python Client", "desc": "Envío de reportes adjuntos (reportes/worker.py)", "x": 780, "y": 390, "w": 200, "h": 80},

            {"id": "r1", "name": "Reportes Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de archivos y programaciones (reportes_repos.py)", "x": 220, "y": 520, "w": 260, "h": 80},
            {"id": "r2", "name": "Notificaciones Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de alertas y bitácora (notificaciones_repos.py)", "x": 540, "y": 520, "w": 260, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste t_reporte_ejecucion, notificacion, t_bitacora", "x": 280, "y": 720, "w": 320, "h": 90}
        ],
        "externals": [
            {"id": "brevo", "name": "Brevo API", "type": "Servicio Externo", "desc": "Envío de correos y documentos adjuntos", "x": 770, "y": 720, "w": 220, "h": 90}
        ],
        "links": [
            ("web", "c1", "Solicita reportes [JSON/HTTPS]"),
            ("web", "c2", "Consulta alertas [JSON/HTTPS]"),
            ("mobile", "c1", "Descarga PDF [JSON/HTTPS]"),
            ("c1", "s1", "Delega generación"),
            ("c2", "s2", "Delega notificación"),
            ("s1", "a1", "Programa despacho por email"),
            ("a1", "brevo", "HTTPS/REST"),
            ("s1", "r1", "Persiste archivo"),
            ("s2", "r2", "Persiste alerta"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP")
        ]
    },
    {
        "id": "07_comercial_crm",
        "tab": "7. CRM",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Comercial y CRM",
        "mmd_filename": "c4_component_07_comercial_crm.mmd",
        "boundary_name": "API Backend [FastAPI + Uvicorn]",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Gestión de prospectos, unidades y pagos SaaS", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Consulta comercial de unidades", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"x": 70, "y": 200, "w": 960, "h": 460},
        "components": [
            {"id": "c1", "name": "CRM Controller", "type": "FastAPI Router", "desc": "Rutas de prospectos e interacciones (crm_routes.py)", "x": 100, "y": 260, "w": 210, "h": 80},
            {"id": "c2", "name": "Unidades Controller", "type": "FastAPI Router", "desc": "Catálogo de inmuebles y modelos (unidad_routes.py)", "x": 350, "y": 260, "w": 210, "h": 80},
            {"id": "c3", "name": "Suscripción & Pagos Controller", "type": "FastAPI Router", "desc": "Checkout Stripe y planes (pago_routes.py)", "x": 600, "y": 260, "w": 210, "h": 80},
            
            {"id": "s1", "name": "CRM Service", "type": "Python Service", "desc": "Embudo comercial y seguimiento (crm_services.py)", "x": 100, "y": 390, "w": 210, "h": 80},
            {"id": "s2", "name": "Unidades Service", "type": "Python Service", "desc": "Gestión de inmuebles y precios (unidad_services.py)", "x": 350, "y": 390, "w": 210, "h": 80},
            {"id": "s3", "name": "Pagos & SaaS Service", "type": "Python Service", "desc": "Cobros y renovación de planes (pago_services.py)", "x": 600, "y": 390, "w": 210, "h": 80},
            {"id": "a1", "name": "Stripe Gateway Adapter", "type": "Python Client", "desc": "Adaptador SDK Stripe (stripe_gateway.py)", "x": 840, "y": 390, "w": 170, "h": 80},

            {"id": "r1", "name": "CRM Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Clientes e interacciones (crm_repos.py)", "x": 100, "y": 520, "w": 210, "h": 80},
            {"id": "r2", "name": "Unidades Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Unidades y modelos (unidad_repos.py)", "x": 350, "y": 520, "w": 210, "h": 80},
            {"id": "r3", "name": "Pagos Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Planes y transacciones (pago_repos.py)", "x": 600, "y": 520, "w": 210, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste t_crm_cliente, t_unidad_construccion, t_pago_suscripcion", "x": 280, "y": 720, "w": 320, "h": 90}
        ],
        "externals": [
            {"id": "stripe", "name": "Stripe API", "type": "Servicio Externo", "desc": "Pasarela de pagos en línea", "x": 780, "y": 720, "w": 220, "h": 90}
        ],
        "links": [
            ("web", "c1", "Gestiona prospectos [JSON/HTTPS]"),
            ("web", "c2", "Catálogo de unidades [JSON/HTTPS]"),
            ("web", "c3", "Pago de plan [JSON/HTTPS]"),
            ("mobile", "c2", "Consulta inmuebles [JSON/HTTPS]"),
            ("c1", "s1", "Delega CRM"),
            ("c2", "s2", "Delega unidades"),
            ("c3", "s3", "Delega pago"),
            ("s3", "a1", "Ejecuta cobro"),
            ("a1", "stripe", "HTTPS/REST"),
            ("s1", "r1", "Persiste cliente"),
            ("s2", "r2", "Persiste unidad"),
            ("s3", "r3", "Persiste pago"),
            ("r1", "db", "SQL/TCP"),
            ("r2", "db", "SQL/TCP"),
            ("r3", "db", "SQL/TCP")
        ]
    },
    {
        "id": "08_asistente_inteligente",
        "tab": "8. IA",
        "title": "Diagrama de Componentes C4 (Nivel 3) - Asistente Inteligente",
        "mmd_filename": "c4_component_08_asistente_inteligente.mmd",
        "boundary_name": "API Backend [FastAPI + Uvicorn]",
        "consumers": [
            {"id": "web", "name": "Aplicación Web", "tech": "Angular 18 + Tailwind CSS", "desc": "Chatbot interactivo comercial y de obra", "x": 250, "y": 60, "w": 220, "h": 80},
            {"id": "mobile", "name": "Aplicación Móvil", "tech": "Flutter + Dart", "desc": "Consultas por voz y texto al asistente", "x": 600, "y": 60, "w": 220, "h": 80}
        ],
        "boundary": {"x": 80, "y": 200, "w": 940, "h": 460},
        "components": [
            {"id": "c1", "name": "AI Assistant Controller", "type": "FastAPI Router", "desc": "Rutas de chat, sugerencias y CRM (ai_routes.py)", "x": 200, "y": 260, "w": 260, "h": 80},
            
            {"id": "s1", "name": "AI Engine Service", "type": "Python Service", "desc": "Orquestación de prompts y memoria (ai/ai_service.py)", "x": 120, "y": 390, "w": 240, "h": 80},
            {"id": "s2", "name": "Context Builder Service", "type": "Python Service", "desc": "Extracción de contexto de obra y empresa (context_builder.py)", "x": 420, "y": 390, "w": 250, "h": 80},
            {"id": "a1", "name": "Gemini & Groq Adapter", "type": "Python Client", "desc": "Cliente SDK a modelos LLM (gemini_provider.py)", "x": 740, "y": 390, "w": 220, "h": 80},

            {"id": "r1", "name": "Assistant Repository", "type": "SQLAlchemy / PostgreSQL", "desc": "Persistencia de sesiones de chat y mensajes (assistant_repos.py)", "x": 200, "y": 520, "w": 260, "h": 80}
        ],
        "persistence": [
            {"id": "db", "name": "Base de Datos Principal", "type": "PostgreSQL (schema: obras)", "desc": "Persiste t_asistente_conversacion, t_asistente_mensaje", "x": 220, "y": 720, "w": 320, "h": 90}
        ],
        "externals": [
            {"id": "gemini", "name": "Gemini / Groq API", "type": "Servicio Externo", "desc": "Modelos LLM de lenguaje natural para inferencia", "x": 730, "y": 720, "w": 240, "h": 90}
        ],
        "links": [
            ("web", "c1", "Envía preguntas y chat [JSON/HTTPS]"),
            ("mobile", "c1", "Consultas operativas [JSON/HTTPS]"),
            ("c1", "s1", "Delega consulta IA"),
            ("s1", "s2", "Solicita contexto de negocio"),
            ("s1", "a1", "Envía prompt enriquecido"),
            ("a1", "gemini", "Inferencia HTTPS/REST"),
            ("s1", "r1", "Persiste conversación"),
            ("r1", "db", "SQL/TCP")
        ]
    }
]

# 1. Generate individual .mmd files
for mod in modules_c4:
    mmd = []
    mmd.append("C4Component")
    mmd.append(f'    title {mod["title"]}\n')
    
    mmd.append("    %% 1. Contenedores consumidores (Arriba)")
    for c in mod["consumers"]:
        mmd.append(f'    Container({c["id"]}, "{c["name"]}", "{c["tech"]}", "{c["desc"]}")')
    mmd.append("")
    
    mmd.append(f'    %% 2. Límite del Contenedor analizado (Centro)')
    mmd.append(f'    Container_Boundary(api, "{mod["boundary_name"]}") {{')
    for comp in mod["components"]:
        mmd.append(f'        Component({comp["id"]}, "{comp["name"]}", "{comp["type"]}", "{comp["desc"]}")')
    mmd.append("    }\n")
    
    mmd.append("    %% 3. Persistencia y Sistemas Externos (Abajo)")
    for p in mod["persistence"]:
        mmd.append(f'    ContainerDb({p["id"]}, "{p["name"]}", "{p["type"]}", "{p["desc"]}")')
    for ext in mod["externals"]:
        mmd.append(f'    System_Ext({ext["id"]}, "{ext["name"]}", "{ext["desc"]}")')
    mmd.append("")
    
    mmd.append("    %% 4. Relaciones unidireccionales etiquetadas")
    for src, tgt, label in mod["links"]:
        parts = label.split(" [")
        action = parts[0]
        tech = parts[1].replace("]", "") if len(parts) > 1 else ""
        if tech:
            mmd.append(f'    Rel({src}, {tgt}, "{action}", "{tech}")')
        else:
            mmd.append(f'    Rel({src}, {tgt}, "{action}")')

    mmd_content = "\n".join(mmd)
    out_mmd_path = f"docs/diagramas/c4/{mod['mmd_filename']}"
    with open(out_mmd_path, "w", encoding="utf-8") as f:
        f.write(mmd_content)
    print(f"Generated MMD: {out_mmd_path}")

# 2. Generate Consolidated Draw.io XML with 8 Tabs
xml = []
xml.append('<?xml version="1.0" encoding="UTF-8"?>')
xml.append('<mxfile host="app.diagrams.net" modified="2026-11-22T12:05:00.000Z" agent="Antigravity" version="24.0.0" type="device">')

for mod in modules_c4:
    xml.append(f'  <diagram id="{mod["id"]}" name="{mod["tab"]}">')
    xml.append('    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1200" pageHeight="900" background="#FFFFFF" math="0" shadow="0">')
    xml.append('      <root>')
    xml.append('        <mxCell id="0" />')
    xml.append('        <mxCell id="1" parent="0" />')

    # Title
    t_val = f"&lt;b style=&quot;font-size:14px;&quot;&gt;{html.escape(mod['title'])}&lt;/b&gt;"
    xml.append(f'        <mxCell id="title_{mod["id"]}" value="{t_val}" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontFamily=Arial;" vertex="1" parent="1">')
    xml.append('          <mxGeometry x="50" y="20" width="700" height="30" as="geometry" />')
    xml.append('        </mxCell>')

    # Consumers
    for c in mod["consumers"]:
        val = f"&lt;b&gt;{html.escape(c['name'])}&lt;/b&gt;&lt;br/&gt;&lt;i style=&quot;font-size:10px;&quot;&gt;[{html.escape(c['tech'])}]&lt;/i&gt;&lt;br/&gt;&lt;span style=&quot;font-size:9.5px;&quot;&gt;{html.escape(c['desc'])}&lt;/span&gt;"
        xml.append(f'        <mxCell id="{c["id"]}" value="{val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#2B6CB0;strokeColor=#1A365D;strokeWidth=1.3;fontFamily=Arial;fontColor=#FFFFFF;align=center;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{c["x"]}" y="{c["y"]}" width="{c["w"]}" height="{c["h"]}" as="geometry" />')
        xml.append('        </mxCell>')

    # Boundary
    b = mod["boundary"]
    b_val = f"&lt;b&gt;Container:&lt;/b&gt; {html.escape(mod['boundary_name'])}"
    xml.append(f'        <mxCell id="boundary" value="{b_val}" style="swimlane;fontStyle=1;align=left;spacingLeft=10;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=0;resizeParentMax=0;resizeLast=0;collapsible=0;marginBottom=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#4A5568;strokeWidth=1.5;strokeDasharray=4 4;fontFamily=Arial;fontSize=11;fontColor=#2D3748;" vertex="1" parent="1">')
    xml.append(f'          <mxGeometry x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" as="geometry" />')
    xml.append('        </mxCell>')

    # Components
    for comp in mod["components"]:
        c_val = f"&lt;b style=&quot;font-size:11px;&quot;&gt;{html.escape(comp['name'])}&lt;/b&gt;&lt;br/&gt;&lt;i style=&quot;font-size:9.5px;&quot;&gt;[Component: {html.escape(comp['type'])}]&lt;/i&gt;&lt;br/&gt;&lt;span style=&quot;font-size:9px;&quot;&gt;{html.escape(comp['desc'])}&lt;/span&gt;"
        xml.append(f'        <mxCell id="{comp["id"]}" value="{c_val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#4299E1;strokeColor=#2B6CB0;strokeWidth=1.2;fontFamily=Arial;fontColor=#FFFFFF;align=center;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{comp["x"]}" y="{comp["y"]}" width="{comp["w"]}" height="{comp["h"]}" as="geometry" />')
        xml.append('        </mxCell>')

    # Persistence
    for p in mod["persistence"]:
        p_val = f"&lt;b style=&quot;font-size:11px;&quot;&gt;{html.escape(p['name'])}&lt;/b&gt;&lt;br/&gt;&lt;i style=&quot;font-size:9.5px;&quot;&gt;[ContainerDb: {html.escape(p['type'])}]&lt;/i&gt;&lt;br/&gt;&lt;span style=&quot;font-size:9px;&quot;&gt;{html.escape(p['desc'])}&lt;/span&gt;"
        xml.append(f'        <mxCell id="{p["id"]}" value="{p_val}" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=10;fillColor=#2B6CB0;strokeColor=#1A365D;strokeWidth=1.2;fontFamily=Arial;fontColor=#FFFFFF;align=center;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{p["x"]}" y="{p["y"]}" width="{p["w"]}" height="{p["h"]}" as="geometry" />')
        xml.append('        </mxCell>')

    # Externals
    for ext in mod["externals"]:
        e_val = f"&lt;b style=&quot;font-size:11px;&quot;&gt;{html.escape(ext['name'])}&lt;/b&gt;&lt;br/&gt;&lt;i style=&quot;font-size:9.5px;&quot;&gt;[System_Ext: {html.escape(ext['type'])}]&lt;/i&gt;&lt;br/&gt;&lt;span style=&quot;font-size:9px;&quot;&gt;{html.escape(ext['desc'])}&lt;/span&gt;"
        xml.append(f'        <mxCell id="{ext["id"]}" value="{e_val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#718096;strokeColor=#4A5568;strokeWidth=1.2;fontFamily=Arial;fontColor=#FFFFFF;align=center;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{ext["x"]}" y="{ext["y"]}" width="{ext["w"]}" height="{ext["h"]}" as="geometry" />')
        xml.append('        </mxCell>')

    # Links
    link_counter = 100
    for src, tgt, label in mod["links"]:
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

print(f"Generated 8-tab C4 Draw.io file: {drawio_c4_path}")
