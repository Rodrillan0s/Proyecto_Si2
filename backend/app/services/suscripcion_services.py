from datetime import date
from fastapi import HTTPException
from app.repos import suscripcion_repos as repo
from app.utils.security import es_admin_sistema
from app.services.suscripcion_policy import capacidades


def enriquecer(fila):
    return {**fila, **capacidades(fila)}


def autorizar_empresa(token, id_empresa=None):
    if es_admin_sistema(token):
        if id_empresa is None:
            raise HTTPException(400, 'Seleccione una empresa.')
        return id_empresa
    usuario = repo.obtener_usuario(token.get('nro_usuario'))
    if (not usuario or usuario['estado'] != 'ACTIVO' or not token.get('id_empresa')
            or usuario['id_empresa'] != token['id_empresa']):
        raise HTTPException(403, 'No tiene un contexto de empresa válido.')
    if id_empresa is not None and id_empresa != usuario['id_empresa']:
        raise HTTPException(403, 'No puede consultar otra empresa.')
    return usuario['id_empresa']


def consultar(token, id_empresa=None):
    empresa = autorizar_empresa(token, id_empresa)
    filas = repo.listar_suscripciones(empresa)
    if not filas:
        raise HTTPException(404, 'Empresa no encontrada.')
    return enriquecer(filas[0])


def asignar(token, id_empresa, datos):
    if not es_admin_sistema(token):
        raise HTTPException(403, 'Solo el administrador global puede gestionar suscripciones.')
    if id_empresa <= 0:
        raise HTTPException(400, 'Empresa inválida.')
    if datos.get('estado') not in ('ACTIVA', 'SUSPENDIDA', 'CANCELADA'):
        raise HTTPException(400, 'Estado de suscripción inválido.')
    try:
        inicio = date.fromisoformat(str(datos.get('fecha_inicio')))
        fin = date.fromisoformat(str(datos['fecha_fin'])) if datos.get('fecha_fin') else None
    except (ValueError, TypeError):
        raise HTTPException(400, 'Las fechas deben tener formato AAAA-MM-DD.')
    if fin and fin < inicio:
        raise HTTPException(400, 'La fecha de fin no puede ser anterior al inicio.')
    datos = {**datos, 'fecha_inicio': inicio, 'fecha_fin': fin}
    try:
        if not repo.asignar(id_empresa, datos, token['nro_usuario']):
            raise HTTPException(404, 'Empresa no encontrada.')
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return consultar(token, id_empresa)
