from dataclasses import dataclass
from fastapi import HTTPException
from app.repos import reportes_repos as repo
from .catalog import REGISTRY, WORKERS
from app.services import suscripcion_policy as subscription


@dataclass(frozen=True)
class Context:
    usuario: int
    empresa: int
    rol: str
    persona: int | None
    permisos: frozenset
    correo: str | None

    def require(self, permission):
        if self.rol != "ADMINISTRADOR" and permission not in self.permisos:
            raise HTTPException(403, "No tiene permiso para esta acción: " + permission)

    def policy(self):
        return {"rol": self.rol, "persona": self.persona, "usuario": self.usuario}


def context(db, user, empresa=None):
    actor = repo.actor(db, user)
    if not actor or actor['estado'] != 'ACTIVO':
        raise HTTPException(403, "La cuenta ya no está activa.")
    rol = actor['nombre_rol']
    if rol == 'ADMINISTRADOR':
        if not empresa:
            raise HTTPException(422, "Seleccione una empresa para consultar reportes.")
    else:
        if empresa and empresa != actor['id_empresa']:
            raise HTTPException(403, "La empresa solicitada no corresponde a su cuenta.")
        empresa = actor['id_empresa']
    if not repo.company_exists(db,(empresa,)):
        raise HTTPException(404, "Empresa inexistente.")
    return Context(actor['id_usuario'], empresa, rol, actor['id_persona'], frozenset(actor['permisos']), actor['correo'])


def allowed(ctx, definition):
    if ctx.rol != 'ADMINISTRADOR' and any(p not in ctx.permisos for p in definition.permisos_extra):
        return False
    if ctx.rol == "CLIENTE":
        return "CLIENTE" in definition.actores and definition.permiso in ctx.permisos
    if ctx.rol in WORKERS:
        return "trabajador" in definition.actores
    return ctx.rol == "ADMINISTRADOR" or definition.permiso in ctx.permisos


def authorize(db, ctx, request, action="Visualizar_reportes", lectura=False):
    ctx.require(action)
    subscription.exigir_reporte(ctx, request.reporte, action, getattr(db, "cur", None), lectura)
    definition = REGISTRY.get(request.reporte)
    if not definition or not allowed(ctx, definition):
        raise HTTPException(403, "Este reporte no está disponible para su cuenta.")
    f = request.filtros
    if definition.obra and not f.id_obra:
        raise HTTPException(422, "Seleccione una obra para comparar costos.")
    if (f.desde or f.hasta) and not definition.fecha:
        raise HTTPException(422, "Este reporte muestra el estado actual; no admite un rango de fechas.")
    if f.id_categoria and request.reporte != 'stock':
        raise HTTPException(422, "El filtro de categoría pertenece al reporte de stock.")
    if f.prioridad and request.reporte not in {'incidencias','incidencias_criticas'}:
        raise HTTPException(422,'La prioridad pertenece al reporte de incidencias.')
    if request.reporte=='incidencias_criticas' and f.prioridad and f.prioridad!='CRITICA':
        raise HTTPException(422,'El reporte de incidencias críticas admite prioridad CRITICA.')
    if request.reporte == "stock":
        if f.id_obra:
            raise HTTPException(422, "El stock es de la empresa; no está distribuido por obra.")
        if ctx.rol not in {"ADMINISTRADOR", "ADMINISTRADOR_EMPRESA"}:
            raise HTTPException(403, "El inventario empresarial requiere ámbito de empresa.")
        return definition, []
    ids = [w['id_obra'] for w in repo.works(db, ctx)]
    if f.id_obra:
        if f.id_obra not in ids:
            raise HTTPException(403, "La obra no pertenece a su ámbito autorizado.")
        ids = [f.id_obra]
    return definition, ids


# =============================================================================
# AUTORIZACIÓN CENTRALIZADA PARA MOTOR SEMÁNTICO Y HERRAMIENTAS IA
# (Autoridad única: ni SemanticCatalog ni compiler.py duplican reglas RBAC)
# =============================================================================

CROSS_MODULE_PERMISSIONS = {
    'retrasos': 'Visualizar_cronograma',
    'incidencias_criticas': 'Visualizar_incidencias',
    'costos': 'Visualizar_control_costos',
    'ordenes_trabajo': 'Visualizar_obras',
    'posventa': None,  # accesible a empresa; RLS aplicado si corresponde
}


def can_access_entity(ctx: Context, entity_def) -> bool:
    """Evalúa si el actor tiene acceso efectivo a una EntityDef declarativa."""
    if ctx.rol == 'ADMINISTRADOR':
        return True
    if entity_def.allowed_roles_only and ctx.rol not in entity_def.allowed_roles_only:
        return False
    if ctx.rol == 'CLIENTE':
        return bool(entity_def.allow_cliente)
    if ctx.rol in WORKERS:
        if not entity_def.allow_workers:
            return False
        return entity_def.required_permission is None or entity_def.required_permission in ctx.permisos
    if entity_def.required_permission and entity_def.required_permission not in ctx.permisos:
        return False
    return True


def authorized_entities(ctx: Context) -> list[str]:
    from app.services.semantic.catalog import ENTITIES
    return [eid for eid, ent in ENTITIES.items() if can_access_entity(ctx, ent)]


def authorize_semantic_query(db, ctx: Context, spec):
    """Valida entidad, permisos efectivos, relaciones y ámbito de obras."""
    from app.services.semantic.catalog import get_entity
    entity = get_entity(spec.entidad)
    if not entity:
        raise HTTPException(422, f"Entidad de consulta desconocida: {spec.entidad}")
    if not can_access_entity(ctx, entity):
        raise HTTPException(403, f"No tiene autorización para consultar la entidad '{spec.entidad}'.")

    # Validar relaciones declaradas
    rel_map = entity.relation_map()
    for rel_name in spec.relaciones:
        rel = rel_map.get(rel_name)
        if not rel:
            raise HTTPException(422, f"Relación '{rel_name}' no registrada en '{spec.entidad}'.")
        if rel.required_permission and ctx.rol != 'ADMINISTRADOR' and rel.required_permission not in ctx.permisos:
            raise HTTPException(403, f"Sin permiso para la relación '{rel_name}'.")

    # Resolver scope de obras cuando la entidad opera por obra
    scope: list[int] = []
    if entity.work_column:
        scope = [w['id_obra'] for w in repo.works(db, ctx)]
        if spec.id_obra:
            if spec.id_obra not in scope:
                raise HTTPException(403, "La obra solicitada no pertenece a su ámbito autorizado.")
            scope = [spec.id_obra]
    elif spec.id_obra:
        raise HTTPException(422, f"La entidad '{spec.entidad}' es de ámbito empresarial y no se filtra por obra.")

    return entity, scope


def authorize_cross_module(db, ctx: Context, spec):
    """Autoriza cada módulo de un cruce por obra, omitiendo los no permitidos con motivo."""
    if ctx.rol == 'CLIENTE' or ctx.rol in WORKERS:
        raise HTTPException(403, "El análisis cruzado entre módulos está reservado a gestión y dirección de obra.")
    scope = [w['id_obra'] for w in repo.works(db, ctx)]
    if spec.id_obra:
        if spec.id_obra not in scope:
            raise HTTPException(403, "La obra solicitada no pertenece a su ámbito autorizado.")
        scope = [spec.id_obra]

    permitidos, omitidos = [], []
    for mod in spec.modulos:
        req = CROSS_MODULE_PERMISSIONS.get(mod)
        if ctx.rol == 'ADMINISTRADOR' or req is None or req in ctx.permisos:
            permitidos.append(mod)
        else:
            omitidos.append({'modulo': mod, 'motivo': f'Sin permiso {req}'})
    if not permitidos:
        raise HTTPException(403, "No tiene permisos sobre ninguno de los módulos solicitados.")
    return permitidos, omitidos, scope


def authorize_tool(ctx: Context, tool_name: str, plan_caps: dict | None = None) -> bool:
    """Autoridad única para exponer y ejecutar herramientas del Orquestador IA."""
    is_admin = ctx.rol == 'ADMINISTRADOR'
    caps = plan_caps or {}

    if tool_name == 'consultar_ayuda_plataforma':
        return True
    if tool_name == 'consultar_datos':
        return len(authorized_entities(ctx)) > 0
    if tool_name == 'analizar_cruce_obras':
        if ctx.rol == 'CLIENTE' or ctx.rol in WORKERS:
            return False
        return is_admin or any(p in ctx.permisos for p in (
            'Visualizar_cronograma', 'Visualizar_incidencias', 'Visualizar_control_costos', 'Visualizar_obras'
        ))
    if tool_name in {'ejecutar_reporte_estandar', 'modificar_reporte_activo'}:
        if not is_admin and caps and not caps.get('reportes_habilitado', True):
            return False
        return is_admin or 'Visualizar_reportes' in ctx.permisos
    if tool_name == 'exportar_reporte_activo':
        if not is_admin and caps and not caps.get('exportar_habilitado', True):
            return False
        return is_admin or 'Exportar_reportes' in ctx.permisos
    if tool_name == 'consultar_pendientes':
        return True  # Cada fuente interna filtra por permisos del actor
    if tool_name == 'ejecutar_diagnostico_operativo':
        if ctx.rol == 'CLIENTE':
            return False
        return is_admin or any(p in ctx.permisos for p in (
            'Visualizar_incidencias', 'Visualizar_ordenes_trabajo', 'Visualizar_inventario', 'Visualizar_consultas_tecnicas'
        ))
    if tool_name in {'recomendar_inmuebles', 'comparar_inmuebles'}:
        return is_admin or ctx.rol == 'CLIENTE' or 'Visualizar_clientes' in ctx.permisos or 'Visualizar_obras' in ctx.permisos
    if tool_name == 'analizar_plano':
        return is_admin or ctx.rol == 'CLIENTE' or any(p in ctx.permisos for p in (
            'Visualizar_obras', 'Visualizar_clientes', 'Visualizar_documentos_tecnicos'
        ))
    if tool_name == 'proponer_operacion':
        return is_admin or any(p in ctx.permisos for p in (
            'Registrar_incidencias', 'Registrar_ordenes_trabajo', 'Registrar_materiales'
        ))
    return False
