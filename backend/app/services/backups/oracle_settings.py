"""Configuración del cliente de la cola VM: sin herramientas ni credenciales OCI."""
import os
from dataclasses import dataclass
from psycopg2.extensions import parse_dsn
from app.config import Config
from .settings import BackupError


@dataclass(frozen=True)
class Settings:
    enabled: bool
    control_dsn: str
    environment: str
    heartbeat_connected: bool
    heartbeat_max_age: int
    oci_namespace: str = 'grdnljcz1opp'
    oci_bucket: str = 'obratec_backups'

    @classmethod
    def load(cls):
        def flag(name):
            return os.getenv(name, '').lower() in {'1', 'true', 'yes'}
        try:
            age = int(os.getenv('BACKUP_VM_HEARTBEAT_MAX_AGE', '120'))
        except ValueError as exc:
            raise BackupError('BACKUP_VM_HEARTBEAT_MAX_AGE debe ser un entero.', 'BACKUP_CONFIG', 503) from exc
        return cls(flag('BACKUP_ENABLED'), os.getenv('BACKUP_CONTROL_DSN', ''),
                   os.getenv('BACKUP_ENVIRONMENT', ''), flag('BACKUP_VM_HEARTBEAT_CONNECTED'),
                   age, os.getenv('BACKUP_VM_OCI_NAMESPACE', 'grdnljcz1opp'),
                   os.getenv('BACKUP_VM_OCI_BUCKET', 'obratec_backups'))

    def requirements(self):
        missing = []
        if not self.enabled:
            missing.append('Activar BACKUP_ENABLED para utilizar la cola del servicio Oracle.')
        try:
            control = parse_dsn(self.control_dsn)
            if not control.get('dbname') or control['dbname'] == Config.DB_NAME:
                raise ValueError()
        except Exception:
            # No incluir DSN ni errores de libpq con datos de conexión.
            missing.append('BACKUP_CONTROL_DSN debe apuntar a una base de control independiente.')
        if not self.environment:
            missing.append('Identificar el entorno con BACKUP_ENVIRONMENT.')
        if not 30 <= self.heartbeat_max_age <= 600:
            missing.append('BACKUP_VM_HEARTBEAT_MAX_AGE debe estar entre 30 y 600 segundos.')
        return missing

    def require(self):
        issues = self.requirements()
        if issues:
            raise BackupError(' '.join(issues), 'BACKUP_SETUP_REQUIRED', 503)
