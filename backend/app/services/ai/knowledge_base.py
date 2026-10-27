"""Base de conocimiento verificada del sistema OBRATEC.
Contiene rutas oficiales de Angular, módulos, procedimientos administrativos y roles autorizados.
Prohíbe estrictamente la invención de pantallas, rutas inexistentes o botones que no existan en la plataforma.
"""
from typing import Any

MODULOS_OBRATEC = [
    {
        "id": "proyectos_obras",
        "nombre": "Obras y Proyectos",
        "ruta": "/proyectos",
        "descripcion": "Gestión integral de obras de construcción, asignación de personal y contratos.",
        "permiso_ver": "Visualizar_obras",
        "capacidades": [
            "Creación y edición de obras (código, nombre, tipo, presupuesto, moneda)",
            "Configuración de fechas de inicio, fin y estado (PLANIFICACION, EN_PROGRESO, SUSPENDIDA, FINALIZADA)",
            "Asignación de jefes de obra, trabajadores y clientes vinculados"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"]
    },
    {
        "id": "control_costos",
        "nombre": "Control de Costos",
        "ruta": "/control-costos",
        "descripcion": "Monitoreo financiero, presupuesto aprobado vs costos reales ejecutados y líneas base.",
        "permiso_ver": "Visualizar_control_costos",
        "capacidades": [
            "Líneas base de costos por obra con historial de versiones",
            "Comparativo de costo proyectado vs ejecutado por categoría (materiales, mano de obra, equipos)",
            "Desviaciones porcentuales y saldo disponible",
            "Métricas financieras consolidadas"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA"]
    },
    {
        "id": "inventario",
        "nombre": "Inventario de Materiales",
        "ruta": "/inventario",
        "descripcion": "Catálogo de insumos de construcción, existencias en almacén y niveles mínimos.",
        "permiso_ver": "Visualizar_inventario",
        "capacidades": [
            "Registro de materiales con código único, nombre, categoría y unidad de medida",
            "Consulta de stock actual y umbrales de stock mínimo de alerta",
            "Control de existencias y valoración de inventario"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"]
    },
    {
        "id": "compras",
        "nombre": "Gestión de Compras",
        "ruta": "/compras",
        "descripcion": "Órdenes de compra de insumos, proveedores asociados y recepciones.",
        "permiso_ver": "Visualizar_ordenes_compra",
        "capacidades": [
            "Emisión de órdenes de compra con detalle de insumos, precios pactados y proveedor",
            "Flujo de estados: BORRADOR -> SOLICITADA -> APROBADA -> EN_TRANSITO -> RECIBIDA -> ANULADA",
            "Recepción física parcial o total en almacén"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA"]
    },
    {
        "id": "ordenes_trabajo",
        "nombre": "Órdenes de Trabajo",
        "ruta": "/ordenes-trabajo",
        "descripcion": "Planificación y asignación de tareas operativas en campo para cuadrillas y personal.",
        "permiso_ver": "Visualizar_ordenes_trabajo",
        "capacidades": [
            "Creación de órdenes de trabajo por obra con tipo de trabajo y cuadrilla",
            "Asignación de trabajadores específicos por tarea",
            "Fechas límite de ejecución y seguimiento de avance",
            "Estados: PENDIENTE, EN_PROCESO, FINALIZADA, CANCELADA"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA", "TRABAJADOR"]
    },
    {
        "id": "incidencias",
        "nombre": "Incidencias de Obra",
        "ruta": "/incidencias",
        "descripcion": "Reporte y resolución de fallas técnicas, averías y problemas constructivos en campo.",
        "permiso_ver": "Visualizar_incidencias",
        "capacidades": [
            "Registro de incidencias con prioridad (BAJA, MEDIA, ALTA, CRITICA)",
            "Vinculación a obra y unidad constructiva específica",
            "Carga de evidencias fotográficas",
            "Transiciones controladas de estado: ABIERTA -> ASIGNADA -> EN_PROCESO -> PENDIENTE_VALIDACION -> RESUELTA -> CERRADA"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA", "TRABAJADOR"]
    },
    {
        "id": "consultas_tecnicas",
        "nombre": "Consultas Técnicas (RFI)",
        "ruta": "/consultas-tecnicas",
        "descripcion": "Solicitudes de información y aclaración de planos o especificaciones de obra.",
        "permiso_ver": "Visualizar_consultas_tecnicas",
        "capacidades": [
            "Emisión formal de RFI con asunto, detalle y nivel de prioridad",
            "Asignación a especialistas o proyectistas para respuesta",
            "Cierre y registro histórico de aclaraciones técnicas"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"]
    },
    {
        "id": "reportes_analitica",
        "nombre": "Centro de Reportes",
        "ruta": "/reportes",
        "descripcion": "Generación de reportes ejecutivos, analítica de obra y exportaciones PDF/Excel.",
        "permiso_ver": "Visualizar_reportes",
        "capacidades": [
            "Catálogo oficial de 12 reportes deterministas",
            "Filtros avanzados por obra, rango de fechas y categorías",
            "Exportación descargable con hash de integridad SHA-256",
            "Generador de consultas analíticas unificadas"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"]
    },
    {
        "id": "equipo_maquinaria",
        "nombre": "Equipos y Maquinaria",
        "ruta": "/equipos-maquinaria",
        "descripcion": "Parque de maquinaria de la empresa y asignaciones a obras específicas.",
        "permiso_ver": "Visualizar_equipos_maquinaria",
        "capacidades": [
            "Catálogo de maquinaria propia o alquilada (marca, modelo, placa/código)",
            "Asignación de equipos a proyectos con fecha de inicio y retiro",
            "Estado operativo (DISPONIBLE, ASIGNADO, MANTENIMIENTO, BAJA)"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"]
    },
    {
        "id": "usuarios_roles",
        "nombre": "Usuarios y Permisos",
        "ruta": "/usuarios",
        "descripcion": "Administración de cuentas, asignación de roles y control de acceso RBAC.",
        "permiso_ver": "Visualizar_usuarios",
        "capacidades": [
            "Creación individual y registro en lote (grupo de usuarios) por empresa",
            "Asignación de roles: ADMINISTRADOR, ADMINISTRADOR_EMPRESA, JEFE DE OBRA, CLIENTE, TRABAJADOR",
            "Control de estado de cuenta (ACTIVO / INACTIVO)",
            "Generación segura de credenciales temporales"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA"]
    },
    {
        "id": "suscripciones_planes",
        "nombre": "Suscripciones y Planes SaaS",
        "ruta": "/suscripciones",
        "descripcion": "Control de planes (Básico, Profesional, Empresarial) y cupos de inteligencia artificial.",
        "permiso_ver": "Visualizar_empresa",
        "capacidades": [
            "Visualización del plan vigente de la empresa",
            "Capacidades habilitadas (reportes, IA, automatización)",
            "Consumo del cupo mensual de consultas IA (configurable según plan contratado)",
            "Gestión de planes del sistema (exclusivo Super Admin en /configuracion-planes)"
        ],
        "roles_permitidos": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA"]
    },
    {
        "id": "backup_restore",
        "nombre": "Copias de Seguridad (Backup & Restore)",
        "ruta": "/backup",
        "descripcion": "Gestión de respaldos de bases de datos PostgreSQL mediante daemon autónomo.",
        "permiso_ver": "Administrar_sistema",
        "capacidades": [
            "Generación de copias de seguridad inmediatas",
            "Programación de backups periódicos",
            "Descarga de archivos de respaldo",
            "Restauración desde la aplicación permanece bloqueada durante la integración conforme a AGENTS.md"
        ],
        "roles_permitidos": ["ADMINISTRADOR"]
    }
]

PROCEDIMIENTOS_OPERATIVOS = [
    {
        "tema": "Creación y configuración de nueva obra",
        "modulo": "proyectos_obras",
        "roles": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA"],
        "pasos": [
            "Ingresa al módulo Obras (/proyectos) desde la barra lateral.",
            "Haz clic en el botón '+ Nueva Obra'.",
            "Diligencia los datos obligatorios: Código identificador, Nombre de la obra, Tipo de proyecto y Presupuesto base.",
            "Define las fechas estimadas de inicio y término.",
            "Guarda el registro. Posteriormente, en el detalle de la obra podrás asignar personal y cargar presupuestos APU."
        ]
    },
    {
        "tema": "Registro de incidencia técnica",
        "modulo": "incidencias",
        "roles": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA", "TRABAJADOR"],
        "pasos": [
            "Navega a Incidencias (/incidencias).",
            "Selecciona '+ Reportar Incidencia'.",
            "Selecciona la Obra correspondiente y la Unidad de construcción (si aplica).",
            "Indica un título descriptivo y la prioridad (BAJA, MEDIA, ALTA o CRÍTICA).",
            "Describe el problema y adjunta fotografías de evidencia si dispones de ellas.",
            "Confirma el reporte. La incidencia iniciará en estado ABIERTA para ser asignada al responsable."
        ]
    },
    {
        "tema": "Aprobación de orden de compra",
        "modulo": "compras",
        "roles": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA"],
        "pasos": [
            "Accede a Gestión de Compras (/compras).",
            "Ubica la orden de compra en estado SOLICITADA.",
            "Revisa la lista de materiales requeridos, las cantidades y los precios unitarios cotizados.",
            "Verifica que el monto total esté alineado con el presupuesto de la obra.",
            "Haz clic en 'Aprobar'. La orden pasará a estado APROBADA para emisión al proveedor."
        ]
    },
    {
        "tema": "Planificación de Orden de Trabajo",
        "modulo": "ordenes_trabajo",
        "roles": ["ADMINISTRADOR", "ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"],
        "pasos": [
            "Ingresa a Órdenes de Trabajo (/ordenes-trabajo).",
            "Selecciona '+ Nueva Orden de Trabajo'.",
            "Escoge la Obra y especifica el tipo de trabajo a ejecutar.",
            "Asigna la cuadrilla o trabajadores responsables.",
            "Fija las fechas de inicio y finalización planificadas y guarda la orden."
        ]
    }
]


PLAN_MODULES = {
    'proyectos_obras': 'obras', 'control_costos': 'control_costos', 'inventario': 'inventario',
    'compras': 'compras', 'ordenes_trabajo': 'ordenes_trabajo', 'incidencias': 'incidencias',
    'consultas_tecnicas': 'obras', 'reportes_analitica': 'reportes', 'equipo_maquinaria': 'equipos',
    'usuarios_roles': 'usuarios', 'suscripciones_planes': None, 'backup_restore': None,
}
PROCEDURE_PERMISSIONS = {
    'proyectos_obras': {'Visualizar_obras', 'Registrar_obras'},
    'incidencias': {'Visualizar_incidencias', 'Registrar_incidencias'},
    'compras': {'Visualizar_ordenes_compra', 'Aprobar_ordenes_compra'},
    'ordenes_trabajo': {'Visualizar_ordenes_trabajo', 'Registrar_ordenes_trabajo'},
}


def buscar_conocimiento(texto: str, rol: str, permisos: frozenset | None = None,
                       modulos=None) -> dict[str, Any] | None:
    """Busca en la base de conocimiento de OBRATEC y retorna contexto relevante filtrado por permisos reales."""
    import re
    import unicodedata

    def _norm(s: str) -> str:
        return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

    t = _norm(texto)
    tokens = set(re.findall(r'[a-z0-9_]+', t))
    stop_words = {"de", "la", "el", "en", "un", "una", "los", "las", "para", "por", "obra", "obratec", "que", "existen"}

    def _modulo_visible(mod: dict) -> bool:
        if rol == "ADMINISTRADOR":
            return True
        if rol not in mod["roles_permitidos"]:
            return False
        if permisos is not None and mod.get("permiso_ver") and mod["permiso_ver"] not in permisos:
            return False
        plan_module = PLAN_MODULES.get(mod['id'])
        if modulos is not None and plan_module and plan_module not in modulos:
            return False
        return True

    # Si es pregunta de catálogo general de módulos o ayuda
    if any(k in tokens for k in ["modulos", "modulo", "menu", "funcionalidades", "ayuda", "funciona"]):
        modulos_permitidos = [
            {"nombre": m["nombre"], "ruta": m["ruta"], "descripcion": m["descripcion"]}
            for m in MODULOS_OBRATEC
            if _modulo_visible(m)
        ]
        return {
            "tipo": "resumen_sistema",
            "modulos": modulos_permitidos,
            "mensaje": "OBRATEC es una plataforma integral SaaS de gestión de obras civiles y construcción."
        }

    # 1. Buscar coincidencias específicas en módulos
    modulos_encontrados = []
    for mod in MODULOS_OBRATEC:
        if not _modulo_visible(mod):
            continue
        puntuacion = 0
        mod_tokens = set(re.findall(r'[a-z0-9_]+', _norm(mod["id"]) + " " + _norm(mod["nombre"]) + " " + _norm(mod["ruta"]))) - stop_words
        comunes = tokens & mod_tokens
        if comunes:
            puntuacion += len(comunes) * 3
        for cap in mod["capacidades"]:
            cap_tokens = {w for w in re.findall(r'[a-z0-9_]+', _norm(cap)) if len(w) > 4 and w not in stop_words}
            puntuacion += len(tokens & cap_tokens)
        if puntuacion > 0:
            modulos_encontrados.append((puntuacion, mod))

    # 2. Buscar en procedimientos
    procedimientos_encontrados = []
    for proc in PROCEDIMIENTOS_OPERATIVOS:
        if rol != "ADMINISTRADOR" and rol not in proc["roles"]:
            continue
        if rol != 'ADMINISTRADOR':
            required = set(proc.get('permisos') or PROCEDURE_PERMISSIONS.get(proc['modulo'], set()))
            if permisos is None or not required or not required.issubset(permisos):
                continue
            plan_module = PLAN_MODULES.get(proc['modulo'])
            if modulos is not None and plan_module and plan_module not in modulos:
                continue
        proc_words = {w for w in re.findall(r'[a-z0-9_]+', _norm(proc["tema"])) if w not in stop_words and len(w) > 3}
        if proc_words & tokens:
            procedimientos_encontrados.append(proc)

    if not modulos_encontrados and not procedimientos_encontrados:
        return None

    modulos_encontrados.sort(key=lambda x: x[0], reverse=True)
    return {
        "tipo": "detalle_modulos",
        "modulos": [m[1] for m in modulos_encontrados[:3]],
        "procedimientos": procedimientos_encontrados[:2]
    }
