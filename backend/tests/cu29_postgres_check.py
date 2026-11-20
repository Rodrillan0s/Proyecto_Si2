"""Ejecutor optativo: PostgreSQL desechable local; nunca escribe en Config.DB_NAME.

--prepare copia SOLO DDL de obras mediante pg_dump en modo de solo lectura.
El destino exige localhost, nombre cu29_test_* y marca de clúster disposable.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
STATE = Path(__file__).resolve().parents[1] / '.pytest_cache' / 'cu29_local.json'
BINS = Path('C:/Program Files/PostgreSQL/17/bin')


def connect_test(settings, database=None):
    import psycopg2
    if settings['host'] != '127.0.0.1' or not settings['dbname'].startswith('cu29_test_'):
        raise RuntimeError('Destino de pruebas no autorizado.')
    connection = psycopg2.connect(host=settings['host'], port=settings['port'],
                                  user=settings['user'], dbname=database or settings['dbname'],
                                  connect_timeout=5)
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_setting('obratec.cu29_test',true)")
        if cursor.fetchone()[0] != 'disposable':
            connection.close()
            raise RuntimeError('Falta la marca de clúster de pruebas desechable.')
    connection.rollback()
    return connection


def prepare(cluster_dir=None):
    if cluster_dir:
        root = Path(cluster_dir).resolve()
        if root.parent != Path(tempfile.gettempdir()).resolve() or not root.name.startswith('obratec-cu29-local-'):
            raise RuntimeError('Directorio de clúster no autorizado.')
        settings = json.loads((root / 'connection.json').read_text(encoding='utf-8'))
    else:
        root = Path(tempfile.mkdtemp(prefix='obratec-cu29-local-'))
        subprocess.run([str(BINS / 'initdb.exe'), '-D', str(root / 'data'), '-U', 'cu29_test',
                        '-A', 'trust', '--encoding=UTF8', '--locale=C'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        with socket.socket() as server:
            server.bind(('127.0.0.1', 0))
            port = server.getsockname()[1]
        settings = dict(host='127.0.0.1', port=port, user='cu29_test')
        (root / 'connection.json').write_text(json.dumps(settings), encoding='utf-8')
        # No capturar pipes: en Windows el daemon puede heredar sus handles.
        subprocess.run([str(BINS / 'pg_ctl.exe'), '-D', str(root / 'data'), '-l', str(root / 'server.log'),
                        '-o', f'-h 127.0.0.1 -p {port} -c obratec.cu29_test=disposable', '-w', 'start'],
                       check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    settings['dbname'] = 'cu29_test_' + uuid4().hex[:12]
    settings['cluster_dir'] = str(root)
    connection = connect_test(settings, 'postgres')
    connection.autocommit = True
    try:
        from psycopg2 import sql
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(settings['dbname'])))
    finally:
        connection.close()
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(settings), encoding='utf-8')

    from app.config import Config
    source_env = os.environ.copy()
    source_env['PGPASSWORD'] = Config.DB_PASSWORD
    source_env['PGOPTIONS'] = '-c default_transaction_read_only=on -c statement_timeout=30000'
    schema_file = root / 'schema_only.sql'
    with schema_file.open('wb') as output:
        result = subprocess.run([str(BINS / 'pg_dump.exe'), '--schema-only', '--schema=obras',
                                 '--no-owner', '--no-privileges', '-h', Config.DB_HOST,
                                 '-p', str(Config.DB_PORT), '-U', Config.DB_USER, '-d', Config.DB_NAME],
                                env=source_env, stdout=output, stderr=subprocess.PIPE, timeout=90)
    if result.returncode:
        raise RuntimeError('No se pudo obtener el DDL de solo lectura; no se importaron datos.')
    target = connect_test(settings)
    target.autocommit = True
    try:
        with target.cursor() as cursor:
            cursor.execute('CREATE EXTENSION IF NOT EXISTS unaccent')
    finally:
        target.close()
    local_env = os.environ.copy()
    local_env.pop('PGPASSWORD', None)
    local_env.pop('PGOPTIONS', None)
    result = subprocess.run([str(BINS / 'psql.exe'), '-h', settings['host'], '-p', str(settings['port']),
                             '-U', settings['user'], '-d', settings['dbname'], '-v', 'ON_ERROR_STOP=1',
                             '-f', str(schema_file)], env=local_env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, timeout=90)
    if result.returncode:
        raise RuntimeError('Importación de DDL local falló: ' + result.stderr.decode(errors='replace')[-1000:])
    print('Preparado PostgreSQL local sin datos de negocio:', settings['dbname'], 'puerto', settings['port'], flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--cluster-dir')
    parser.add_argument('--stage', choices=['1', '2', '3', '4', 'all'], default='all')
    parser.add_argument('--stop', action='store_true')
    args = parser.parse_args()
    if args.prepare:
        prepare(args.cluster_dir)
        return 0
    settings = json.loads(STATE.read_text(encoding='utf-8'))
    connection = connect_test(settings)
    connection.close()
    if args.stop:
        root = Path(settings['cluster_dir']).resolve()
        if root.parent != Path(tempfile.gettempdir()).resolve() or not root.name.startswith('obratec-cu29-local-'):
            raise RuntimeError('Directorio de clúster no autorizado para detener.')
        subprocess.run([str(BINS / 'pg_ctl.exe'), '-D', str(root / 'data'), '-m', 'fast', '-w', 'stop'],
                       check=True, timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print('Clúster CU29 desechable detenido.')
        return 0
    os.environ['CU29_TEST_SETTINGS'] = json.dumps(settings)
    import pytest
    tests = ['-q', '-p', 'no:cacheprovider', 'tests/test_cu29_postgres.py', '--tb=short']
    if args.stage != 'all':
        tests += ['-k', 'stage' + args.stage]
    return pytest.main(tests)


if __name__ == '__main__':
    raise SystemExit(main())
