import logging
import threading
from datetime import datetime, timezone
from uuid import uuid4
from app.repos import backup_repos as repo
from app.services.backup_services import administrator, preflight
from .settings import Settings, BackupError
from . import engine, restoration, storage

log = logging.getLogger(__name__)


def tick():
    settings = Settings.load()
    settings.require()
    repo.interrupted_maintenance()
    if repo.control()['mantenimiento']:
        return False
    preflight(settings)
    repo.due_schedule(datetime.now(timezone.utc))
    worker = str(uuid4())
    claim = repo.claim(worker)
    if not claim:
        return False
    kind, row = claim
    stop = threading.Event()
    heartbeat_error = []
    def beat():
        if heartbeat_error:
            raise BackupError('No se puede renovar el lease de control.', 'BACKUP_LEASE_LOST')
    def renew():
        while not stop.wait(15):
            try:
                repo.heartbeat(kind, row['id'], worker)
            except Exception as exc:
                heartbeat_error.append(exc)
                return
    heartbeat = threading.Thread(target=renew, daemon=True)
    heartbeat.start()
    try:
        # Revalidar al ejecutar, incluyendo programaciones de cuentas revocadas.
        administrator({'nro_usuario': row['id_usuario']})
        if kind == 'ejecucion':
            archive = engine.create(settings, row, beat)
            if settings.rehearsal_enabled:
                from datetime import timedelta
                previous = repo.last_verified()
                if not previous or previous < datetime.now(timezone.utc)-timedelta(days=settings.rehearsal_days):
                    rehearsal = repo.validate_queue(archive, row['id_usuario'])
                    repo.update('restauracion', rehearsal['id'], operacion='ENSAYO')
        elif row['operacion'] == 'APLICAR':
            restoration.apply(settings, row, beat)
        else:
            restoration.validate(settings, row, beat)
            if row['operacion'] == 'ENSAYO':
                from . import postgres
                verified = repo.get('restauracion', row['id'])
                postgres.drop_stage(settings, verified['stage_db'])
                storage.cleanup_work(settings, verified['stage_dir'])
                repo.update('restauracion', row['id'], estado='COMPLETADA', etapa='Ensayo periódico verificado; no se aplicaron cambios al negocio', finished_at=datetime.now(timezone.utc))
    except Exception as exc:
        message = str(exc) if isinstance(exc, BackupError) else 'La operación falló. Revisa la consola del worker y sus permisos.'
        state = repo.get(kind, row['id'])
        if kind == 'ejecucion':
            if state['estado'] == 'LISTO':
                # Una falla posterior al registro (p.ej. encolar ensayo) no invalida ciphertext.
                repo.update(kind, row['id'], error='Copia disponible; una operación posterior requiere revisión.')
            elif (isinstance(exc,BackupError) and exc.code in {'BACKUP_DATABASE_UNAVAILABLE','BACKUP_TIMEOUT'}
                  and row['intentos'] < 3 and not repo.control()['mantenimiento']):
                repo.update(kind, row['id'], estado='PENDIENTE', worker=None, lease_until=None,
                    etapa='Reintento acotado tras fallo temporal', error=message[:500])
            else:
                repo.update(kind, row['id'], estado='FALLIDO', error=message[:500], finished_at=datetime.now(timezone.utc))
        else:
            final = state['estado'] if state['estado'] in {'REVERTIDA', 'REQUIERE_INTERVENCION'} else 'REQUIERE_INTERVENCION'
            repo.update(kind, row['id'], estado=final, error=message[:500])
        repo.event(row['id'], row['id_usuario'], 'OPERACION_FALLIDA', {'mensaje': message[:500]})
        log.error('Backup %s (%s): %s', row['id'], kind, message)
    finally:
        stop.set()
        heartbeat.join(timeout=6)
    # Retención solo después de completar un trabajo y fuera de mantenimiento.
    if not repo.control()['mantenimiento']:
        schedule = repo.get('programacion', 1)
        days = schedule['configuracion']['retencion_dias'] if schedule else 30
        for archive in repo.retention_candidates(days):
            storage.delete(settings, archive)
            repo.update('archivo', archive['id'], eliminado_en=datetime.now(timezone.utc))
            repo.event(archive['id'], None, 'RETENCION_APLICADA')
    return True
