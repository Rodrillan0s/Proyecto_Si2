"""Cliente global del Backup Service VM. La API únicamente encola/consulta."""
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote
from fastapi import HTTPException
from app.repos import backup_jobs_repos as repo, backup_repos as control_repo, reportes_repos as business
from app.utils.security import decode_access_token
from .backups.oracle_settings import Settings, BackupError
from .backups.contracts import Schedule, next_run


def administrator(token):
    try:
        user = int(token.get('nro_usuario'))
    except (TypeError, ValueError):
        raise HTTPException(403, 'Se requiere un administrador global activo.')
    with business.transaction(snapshot=True) as db:
        actor = business.actor(db, user)
        if not actor or actor['estado'] != 'ACTIVO' or actor['nombre_rol'] != 'ADMINISTRADOR':
            raise HTTPException(403, 'Solo el administrador global activo puede gestionar respaldos de todos los tenants.')
    return user


def identifier(value):
    text = str(value)
    if not re.fullmatch(r'[1-9][0-9]{0,18}', text) or int(text) > 9223372036854775807:
        raise HTTPException(422, 'El identificador debe ser un entero positivo de backup_jobs.')
    return int(text)


def safe_error(value):
    if not value:
        return None
    text = re.sub(r'(?i)(?:https?|postgres(?:ql)?)://\S+', '[URL omitida]', str(value))
    text = re.sub(r'(?i)(password|token|secret|authorization)\s*[:=]\s*\S+', r'\1=[omitido]', text)
    return text[:500]


def public_archive(row):
    return {'id': str(row['id']), 'nombre': row.get('object_name'), 'object_name': row.get('object_name'),
            'bytes': row.get('size_bytes'), 'size_bytes': row.get('size_bytes'), 'sha256': row.get('sha256'),
            'alcance': 'base_datos', 'schema': 'obras', 'corte': row.get('fecha_inicio') or row.get('fecha_solicitud'),
            'entorno_origen': Settings.load().environment, 'replica_remota': row['estado'] == 'COMPLETADO',
            'verificado_en': row.get('fecha_fin'), 'eliminado_en': None}


def public_job(row):
    stage = {'PENDIENTE': 'En cola para procesamiento', 'PROCESANDO': 'Procesando respaldo',
             'COMPLETADO': 'Respaldo completado', 'FALLIDO': 'Respaldo fallido'}
    result = {'id': str(row['id']), 'tipo': row['tipo'], 'estado': row['estado'],
              'etapa': stage.get(row['estado'], row['estado']), 'error': safe_error(row.get('error')),
              'archivo': str(row['id']) if row['tipo'] == 'BACKUP' and row['estado'] == 'COMPLETADO' else None,
              'origen': row['origen'], 'solicitud': {'alcance': 'base_datos'},
              'created_at': row['fecha_solicitud'], 'started_at': row.get('fecha_inicio'),
              'finished_at': row.get('fecha_fin'), 'object_name': row.get('object_name'),
              'sha256': row.get('sha256'), 'size_bytes': row.get('size_bytes'),
              'job_relacionado_id': str(row['job_relacionado_id']) if row.get('job_relacionado_id') else None}
    if result['archivo']:
        result['respaldo'] = public_archive(row)
    return result


def public_restore(row):
    # La relación existente es PRE_RESTORE -> RESTORE, no backup fuente.
    return dict(public_job(row), respaldo=None, pasos=[], desafio=None, aplicar_en=row.get('fecha_inicio'),
                confirmacion_requerida='RESTAURAR TODOS LOS TENANTS '+str(row['id']),
                fuente_no_identificada=True)


def heartbeat(control, settings):
    last = control.get('heartbeat') if control and settings.heartbeat_connected else None
    age = (datetime.now(timezone.utc)-last).total_seconds() if last else None
    return last, bool(age is not None and 0 <= age < settings.heartbeat_max_age)


def status():
    settings = Settings.load()
    issues = settings.requirements()
    state = None
    queue_ready = False
    if settings.enabled:
        try:
            state = control_repo.control()
            repo.installation()
            queue_ready = True
        except BackupError as exc:
            issues.append(str(exc))
    last, alive = heartbeat(state, settings)
    download_issues = []
    if queue_ready and not issues:
        try:
            repo.download_installation()
        except BackupError as exc:
            download_issues.append(str(exc))
    else:
        download_issues.append('Preparar la conexión y la cola del servicio Oracle.')
    restore_issues = ['Restauración desde la aplicación temporalmente bloqueada durante la integración con el daemon.']
    if not settings.heartbeat_connected:
        restore_issues.append('El daemon Oracle todavía no publica un heartbeat conectado a la aplicación.')
    elif not alive:
        restore_issues.append('El daemon no tiene un heartbeat reciente; no se aceptan operaciones destructivas.')
    return {'configurado': not issues, 'control_disponible': state is not None, 'cola_disponible': queue_ready,
            'requisitos': issues, 'worker_activo': alive, 'ultimo_latido': last,
            'heartbeat_integrado': settings.heartbeat_connected, 'entorno': settings.environment or 'Sin identificar',
            'alcance_global': True, 'schema': 'obras', 'motor': 'oracle_vm',
            'mantenimiento': bool(state and state['mantenimiento']), 'motivo': state.get('motivo') if state else None,
            'replica_remota': True, 'almacenamiento': 'oci_object_storage',
            'restauracion_habilitada': False, 'requisitos_restauracion': restore_issues,
            'descarga_habilitada': not download_issues, 'requisitos_descarga': download_issues,
            'importacion_habilitada': False,
            'retencion_gestionada': False, 'programacion_requiere_despachador': True,
            'advertencias': [] if settings.heartbeat_connected else
                ['Heartbeat pendiente: encolar una copia no acredita que el daemon esté activo.']}


def preflight(settings=None):
    settings = settings or Settings.load()
    settings.require()
    state = control_repo.control()
    repo.installation()
    if state['mantenimiento']:
        raise BackupError('Sistema en mantenimiento; se conserva la barrera hasta revisión.', 'BACKUP_MAINTENANCE', 503)
    if settings.heartbeat_connected and not heartbeat(state, settings)[1]:
        raise BackupError('El daemon Oracle no tiene heartbeat reciente.', 'BACKUP_SERVICE_UNAVAILABLE', 503)
    return {'motor': 'oracle_vm', 'schema': 'obras', 'heartbeat_verificado': heartbeat(state, settings)[1]}


def create(actor, request, key):
    if not key or not 8 <= len(key) <= 120:
        raise HTTPException(422, 'Envía Idempotency-Key de 8 a 120 caracteres.')
    preflight()
    return public_job(repo.queue(actor, 'manual:'+str(actor)+':'+key))


def execution(value):
    row = repo.get(identifier(value))
    if not row or row['tipo'] != 'BACKUP':
        raise HTTPException(404, 'Respaldo inexistente.')
    return public_job(row)


def checked_source(row):
    if (not row or row['tipo'] != 'BACKUP' or row['estado'] != 'COMPLETADO'
            or not row.get('object_name') or not re.fullmatch(r'[0-9a-fA-F]{64}', row.get('sha256') or '')
            or not isinstance(row.get('size_bytes'), int) or row['size_bytes'] <= 0):
        raise BackupError('Selecciona un BACKUP COMPLETADO con metadatos de integridad válidos.')
    return row


def download_result(row, source, settings):
    source = checked_source(source)
    result = {'id': str(row['id']), 'job_id': str(row['job_id']), 'estado': row['estado'],
              'expira_en': row.get('expira_en'), 'url': None,
              'nombre': source['object_name'].rsplit('/', 1)[-1], 'error': None}
    if row['estado'] in {'PENDIENTE', 'PROCESANDO'}:
        return result
    if row['estado'] == 'FALLIDO':
        result['error'] = safe_error(row.get('error')) or 'El daemon no pudo preparar la descarga.'
        return result
    expiry = row.get('expira_en')
    if row['estado'] != 'COMPLETADO' or not isinstance(expiry, datetime) or expiry.tzinfo is None:
        raise BackupError('El servicio devolvió una solicitud de descarga incompleta.', 'BACKUP_DOWNLOAD_INVALID', 502)
    if expiry <= datetime.now(timezone.utc):
        return dict(result, estado='EXPIRADO', error='El enlace venció. Solicita la descarga nuevamente.')
    url = row.get('par_url') or ''
    try:
        parsed = urlsplit(url)
        path = unquote(parsed.path)
        object_name = source['object_name']
        suffix = '/n/'+settings.oci_namespace+'/b/'+settings.oci_bucket+'/o/'+object_name
        valid = (len(url) <= 16384 and not re.search(r'[\x00-\x20\x7f\\]', url)
                 and parsed.scheme == 'https' and parsed.port in (None, 443)
                 and parsed.username is None and parsed.password is None and not parsed.query and not parsed.fragment
                 and not re.search(r'[\x00-\x1f\x7f\\]', path)
                 and re.fullmatch(r'objectstorage\.[a-z0-9-]+\.oraclecloud\.com', parsed.hostname or '')
                 and re.fullmatch(r'/p/[^/\s]+/n/[^/\s]+/b/[^/\s]+/o/.+', path)
                 and path.endswith(suffix) and path[path.index('/n/'):] == suffix
                 and not any(part in {'.', '..'} for part in object_name.split('/')))
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise BackupError('El enlace recibido no corresponde al objeto OCI autorizado.', 'BACKUP_DOWNLOAD_INVALID', 502)
    return dict(result, url=url)


def download(value, actor):
    source_id = identifier(value)
    checked_source(repo.get(source_id))
    settings = Settings.load()
    settings.require()
    repo.download_installation()
    row, source = repo.request_download(source_id, actor, checked_source)
    return download_result(row, source, settings)


def download_status(value, actor):
    settings = Settings.load()
    settings.require()
    row, source = repo.download_request(identifier(value), actor)
    if not row:
        raise HTTPException(404, 'Solicitud de descarga inexistente.')
    return download_result(row, source, settings)


def schedule():
    row = control_repo.get('programacion', 1)
    if not row:
        return {'configuracion': Schedule().model_dump(), 'next_run': None}
    # Una programación legacy completa se muestra pausada; leer no cambia BD.
    if row['configuracion'].get('alcance') != 'base_datos':
        return dict(row, configuracion=dict(row['configuracion'], alcance='base_datos', habilitada=False),
                    advertencias=['Programación legacy incompatible. Revisar y guardar antes de reactivar.'])
    return row


def save_schedule(actor, config):
    if config.habilitada:
        preflight()
    return control_repo.save_schedule(config.model_dump(), actor, next_run(config, datetime.now(timezone.utc)))


def dispatch_schedule():
    preflight()
    job = repo.dispatch_schedule(administrator)
    return {'encolado': bool(job), 'trabajo': public_job(job) if job else None}


def restore_unavailable():
    raise BackupError('RESTORE desde FastAPI está temporalmente bloqueado. Se conserva el destino de prueba del daemon; producción no está habilitada.',
                      'BACKUP_RESTORE_MIGRATION', 503)


def validate(actor, request):
    checked_source(repo.get(identifier(request.archivo)))
    restore_unavailable()


def restore(value):
    row = repo.get(identifier(value))
    if not row or row['tipo'] != 'RESTORE':
        raise HTTPException(404, 'Restauración inexistente.')
    return public_restore(row)


def apply(actor, value, request, current_token):
    value = str(identifier(value))
    if request.confirmacion != 'RESTAURAR TODOS LOS TENANTS '+value:
        raise BackupError('Escribe la confirmación completa de restauración global.')
    fresh = decode_access_token(request.token_reautenticacion)
    payload = fresh.get('payload', {})
    issued = payload.get('iat', 0)
    if (not fresh.get('success') or administrator(payload) != actor or not isinstance(issued, (int, float))
            or time.time()-issued > 300 or issued > time.time()+5):
        raise HTTPException(401, 'Inicia sesión nuevamente como el mismo administrador para confirmar (máximo 5 minutos).')
    if request.token_reautenticacion == current_token:
        raise HTTPException(401, 'Se requiere una nueva autenticación para esta restauración.')
    restore_unavailable()


async def import_archive(actor, request):
    raise BackupError('Los paquetes .obratec legacy no forman parte del pipeline Oracle.', 'BACKUP_IMPORT_RETIRED', 410)
