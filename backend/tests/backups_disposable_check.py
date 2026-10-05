"""Ensayo destructivo SOLO en bases efímeras creadas por este script.

No se ejecuta durante la validación normal. Requiere un clúster de pruebas designado
y BACKUP_TEST_ADMIN_DSN (dbname=postgres), además de las herramientas PostgreSQL 17.
"""
import argparse
import json
import os
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn, make_dsn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import Config
from app.repos import backup_repos as repo
from app.services.backups.settings import Settings
from app.services.backups import engine, restoration, postgres, storage


FIXTURE = """
CREATE SCHEMA obras;
CREATE TABLE obras.t_empresa(id_empresa integer PRIMARY KEY, nombre text NOT NULL);
CREATE TABLE obras.t_rol(id_rol integer PRIMARY KEY,nombre_rol text NOT NULL);
CREATE TABLE obras.t_usuario(id_usuario integer PRIMARY KEY,id_rol integer REFERENCES obras.t_rol,
 id_empresa integer REFERENCES obras.t_empresa,estado text NOT NULL);
CREATE TABLE obras.t_incidencia_evidencia(id serial PRIMARY KEY,id_empresa integer REFERENCES obras.t_empresa,ruta_archivo text NOT NULL);
CREATE TABLE obras.t_prueba(id serial PRIMARY KEY,id_empresa integer REFERENCES obras.t_empresa,total numeric NOT NULL CHECK(total>=0));
CREATE TABLE obras.t_historial(id serial PRIMARY KEY,mensaje text NOT NULL);
CREATE FUNCTION obras.fn_trigger_prueba() RETURNS trigger LANGUAGE plpgsql AS $$
 BEGIN INSERT INTO obras.t_historial(mensaje) VALUES('insertado'); RETURN NEW; END $$;
CREATE TRIGGER prueba AFTER INSERT ON obras.t_prueba FOR EACH ROW EXECUTE FUNCTION obras.fn_trigger_prueba();
CREATE FUNCTION obras.fn_prueba(empresa integer) RETURNS numeric LANGUAGE sql AS $$
 SELECT sum(total) FROM obras.t_prueba WHERE id_empresa=empresa $$;
CREATE PROCEDURE obras.sp_prueba() LANGUAGE plpgsql AS $$ BEGIN NULL; END $$;
INSERT INTO obras.t_empresa VALUES(1,'tenant A'),(2,'tenant B');
INSERT INTO obras.t_rol VALUES(1,'ADMINISTRADOR'),(2,'ADMINISTRADOR_EMPRESA');
INSERT INTO obras.t_usuario VALUES(1,1,1,'ACTIVO'),(2,2,2,'ACTIVO');
INSERT INTO obras.t_prueba(id_empresa,total) VALUES(1,10.25),(2,20.50);
INSERT INTO obras.t_incidencia_evidencia(id_empresa,ruta_archivo) VALUES(1,'uploads/incidencias/1/a.jpg'),(2,'uploads/incidencias/2/b.jpg');
"""


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--allow-create-disposable-databases',action='store_true',required=True)
    parser.add_argument('--environment',required=True)
    args=parser.parse_args()
    if args.environment != 'pruebas-desechables':
        raise SystemExit('Se requiere environment=pruebas-desechables.')
    dsn=os.getenv('BACKUP_TEST_ADMIN_DSN','')
    options=parse_dsn(dsn)
    if not dsn or options.get('dbname') != 'postgres':
        raise SystemExit('Designa BACKUP_TEST_ADMIN_DSN hacia postgres en un clúster de pruebas.')
    configured_host=(Config.DB_HOST or '',str(Config.DB_PORT or '5432'))
    if (options.get('host',''),str(options.get('port','5432'))) == configured_host:
        raise SystemExit('No se permite usar el host/puerto configurado de negocio para este ensayo destructivo.')
    suffix=uuid4().hex[:16]
    main_db='obratec_test_'+suffix;control_db='obratec_test_control_'+suffix
    created=[];stages=[]
    admin=psycopg2.connect(dsn);admin.autocommit=True
    try:
        with admin.cursor() as cur:
            cur.execute('SHOW server_version_num')
            if int(cur.fetchone()[0])//10000 != 17:
                raise SystemExit('Este ensayo requiere PostgreSQL 17.')
            for name in (main_db,control_db):
                cur.execute(sql.SQL('CREATE DATABASE {} TEMPLATE template0').format(sql.Identifier(name)));created.append(name)
        conn=psycopg2.connect(make_dsn(dsn,dbname=main_db))
        with conn:
            with conn.cursor() as cur:cur.execute(FIXTURE)
        conn.close()
        conn=psycopg2.connect(make_dsn(dsn,dbname=control_db))
        with conn:
            with conn.cursor() as cur:cur.execute((Path(__file__).parents[1]/'database/20261004_backup_control.sql').read_text())
        conn.close()
        with tempfile.TemporaryDirectory() as directory:
            area=Path(directory); release=area/'release';backup=area/'backups'
            for relative,content in {'backend/uploads/incidencias/1/a.jpg':b'photo-A','backend/uploads/incidencias/2/b.jpg':b'photo-B',
                    'backend/app/app.py':b'# fixture release','frontend/src/main.ts':b'// fixture release'}.items():
                file=release/relative;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(content)
            key=os.urandom(32)
            config=replace(Settings.load(),enabled=True,control_dsn=make_dsn(dsn,dbname=control_db),directory=backup,
                key_id='fixture',keys={'fixture':key},environment=args.environment,external_writers_coordinated=True,
                persistent_storage=True,restore_dsn=dsn,release_target=release,s3_bucket='',max_bytes=100*1024**2,
                sslmode=options.get('sslmode','prefer'))
            with (patch.object(Config,'DB_HOST',options.get('host')),patch.object(Config,'DB_PORT',options.get('port','5432')),
                 patch.object(Config,'DB_USER',options.get('user')),patch.object(Config,'DB_PASSWORD',options.get('password')),
                 patch.object(Config,'DB_NAME',main_db),patch.object(Settings,'load',return_value=config)):
                storage.prepare(config)
                job=repo.queue(1,{'alcance':'sistema_completo'},'fixture:'+suffix)
                archive=engine.create(config,job)
                row=repo.validate_queue(archive,1);stages.append(postgres.stage_name(row['id']))
                restoration.validate(config,row,lambda:None)
                actual=repo.get('restauracion',row['id'])
                assert actual['estado']=='VALIDADA'
                stage=postgres.connection(config,actual['stage_db'],True)
                with stage:
                    with stage.cursor() as cur:
                        cur.execute('SELECT obras.fn_prueba(1),obras.fn_prueba(2)')
                        assert [str(value) for value in cur.fetchone()]==['10.25','20.50']
                        cur.execute('INSERT INTO obras.t_prueba(id_empresa,total) VALUES(1,1) RETURNING id');assert cur.fetchone()[0]==3
                        cur.execute('SELECT count(*) FROM obras.t_historial');assert cur.fetchone()[0]==3
                        cur.execute('CALL obras.sp_prueba()')
                stage.close()
                assert (Path(actual['stage_dir'])/'package/uploads/incidencias/2/b.jpg').read_bytes()==b'photo-B'
                print('OK: dos tenants, datos, funciones/procedimiento, trigger, FK, secuencias, evidencias, cifrado y ensayo temporal.')
    finally:
        with admin.cursor() as cur:
            for name in stages+list(reversed(created)):
                if not (name.startswith('obratec_test_') or name.startswith('obratec_stage_')):
                    raise RuntimeError('Destino de limpieza rechazado.')
                cur.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(name)))
        admin.close()


if __name__=='__main__':
    try:main()
    except Exception:
        raise SystemExit('Ensayo fallido; revisar herramientas/privilegios en el clúster de pruebas, sin compartir DSN.')
