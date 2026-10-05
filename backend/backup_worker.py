"""Worker en primer plano; el servicio HTTP no lo arranca automáticamente."""
import argparse
import logging
import time
from app.services.backups.worker import tick
from app.services.backups.settings import BackupError


def main():
    parser = argparse.ArgumentParser(description='Worker durable de backups OBRATEC')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--interval', type=int, default=15)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    while True:
        try:
            tick()
        except BackupError as exc:
            logging.error('%s: %s', exc.code, exc)
            if args.once:
                return 1
        except Exception:
            logging.error('El worker falló; revisar la base de control y la instalación. No se expone información de conexión.')
            if args.once:
                return 1
        if args.once:
            return 0
        time.sleep(max(1, args.interval))


if __name__ == '__main__':
    raise SystemExit(main())
