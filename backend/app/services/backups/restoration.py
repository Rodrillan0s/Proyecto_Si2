"""Restauración por etapas, diario durable y compensación explícita de promociones."""
import json
import os
import secrets
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from app.config import Config
from app.repos import backup_repos as repo
from . import crypto, packages, postgres, storage, engine
from .coordination import drain
from .settings import ROOT, BackupError


def check_evidence(settings, directory, manifest):
    if manifest.get('evidencias_no_disponibles'):
        raise BackupError('La base está respaldada, pero faltaban evidencias al capturarla. '
                          'Este paquete no certifica la recuperación completa del sistema.',
                          'BACKUP_EVIDENCE_UNAVAILABLE')
    root = settings.release_target or ROOT
    for reference, digest in manifest['evidencias_sha256'].items():
        packages.safe_name(reference)
        if not reference.startswith('uploads/'):
            raise BackupError('Referencia de evidencia insegura.')
        target = directory/reference if manifest['alcance'] == 'sistema_completo' else root/'backend'/reference
        if not target.is_file() or target.is_symlink() or crypto.sha256(target) != digest:
            raise BackupError('Las evidencias no corresponden a este corte. Usa un respaldo del sistema completo.')


def verify_files(directory, manifest):
    for entry in manifest['archivos']:
        packages.safe_name(entry['ruta'])
        target = directory/entry['ruta']
        if not target.is_file() or target.is_symlink() or target.stat().st_size != entry['bytes'] or crypto.sha256(target) != entry['sha256']:
            raise BackupError('El área de validación cambió; vuelve a validar el respaldo.')


def validate(settings, row, beat):
    archive = repo.get('archivo', row['archivo'])
    source = storage.obtain(settings, archive)
    work = settings.directory/'work'/('restore_'+str(row['id']))
    work.mkdir(mode=0o700, exist_ok=False)
    stage = postgres.stage_name(row['id'])
    repo.update('restauracion', row['id'], stage_db=stage, stage_dir=str(work), etapa='Autenticando paquete y comprobando inventario')
    metadata = crypto.decrypt(source, work/'package.zip', settings.keys, settings.max_bytes)
    manifest = packages.unpack(work/'package.zip', work/'package', settings)
    if metadata['id'] != manifest['id'] or manifest != archive['manifiesto']:
        raise BackupError('El paquete y el catálogo de control no corresponden.')
    installed = postgres.versions(settings, recovery=True)
    if installed['servidor_major'] != manifest['postgres']['servidor_major'] or installed['dump_major'] < manifest['postgres']['dump_major']:
        raise BackupError('Versiones incompatibles: restaura en la versión PostgreSQL original y con herramientas compatibles.')
    check_evidence(settings, work/'package', manifest)
    repo.update('restauracion', row['id'], etapa='Restaurando a una base temporal, sin modificar el sistema actual')
    postgres.create_stage(settings, stage, manifest['inventario_bd']['base'])
    actual = postgres.restore_stage(settings, stage, work/'package'/'database.dump', beat)
    if actual != manifest['inventario_bd']:
        raise BackupError('El ensayo no reproduce conteos, objetos, permisos o secuencias del corte.')
    now = datetime.now(timezone.utc)
    repo.update('archivo', archive['id'], verificado_en=now)
    repo.update('restauracion', row['id'], estado='VALIDADA', etapa='Ensayo completo verificado; pendiente de confirmación',
                desafio=secrets.token_urlsafe(40), validada_en=now, worker=None, lease_until=None)
    repo.event(row['id'], row['id_usuario'], 'VALIDACION_COMPLETA', {'sha256': archive['sha256'], 'corte': manifest['corte']})


def hook(command, settings, row, beat):
    if not command:
        raise BackupError('No está configurado el hook operativo.')
    env = os.environ.copy()
    env.update({'OBRATEC_RESTORE_ID': str(row['id']), 'OBRATEC_BACKUP_ENVIRONMENT': settings.environment,
                'OBRATEC_MAINTENANCE': '1', 'OBRATEC_RELEASE_TARGET': str(settings.release_target)})
    # Exclusivamente configuración del operador, nunca comandos enviados por la API.
    process = subprocess.Popen(list(command), shell=False, env=env, stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    deadline = time.monotonic()+settings.timeout
    try:
        while process.poll() is None:
            beat()
            if time.monotonic() > deadline:
                raise BackupError('El hook operativo superó el tiempo permitido.')
            time.sleep(0.25)
        if process.returncode:
            raise BackupError('El hook operativo rechazó la operación. Revisa la consola del worker.')
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def journal_step(row, journal, label, kind, source, target, perform):
    step = {'paso': label, 'tipo': kind, 'origen': str(source), 'destino': str(target), 'estado': 'PREPARADO'}
    journal.append(step)
    repo.update('restauracion', row['id'], diario=journal, etapa=label)
    perform()
    step['estado'] = 'HECHO'
    repo.update('restauracion', row['id'], diario=journal)


def file_move(source, target, roots):
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target or not all(any(path == root or root in path.parents for root in roots) for path in (source, target)):
        raise BackupError('Promoción de archivo fuera de los directorios autorizados.')
    if source.is_symlink() or target.exists() or not source.exists():
        raise BackupError('El estado del filesystem impide una promoción segura.')
    target.parent.mkdir(parents=True, exist_ok=True)
    # Requiere el mismo volumen. No convertir un rename fallido en copia parcial.
    os.rename(source, target)


def compensate(settings, row, journal, beat):
    promotion_root = settings.release_target.parent/('.obratec_restore_'+str(row['id']))
    roots = (settings.release_target.resolve(), (settings.directory/'work').resolve(), promotion_root.resolve())
    hook(settings.stop_hook, settings, row, beat)
    for step in reversed(journal):
        if step['estado'] == 'REVERTIDO':
            continue
        source, target = step['origen'], step['destino']
        if step['tipo'] == 'database':
            src_exists, dst_exists = postgres.exists(settings, source), postgres.exists(settings, target)
            reverse = lambda: postgres.rename(settings, target, source)
        else:
            src_exists, dst_exists = Path(source).exists(), Path(target).exists()
            reverse = lambda: file_move(target, source, roots)
        if src_exists and not dst_exists:
            # La operación PREPARADA no llegó a ejecutarse.
            if step['estado'] == 'HECHO':
                raise BackupError('El diario y los recursos no coinciden; se necesita intervención.')
        elif dst_exists and not src_exists:
            reverse()
        else:
            raise BackupError('Promoción ambigua; se conservarán ambas generaciones para revisión.')
        step['estado'] = 'REVERTIDO'
        repo.update('restauracion', row['id'], diario=journal)
    hook(settings.start_hook, settings, row, beat)
    hook(settings.health_hook, settings, row, beat)
    repo.update('restauracion', row['id'], estado='REVERTIDA', etapa='Sistema anterior recuperado; vuelve a iniciar sesión', finished_at=datetime.now(timezone.utc))
    repo.barrier(row['id'], False)


def apply(settings, row, beat, disaster=False):
    issues = settings.restore_requirements()
    if issues:
        raise BackupError(' '.join(issues))
    if settings.release_target == ROOT or settings.release_target in ROOT.parents:
        raise BackupError('Para promover software ejecuta el worker instalado fuera del release actual.')
    archive = repo.get('archivo', row['archivo'])
    storage.obtain(settings, archive)
    work = Path(row['stage_dir']).resolve()
    expected_work = (settings.directory/'work'/('restore_'+str(row['id']))).resolve()
    if work != expected_work or row['stage_db'] != postgres.stage_name(row['id']):
        raise BackupError('El área temporal de esta restauración no es válida.')
    manifest = archive['manifiesto']
    verify_files(work/'package', manifest)
    check_evidence(settings, work/'package', manifest)
    if (datetime.now(timezone.utc)-row['validada_en']).total_seconds() > 3600:
        raise BackupError('La validación venció antes de aplicar; vuelve a validarla.')
    staged = postgres.connection(settings, row['stage_db'], True)
    try:
        if postgres.inventory(staged) != manifest['inventario_bd']:
            raise BackupError('La base temporal cambió desde su validación.')
    finally:
        staged.close()
    journal = []
    promotion_root = settings.release_target.parent/('.obratec_restore_'+str(row['id']))
    if manifest['alcance'] == 'sistema_completo':
        # Copiar y verificar fuera del release antes de renames en el mismo filesystem.
        promotion_root.mkdir(mode=0o700, exist_ok=False)
        needed = sum(entry['bytes'] for entry in manifest['archivos'] if entry['ruta'] != 'database.dump')
        if shutil.disk_usage(promotion_root).free < needed+128*1024**2:
            raise BackupError('No hay espacio suficiente para preparar el release en su volumen.')
        for entry in manifest['archivos']:
            name = entry['ruta']
            if name == 'database.dump':
                continue
            source = work/'package'/name
            target = promotion_root/'staged'/name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with open(source, 'rb') as src, open(target, 'xb') as dst:
                shutil.copyfileobj(src, dst, crypto.CHUNK)
                dst.flush(); os.fsync(dst.fileno())
            os.chmod(target, (entry.get('modo',0o644) & 0o755) if name.startswith('release/') else 0o600)
            if name.startswith('release/'):
                parent = target.parent
                while parent != promotion_root:
                    os.chmod(parent,0o755)
                    parent = parent.parent
            if crypto.sha256(target) != entry['sha256']:
                raise BackupError('La copia del release no pasó la verificación de integridad.')
            beat()
    repo.update('restauracion', row['id'], estado='MANTENIMIENTO', etapa='Preparando copia preventiva del estado actual')
    try:
        drain(row['id'], 'Restauración global confirmada', beat)
        original_exists = postgres.exists(settings, Config.DB_NAME)
        if not original_exists and not disaster:
            raise BackupError('La base actual no existe; usa el procedimiento de recuperación de desastre del operador.')
        prearchive = None
        if original_exists:
            preventive = repo.queue(row['id_usuario'], {'alcance': 'sistema_completo'},
                'pre-restore:'+str(row['id']), 'PRE_RESTAURACION', True)
            repo.update('ejecucion', preventive['id'], estado='GENERANDO')
            prearchive = engine.create(settings, preventive, beat, row['id'])
            temp_row = repo.validate_queue(prearchive, row['id_usuario'])
            validate(settings, temp_row, beat)
            verified = repo.get('restauracion', temp_row['id'])
            postgres.drop_stage(settings, verified['stage_db'])
            storage.cleanup_work(settings, verified['stage_dir'])
            repo.update('restauracion', temp_row['id'], estado='COMPLETADA', etapa='Ensayo de copia preventiva completo', finished_at=datetime.now(timezone.utc))
        else:
            repo.event(row['id'], row['id_usuario'], 'RECUPERACION_DESASTRE', {'base_original_ausente': True, 'copia_preventiva_imposible': True})
        repo.update('restauracion', row['id'], prebackup=prearchive, estado='APLICANDO', etapa='Deteniendo servicios y cerrando pools')
        hook(settings.stop_hook, settings, row, beat)
        # La sesión antigua no debe sobrevivir ni a una compensación posterior.
        repo.epoch(increment=True)
        old_db = 'obratec_old_'+str(row['id']).replace('-', '')[:24]
        if original_exists:
            journal_step(row, journal, 'Preservar base actual', 'database', Config.DB_NAME, old_db,
                         lambda: postgres.rename(settings, Config.DB_NAME, old_db))
        journal_step(row, journal, 'Promover base validada', 'database', row['stage_db'], Config.DB_NAME,
                     lambda: postgres.rename(settings, row['stage_db'], Config.DB_NAME))
        root = settings.release_target.resolve()
        roots = (root, (settings.directory/'work').resolve(), promotion_root.resolve())
        if manifest['alcance'] == 'sistema_completo':
            (promotion_root/'staged'/'uploads').mkdir(parents=True, exist_ok=True)
            parts = list(packages.RELEASE_TREES)+list(packages.RELEASE_FILES)+['backend/uploads']
            for relative in parts:
                current = root/relative
                staged_file = promotion_root/'staged'/('uploads' if relative == 'backend/uploads' else 'release/'+relative)
                preserved = promotion_root/'previous_release'/relative
                if current.exists():
                    journal_step(row, journal, 'Preservar '+relative, 'file', current, preserved,
                        lambda a=current, b=preserved: file_move(a, b, roots))
                if staged_file.exists():
                    journal_step(row, journal, 'Promover '+relative, 'file', staged_file, current,
                        lambda a=staged_file, b=current: file_move(a, b, roots))
        postgres.quarantine_reports(settings)
        check_evidence(settings, root/'backend', dict(manifest, alcance='base_datos'))
        hook(settings.start_hook, settings, row, beat)
        hook(settings.health_hook, settings, row, beat)
        repo.update('restauracion', row['id'], estado='COMPLETADA', etapa='Restauración completa; inicia sesión nuevamente. Reportes pausados.', finished_at=datetime.now(timezone.utc))
        repo.event(row['id'], row['id_usuario'], 'RESTAURACION_COMPLETA', {'base_preservada': old_db, 'prebackup': prearchive})
        repo.barrier(row['id'], False)
    except Exception:
        if journal:
            try:
                compensate(settings, row, journal, beat)
            except Exception:
                repo.update('restauracion', row['id'], estado='REQUIERE_INTERVENCION', etapa='Mantenimiento conservado; revisar diario antes de recuperar', diario=journal)
        else:
            # Si ni siquiera drenó, no liberar una barrera con escritores inciertos.
            repo.update('restauracion', row['id'], estado='REQUIERE_INTERVENCION', etapa='Preparación interrumpida; revisar mantenimiento')
        raise
