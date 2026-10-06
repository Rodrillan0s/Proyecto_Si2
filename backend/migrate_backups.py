"""Instalación explícita en la base de control. No crea bases ni toca negocio."""
import argparse
from pathlib import Path
import psycopg2
from psycopg2.extensions import parse_dsn
from app.config import Config
from app.services.backups.oracle_settings import Settings, BackupError


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--environment', required=True, help='Debe coincidir con BACKUP_ENVIRONMENT')
    args = parser.parse_args()
    settings = Settings.load()
    if not settings.control_dsn or args.environment != settings.environment or not settings.environment:
        raise BackupError('Identifica el entorno y configura BACKUP_CONTROL_DSN.')
    options = parse_dsn(settings.control_dsn)
    if not options.get('dbname') or options['dbname'] == Config.DB_NAME:
        raise BackupError('Se rechazó migrar la base de negocio.')
    conn = psycopg2.connect(settings.control_dsn, connect_timeout=5)
    try:
        if not args.apply:
            conn.set_session(readonly=True)
        with conn:
            with conn.cursor() as cur:
                if args.apply:
                    cur.execute((Path(__file__).parent/'database'/'20261005_backup_vm_integration.sql').read_text(encoding='utf-8'))
                    print('Migración auxiliar VM aplicada. Cola y daemon existentes conservados.')
                else:
                    cur.execute("SELECT schemaname,tablename FROM pg_tables WHERE schemaname='backup_control' OR (schemaname='public' AND tablename='backup_jobs') ORDER BY schemaname,tablename")
                    print('Tablas presentes:', ', '.join('.'.join(row) for row in cur.fetchall()) or 'ninguna')
    finally:
        conn.close()


if __name__ == '__main__':
    try:
        main()
    except BackupError as exc:
        raise SystemExit(str(exc))
    except Exception:
        raise SystemExit('No se pudo instalar/verificar el control. Revisa conexión y permisos sin compartir credenciales.')
