"""Inventario cerrado, sin extracción de rutas proporcionadas directamente al filesystem."""
import json
import os
import stat
import zipfile
from pathlib import Path, PurePosixPath
from .crypto import sha256, CHUNK
from .settings import ROOT, BackupError

EXCLUDED = {'.git', '.env', '.venv', 'venv', 'node_modules', '__pycache__', '.angular',
            '.pytest_cache', '.codex', '.agents', '.aws', '.ssh', 'secrets', 'credentials',
            'uploads', 'backups', 'logs', 'coverage'}
RELEASE_TREES = ('backend/app', 'backend/database', 'frontend/src', 'frontend/public', 'frontend/dist')
RELEASE_FILES = ('backend/run.py', 'backend/reportes_worker.py', 'backend/backup_worker.py',
    'backend/backup_recovery.py', 'backend/migrate_backups.py', 'backend/migrate_reportes.py',
    'backend/requirements.txt', 'backend/requirements-backup.txt', 'backend/requirements-voice.txt',
    'frontend/package.json', 'frontend/package-lock.json', 'frontend/angular.json',
    'frontend/tsconfig.json', 'frontend/tsconfig.app.json', 'frontend/tailwind.config.js',
    'frontend/postcss.config.js')


def safe_name(name):
    path = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or '\x00' in name or path.is_absolute()
            or any(part in {'..', '.', ''} for part in name.split('/'))):
        raise BackupError('El archivo contiene una ruta insegura.', 'BACKUP_INVALID_PACKAGE')
    return path


def evidence_name(reference):
    """Incidencias persiste os.path.join: normalizar solo su ruta relativa."""
    if not isinstance(reference, str):
        raise BackupError('Referencia de evidencia inválida.')
    name = reference.replace('\\', '/')
    safe_name(name)
    if not name.startswith('uploads/'):
        raise BackupError('Hay evidencias fuera de uploads; corrige sus rutas antes de respaldar.')
    return name


def allowed_release(name):
    if any(part.lower() in EXCLUDED or part.lower().startswith('.env') or
           part.lower().endswith(('.pem', '.key', '.p12', '.pfx', '.pyc')) for part in PurePosixPath(name).parts):
        return False
    return name in RELEASE_FILES or any(name.startswith(tree+'/') for tree in RELEASE_TREES)


def sources(full, root=ROOT):
    yield 'database.dump', None
    if not full:
        return
    upload = root/'backend'/'uploads'
    if upload.exists():
        for file in sorted(upload.rglob('*')):
            if file.is_symlink():
                raise BackupError('No se permiten enlaces simbólicos en evidencias.')
            if file.is_file():
                if upload.resolve() not in file.resolve().parents:
                    raise BackupError('Una evidencia apunta fuera del árbol uploads.')
                yield 'uploads/'+file.relative_to(upload).as_posix(), file
    for tree in RELEASE_TREES:
        directory = root/tree
        if directory.exists():
            for file in sorted(directory.rglob('*')):
                name = file.relative_to(root).as_posix()
                if allowed_release(name) and file.is_file():
                    if file.is_symlink() or root.resolve() not in file.resolve().parents:
                        raise BackupError('No se permiten enlaces simbólicos en el release.')
                    yield 'release/'+name, file
    for name in RELEASE_FILES:
        file = root/name
        if file.is_file() and not file.is_symlink():
            yield 'release/'+name, file


def build(destination, dump, manifest, settings, root=ROOT):
    entries = []
    total = 0
    with zipfile.ZipFile(destination, 'x', allowZip64=True) as archive:
        for name, file in sources(manifest['alcance'] == 'sistema_completo', root):
            file = dump if file is None else file
            safe_name(name)
            total += file.stat().st_size
            if total > settings.max_bytes or len(entries) >= settings.max_files:
                raise BackupError('El paquete supera los límites de tamaño o cantidad de archivos.')
            digest = sha256(file)
            archive.write(file, name, compress_type=zipfile.ZIP_STORED if name == 'database.dump' else zipfile.ZIP_DEFLATED)
            if digest != sha256(file):
                raise BackupError('Un archivo cambió durante la captura. Coordina todos los escritores.')
            entries.append({'ruta': name, 'bytes': file.stat().st_size, 'sha256': digest,
                            'modo': stat.S_IMODE(file.stat().st_mode) & 0o755})
        manifest = dict(manifest, archivos=entries)
        encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=False).encode()
        if len(encoded) > 32*1024**2:
            raise BackupError('Inventario del paquete demasiado grande.')
        archive.writestr('manifest.json', encoded)
    return manifest


def unpack(source, destination, settings):
    destination = Path(destination).resolve()
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    try:
        with zipfile.ZipFile(source) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            if len(infos) > settings.max_files+1 or len(names) != len(set(names)) or 'manifest.json' not in names:
                raise BackupError('Inventario duplicado, ausente o demasiado grande.')
            manifest_info = archive.getinfo('manifest.json')
            if manifest_info.file_size > 32*1024**2:
                raise BackupError('Manifiesto demasiado grande.')
            manifest = json.loads(archive.read(manifest_info))
            if manifest.get('formato') != 1 or manifest.get('alcance') not in {'base_datos', 'sistema_completo'}:
                raise BackupError('Versión o alcance del paquete incompatible.')
            entries = manifest['archivos']
            expected = {entry['ruta']: entry for entry in entries}
            if len(expected) != len(entries) or set(expected) != set(names)-{'manifest.json'} or 'database.dump' not in expected:
                raise BackupError('El inventario no coincide con el contenido.')
            total = 0
            for info in infos:
                name = info.filename
                safe_name(name)
                mode = info.external_attr >> 16
                if info.is_dir() or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in {0, stat.S_IFREG}):
                    raise BackupError('El paquete contiene enlaces o entradas especiales.')
                if name == 'manifest.json':
                    continue
                if not (name == 'database.dump' or name.startswith('uploads/') or
                        name.startswith('release/') and allowed_release(name[8:])):
                    raise BackupError('El paquete contiene archivos fuera del alcance permitido.')
                if manifest['alcance'] == 'base_datos' and name != 'database.dump':
                    raise BackupError('Un respaldo de base de datos no debe contener software/evidencias.')
                total += info.file_size
                if total > settings.max_bytes or info.file_size != expected[name]['bytes']:
                    raise BackupError('Tamaño del paquete incompatible con su inventario.')
                target = destination.joinpath(*PurePosixPath(name).parts)
                if destination not in target.resolve().parents:
                    raise BackupError('Ruta fuera del directorio temporal.')
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, open(target, 'xb') as dst:
                    os.chmod(target, 0o600)
                    copied = 0
                    for chunk in iter(lambda: src.read(CHUNK), b''):
                        copied += len(chunk)
                        if copied > info.file_size:
                            raise BackupError('Archivo expandido mayor al inventario.')
                        dst.write(chunk)
                if sha256(target) != expected[name]['sha256']:
                    raise BackupError('La huella de un archivo no coincide con el inventario.')
            with open(destination/'database.dump', 'rb') as stream:
                if stream.read(5) != b'PGDMP':
                    raise BackupError('El paquete no contiene un pg_dump custom válido.')
            return manifest
    except (zipfile.BadZipFile, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise BackupError('Paquete incompatible o dañado.', 'BACKUP_INVALID_PACKAGE') from exc
