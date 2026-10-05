"""Consola del plano de control VM. No ejecuta herramientas PostgreSQL ni OCI."""
import argparse
import json
from app.repos import backup_repos as repo
from app.services import backup_services as service
from app.services.backups.oracle_settings import Settings, BackupError


def main():
    parser = argparse.ArgumentParser(description='Control del Backup Service Oracle')
    parser.add_argument('--environment', required=True)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--status', action='store_true')
    actions.add_argument('--preflight', action='store_true')
    actions.add_argument('--dispatch-schedule', action='store_true',
                         help='Un ciclo de encolado AUTOMATICO; no ejecuta el backup')
    args = parser.parse_args()
    settings = Settings.load()
    if not settings.environment or args.environment != settings.environment:
        raise BackupError('El entorno no coincide con BACKUP_ENVIRONMENT.')
    if args.status:
        print(json.dumps(service.status(), default=str, ensure_ascii=False))
    elif args.preflight:
        print(json.dumps(service.preflight(), ensure_ascii=False))
    else:
        print(json.dumps(service.dispatch_schedule(), default=str, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except BackupError as exc:
        raise SystemExit(exc.code+': '+str(exc))
