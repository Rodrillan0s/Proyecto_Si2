"""Personal de obra: autorización y regresión PostgreSQL en un esquema aislado.

SI2_TEST_PERSONAL_DB=1 habilita la integración. Todo el esquema se revierte al
terminar cada prueba; no se asignan usuarios ni se alteran datos de producción.
"""
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Config
from app.repos import obra_repos as repo, incidencia_repos
from app.routes import obra_routes
from app.services import obra_services as svc
from app.utils import security


ADMIN = {'nombre_rol': 'ADMINISTRADOR_EMPRESA', 'id_empresa': 1, 'nro_usuario': 20}
GLOBAL = {'nombre_rol': 'ADMINISTRADOR', 'nro_usuario': 1}


class PersonalAuthorizationTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(obra_routes.router, prefix='/api/proyectos')
        self.actor = dict(ADMIN)
        app.dependency_overrides[security.verificar_token] = lambda: self.actor
        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def test_actor_sin_permiso_no_puede_asignar(self):
        with patch.object(security, 'obtener_permisos_rol', return_value=set()), \
                patch.object(repo, 'asignar_personal') as insert:
            self.assertEqual(self.client.post('/api/proyectos/8/personal', json={'id_usuario': 14}).status_code, 403)
            insert.assert_not_called()

    def test_trabajador_no_puede_asignar_aunque_tenga_permiso(self):
        self.actor = {'nombre_rol': 'ELECTRICO', 'id_empresa': 1, 'nro_usuario': 14}
        with patch.object(security, 'obtener_permisos_rol', return_value={'Modificar_obras'}), \
                patch.object(repo, 'asignar_personal') as insert:
            self.assertEqual(self.client.post('/api/proyectos/8/personal', json={'id_usuario': 14}).status_code, 403)
            insert.assert_not_called()

    def test_no_confia_en_empresa_ni_rol_del_body_y_registra_bitacora(self):
        with patch.object(security, 'obtener_permisos_rol', return_value={'Modificar_obras'}), \
                patch.object(repo, 'obtener_obra_detalle_sp', return_value={'success': True, 'data': {'id_empresa': 1}}), \
                patch.object(repo, 'asignar_personal', return_value=True) as insert, \
                patch.object(svc.bitacora_repos, 'registrar_bitacora') as log:
            response = self.client.post('/api/proyectos/8/personal', json={
                'id_usuario': 14, 'id_empresa': 2, 'nombre_rol': 'JEFE DE OBRA'})
            self.assertEqual(response.status_code, 200)
            insert.assert_called_once_with(8, 14, 1)
            self.assertEqual(log.call_args.kwargs['accion'], 'ASIGNAR_PERSONAL')

    def test_ids_invalidos(self):
        with patch.object(repo, 'asignar_personal') as insert:
            for value in (None, True, '14', 0, -1, 14.5):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    svc.asignar_personal(8, value, ADMIN)
            insert.assert_not_called()

    def test_token_sin_empresa_rechazado(self):
        for candidatos in (False, True):
            with self.assertRaises(ValueError):
                svc.listar_personal(8, {'nombre_rol': 'ADMINISTRADOR_EMPRESA'}, candidatos)

    def test_obra_de_otro_tenant_rechazada(self):
        with patch.object(repo, 'obtener_obra_detalle_sp', return_value={'success': True, 'data': {'id_empresa': 2}}), \
                patch.object(repo, 'asignar_personal') as insert:
            with self.assertRaises(ValueError):
                svc.asignar_personal(8, 14, ADMIN)
            insert.assert_not_called()

    def test_duplicado_no_repite_bitacora(self):
        with patch.object(repo, 'obtener_obra_detalle_sp', return_value={'success': True, 'data': {'id_empresa': 1}}), \
                patch.object(repo, 'asignar_personal', return_value=False), \
                patch.object(svc.bitacora_repos, 'registrar_bitacora') as log:
            self.assertFalse(svc.asignar_personal(8, 14, ADMIN)['asignado'])
            log.assert_not_called()


@unittest.skipUnless(os.getenv('SI2_TEST_PERSONAL_DB') == '1', 'Integración PostgreSQL optativa')
class PersonalPostgresTests(unittest.TestCase):
    def setUp(self):
        import psycopg2
        self.conn = psycopg2.connect(host=Config.DB_HOST, port=Config.DB_PORT,
                                    dbname=Config.DB_NAME, user=Config.DB_USER,
                                    password=Config.DB_PASSWORD, connect_timeout=8)
        self.addCleanup(self.conn.close)
        self.addCleanup(self.conn.rollback)
        self.schema = 'test_personal_' + uuid4().hex
        self.cur = self.conn.cursor()
        self.cur.execute(f'CREATE SCHEMA {self.schema}')
        for table in ('t_obra', 't_usuario', 't_rol', 't_persona', 't_tipo_obra',
                      't_detalle_obra', 't_obra_usuario', 't_orden_trabajo',
                      't_orden_trabajo_usuario'):
            self.cur.execute(f'CREATE TABLE {self.schema}.{table} (LIKE obras.{table} INCLUDING ALL)')
        for table in ('t_rol', 't_persona', 't_tipo_obra', 't_obra', 't_usuario',
                      't_detalle_obra', 't_orden_trabajo', 't_orden_trabajo_usuario'):
            self.cur.execute(f'INSERT INTO {self.schema}.{table} SELECT * FROM obras.{table}')
        # IDs reales Jhon/Green Tower, con estado inicial controlado en la copia.
        self.cur.execute(f"UPDATE {self.schema}.t_usuario SET id_empresa=1, estado='ACTIVO', id_rol=5 WHERE id_usuario=14")
        self.cur.execute(f'UPDATE {self.schema}.t_detalle_obra SET id_supervisor=NULL WHERE id_obra=8')
        self.cur.execute(f"UPDATE {self.schema}.t_obra SET id_empresa=1 WHERE id_obra IN (8,9)")
        # Crear segunda obra solo si no existe en la copia.
        self.cur.execute(f"""INSERT INTO {self.schema}.t_obra (id_obra,id_empresa,nombre,codigo)
                            VALUES (9,1,'Segunda obra','TEST-PERSONAL-9') ON CONFLICT DO NOTHING""")
        for uid, empresa, estado, rol in ((90001, 2, 'ACTIVO', 5), (90002, 1, 'INACTIVO', 5),
                                         (90003, 1, 'ACTIVO', 4), (90004, 1, 'ACTIVO', 4),
                                         (90005, 1, 'ACTIVO', 2), (90006, 1, 'ACTIVO', 6),
                                         (90007, 1, 'ACTIVO', 7), (90008, 1, 'ACTIVO', 8)):
            self.cur.execute(f"""INSERT INTO {self.schema}.t_usuario
                (id_usuario,username,id_empresa,id_persona,id_rol,estado)
                VALUES (%s,%s,%s,(SELECT id_persona FROM {self.schema}.t_usuario WHERE id_usuario=14),%s,%s)
            """, (uid, f'personal-test-{uid}', empresa, rol, estado))
        # Procedimiento de asignación de jefes sin cambios.
        self.cur.execute("SELECT pg_get_functiondef('obras.sp_asignar_responsable_obra(integer,integer,integer)'::regprocedure)")
        self.cur.execute(self.cur.fetchone()[0].replace('obras.', self.schema + '.'))
        migration = (Path(__file__).parents[1] / 'database/migration_personal_obra.sql').read_text(encoding='utf-8')
        migration = migration.replace('BEGIN;\n', '', 1).removesuffix('COMMIT;\n')
        self.cur.execute(migration.replace('obras.', self.schema + '.'))
        conn, schema = self.conn, self.schema

        class Database:
            def create_connection(self):
                pass

            def close_connection(self):
                pass

            def execute_query(self, query, params=None, fetchall=False, fetchone=False, commit=False):
                # Conserva FOR UPDATE y SQL PostgreSQL; nunca confirma esta copia.
                with conn.cursor() as cur:
                    cur.execute(query.replace('obras.', schema + '.'), params)
                    if fetchall:
                        return cur.fetchall()
                    if fetchone:
                        return cur.fetchone()
                    return cur.rowcount

        for module in (repo, incidencia_repos):
            p = patch.object(module, 'PostgreSQL', Database)
            p.start()
            self.addCleanup(p.stop)
        p = patch.object(svc.bitacora_repos, 'registrar_bitacora')
        self.log = p.start()
        self.addCleanup(p.stop)

    def query(self, sql, params=()):
        self.cur.execute(sql.replace('obras.', self.schema + '.'), params)
        return self.cur.fetchall() if self.cur.description else []

    def supervisor(self):
        return self.query('SELECT id_supervisor FROM obras.t_detalle_obra WHERE id_obra=8')

    def test_jhon_listado_candidato_cu19_sin_supervisor_ni_ot(self):
        ot = [self.query(f'SELECT * FROM obras.{t} ORDER BY 1,2') for t in ('t_orden_trabajo','t_orden_trabajo_usuario')]
        supervisor = self.supervisor()
        self.assertIn(14, [u['id_usuario'] for u in svc.listar_personal(8, ADMIN, True)['data']])
        self.assertTrue(svc.asignar_personal(8, 14, ADMIN)['asignado'])
        self.assertIn(14, [u['id_usuario'] for u in svc.listar_personal(8, ADMIN)['data']])
        self.assertNotIn(14, [u['id_usuario'] for u in svc.listar_personal(8, ADMIN, True)['data']])
        self.assertIn(14, [u['nro_usuario'] for u in incidencia_repos.obtener_usuarios_asignables(1, 8)])
        self.assertFalse(svc.asignar_personal(8, 14, ADMIN)['asignado'])
        self.assertEqual(self.query('SELECT COUNT(*) FROM obras.t_obra_usuario WHERE id_obra=8 AND id_usuario=14'), [(1,)])
        self.assertEqual(self.supervisor(), supervisor)
        self.assertEqual(ot, [self.query(f'SELECT * FROM obras.{t} ORDER BY 1,2') for t in ('t_orden_trabajo','t_orden_trabajo_usuario')])
        self.assertEqual(repo.obtener_obra_detalle_sp(8, 1)['data']['responsables'], [])

    def test_rechaza_otro_tenant_inactivo_inexistente_y_rol_no_permitido(self):
        for actor in (ADMIN, GLOBAL):
            for uid in (90001, 90002, 90003, 90005, 999999):
                with self.subTest(actor=actor['nombre_rol'], uid=uid), self.assertRaises(ValueError):
                    svc.asignar_personal(8, uid, actor)
        self.assertEqual(self.query('SELECT COUNT(*) FROM obras.t_obra_usuario'), [(0,)])

    def test_global_y_multiples_obras(self):
        self.assertTrue(svc.asignar_personal(8, 14, GLOBAL)['asignado'])
        self.assertTrue(svc.asignar_personal(9, 14, ADMIN)['asignado'])
        self.assertEqual(self.query('SELECT id_obra FROM obras.t_obra_usuario WHERE id_usuario=14 ORDER BY 1'), [(8,), (9,)])

    def test_cuatro_roles_reales_y_candidatos_elegibles(self):
        candidatos = svc.listar_personal(8, ADMIN, True)['data']
        ids = {u['id_usuario'] for u in candidatos}
        self.assertTrue({14,90006,90007,90008}.issubset(ids))
        self.assertTrue({90001,90002,90003,90005}.isdisjoint(ids))
        for uid in (14,90006,90007,90008):
            self.assertTrue(svc.asignar_personal(8, uid, ADMIN)['asignado'])
        self.assertEqual({u['id_usuario'] for u in svc.listar_personal(8, ADMIN)['data']}, {14,90006,90007,90008})
        self.assertEqual(self.supervisor(), [(None,)])

    def test_jefatura_y_retiro_nunca_eligen_trabajador(self):
        svc.asignar_personal(8, 14, ADMIN)
        self.assertFalse(repo.asignar_responsable_sp(8, 14, 1)['success'])
        for uid in (90003, 90004):
            self.assertTrue(repo.asignar_responsable_sp(8, uid, 1)['success'])
        self.assertEqual(self.supervisor(), [(90003,)])
        self.assertEqual({u['id_usuario'] for u in repo.obtener_obra_detalle_sp(8, 1)['data']['responsables']}, {90003,90004})
        self.assertTrue(repo.retirar_responsable_sp(8, 90003, 1)['success'])
        self.assertEqual(self.supervisor(), [(90004,)])
        self.assertTrue(repo.retirar_responsable_sp(8, 90004, 1)['success'])
        self.assertEqual(self.supervisor(), [(None,)])
        self.assertEqual(self.query('SELECT id_usuario FROM obras.t_obra_usuario WHERE id_obra=8'), [(14,)])

    def test_reemplazo_supervisor_excluye_jefes_inactivos_y_otro_tenant(self):
        svc.asignar_personal(8, 14, ADMIN)
        for uid in (90003,90004):
            self.assertTrue(repo.asignar_responsable_sp(8, uid, 1)['success'])
        self.query("UPDATE obras.t_usuario SET estado='INACTIVO' WHERE id_usuario=90004")
        self.assertTrue(repo.retirar_responsable_sp(8, 90003, 1)['success'])
        self.assertEqual(self.supervisor(), [(None,)])
        self.query("UPDATE obras.t_usuario SET estado='ACTIVO',id_empresa=2 WHERE id_usuario=90004")
        self.query('UPDATE obras.t_detalle_obra SET id_supervisor=90004 WHERE id_obra=8')
        self.assertTrue(repo.retirar_responsable_sp(8, 90004, 1)['success'])
        self.assertEqual(self.supervisor(), [(None,)])


if __name__ == '__main__':
    unittest.main()
