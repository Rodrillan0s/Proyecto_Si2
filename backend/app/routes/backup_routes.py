from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from pydantic import Field
from app.utils.security import verificar_token
from app.services import backup_services as service
from app.services.backups.contracts import BackupRequest, Schedule, ValidateRequest, ApplyRequest, Contract
from app.repos import backup_jobs_repos as repo

router = APIRouter(tags=['Backups'])


def global_admin(token=Depends(verificar_token)):
    return service.administrator(token)


class Reauthentication(Contract):
    identificador: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=200)


@router.get('/estado')
def estado(actor=Depends(global_admin)):
    return service.status()


@router.post('/ejecuciones', status_code=202)
def crear(request: BackupRequest, actor=Depends(global_admin), idempotency_key: Annotated[str | None, Header()] = None):
    return service.create(actor, request, idempotency_key)


@router.get('/ejecuciones')
def historial(pagina: int = Query(1, ge=1), limite: int = Query(20, ge=1, le=100),
              estado: str | None = Query(None, pattern='^(PENDIENTE|PROCESANDO|COMPLETADO|FALLIDO)$'), actor=Depends(global_admin)):
    result = repo.history(pagina, limite, estado)
    result['items'] = [service.public_job(row) for row in result['items']]
    return result


@router.get('/ejecuciones/{id}')
def ejecucion(id: str, actor=Depends(global_admin)):
    return service.execution(id)


@router.get('/ejecuciones/{id}/archivo')
@router.post('/ejecuciones/{id}/archivo')
def descargar(id: str, response: Response, actor=Depends(global_admin)):
    result = service.download(id, actor)
    return download_response(result, response)


def download_response(result, response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    response.status_code = 202 if result['estado'] in {'PENDIENTE', 'PROCESANDO'} else 200
    return result


@router.get('/descargas/{id}')
def consultar_descarga(id: str, response: Response, actor=Depends(global_admin)):
    return download_response(service.download_status(id, actor), response)


@router.get('/programacion')
def programacion(actor=Depends(global_admin)):
    return service.schedule()


@router.put('/programacion')
def guardar(request: Schedule, actor=Depends(global_admin)):
    return service.save_schedule(actor, request)


@router.patch('/programacion')
def pausar(request: dict, actor=Depends(global_admin)):
    if set(request) != {'habilitada'} or type(request['habilitada']) is not bool:
        raise HTTPException(422, 'Envía únicamente habilitada: true o false.')
    config = service.schedule()['configuracion']
    return service.save_schedule(actor, Schedule.model_validate(dict(config, **request)))


@router.post('/programacion/ejecutar', status_code=202)
def despachar(actor=Depends(global_admin)):
    """Un ciclo: encola una ocurrencia vencida. No ejecuta backups ni inicia procesos."""
    return service.dispatch_schedule()


@router.post('/importaciones', status_code=201)
async def importar(request: Request, actor=Depends(global_admin)):
    if request.headers.get('content-type', '').split(';')[0] != 'application/octet-stream':
        raise HTTPException(415, 'Envía el paquete OBRATEC como application/octet-stream.')
    return await service.import_archive(actor, request)


@router.get('/restauraciones')
def restauraciones(actor=Depends(global_admin)):
    return [service.public_restore(row) for row in repo.restore_history()]


@router.post('/restauraciones/validar', status_code=202)
def validar(request: ValidateRequest, actor=Depends(global_admin)):
    return service.validate(actor, request)


@router.get('/restauraciones/{id}')
def restauracion(id: str, actor=Depends(global_admin)):
    return service.restore(id)


@router.post('/reautenticacion')
def reautenticar(request: Reauthentication, actor=Depends(global_admin)):
    from app.services.auth_services import loguear_usuario
    from app.services.backups.coordination import writer
    with writer('BACKUP_REAUTH'):
        try:
            response = loguear_usuario(request.model_dump())
        except ValueError as exc:
            from app.services.backups.settings import BackupError
            raise BackupError(str(exc), 'BACKUP_REAUTH_FAILED', 401) from exc
        if response['usuario']['nro_usuario'] != actor:
            raise HTTPException(403, 'Confirma con la misma cuenta de administrador.')
        return {'token': response['token']}


@router.post('/restauraciones/{id}/aplicar', status_code=202)
def aplicar(id: str, request: ApplyRequest, actor=Depends(global_admin), authorization: str = Header(...)):
    return service.apply(actor, id, request, authorization.removeprefix('Bearer ').strip())


@router.get('/manual', status_code=202, deprecated=True)
def manual(actor=Depends(global_admin), idempotency_key: Annotated[str | None, Header()] = None):
    """Transición: devuelve el ID durable de la cola VM; no espera al daemon."""
    return service.create(actor, BackupRequest(alcance='base_datos'), idempotency_key)
