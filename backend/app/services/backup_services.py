"""Casos de uso globales: independientes de la empresa seleccionada."""
import time
from datetime import datetime, timezone
from uuid import UUID, uuid4
from fastapi import HTTPException
from app.repos import backup_repos as repo, reportes_repos as business
from app.utils.security import decode_access_token
from .backups.settings import Settings, BackupError
from .backups.contracts import Schedule, next_run
from .backups import postgres, storage


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
    try:
        return str(UUID(str(value)))
    except (ValueError, TypeError):
        raise HTTPException(422, 'Identificador de respaldo inválido.')


def public_job(row):
    return {key: value for key, value in row.items() if key not in {'worker', 'identidad', 'lease_until'}}


def public_archive(row):
    manifest = row['manifiesto']
    missing = len(manifest.get('evidencias_no_disponibles', []))
    return {'id': row['id'], 'nombre': row['nombre'], 'bytes': row['bytes'], 'sha256': row['sha256'],
        'alcance': row['alcance'], 'corte': manifest.get('corte'), 'entorno_origen': manifest.get('entorno'),
        'version_postgres': manifest.get('postgres'), 'release_sha256': manifest.get('release_sha256'),
        'verificado_en': row['verificado_en'], 'eliminado_en': row['eliminado_en'], 'replica_remota': bool(row['remoto']),
        'advertencias': [f'La base está respaldada; {missing} evidencias externas no estaban disponibles.'] if missing else []}


def public_restore(row):
    result = {key: value for key, value in row.items() if key not in {'worker', 'lease_until', 'stage_db', 'stage_dir', 'diario'}}
    result['respaldo'] = public_archive(repo.get('archivo', row['archivo']))
    result['pasos'] = [{'paso': step['paso'], 'estado': step['estado']} for step in row['diario']]
    result['confirmacion_requerida'] = 'RESTAURAR TODOS LOS TENANTS '+str(row['id'])
    return result


def status():
    settings = Settings.load()
    issues = settings.requirements()
    for name in ('pg_dump', 'pg_restore'):
        try:
            postgres.tool(name)
        except BackupError as exc:
            if str(exc) not in issues:
                issues.append(str(exc))
    control = None
    if settings.enabled:
        try:
            control = repo.control()
        except BackupError as exc:
            issues.append(str(exc))
    heartbeat = control.get('heartbeat') if control else None
    alive = bool(heartbeat and (datetime.now(timezone.utc)-heartbeat).total_seconds() < 120)
    restore_issues = issues+settings.restore_requirements()
    return {'configurado': not issues, 'control_disponible': control is not None, 'requisitos': issues, 'worker_activo': alive,
        'ultimo_latido': heartbeat, 'entorno': settings.environment or 'Sin identificar',
        'alcance_global': True, 'mantenimiento': bool(control and control['mantenimiento']),
        'motivo': control.get('motivo') if control else None,
        'replica_remota': bool(settings.s3_bucket), 'almacenamiento_persistente': settings.persistent_storage,
        'restauracion_habilitada': not restore_issues, 'requisitos_restauracion': restore_issues}


def preflight(settings=None):
    settings = settings or Settings.load()
    storage.prepare(settings)
    repo.control()
    versions = postgres.versions(settings)
    import shutil
    conn = postgres.connection(settings)
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT pg_database_size(current_database())')
            database_size = cur.fetchone()[0]
    finally:
        conn.close()
    from .backups.packages import sources
    from .backups.settings import ROOT
    file_size = sum(file.stat().st_size for _,file in sources(True, settings.release_target or ROOT) if file is not None)
    estimated = database_size+file_size
    if estimated > settings.max_bytes:
        raise BackupError('La base y archivos superan el límite del paquete. Ajusta la cuota antes de crear copias.', 'BACKUP_QUOTA_EXCEEDED', 503)
    if shutil.disk_usage(settings.directory).free < max(128*1024**2, estimated*6):
        raise BackupError('Falta espacio para volcado, paquetes, cifrado y ensayo. Libera espacio o cambia el volumen.', 'BACKUP_STORAGE_FULL', 503)
    return versions


def create(actor, request, key):
    if not key or not 8 <= len(key) <= 120:
        raise HTTPException(422, 'Envía Idempotency-Key de 8 a 120 caracteres.')
    preflight()
    return public_job(repo.queue(actor, request.model_dump(), 'manual:'+str(actor)+':'+key))


def execution(value):
    row = repo.get('ejecucion', identifier(value))
    if not row:
        raise HTTPException(404, 'Respaldo inexistente.')
    result = public_job(row)
    if row['archivo']:
        result['respaldo'] = public_archive(repo.get('archivo', row['archivo']))
    return result


def download(value):
    row = repo.get('ejecucion', identifier(value))
    if not row:
        raise HTTPException(404, 'Respaldo inexistente.')
    if row['estado'] != 'LISTO' or not row['archivo']:
        raise BackupError('La copia todavía no está lista para descargar.')
    archive = repo.get('archivo', row['archivo'])
    return storage.obtain(Settings.load(), archive), archive['nombre']


def schedule():
    row = repo.get('programacion', 1)
    return row or {'configuracion': Schedule().model_dump(), 'next_run': None}


def save_schedule(actor, config):
    if config.habilitada:
        preflight()
    return repo.save_schedule(config.model_dump(), actor, next_run(config, datetime.now(timezone.utc)))


def validate(actor, request):
    settings = Settings.load()
    preflight(settings)
    issues = settings.restore_requirements()
    if issues:
        raise BackupError(' '.join(issues), 'BACKUP_RESTORE_SETUP_REQUIRED', 503)
    archive = repo.get('archivo', identifier(request.archivo))
    if not archive or archive['eliminado_en']:
        raise HTTPException(404, 'El archivo de respaldo no está disponible.')
    return public_restore(repo.validate_queue(archive['id'], actor))


def restore(value):
    row = repo.get('restauracion', identifier(value))
    if not row:
        raise HTTPException(404, 'Validación inexistente.')
    return public_restore(row)


def apply(actor, value, request, current_token):
    settings = Settings.load()
    settings.require()
    issues = settings.restore_requirements()
    if issues:
        raise BackupError(' '.join(issues), 'BACKUP_RESTORE_SETUP_REQUIRED', 503)
    value = identifier(value)
    if request.confirmacion != 'RESTAURAR TODOS LOS TENANTS '+value:
        raise BackupError('Escribe la confirmación completa de restauración global.')
    fresh = decode_access_token(request.token_reautenticacion)
    payload = fresh.get('payload', {})
    issued = payload.get('iat', 0)
    if not fresh.get('success') or administrator(payload) != actor or time.time()-issued > 300 or issued > time.time()+5:
        raise HTTPException(401, 'Inicia sesión nuevamente como el mismo administrador para confirmar (máximo 5 minutos).')
    if request.token_reautenticacion == current_token:
        raise HTTPException(401, 'Se requiere una nueva autenticación para esta restauración.')
    return public_restore(repo.confirm_restore(value, actor, request.desafio))


async def import_archive(actor, request):
    import asyncio
    from .backups.crypto import decrypt, sha256
    from .backups.packages import unpack
    settings = Settings.load()
    await asyncio.to_thread(preflight, settings)
    directory = settings.directory/'work'/str(uuid4())
    directory.mkdir(mode=0o700)
    encrypted = directory/'uploaded.obratec'
    try:
        count = 0
        with open(encrypted, 'xb') as out:
            async for chunk in request.stream():
                count += len(chunk)
                if count > settings.max_bytes:
                    raise BackupError('El archivo importado supera el límite.', 'BACKUP_UPLOAD_TOO_LARGE', 413)
                out.write(chunk)
        metadata = await asyncio.to_thread(decrypt, encrypted, directory/'package.zip', settings.keys, settings.max_bytes)
        manifest = await asyncio.to_thread(unpack, directory/'package.zip', directory/'package', settings)
        if manifest['id'] != metadata['id'] or manifest['key_id'] != metadata['key_id']:
            raise BackupError('La cabecera y el manifiesto no corresponden al mismo respaldo.')
        name = 'import_'+str(uuid4())+'.obratec'
        digest = await asyncio.to_thread(sha256, encrypted)
        _, remote = await asyncio.to_thread(storage.publish, settings, encrypted, name)
        archive = await asyncio.to_thread(repo.register_archive, None, name, digest, count, manifest, remote)
        await asyncio.to_thread(repo.event, archive, actor, 'ARCHIVO_IMPORTADO')
        return public_archive(await asyncio.to_thread(repo.get, 'archivo', archive))
    finally:
        await asyncio.to_thread(storage.cleanup_work, settings, directory)
