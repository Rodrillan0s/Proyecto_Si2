"""Ejecuta SQL del repositorio con datos aislados; no modifica la BD real."""
import sqlite3
import unittest
from unittest.mock import patch

from app.repos import incidencia_repos as repo
from app.services import incidencia_services as svc


class CandidatosIncidenciaTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        self.conn.execute("ATTACH DATABASE ':memory:' AS obras")
        self.conn.create_function('GREATEST', 2, max)
        self.conn.executescript("""
            CREATE TABLE obras.t_usuario(id_usuario INTEGER, username TEXT,
                id_empresa INTEGER, id_persona INTEGER, id_rol INTEGER, estado TEXT);
            CREATE TABLE obras.t_rol(id_rol INTEGER, nombre_rol TEXT);
            CREATE TABLE obras.t_persona(id_persona INTEGER, nombre_completo TEXT);
            CREATE TABLE obras.t_obra(id_obra INTEGER, id_empresa INTEGER);
            CREATE TABLE obras.t_detalle_obra(id_obra INTEGER, id_supervisor INTEGER);
            CREATE TABLE obras.t_obra_usuario(id_obra INTEGER, id_usuario INTEGER);
            CREATE TABLE obras.t_incidencia(id_incidencia INTEGER, id_obra INTEGER,
                id_responsable INTEGER, estado TEXT, fecha_inicio_atencion TEXT,
                fecha_fin_atencion TEXT);
            CREATE TABLE obras.t_orden_trabajo(orden_nro INTEGER, id_obra INTEGER,
                estado TEXT, cuadrilla INTEGER);
            CREATE TABLE obras.t_orden_trabajo_usuario(id_orden_trabajo INTEGER,
                id_usuario INTEGER);
            CREATE TABLE obras.t_incidencia_orden_trabajo(id_incidencia INTEGER,
                orden_nro INTEGER);
            INSERT INTO obras.t_rol VALUES(1,'ELECTRICO'),(2,'JEFE DE OBRA');
            INSERT INTO obras.t_usuario VALUES
                (14,'Jhon',1,14,1,'ACTIVO'),(15,'Otro tenant',2,15,1,'ACTIVO'),
                (16,'Otra obra',1,16,1,'ACTIVO'),(17,'Inactivo',1,17,1,'INACTIVO'),
                (18,'Carlos',1,18,2,'ACTIVO');
            INSERT INTO obras.t_persona VALUES(14,'Jhon');
            INSERT INTO obras.t_obra VALUES(8,1),(9,1),(10,2);
            INSERT INTO obras.t_obra_usuario VALUES
                (8,14),(9,14),(8,15),(9,16),(8,17),(8,18),(10,14);
            INSERT INTO obras.t_incidencia VALUES(1,8,NULL,'ABIERTA',NULL,NULL);
            INSERT INTO obras.t_orden_trabajo VALUES(7,8,'EN_PROCESO',3);
            INSERT INTO obras.t_orden_trabajo_usuario VALUES(7,18);
            INSERT INTO obras.t_incidencia_orden_trabajo VALUES(1,7);
        """)
        conn = self.conn

        class Database:
            def __init__(self):
                self.conn = conn

            def create_connection(self):
                pass

            def close_connection(self):
                pass

            def execute_query(self, query, params=None, fetchall=False, fetchone=False):
                query = query.replace('%s::INTEGER', '%s').replace('%s', '?')
                query = query.replace('FOR UPDATE OF i', '')
                query = query.replace('UPDATE obras.t_incidencia i', 'UPDATE obras.t_incidencia AS i')
                query = query.replace('RETURNING i.id_incidencia', 'RETURNING id_incidencia')
                cursor = conn.execute(query, params or ())
                return cursor.fetchall() if fetchall else cursor.fetchone()

        self.db_patch = patch.object(repo, 'PostgreSQL', Database)
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.conn.close)

    def test_candidatos_activos_de_la_obra_sin_permiso_administrativo(self):
        candidatos = repo.obtener_usuarios_asignables(1, 8)
        self.assertEqual({u['nro_usuario'] for u in candidatos}, {14, 18})
        jhon = next(u for u in candidatos if u['nro_usuario'] == 14)
        self.assertEqual((jhon['nombre_completo'], jhon['nombre_rol']), ('Jhon', 'ELECTRICO'))
        self.assertEqual({u['nro_usuario'] for u in repo.obtener_usuarios_asignables(1, 9)}, {14,16,18})
        self.assertEqual(repo.obtener_usuarios_asignables(2, 10), [])
        self.assertEqual(repo.obtener_usuarios_asignables(None, 8), [])

    def test_patch_rechaza_usuario_de_otra_obra_o_inactivo(self):
        token = {'id_empresa': 1, 'nro_usuario': 18, 'nombre_rol': 'JEFE DE OBRA'}
        with patch.object(repo, 'obtener_estado_actual', return_value=('ABIERTA', None)), \
                patch.object(repo, 'obtener_detalle', return_value={'id_obra': 8}), \
                patch.object(repo, 'asignar_responsable') as asignar:
            for usuario in (15, 16, 17):
                with self.subTest(usuario=usuario), self.assertRaises(svc.IncidenciaError):
                    svc.asignar_responsable(1, {'id_responsable': usuario, 'id_empresa': 2}, token)
            asignar.assert_not_called()

    def test_roles_de_campo_y_jefatura_sin_clientes_ni_administradores(self):
        self.conn.executescript("""
            INSERT INTO obras.t_rol VALUES
                (3,'PLOMERO'),(4,'MAESTROALBAÑIL'),(5,'ALBAÑIL'),
                (6,'CLIENTE'),(7,'ADMINISTRADOR'),(8,'ADMINISTRADOR_EMPRESA');
            INSERT INTO obras.t_usuario VALUES
                (20,'Pedro',1,NULL,3,'ACTIVO'),(21,'Maestro',1,NULL,4,'ACTIVO'),
                (22,'Albañil',1,NULL,5,'ACTIVO'),(23,'Cliente',1,NULL,6,'ACTIVO'),
                (24,'Admin',1,NULL,7,'ACTIVO'),(25,'Admin empresa',1,NULL,8,'ACTIVO');
            INSERT INTO obras.t_obra_usuario VALUES (8,20),(8,21),(8,22),(8,23),(8,24),(8,25);
        """)
        self.assertEqual({u['nro_usuario'] for u in repo.obtener_usuarios_asignables(1,8)}, {14,18,20,21,22})
        with patch.object(repo, 'obtener_estado_actual', return_value=('ABIERTA', None)), \
                patch.object(repo, 'obtener_detalle', return_value={'id_obra': 8}), \
                patch.object(repo, 'asignar_responsable') as asignar:
            for uid in (23,24,25):
                with self.subTest(uid=uid), self.assertRaises(svc.IncidenciaError):
                    svc.asignar_responsable(1, {'id_responsable': uid}, {'nombre_rol':'ADMINISTRADOR'})
            asignar.assert_not_called()

    def test_sin_vinculo_no_aparece_y_no_puede_asignarse(self):
        self.conn.execute('DELETE FROM obras.t_obra_usuario WHERE id_obra=8 AND id_usuario=14')
        self.assertNotIn(14, {u['nro_usuario'] for u in repo.obtener_usuarios_asignables(1,8)})
        with patch.object(repo, 'obtener_estado_actual', return_value=('ABIERTA', None)), \
                patch.object(repo, 'obtener_detalle', return_value={'id_obra': 8}), \
                patch.object(repo, 'asignar_responsable') as asignar:
            with self.assertRaises(svc.IncidenciaError):
                svc.asignar_responsable(1, {'id_responsable':14}, {'nombre_rol':'ADMINISTRADOR'})
            asignar.assert_not_called()

    def test_jefe_y_supervisor_por_empresa_sin_vinculo_obra(self):
        self.conn.executescript("""
            INSERT INTO obras.t_rol VALUES (9,'SUPERVISOR'),(10,'SUPERVISOR_OBRA');
            INSERT INTO obras.t_usuario VALUES
                (30,'Supervisor',1,NULL,9,'ACTIVO'),
                (31,'Supervisor otra empresa',2,NULL,9,'ACTIVO'),
                (32,'Supervisor inactivo',1,NULL,9,'INACTIVO'),
                (33,'Supervisor otro nombre',1,NULL,10,'ACTIVO');
            DELETE FROM obras.t_obra_usuario WHERE id_usuario=18;
            DELETE FROM obras.t_obra_usuario WHERE id_usuario=14;
        """)
        self.assertEqual({u['nro_usuario'] for u in repo.obtener_usuarios_asignables(1,8)}, {18,30,33})

    def test_patch_asigna_jefe_y_supervisor_sin_vinculo(self):
        self.conn.executescript("""
            ALTER TABLE obras.t_incidencia ADD COLUMN id_usuario_registro INTEGER;
            UPDATE obras.t_incidencia SET id_usuario_registro=14 WHERE id_incidencia=1;
            DELETE FROM obras.t_obra_usuario WHERE id_usuario=18;
            INSERT INTO obras.t_rol VALUES (9,'SUPERVISOR');
            INSERT INTO obras.t_usuario VALUES (30,'Supervisor',1,NULL,9,'ACTIVO');
        """)
        tablas_ot = ('t_orden_trabajo','t_orden_trabajo_usuario','t_incidencia_orden_trabajo')
        antes = [self.conn.execute(f'SELECT * FROM obras.{t}').fetchall() for t in tablas_ot]
        with patch.object(repo, 'obtener_detalle', return_value={'id_obra':8}), \
                patch.object(repo, 'crear_seguimiento'), patch.object(svc, '_log'):
            for uid in (18,30):
                with self.subTest(uid=uid):
                    result = svc.asignar_responsable(1, {'id_responsable':uid}, {'nombre_rol':'ADMINISTRADOR','id_empresa':2})
                    self.assertEqual(result['estado'],'ASIGNADA')
                    self.assertEqual(self.conn.execute('SELECT id_usuario_registro,id_responsable,estado FROM obras.t_incidencia WHERE id_incidencia=1').fetchone(),(14,uid,'ASIGNADA'))
        self.assertEqual(antes,[self.conn.execute(f'SELECT * FROM obras.{t}').fetchall() for t in tablas_ot])

    def test_jefes_y_supervisores_de_otro_tenant_o_inactivos_rechazados(self):
        self.conn.executescript("""
            INSERT INTO obras.t_rol VALUES (9,'SUPERVISOR');
            INSERT INTO obras.t_usuario VALUES
                (30,'Jefe otra empresa',2,NULL,2,'ACTIVO'),
                (31,'Jefe inactivo',1,NULL,2,'INACTIVO'),
                (32,'Supervisor otra empresa',2,NULL,9,'ACTIVO'),
                (33,'Supervisor inactivo',1,NULL,9,'INACTIVO');
        """)
        self.assertTrue({30,31,32,33}.isdisjoint({u['nro_usuario'] for u in repo.obtener_usuarios_asignables(1,8)}))
        with patch.object(repo, 'obtener_detalle', return_value={'id_obra':8}), \
                patch.object(repo, 'asignar_responsable') as asignar:
            for uid in (30,31,32,33):
                with self.subTest(uid=uid), self.assertRaises(svc.IncidenciaError):
                    svc.asignar_responsable(1, {'id_responsable':uid}, {'nombre_rol':'ADMINISTRADOR'})
            asignar.assert_not_called()

    def test_endpoints_global_usan_empresa_real_y_no_modifican_ot(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.routes import incidencia_routes
        from app.utils.security import verificar_token
        app = FastAPI()
        app.include_router(incidencia_routes.router, prefix='/api/incidencias')
        app.dependency_overrides[verificar_token] = lambda: {'nombre_rol':'ADMINISTRADOR','nro_usuario':18,'id_empresa':2}
        tablas = ('t_orden_trabajo','t_orden_trabajo_usuario','t_incidencia_orden_trabajo')
        def ot():
            return [self.conn.execute(f'SELECT * FROM obras.{t}').fetchall() for t in tablas]
        antes = ot()
        with TestClient(app) as client, \
                patch.object(repo, 'obtener_detalle', return_value={'id_obra':8}), \
                patch.object(repo, 'obtener_estado_actual', return_value=('ABIERTA',None)), \
                patch.object(repo, 'crear_seguimiento'), patch.object(svc, '_log'):
            response = client.get('/api/incidencias/1/responsables?id_empresa=2')
            self.assertEqual(response.status_code,200)
            self.assertEqual({u['nro_usuario'] for u in response.json()['data']},{14,18})
            for uid in (15,16,17):
                with self.subTest(uid=uid):
                    self.assertEqual(client.patch('/api/incidencias/1/responsable',json={'id_responsable':uid,'id_empresa':2}).status_code,404)
            response = client.patch('/api/incidencias/1/responsable',json={'id_responsable':14,'id_empresa':2})
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['estado'],'ASIGNADA')
        self.assertEqual(self.conn.execute('SELECT id_responsable,estado FROM obras.t_incidencia WHERE id_incidencia=1').fetchone(),(14,'ASIGNADA'))
        self.assertEqual(ot(),antes)

    def test_julian_get_y_patch_jhon_comparten_vinculo_sin_modificar_ot005(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.routes import incidencia_routes
        from app.utils import security

        # Solo datos aislados: incidencia #9 de obra 8; OT-005 de Carlos.
        self.conn.executescript("""
            INSERT INTO obras.t_usuario VALUES (13,'JULIAN',1,NULL,2,'ACTIVO');
            UPDATE obras.t_incidencia SET id_incidencia=9;
            UPDATE obras.t_orden_trabajo SET orden_nro=5;
            UPDATE obras.t_orden_trabajo_usuario SET id_orden_trabajo=5;
            UPDATE obras.t_incidencia_orden_trabajo SET id_incidencia=9,orden_nro=5;
        """)
        app = FastAPI()
        app.include_router(incidencia_routes.router, prefix='/api/incidencias')
        app.dependency_overrides[security.verificar_token] = lambda: {
            'nombre_rol': 'JEFE DE OBRA', 'nro_usuario': 13, 'id_empresa': 1,
        }
        tablas = ('t_orden_trabajo', 't_orden_trabajo_usuario', 't_incidencia_orden_trabajo')
        def snapshot_ot():
            return [self.conn.execute(f'SELECT * FROM obras.{t}').fetchall() for t in tablas]
        antes = snapshot_ot()
        self.assertEqual(self.conn.execute(
            'SELECT id_usuario FROM obras.t_orden_trabajo_usuario WHERE id_orden_trabajo=5'
        ).fetchall(), [(18,)])
        with TestClient(app) as client, \
                patch.object(security, 'obtener_permisos_rol', return_value={'Asignar_incidencias'}), \
                patch.object(repo, 'obtener_detalle', return_value={'id_obra': 8}), \
                patch.object(repo, 'crear_seguimiento'), patch.object(svc, '_log'), \
                patch.object(repo, 'obtener_usuarios_asignables', wraps=repo.obtener_usuarios_asignables) as candidatos:
            for vinculado in (False, True):
                with self.subTest(vinculado=vinculado):
                    self.conn.execute('DELETE FROM obras.t_obra_usuario WHERE id_obra=8 AND id_usuario=14')
                    if vinculado:
                        self.conn.execute('INSERT INTO obras.t_obra_usuario VALUES(8,14)')
                    candidatos.reset_mock()
                    response = client.get('/api/incidencias/9/responsables')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(14 in {u['nro_usuario'] for u in response.json()['data']}, vinculado)
                    response = client.patch('/api/incidencias/9/responsable', json={'id_responsable': 14})
                    self.assertEqual(response.status_code, 200 if vinculado else 404)
                    self.assertEqual(candidatos.call_args_list, [unittest.mock.call(1, 8), unittest.mock.call(1, 8)])
                    self.assertEqual(self.conn.execute(
                        'SELECT id_responsable,estado FROM obras.t_incidencia WHERE id_incidencia=9'
                    ).fetchone(), (14, 'ASIGNADA') if vinculado else (None, 'ABIERTA'))
                    self.assertEqual(snapshot_ot(), antes)

    def test_asignar_electricista_y_atender_sin_alterar_ot(self):
        tablas_ot = ('t_orden_trabajo', 't_orden_trabajo_usuario', 't_incidencia_orden_trabajo')
        def snapshot():
            return [self.conn.execute(f'SELECT * FROM obras.{t}').fetchall() for t in tablas_ot]
        antes = snapshot()
        gestor = {'id_empresa': 1, 'nro_usuario': 18, 'nombre_rol': 'JEFE DE OBRA'}
        jhon = {'id_empresa': 1, 'nro_usuario': 14, 'nombre_rol': 'ELECTRICO'}
        def estado(*args):
            return self.conn.execute('SELECT estado,id_responsable FROM obras.t_incidencia WHERE id_incidencia=1').fetchone()
        with patch.object(repo, 'obtener_estado_actual', side_effect=estado), \
                patch.object(repo, 'obtener_detalle', return_value={'id_obra': 8}), \
                patch.object(repo, 'crear_seguimiento') as seguimiento, \
                patch.object(svc, '_log'):
            resultado = svc.asignar_responsable(1, {'id_responsable': 14}, gestor)
            self.assertEqual(resultado['estado'], 'ASIGNADA')
            for nuevo in ('EN_PROCESO', 'PENDIENTE_VALIDACION'):
                with self.assertRaises(svc.IncidenciaError) as error:
                    svc.cambiar_estado(1, {'estado': nuevo}, gestor)
                self.assertEqual(error.exception.status_code, 403)
                self.assertEqual(svc.cambiar_estado(1, {'estado': nuevo}, jhon)['estado_nuevo'], nuevo)
            with patch.object(svc, '_tiene_permiso', return_value=True):
                svc.cambiar_estado(1, {'estado': 'EN_PROCESO'}, gestor)
                svc.cambiar_estado(1, {'estado': 'PENDIENTE_VALIDACION'}, jhon)
                svc.cambiar_estado(1, {'estado': 'RESUELTA'}, gestor)
            self.assertEqual(seguimiento.call_count, 6)
        row = self.conn.execute('SELECT estado,fecha_inicio_atencion,fecha_fin_atencion FROM obras.t_incidencia').fetchone()
        self.assertEqual(row[0], 'RESUELTA')
        self.assertIsNotNone(row[1])
        self.assertGreaterEqual(row[2], row[1])
        self.assertEqual(snapshot(), antes)
