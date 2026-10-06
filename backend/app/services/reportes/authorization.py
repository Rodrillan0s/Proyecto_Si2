from dataclasses import dataclass
from fastapi import HTTPException
from app.repos import reportes_repos as repo
from .catalog import REGISTRY, WORKERS


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


def authorize(db, ctx, request, action="Visualizar_reportes"):
    ctx.require(action)
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
