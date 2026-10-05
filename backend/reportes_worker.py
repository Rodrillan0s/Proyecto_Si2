"""python reportes_worker.py [--once]. Servicio separado del servidor HTTP."""
import argparse
import logging
import time
from app.services.reportes.worker import tick


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    while True:
        try:
            busy = tick()
        except Exception:
            logging.error('El worker no pudo completar el ciclo. Revise conectividad y migración.')
            if args.once:
                raise SystemExit(1)
            busy = False
        if args.once:
            break
        time.sleep(1 if busy else 15)


if __name__=='__main__':
    main()
