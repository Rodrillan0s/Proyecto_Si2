"""Comprobación manual contra BD real; todos los cambios se revierten.

Ejecutar desde backend: .venv/Scripts/python tests/cu19_unidad_real_check.py
Usa routers reales y JWT locales; no sustituye la prueba visual móvil/web.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from unittest.mock import patch
import psycopg2
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.config import Config
from app.classes.postgres import PostgreSQL
from app.routes import incidencia_routes, unidad_routes
from app.services import incidencia_services
from app.utils.security import create_access_token


def main():
    conn = psycopg2.connect(host=Config.DB_HOST, port=Config.DB_PORT,
                           dbname=Config.DB_NAME, user=Config.DB_USER,
                           password=Config.DB_PASSWORD, connect_timeout=10)
    next_id = -190700
    created = []

    class Connection:
        def commit(self):
            pass

        def rollback(self):
            raise RuntimeError('La prueba debe abortar ante un error SQL')

    class Cursor:
        def __init__(self):
            self.cursor = conn.cursor()

        def execute(self, sql, params=None):
            nonlocal next_id
            if sql.lstrip().upper().startswith('INSERT INTO OBRAS.T_INCIDENCIA'):
                table = ('t_incidencia_seguimiento' if 'INSERT INTO obras.t_incidencia_seguimiento' in sql
                         else 't_incidencia')
                column = 'id_seguimiento' if table.endswith('seguimiento') else 'id_incidencia'
                next_id -= 1
                start = sql.index('(')
                sql = sql[:start + 1] + column + ', ' + sql[start + 1:]
                sql = sql.replace('VALUES (', 'VALUES (%s, ', 1)
                params = (next_id,) + tuple(params)
            self.cursor.execute(sql, params)

        def __getattr__(self, name):
            return getattr(self.cursor, name)

    def open_db(db):
        db.conn = Connection()
        db.cur = Cursor()

    def close_db(db, commit=False):
        db.cur.close()
        db.conn = db.cur = None

    app = FastAPI()
    app.include_router(incidencia_routes.router, prefix='/api/incidencias')
    app.include_router(unidad_routes.router)
    try:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout='20s'")
            cur.execute("SELECT u.id_usuario,u.username,p.nombre_completo,r.nombre_rol,u.id_empresa "
                        "FROM obras.t_usuario u JOIN obras.t_rol r ON r.id_rol=u.id_rol "
                        "LEFT JOIN obras.t_persona p ON p.id_persona=u.id_persona "
                        "WHERE u.id_usuario IN (13,14)")
            users = {row[0]: row for row in cur.fetchall()}
            cur.execute("SELECT u.id_unidad,e.id_obra,o.nombre FROM obras.t_unidad_construccion u "
                        "JOIN obras.t_estructura_obra e ON e.id_estructura=u.id_estructura "
                        "JOIN obras.t_obra o ON o.id_obra=e.id_obra WHERE u.codigo='UNI-000007'")
            unit, obra, nombre = cur.fetchone()
            assert nombre == 'Green Tower'
            cur.execute("SELECT u.id_unidad FROM obras.t_unidad_construccion u "
                        "JOIN obras.t_estructura_obra e ON e.id_estructura=u.id_estructura "
                        "WHERE e.id_obra<>%s LIMIT 1", (obra,))
            foreign = cur.fetchone()
            assert foreign, 'Se necesita una unidad de otra obra para la prueba'

        def headers(uid):
            user = users[uid]
            jwt = create_access_token(user[0], user[1], user[3], user[4], '', user[2], None)
            return {'Authorization': 'Bearer ' + jwt}

        with patch.object(PostgreSQL, 'create_connection', open_db), \
             patch.object(PostgreSQL, 'close_connection', close_db), \
             patch.object(incidencia_services, '_log', lambda *a, **k: None), \
             TestClient(app) as client:
            response = client.get('/api/incidencias/obras-registro', headers=headers(14))
            assert response.status_code == 200, response.text
            assert any(o['id_obra'] == obra for o in response.json()['data'])
            response = client.get(f'/api/proyectos/{obra}/unidades/', headers=headers(14))
            assert response.status_code == 200, response.text
            assert any(u['id_unidad'] == unit for u in response.json()['data'])
            body = dict(id_obra=obra, id_unidad=unit, titulo='Prueba CU19 unidad móvil',
                        descripcion='Prueba transaccional revertida', prioridad='BAJA')
            for selected in (unit, None):
                response = client.post('/api/incidencias/', json={**body, 'id_unidad': selected}, headers=headers(14))
                assert response.status_code == 201, response.text
                iid = response.json()['id_incidencia']
                created.append(iid)
                with conn.cursor() as cur:
                    cur.execute('SELECT id_unidad,id_usuario_registro,id_responsable,estado FROM obras.t_incidencia WHERE id_incidencia=%s', (iid,))
                    assert cur.fetchone() == (selected, 14, None, 'ABIERTA')
                response = client.get(f'/api/incidencias/{iid}', headers=headers(13))
                assert response.status_code == 200, response.text
                detail = response.json()['data']
                assert detail['obra_nombre'] == 'Green Tower'
                assert detail['unidad_codigo'] == ('UNI-000007' if selected else None)
                assert ' '.join(detail['usuario_registro_nombre'].split()) == 'JHON JONES'
                assert detail['id_responsable'] is None and detail['estado'] == 'ABIERTA'
            response = client.post('/api/incidencias/', json={**body, 'id_unidad': foreign[0]}, headers=headers(14))
            assert response.status_code == 400, response.text
            print('PASS: Jhon lista UNI-000007; registro con/sin unidad; BD y detalle de Julián correctos; unidad ajena rechazada.')
    finally:
        conn.rollback()
        with conn.cursor() as cur:
            cur.execute('SELECT count(*) FROM obras.t_incidencia WHERE id_incidencia=ANY(%s)', (created,))
            assert cur.fetchone()[0] == 0
        conn.close()
        print('ROLLBACK verificado; sin incidencias persistentes ni consumo de secuencias.')


if __name__ == '__main__':
    main()
