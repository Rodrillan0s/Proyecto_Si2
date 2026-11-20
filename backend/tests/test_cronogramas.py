"""CU39. Unitarias sin red; integración solo en el clúster local cu39_test:55439.

CU39_TEST_DSN=host=127.0.0.1 port=55439 dbname=cu39_test user=cu39_test
Nunca habilitar con la base configurada de negocio. El guard valida destino.
"""
from contextlib import contextmanager
from datetime import date
from pathlib import Path
import copy
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch, MagicMock
import psycopg2
from psycopg2.extensions import parse_dsn
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.schemas.cronograma_schema import Actividad, CronogramaCreate, CronogramaUpdate, PlanificacionUpdate
from app.services import cronograma_services as svc
from app.repos import cronograma_repos as repo
from app.routes import cronograma_routes
from app.utils import security
from app.services.planes_catalog import modulo_ruta

PERMISOS={'Visualizar_cronograma','Registrar_cronograma','Modificar_cronograma','Planificar_cronograma'}
JEFE={'nombre_rol':'JEFE DE OBRA','id_empresa':1,'nro_usuario':2}
SUP={'nombre_rol':'SUPERVISOR_OBRA','id_empresa':1,'nro_usuario':3}
ADMIN={'nombre_rol':'ADMINISTRADOR_EMPRESA','id_empresa':1,'nro_usuario':4}
GLOBAL={'nombre_rol':'ADMINISTRADOR','nro_usuario':1}


def actividad(key='a',**changes):
    return dict(clave=key,nombre=key,descripcion='',tipo='ACTIVIDAD',fecha_inicio='2026-01-01',
        fecha_fin='2026-01-05',inicio_real=None,fin_real=None,avance=0,dependencias=[],**changes)


def plan(items=None,**changes):
    result=dict(nombre='Plan base',descripcion='',fecha_inicio='2026-01-01',fecha_fin='2026-12-31',
                actividades=items if items is not None else [actividad()])
    result.update(changes)
    return result


class PlanTests(unittest.TestCase):
    def test_schema_rechaza_invariantes(self):
        cases=[dict(nombre=' '),dict(fecha_fin='2025-01-01'),dict(id_empresa=2)]
        for change in cases:
            with self.subTest(change=change),self.assertRaises(ValidationError): CronogramaCreate(**plan(**change))
        for change in [dict(avance=100),dict(avance=1),dict(avance=True),dict(inicio_real='2026-01-05',fin_real='2026-01-04'),
                       dict(tipo='HITO'),dict(dependencias=['x','x'])]:
            a=actividad();a.update(change)
            with self.subTest(change=change),self.assertRaises(ValidationError): Actividad(**a)

    def test_ciclos_autorreferencia_y_ajenas(self):
        for items in [[dict(actividad(),dependencias=['a'])],[dict(actividad(),dependencias=['otra'])],
                      [dict(actividad(),dependencias=['b']),dict(actividad('b'),dependencias=['a'])],
                      [actividad(),actividad()]]:
            with self.subTest(items=items),self.assertRaises(svc.CronogramaError): svc.validar_plan(CronogramaCreate(**plan(items)))

    def test_dependencia_incoherente(self):
        items=[actividad(),dict(actividad('b'),dependencias=['a'])]
        with self.assertRaises(svc.CronogramaError): svc.validar_plan(CronogramaCreate(**plan(items)))

    def test_dependencia_real_requiere_predecesora_completada(self):
        items=[actividad(),dict(actividad('b'),fecha_inicio='2026-01-06',fecha_fin='2026-01-10',
            inicio_real='2026-01-06',dependencias=['a'])]
        with self.assertRaises(svc.CronogramaError): svc.validar_plan(CronogramaCreate(**plan(items)))

    def test_hito_y_dag_validos(self):
        items=[dict(actividad(),inicio_real='2026-01-01',fin_real='2026-01-05',avance=100),
            dict(actividad('b'),tipo='HITO',fecha_inicio='2026-01-05',fecha_fin='2026-01-05',dependencias=['a'])]
        svc.validar_plan(CronogramaCreate(**plan(items)))

    def test_limites_y_fechas_futuras(self):
        for change in [dict(fecha_inicio='2025-12-31'),dict(fecha_fin='2027-01-01'),dict(inicio_real='2099-01-01')]:
            a=actividad();a.update(change)
            with self.subTest(change=change),self.assertRaises(svc.CronogramaError): svc.validar_plan(CronogramaCreate(**plan([a])))

    def test_retraso_historico_y_pendiente(self):
        datos=CronogramaCreate(**plan([dict(actividad(),inicio_real='2026-01-01',fin_real='2026-01-08',avance=100),actividad('b')])).model_dump()
        r=svc.presentar(datos,corte=date(2026,1,10))
        self.assertEqual([a['dias_retraso'] for a in r['actividades']],[3,5])
        self.assertEqual(r['resumen']['completadas'],1)
        self.assertTrue(r['actividades'][1]['inicio_retrasado'])
        old=svc.presentar(datos,corte=date(2026,1,4))
        self.assertEqual(old['actividades'][0]['estado'],'EN_CURSO')
        self.assertEqual(old['actividades'][0]['dias_retraso'],0)

    def test_filtro_solapamiento_no_borra_agregado(self):
        data=CronogramaCreate(**plan()).model_dump()
        self.assertEqual(len(svc.presentar(data,desde=date(2026,1,5))['programadas']),1)
        r=svc.presentar(data,desde=date(2026,2,1))
        self.assertEqual(r['programadas'],[]);self.assertEqual(len(r['actividades']),1)
        with self.assertRaises(svc.CronogramaError): svc.presentar(data,date(2026,2,1),date(2026,1,1))

    def test_barrera_suscripcion_incluye_obras(self):
        self.assertEqual(modulo_ruta('/api/obras/10/cronogramas/1/planificacion'),'obras')

    def test_transaccion_confirma_y_revierte(self):
        db=MagicMock()
        with patch.object(repo,'PostgreSQL',return_value=db):
            with repo.sesion(True): pass
            db.conn.commit.assert_called_once();db.close_connection.assert_called_once_with()
            db.reset_mock()
            with self.assertRaises(RuntimeError),repo.sesion(True): raise RuntimeError('fallo')
            db.conn.commit.assert_not_called();db.close_connection.assert_called_once_with()

    def test_autorizacion_contexto_y_rol(self):
        with patch.object(security,'obtener_permisos_rol',return_value=PERMISOS),patch.object(repo,'obra',return_value={'id_empresa':1}) as obra:
            for token in ({},dict(JEFE,id_empresa=None),dict(JEFE,nombre_rol='CLIENTE')):
                with self.subTest(token=token),self.assertRaises(svc.CronogramaError): svc.autorizar(None,10,token)
            svc.autorizar(None,10,ADMIN); self.assertEqual(obra.call_args.args[2],1)
            svc.autorizar(None,10,GLOBAL); self.assertIsNone(obra.call_args.args[2])
            with self.assertRaises(svc.CronogramaError): svc.autorizar(None,10,SUP,'crear')
            svc.autorizar(None,10,SUP,'planificacion')

    def test_sin_permiso_no_consulta_recurso(self):
        with patch.object(security,'obtener_permisos_rol',return_value=set()),patch.object(repo,'obra') as obra:
            with self.assertRaises(svc.CronogramaError): svc.autorizar(None,10,JEFE)
            obra.assert_not_called()

    def test_ruta_retrasos_y_validacion_http(self):
        app=FastAPI();app.include_router(cronograma_routes.router)
        app.dependency_overrides[security.verificar_token]=lambda:JEFE
        with TestClient(app) as client,patch.object(svc,'consultar_retrasos',return_value={'data':[]}) as retrasos:
            self.assertEqual(client.get('/api/obras/10/cronogramas/retrasos').status_code,200)
            retrasos.assert_called_once()
            self.assertEqual(client.post('/api/obras/10/cronogramas/',json=plan(nombre=' ')).status_code,422)
            self.assertEqual(client.delete('/api/obras/10/cronogramas/1').status_code,422)


@unittest.skipUnless(os.getenv('CU39_TEST_DSN'),'Requiere clúster local CU39 explícito')
class PersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsn=os.environ['CU39_TEST_DSN']
        options=parse_dsn(cls.dsn)
        if options.get('host')!='127.0.0.1' or options.get('port')!='55439' or options.get('dbname')!='cu39_test':
            raise RuntimeError('Destino rechazado: estas pruebas solo escriben en 127.0.0.1:55439/cu39_test')
        cls.conn=psycopg2.connect(cls.dsn);cls.conn.autocommit=True
        with cls.conn.cursor() as c:
            c.execute('''CREATE SCHEMA IF NOT EXISTS obras;
                CREATE TABLE IF NOT EXISTS obras.t_empresa(id_empresa integer PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS obras.t_obra(id_obra integer PRIMARY KEY,id_empresa integer NOT NULL REFERENCES obras.t_empresa,nombre text);
                CREATE TABLE IF NOT EXISTS obras.t_usuario(id_usuario integer PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS obras.t_rol(id_rol serial PRIMARY KEY,nombre_rol varchar(80));
                CREATE TABLE IF NOT EXISTS obras.t_modulo(id_modulo serial PRIMARY KEY,nombre_modulo varchar(50));
                CREATE TABLE IF NOT EXISTS obras.t_permiso(id_permiso serial PRIMARY KEY,nombre_permiso varchar(80),id_modulo integer REFERENCES obras.t_modulo);
                CREATE TABLE IF NOT EXISTS obras.t_rol_permiso(id_rol integer REFERENCES obras.t_rol,id_permiso integer REFERENCES obras.t_permiso,PRIMARY KEY(id_rol,id_permiso));
                CREATE TABLE IF NOT EXISTS obras.t_bitacora(id_bitacora serial PRIMARY KEY,id_usuario integer REFERENCES obras.t_usuario,modulo varchar(50),accion varchar(50),descripcion varchar(256),ip varchar(20),estado varchar(30));
                INSERT INTO obras.t_empresa VALUES(1),(2) ON CONFLICT DO NOTHING;
                INSERT INTO obras.t_obra VALUES(10,1,'Obra A'),(20,2,'Obra B') ON CONFLICT DO NOTHING;
                INSERT INTO obras.t_usuario VALUES(1),(2),(3),(4) ON CONFLICT DO NOTHING;
                INSERT INTO obras.t_rol(nombre_rol) SELECT n FROM unnest(ARRAY['ADMINISTRADOR','ADMINISTRADOR_EMPRESA','JEFE DE OBRA','CLIENTE']) n WHERE NOT EXISTS(SELECT 1 FROM obras.t_rol WHERE nombre_rol=n);
                INSERT INTO obras.t_modulo(nombre_modulo) SELECT 'Modulo_obras' WHERE NOT EXISTS(SELECT 1 FROM obras.t_modulo WHERE nombre_modulo='Modulo_obras');
                INSERT INTO obras.t_permiso(nombre_permiso,id_modulo) SELECT 'Visualizar_obras',id_modulo FROM obras.t_modulo WHERE nombre_modulo='Modulo_obras' AND NOT EXISTS(SELECT 1 FROM obras.t_permiso WHERE nombre_permiso='Visualizar_obras');''')
            migration=(Path(__file__).resolve().parents[1]/'database/20261025_cu39_cronogramas.sql').read_text(encoding='utf-8')
            c.execute('BEGIN');c.execute(migration);c.execute('COMMIT')
            c.execute('BEGIN');c.execute(migration);c.execute('COMMIT')
        cls.addClassCleanup(cls.conn.close)

    def setUp(self):
        with self.conn.cursor() as c: c.execute('TRUNCATE obras.t_cronograma,obras.t_bitacora RESTART IDENTITY CASCADE')
        dsn=self.dsn
        class LocalDB(repo.PostgreSQL):
            def create_connection(self):
                self.conn=psycopg2.connect(dsn);self.cur=self.conn.cursor();self._from_pool=False
        self.addCleanup(patch.stopall)
        patch.object(repo,'PostgreSQL',LocalDB).start()
        def permisos(rol):
            with self.conn.cursor() as c:
                c.execute('''SELECT p.nombre_permiso FROM obras.t_rol r JOIN obras.t_rol_permiso rp USING(id_rol)
                    JOIN obras.t_permiso p USING(id_permiso) WHERE r.nombre_rol=%s''',(rol,))
                return {r[0] for r in c.fetchall()}
        patch.object(security,'obtener_permisos_rol',side_effect=permisos).start()

    def crear(self): return svc.crear_cronograma(10,CronogramaCreate(**plan()),JEFE)['data']

    def test_crear_actualizar_leer_eliminar_persisten_y_auditan(self):
        c=self.crear(); cid=c['id_cronograma']
        payload=plan(nombre='Revisado',version=c['version'])
        result=svc.actualizar_cronograma(10,cid,CronogramaUpdate(**payload),JEFE)['data']
        self.assertEqual(result['version'],2)
        self.assertEqual(svc.obtener_cronograma(10,cid,JEFE)['data']['nombre'],'Revisado')
        svc.eliminar_cronograma(10,cid,2,JEFE)
        self.assertEqual(svc.listar_cronogramas(10,JEFE)['data'],[])
        with self.conn.cursor() as cur:
            cur.execute('SELECT count(*) FROM obras.t_bitacora');self.assertEqual(cur.fetchone()[0],3)

    def test_aislamiento_todas_las_operaciones_y_contexto(self):
        cid=self.crear()['id_cronograma']
        for token in [dict(JEFE,id_empresa=2),dict(ADMIN,id_empresa=2)]:
            actions=[lambda:svc.listar_cronogramas(10,token),lambda:svc.obtener_cronograma(10,cid,token),
                lambda:svc.crear_cronograma(10,CronogramaCreate(**plan()),token),
                lambda:svc.actualizar_cronograma(10,cid,CronogramaUpdate(**plan(version=1)),token),
                lambda:svc.eliminar_cronograma(10,cid,1,token),lambda:svc.consultar_retrasos(10,token)]
            for action in actions:
                with self.subTest(token=token),self.assertRaises(svc.CronogramaError) as exc: action()
                self.assertEqual(exc.exception.status_code,404)
        self.assertEqual(len(svc.listar_cronogramas(10,GLOBAL)['data']),1)
        with self.assertRaises(svc.CronogramaError): svc.obtener_cronograma(20,cid,GLOBAL)

    def test_conflicto_de_version_no_sobrescribe(self):
        cid=self.crear()['id_cronograma'];payload=CronogramaUpdate(**plan(version=1))
        svc.actualizar_cronograma(10,cid,payload,JEFE)
        with self.assertRaises(svc.CronogramaError) as exc: svc.actualizar_cronograma(10,cid,payload,JEFE)
        self.assertEqual(exc.exception.status_code,409)
        with self.assertRaises(svc.CronogramaError): svc.eliminar_cronograma(10,cid,1,JEFE)
        self.assertEqual(svc.obtener_cronograma(10,cid,JEFE)['data']['version'],2)

    def test_supervisor_planifica_pero_no_modifica_cabecera(self):
        cid=self.crear()['id_cronograma']
        items=[actividad(),dict(actividad('h'),tipo='HITO',fecha_inicio='2026-01-05',fecha_fin='2026-01-05',dependencias=['a'])]
        result=svc.actualizar_cronograma(10,cid,PlanificacionUpdate(version=1,actividades=items),SUP,planificacion=True)['data']
        self.assertEqual(result['actividades'][1]['dependencias'],['a'])
        for action in [lambda:svc.crear_cronograma(10,CronogramaCreate(**plan()),SUP),
                       lambda:svc.actualizar_cronograma(10,cid,CronogramaUpdate(**plan(version=2)),SUP),lambda:svc.eliminar_cronograma(10,cid,2,SUP)]:
            with self.assertRaises(svc.CronogramaError): action()

    def test_fallo_auditoria_revierte_datos(self):
        with patch.object(repo,'auditar',side_effect=RuntimeError('fallo auditoria')),self.assertRaises(RuntimeError): self.crear()
        self.assertEqual(svc.listar_cronogramas(10,JEFE)['data'],[])

    def test_fallo_actividad_revierte_actualizacion_y_version(self):
        cid=self.crear()['id_cronograma']
        with patch.object(repo,'actividades',side_effect=RuntimeError('fallo')),self.assertRaises(RuntimeError):
            svc.actualizar_cronograma(10,cid,CronogramaUpdate(**plan(version=1,nombre='No guardar')),JEFE)
        result=svc.obtener_cronograma(10,cid,JEFE)['data']
        self.assertEqual(result['version'],1);self.assertEqual(result['nombre'],'Plan base')

    def test_ruta_real_y_retrasos(self):
        self.crear();app=FastAPI();app.include_router(cronograma_routes.router)
        app.dependency_overrides[security.verificar_token]=lambda:JEFE
        with TestClient(app) as client:
            r=client.get('/api/obras/10/cronogramas/retrasos?corte=2026-01-10')
            self.assertEqual(r.status_code,200);self.assertEqual(r.json()['data'][0]['dias_retraso'],5)

    def test_dos_escrituras_simultaneas_solo_una_gana(self):
        cid=self.crear()['id_cronograma']
        ready=Barrier(2)
        def write(nombre):
            ready.wait(timeout=5)
            try:
                svc.actualizar_cronograma(10,cid,CronogramaUpdate(**plan(version=1,nombre=nombre)),GLOBAL)
                return 200
            except svc.CronogramaError as exc:
                return exc.status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(write,['Edición A','Edición B']))
        self.assertEqual(sorted(results),[200,409])
        self.assertEqual(svc.obtener_cronograma(10,cid,JEFE)['data']['version'],2)


if __name__=='__main__': unittest.main()
