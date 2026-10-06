"""Publicar solo tras verificar la autenticación íntegra del ciphertext."""
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from uuid import uuid4
from . import postgres, packages, crypto, storage
from .coordination import drain
from .settings import ROOT, BackupError
from app.repos import backup_repos as repo


def evidence_inventory(root, captured, missing=None):
    result = {}
    for reference in captured['evidencias']:
        reference = packages.evidence_name(reference)
        path = packages.safe_name(reference)
        target = root/'backend'/str(path)
        upload_root = (root/'backend'/'uploads').resolve()
        if upload_root not in target.resolve().parents or target.is_symlink():
            raise BackupError('Hay una evidencia fuera del directorio permitido o con enlace simbólico.')
        if not target.is_file():
            if missing is not None:
                missing.append(reference)
                continue
            raise BackupError('Hay evidencias registradas sin archivo local accesible. No se puede certificar la copia.',
                              'BACKUP_EVIDENCE_UNAVAILABLE')
        result[reference] = crypto.sha256(target)
    return result


def create(settings, job, beat=lambda: None, barrier_owner=None):
    versions = postgres.versions(settings)
    root = settings.release_target or ROOT
    owner = barrier_owner or job['id']
    work = settings.directory/'work'/str(uuid4())
    work.mkdir(mode=0o700)
    locked = False
    try:
        repo.update('ejecucion', job['id'], etapa='Coordinando escritores y evidencias')
        drain(owner, 'Capturando respaldo consistente', beat)
        locked = True
        captured = postgres.dump(settings, work/'database.dump', beat)
        missing = []
        evidence = evidence_inventory(root, captured,
            missing=missing if job['solicitud']['alcance'] == 'base_datos' else None)
        manifest = {'formato': 1, 'id': str(job['id']), 'key_id': settings.key_id,
            'alcance': job['solicitud']['alcance'], 'entorno': settings.environment,
            'corte': datetime.now(timezone.utc).isoformat(), 'postgres': versions,
            'inventario_bd': captured, 'evidencias_sha256': evidence,
            'evidencias_no_disponibles': missing,
            'movil': 'Cliente externo; validar compatibilidad de API antes de restaurar',
            'roles_cluster': 'Roles/tablespaces externos: aprovisionar aparte sin contraseñas'}
        repo.update('ejecucion', job['id'], etapa='Empaquetando base, evidencias y software')
        manifest = packages.build(work/'package.zip', work/'database.dump', manifest, settings, root)
        manifest['release_sha256'] = hashlib.sha256(json.dumps(
            [entry for entry in manifest['archivos'] if entry['ruta'].startswith('release/')], sort_keys=True).encode()).hexdigest()
        with zipfile.ZipFile(work/'package.zip') as src, zipfile.ZipFile(work/'sealed.zip', 'x') as dst:
            for entry in src.infolist():
                if entry.filename == 'manifest.json':
                    continue
                with src.open(entry) as input_file, dst.open(entry, 'w', force_zip64=True) as output_file:
                    shutil.copyfileobj(input_file, output_file, crypto.CHUNK)
            dst.writestr('manifest.json', json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode())
        if barrier_owner is None:
            repo.barrier(owner, False)
            locked = False
        repo.update('ejecucion', job['id'], estado='VERIFICANDO', etapa='Cifrando y verificando integridad')
        beat()
        crypto.encrypt(work/'sealed.zip', work/'encrypted.partial', settings.key_id, settings.keys[settings.key_id], job['id'], settings.max_bytes)
        crypto.decrypt(work/'encrypted.partial', work/'verified.zip', settings.keys, settings.max_bytes)
        if crypto.sha256(work/'verified.zip') != crypto.sha256(work/'sealed.zip'):
            raise BackupError('Falló la verificación del paquete cifrado.')
        digest, size = crypto.sha256(work/'encrypted.partial'), (work/'encrypted.partial').stat().st_size
        name = 'obratec_'+str(job['id'])+'.obratec'
        _, remote = storage.publish(settings, work/'encrypted.partial', name)
        beat()
        return repo.register_archive(job, name, digest, size, manifest, remote)
    finally:
        if locked and barrier_owner is None:
            repo.barrier(owner, False)
        storage.cleanup_work(settings, work)
