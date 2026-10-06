"""Configuración operativa; jamás devuelve credenciales al cliente."""
import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path

from app.config import Config

ROOT = Path(__file__).resolve().parents[4]


class BackupError(Exception):
    def __init__(self, message, code='BACKUP_ERROR', status=409):
        super().__init__(message)
        self.code, self.status = code, status


@dataclass(frozen=True)
class Settings:
    enabled: bool
    control_dsn: str
    directory: Path | None
    key_id: str
    keys: dict
    environment: str
    sslmode: str
    timeout: int
    max_bytes: int
    max_files: int
    external_writers_coordinated: bool
    persistent_storage: bool
    restore_enabled: bool
    restore_dsn: str
    stop_hook: tuple
    start_hook: tuple
    health_hook: tuple
    release_target: Path | None
    worker_external: bool
    s3_bucket: str
    s3_prefix: str
    s3_endpoint: str
    rehearsal_enabled: bool = False
    rehearsal_days: int = 7

    @classmethod
    def load(cls):
        def flag(name):
            return os.getenv(name, '').lower() in {'1', 'true', 'yes'}
        def path(name):
            value = os.getenv(name)
            return Path(value).expanduser().resolve() if value else None
        def command(name):
            value = json.loads(os.getenv(name, '[]'))
            if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
                raise BackupError('El hook debe ser un arreglo JSON de argumentos.', 'BACKUP_CONFIG', 503)
            return tuple(value)
        try:
            keys = json.loads(os.getenv('BACKUP_KEYS_JSON', '{}'))
            if not isinstance(keys, dict):
                raise ValueError()
            keys = {key: base64.b64decode(value, validate=True) for key, value in keys.items()}
            if any(len(value) != 32 for value in keys.values()):
                raise ValueError()
            return cls(flag('BACKUP_ENABLED'), os.getenv('BACKUP_CONTROL_DSN', ''),
                path('BACKUP_DIRECTORY'), os.getenv('BACKUP_KEY_ID', ''), keys,
                os.getenv('BACKUP_ENVIRONMENT', ''), os.getenv('DB_SSLMODE', 'require'),
                int(os.getenv('BACKUP_TIMEOUT_SECONDS', '3600')),
                int(os.getenv('BACKUP_MAX_BYTES', str(10 * 1024**3))),
                int(os.getenv('BACKUP_MAX_FILES', '100000')),
                flag('BACKUP_EXTERNAL_WRITERS_COORDINATED'), flag('BACKUP_STORAGE_PERSISTENT'),
                flag('BACKUP_RESTORE_ENABLED'), os.getenv('BACKUP_RESTORE_DSN', ''),
                command('BACKUP_STOP_HOOK'), command('BACKUP_START_HOOK'), command('BACKUP_HEALTH_HOOK'),
                path('BACKUP_RELEASE_TARGET'), flag('BACKUP_WORKER_EXTERNAL'),
                os.getenv('BACKUP_S3_BUCKET', ''), os.getenv('BACKUP_S3_PREFIX', 'obratec/'),
                os.getenv('BACKUP_S3_ENDPOINT', ''), flag('BACKUP_REHEARSAL_ENABLED'),
                int(os.getenv('BACKUP_REHEARSAL_INTERVAL_DAYS', '7')))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise BackupError('Revise la configuración de copias de respaldo.', 'BACKUP_CONFIG', 503) from exc

    def requirements(self):
        import importlib.util
        from psycopg2.extensions import parse_dsn
        missing = []
        if not self.enabled:
            missing.append('Activar BACKUP_ENABLED después de instalar la base de control.')
        if not self.control_dsn:
            missing.append('Configurar BACKUP_CONTROL_DSN y aplicar la migración de control.')
        else:
            try:
                control = parse_dsn(self.control_dsn)
                if not control.get('dbname') or control['dbname'] == Config.DB_NAME:
                    missing.append('La base de control debe tener un nombre distinto de la base de negocio.')
            except Exception:
                missing.append('BACKUP_CONTROL_DSN no es una conexión PostgreSQL válida.')
        if not self.directory:
            missing.append('Configurar BACKUP_DIRECTORY en un volumen persistente externo al proyecto.')
        elif any(root == self.directory or root in self.directory.parents for root in (ROOT, self.release_target or ROOT)) or self.directory == Path(self.directory.anchor):
            missing.append('BACKUP_DIRECTORY debe estar fuera del proyecto y no ser la raíz de un disco.')
        if not self.persistent_storage:
            missing.append('Confirmar volumen persistente con BACKUP_STORAGE_PERSISTENT.')
        if not self.key_id or self.key_id not in self.keys:
            missing.append('Configurar BACKUP_KEY_ID y una clave AES de 32 bytes en BACKUP_KEYS_JSON.')
        if not self.environment:
            missing.append('Identificar el entorno con BACKUP_ENVIRONMENT.')
        if not self.external_writers_coordinated:
            missing.append('Coordinar escritores externos y confirmar BACKUP_EXTERNAL_WRITERS_COORDINATED.')
        if not importlib.util.find_spec('cryptography'):
            missing.append('Instalar backend/requirements-backup.txt.')
        if self.s3_bucket and not importlib.util.find_spec('boto3'):
            missing.append('Instalar boto3 para la réplica privada S3.')
        if self.timeout < 30 or self.max_bytes < 1024 or self.max_files < 1:
            missing.append('Límites de tiempo, tamaño o archivos inválidos.')
        if self.rehearsal_enabled:
            missing.extend(self.restore_requirements())
            if not 1 <= self.rehearsal_days <= 90:
                missing.append('BACKUP_REHEARSAL_INTERVAL_DAYS debe estar entre 1 y 90.')
        return missing

    def require(self):
        issues = self.requirements()
        if issues:
            raise BackupError(' '.join(issues), 'BACKUP_SETUP_REQUIRED', 503)

    def restore_requirements(self):
        issues = []
        if not self.restore_enabled:
            issues.append('Activar BACKUP_RESTORE_ENABLED en el entorno designado.')
        if not self.restore_dsn:
            issues.append('Configurar BACKUP_RESTORE_DSN con permisos de creación y promoción de bases.')
        else:
            try:
                from psycopg2.extensions import parse_dsn
                restore = parse_dsn(self.restore_dsn)
                if (restore.get('host', '') != (Config.DB_HOST or '') or
                    str(restore.get('port', '5432')) != str(Config.DB_PORT or '5432') or
                    restore.get('dbname') != 'postgres'):
                    issues.append('La cuenta de restauración debe conectar a postgres en el mismo host y puerto del negocio.')
            except Exception:
                issues.append('BACKUP_RESTORE_DSN no es válido.')
        if not (self.stop_hook and self.start_hook and self.health_hook):
            issues.append('Configurar hooks de detener servicios, arrancar y verificar salud.')
        if not self.worker_external:
            issues.append('Ejecutar el worker desde una instalación externa al release restaurado.')
        if not self.release_target or not (self.release_target/'backend').is_dir() or not (self.release_target/'frontend').is_dir():
            issues.append('BACKUP_RELEASE_TARGET debe identificar el release actual del backend y frontend.')
        return issues
