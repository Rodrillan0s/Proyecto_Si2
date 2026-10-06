"""Ejecuta las consultas reales de lectura sobre SQLite aislado.

SQLite adapta placeholders y bool de PostgreSQL; no conecta a datos reales.
La concurrencia comprueba visibilidad tras commits, no bloqueos de PostgreSQL.
"""
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock

import pytest

from app.repos import orden_Trabajo_repos as ot_repo, incidencia_repos as inc_repo
from app.services import incidencia_services as svc


@pytest.fixture
def datos(monkeypatch, tmp_path):
    archivo = str(tmp_path / 'obras.db')
    db = sqlite3.connect(':memory:', check_same_thread=False)
    db.execute('ATTACH DATABASE ? AS obras', (archivo,))
    db.executescript('''
        CREATE TABLE obras.t_empresa(id_empresa INTEGER PRIMARY KEY, nombre_empresa TEXT);
        CREATE TABLE obras.t_obra(id_obra INTEGER PRIMARY KEY, codigo TEXT, nombre TEXT, id_empresa INTEGER);
        CREATE TABLE obras.t_orden_trabajo(orden_nro INTEGER PRIMARY KEY, id_obra INTEGER,
            tipo_trab TEXT, cuadrilla INTEGER, estado TEXT, fecha_inicio TEXT, fecha_fin TEXT, observacion TEXT);
        CREATE TABLE obras.t_orden_trabajo_usuario(id_orden_trabajo INTEGER, id_usuario INTEGER);
        CREATE TABLE obras.t_incidencia(id_incidencia INTEGER PRIMARY KEY, id_obra INTEGER,
            estado TEXT, id_responsable INTEGER);
        CREATE TABLE obras.t_incidencia_orden_trabajo(id_incidencia INTEGER, orden_nro INTEGER,
            fecha_registro TEXT, id_usuario INTEGER, UNIQUE(id_incidencia, orden_nro));
        CREATE TABLE obras.t_usuario(id_usuario INTEGER, username TEXT, id_persona INTEGER);
        CREATE TABLE obras.t_persona(id_persona INTEGER, nombre_completo TEXT);
        INSERT INTO obras.t_empresa VALUES(1, 'Empresa A'),(2, 'Empresa B');
        INSERT INTO obras.t_obra VALUES(8,'GT','Green Tower',1),(9,'OTRA','Otra obra',1),(20,'B','Otra empresa',2);
        INSERT INTO obras.t_orden_trabajo VALUES
            (5,8,'Electricidad',1,'EN_PROCESO',NULL,NULL,NULL),
            (6,8,'Electricidad',1,'EN_PROCESO',NULL,NULL,NULL),
            (7,8,'Electricidad',1,'EN_PROCESO',NULL,NULL,NULL),
            (20,20,'Electricidad',1,'EN_PROCESO',NULL,NULL,NULL);
        INSERT INTO obras.t_orden_trabajo_usuario VALUES(5,13),(6,13),(7,13),(20,21);
        INSERT INTO obras.t_usuario VALUES(13,'CARLOS',NULL),(14,'JHON ELECTRICO',NULL),(12,'JULIAN',NULL);
        INSERT INTO obras.t_incidencia VALUES(9,8,'ABIERTA',NULL),(10,8,'EN_PROCESO',14),(11,8,'CERRADA',14);
    ''')

    class LecturaAislada:
        def create_connection(self):
            pass

        def close_connection(self):
            pass

        def execute_query(self, query, params=(), fetchone=False, fetchall=False, **kwargs):
            assert query.lstrip().startswith('SELECT'), 'Las lecturas no deben escribir OT'
            cursor = db.execute(query.replace('%s', '?').replace('FOR UPDATE OF i', ''), params)
            names = [col[0] for col in cursor.description]

            def fila(row):
                if row is None:
                    return None
                return tuple(bool(value) if name == 'afectada_por_incidencia' else value
                             for name, value in zip(names, row))

            return fila(cursor.fetchone()) if fetchone else [fila(row) for row in cursor.fetchall()]

    monkeypatch.setattr(ot_repo, 'PostgreSQL', LecturaAislada)
    monkeypatch.setattr(inc_repo, 'PostgreSQL', LecturaAislada)
    yield db, archivo
    db.close()


def vincular(db, incidencia=9, orden=5):
    db.execute('INSERT INTO obras.t_incidencia_orden_trabajo VALUES(?,?,NULL,12)', (incidencia, orden))
    db.commit()


def leer(orden=5, empresa=1):
    return ot_repo.obtener_orden_trabajo_fn(orden, 12, 'JEFE_DE_OBRA', empresa)


def afectada(orden=5):
    return leer(orden)['data']['afectada_por_incidencia']


@pytest.mark.parametrize('estado,esperado', [
    ('ABIERTA', True), ('ASIGNADA', True), ('EN_PROCESO', True),
    ('PENDIENTE_VALIDACION', True), ('RESUELTA', False), ('CERRADA', False),
])
def test_estados_en_lista_detalle_y_vinculos(datos, estado, esperado):
    db, _ = datos
    db.execute('UPDATE obras.t_incidencia SET estado=? WHERE id_incidencia=9', (estado,))
    vincular(db)
    assert afectada() is esperado
    lista = ot_repo.listar_ordenes_trabajo_fn(12, 'JEFE_DE_OBRA', id_empresa_token=1)['data']
    assert next(ot for ot in lista if ot['orden_nro'] == 5)['afectada_por_incidencia'] is esperado
    assert inc_repo.listar_ordenes_trabajo_incidencia(9)[0]['afectada_por_incidencia'] is esperado
    assert leer()['data']['estado'] == 'EN_PROCESO'


def test_multiples_y_ultima_resolucion(datos):
    db, _ = datos
    vincular(db, 9)
    vincular(db, 10)
    vincular(db, 11)
    db.execute("UPDATE obras.t_incidencia SET estado='RESUELTA' WHERE id_incidencia=9")
    assert afectada() is True
    # Incluso al consultar la incidencia ya resuelta, la OT sigue afectada por #10.
    assert inc_repo.listar_ordenes_trabajo_incidencia(9)[0]['afectada_por_incidencia'] is True
    db.execute("UPDATE obras.t_incidencia SET estado='RESUELTA' WHERE id_incidencia=10")
    assert afectada() is False
    db.execute("UPDATE obras.t_incidencia SET estado='CERRADA' WHERE id_incidencia=10")
    assert afectada() is False


def test_una_incidencia_tres_ot(datos):
    db, _ = datos
    for orden in (5, 6, 7):
        vincular(db, 9, orden)
    assert all(afectada(orden) for orden in (5, 6, 7))
    db.execute("UPDATE obras.t_incidencia SET estado='RESUELTA' WHERE id_incidencia=9")
    assert all(afectada(orden) is False for orden in (5, 6, 7))


@pytest.mark.parametrize('otra_activa', [True, False])
def test_desvincular(datos, otra_activa):
    db, _ = datos
    vincular(db, 9)
    vincular(db, 10)
    if not otra_activa:
        db.execute("UPDATE obras.t_incidencia SET estado='RESUELTA' WHERE id_incidencia=10")
    db.execute('DELETE FROM obras.t_incidencia_orden_trabajo WHERE id_incidencia=9 AND orden_nro=5')
    assert afectada() is otra_activa


@pytest.mark.parametrize('estado_ot', ['EN_PROCESO', 'FINALIZADO', 'CANCELADO'])
def test_green_tower_jhon_rechazo_aprobacion_y_responsables(datos, monkeypatch, estado_ot):
    db, _ = datos
    db.execute('UPDATE obras.t_orden_trabajo SET estado=? WHERE orden_nro=5', (estado_ot,))
    vincular(db)
    repo = Mock()
    repo.obtener_estado_actual.side_effect = lambda i, e: db.execute(
        'SELECT estado,id_responsable FROM obras.t_incidencia WHERE id_incidencia=?', (i,)).fetchone()

    def cambiar(i, empresa, previo, nuevo, responsable):
        return db.execute('UPDATE obras.t_incidencia SET estado=? WHERE id_incidencia=? AND estado=?',
                          (nuevo, i, previo)).rowcount == 1

    def asignar(i, empresa, responsable, estado):
        db.execute('UPDATE obras.t_incidencia SET id_responsable=?,estado=? WHERE id_incidencia=?',
                   (responsable, estado, i))
        return True

    repo.cambiar_estado.side_effect = cambiar
    repo.asignar_responsable.side_effect = asignar
    repo.obtener_empresa_incidencia.return_value = 1
    repo.obtener_detalle.return_value = {'id_obra':8}
    repo.usuario_pertenece_a_empresa.return_value = True
    repo.obtener_usuarios_asignables.return_value = [{'nro_usuario':14,'nombre_rol':'ELECTRICO'}]
    monkeypatch.setattr(svc, 'incidencia_repos', repo)
    monkeypatch.setattr(svc, 'bitacora_repos', Mock())
    monkeypatch.setattr(svc, '_tiene_permiso', lambda token, permiso: token['nro_usuario'] == 12)
    julian = {'nro_usuario':12,'id_empresa':1,'nombre_rol':'JEFE DE OBRA'}
    jhon = {'nro_usuario':14,'id_empresa':1,'nombre_rol':'ELECTRICO'}
    svc.asignar_responsable(9, {'id_responsable':14}, julian)
    assert afectada() is True
    assert db.execute('SELECT id_responsable FROM obras.t_incidencia WHERE id_incidencia=9').fetchone() == (14,)
    assert db.execute('SELECT id_usuario FROM obras.t_orden_trabajo_usuario WHERE id_orden_trabajo=5').fetchall() == [(13,)]
    for estado, actor, esperado in [
        ('EN_PROCESO', jhon, True), ('PENDIENTE_VALIDACION', jhon, True),
        ('EN_PROCESO', julian, True), ('PENDIENTE_VALIDACION', jhon, True),
        ('RESUELTA', julian, False), ('CERRADA', julian, False),
    ]:
        svc.cambiar_estado(9, {'estado':estado}, actor)
        assert afectada() is esperado
        assert leer()['data']['estado'] == estado_ot
        assert db.execute('SELECT id_usuario FROM obras.t_orden_trabajo_usuario WHERE id_orden_trabajo=5').fetchall() == [(13,)]


def test_otra_empresa_no_lee_afectacion(datos):
    db, _ = datos
    vincular(db)
    assert leer(5, empresa=2)['success'] is False
    lista = ot_repo.listar_ordenes_trabajo_fn(21, 'JEFE_DE_OBRA', id_empresa_token=2)['data']
    assert [ot['orden_nro'] for ot in lista] == [20]
    assert lista[0]['afectada_por_incidencia'] is False
    assert ot_repo.obtener_orden_trabajo_fn(5, 21, 'ELECTRICO', 2)['success'] is False


def test_vinculo_inconsistente_otra_obra_no_afecta(datos):
    db, _ = datos
    # Simula datos inválidos previos; el trigger real además impide crearlos.
    db.execute('UPDATE obras.t_incidencia SET id_obra=20 WHERE id_incidencia=9')
    vincular(db)
    assert afectada() is False


@pytest.mark.parametrize('operacion', ['leer', 'vincular'])
def test_incidencia_otra_empresa_no_consulta_ni_vincula(datos, monkeypatch, operacion):
    repo = Mock()
    repo.obtener_detalle.return_value = None
    monkeypatch.setattr(svc, 'incidencia_repos', repo)
    token = {'id_empresa':2,'nro_usuario':21,'nombre_rol':'JEFE DE OBRA'}
    with pytest.raises(svc.IncidenciaError) as error:
        if operacion == 'leer':
            svc.listar_ordenes_trabajo(9, token)
        else:
            svc.actualizar_ordenes_trabajo(9, {'ordenes':[5], 'id_empresa':1}, token)
    assert error.value.status_code == 404
    repo.obtener_detalle.assert_called_once_with(9, 2)
    repo.listar_ordenes_trabajo_incidencia.assert_not_called()
    repo.reemplazar_ordenes_trabajo.assert_not_called()


def test_ot_otra_obra_rechazada_por_servicio(datos, monkeypatch):
    repo = Mock()
    repo.obtener_detalle.return_value = {'id_obra':8,'estado':'EN_PROCESO'}
    repo.obtener_empresa_incidencia.return_value = 1
    repo.filtrar_ordenes_de_obra.return_value = set()
    monkeypatch.setattr(svc, 'incidencia_repos', repo)
    with pytest.raises(svc.IncidenciaError):
        svc.actualizar_ordenes_trabajo(9, {'ordenes':[20], 'id_empresa':2},
                                     {'id_empresa':1,'nro_usuario':12,'nombre_rol':'JEFE DE OBRA'})
    repo.filtrar_ordenes_de_obra.assert_called_once_with([20], 8, 1)
    repo.reemplazar_ordenes_trabajo.assert_not_called()


def test_contrato_get_api_ot_e_incidencias(datos, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.routes import orden_Trabajo_routes, incidencia_routes
    from app.utils.security import verificar_token

    db, _ = datos
    vincular(db)
    token = {'id_empresa':1,'nro_usuario':12,'nombre_rol':'JEFE_DE_OBRA'}
    monkeypatch.setattr('app.utils.security.obtener_permisos_rol',
                        lambda rol: {'Visualizar_ordenes_trabajo','Visualizar_incidencias'})
    monkeypatch.setattr(inc_repo, 'obtener_detalle',
                        lambda i, empresa: {'id_obra':8} if empresa == 1 else None)
    app = FastAPI()
    app.include_router(orden_Trabajo_routes.router)
    app.include_router(incidencia_routes.router, prefix='/api/incidencias')
    app.dependency_overrides[verificar_token] = lambda: dict(token)
    with TestClient(app) as cliente:
        detalle = cliente.get('/api/ordenes-trabajo/5')
        assert detalle.status_code == 200
        assert detalle.json()['data']['afectada_por_incidencia'] is True
        assert detalle.json()['data']['estado'] == 'EN_PROCESO'
        lista = cliente.get('/api/ordenes-trabajo/').json()['data']
        assert next(ot for ot in lista if ot['orden_nro'] == 5)['afectada_por_incidencia'] is True
        vinculos = cliente.get('/api/incidencias/9/ordenes-trabajo')
        assert vinculos.status_code == 200
        assert vinculos.json()['data'][0]['afectada_por_incidencia'] is True
        token['id_empresa'] = 2
        assert cliente.get('/api/incidencias/9/ordenes-trabajo').status_code == 404
        assert cliente.get('/api/ordenes-trabajo/5').status_code == 400


def test_dos_resoluciones_concurrentes_visibilidad_commits(datos):
    db, archivo = datos
    vincular(db, 9)
    vincular(db, 10)
    barrera = Barrier(2)

    def resolver(incidencia):
        conexion = sqlite3.connect(archivo, timeout=10)
        try:
            barrera.wait(timeout=10)
            conexion.execute("UPDATE t_incidencia SET estado='RESUELTA' WHERE id_incidencia=?", (incidencia,))
            # Un cambio sin commit no debe liberar la OT para otro lector.
            from app.repos.orden_trabajo_afectacion import AFECTADA_POR_INCIDENCIA_SQL
            visible = sqlite3.connect(archivo)
            try:
                expresion = AFECTADA_POR_INCIDENCIA_SQL.replace('obras.', '')
                assert visible.execute('SELECT '+expresion+' FROM t_orden_trabajo ot WHERE orden_nro=5').fetchone() == (1,)
            finally:
                visible.close()
            conexion.commit()
        finally:
            conexion.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(resolver, (9, 10)))
    assert afectada() is False
    assert leer()['data']['estado'] == 'EN_PROCESO'
