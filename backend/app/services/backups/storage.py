import os
import shutil
from pathlib import Path
from .crypto import sha256
from .settings import BackupError


def prepare(settings):
    settings.require()
    directory = settings.directory
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    for name in ('archives', 'work', 'imports'):
        (directory/name).mkdir(mode=0o700, exist_ok=True)
    if shutil.disk_usage(directory).free < 128*1024**2:
        raise BackupError('El volumen de respaldo tiene menos de 128 MiB libres.', 'BACKUP_STORAGE_FULL', 503)
    return directory


def archive_path(settings, name):
    if Path(name).name != name or not name.endswith('.obratec') or '/' in name or '\\' in name:
        raise BackupError('Nombre de archivo de respaldo inválido.')
    return settings.directory/'archives'/name


def client(settings):
    import boto3
    return boto3.client('s3', endpoint_url=settings.s3_endpoint or None)


def publish(settings, source, name):
    target = archive_path(settings, name)
    if target.exists():
        raise BackupError('El archivo de destino ya existe.')
    remote = None
    if settings.s3_bucket:
        key = settings.s3_prefix+name
        s3 = client(settings)
        # El ciphertext es privado; checksum del contenido en metadata, sin secretos.
        s3.upload_file(str(source), settings.s3_bucket, key,
                       ExtraArgs={'Metadata': {'sha256': sha256(source)}})
        remote = key
    os.replace(source, target)
    return target, remote


def obtain(settings, archive):
    if archive['eliminado_en']:
        raise BackupError('El respaldo venció según la retención.', 'BACKUP_EXPIRED', 410)
    path = archive_path(settings, archive['nombre'])
    if not path.is_file() and archive.get('remoto') and settings.s3_bucket:
        temporary = path.with_suffix('.fetching')
        try:
            client(settings).download_file(settings.s3_bucket, archive['remoto'], str(temporary))
            if sha256(temporary) != archive['sha256']:
                raise BackupError('La réplica no coincide con su huella.')
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    if not path.is_file() or path.stat().st_size != archive['bytes'] or sha256(path) != archive['sha256']:
        raise BackupError('El archivo no está disponible o su huella cambió.', 'BACKUP_ARCHIVE_UNAVAILABLE')
    return path


def delete(settings, archive):
    path = archive_path(settings, archive['nombre'])
    if archive.get('remoto') and settings.s3_bucket:
        client(settings).delete_object(Bucket=settings.s3_bucket, Key=archive['remoto'])
    path.unlink(missing_ok=True)


def cleanup_work(settings, directory):
    directory = Path(directory).resolve()
    allowed = (settings.directory/'work').resolve()
    if directory != allowed and allowed in directory.parents and not directory.is_symlink():
        shutil.rmtree(directory)
    else:
        raise BackupError('Se rechazó limpiar un directorio fuera del área temporal.')
