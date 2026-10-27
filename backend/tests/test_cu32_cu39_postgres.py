"""Servicios, repositorios y endpoints reales con datos sintéticos locales.

Ejecutar con cu32_cu39_postgres_check.py. La fixture pg comprueba nombre,
localhost y marca disposable antes de truncar o instalar las migraciones.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from pathlib import Path
from threading import Barrier

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from test_cu29_postgres import pg, scalar, sql_write, TOKEN
from app.routes import control_costos_routes, cronograma_routes, obra_routes
from app.services import control_costos_services as costos
from app.services import gastos_operativos_services as gastos
from app.services import trabajadores_costos_services as trabajadores
from app.utils import security


@pytest.fixture
def db(pg):
    sql_write(pg, "UPDATE obras.t_modulo SET nombre_modulo='Modulo_obras' WHERE id_modulo=1")
    sql_write(pg, "SELECT setval(pg_get_serial_sequence('obras.t_rol','id_rol'),100)")
    root = Path(__file__).resolve().parents[1] / 'database'
    # Aplicar dos veces comprueba la instalación idempotente SOLO en local.
    for _ in range(2):
        for migration in ['20261025_cu39_cronogramas.sql', 'migration_cu32_mano_obra_trabajadores.sql']:
            sql_write(pg, 'BEGIN;\n' + (root / migration).read_text(encoding='utf-8') + '\nCOMMIT;')
    for permission in ['Modificar_obras', 'Registrar_costos_ejecutados']:
        sql_write(pg, 'INSERT INTO obras.t_permiso(nombre_permiso,id_modulo) VALUES(%s,1)', (permission,))
    sql_write(pg, 'INSERT INTO obras.t_rol_permiso SELECT 3,id_permiso FROM obras.t_permiso ON CONFLICT DO NOTHING')
    sql_write(pg, "UPDATE obras.t_obra SET moneda='BOB' WHERE id_obra=12")
    security._PERMISOS_ROL_CACHE.clear()
    security._CACHE_EXPIRY = 0
    yield pg
    security._PERMISOS_ROL_CACHE.clear()
    security._CACHE_EXPIRY = 0


def client(uid=99, empresa=5, rol='ADMINISTRADOR_EMPRESA'):
    app = FastAPI()
    for router in [cronograma_routes.router, control_costos_routes.router]:
        app.include_router(router)
    app.include_router(obra_routes.router, prefix='/api/proyectos')
    jwt = security.create_access_token(uid, f'test_{uid}', rol, empresa, 'Pruebas', 'Actor sintético', None)
    return TestClient(app, headers={'Authorization': 'Bearer ' + jwt}, raise_server_exceptions=False)


def presupuesto(db):
    apu = scalar(db, """INSERT INTO obras.t_analisis_precio_unitario
        (id_obra,id_empresa,nombre,id_unidad_medida,codigo,costo_directo)
        VALUES(12,5,'Partida sintética',1,'PRUEBA',500) RETURNING id_analisis_precio_unitario""")
    estimacion = scalar(db, """INSERT INTO obras.t_estimacion
        (id_obra,id_empresa,nombre,estado,monto_total) VALUES(12,5,'Base sintética','BORRADOR',500)
        RETURNING id_estimacion""")
    partida = scalar(db, """INSERT INTO obras.t_estimacion_analisis_precio_unitario
        (id_estimacion,id_analisis_precio_unitario,cantidad,item_codigo,precio_unitario,costo_directo_unitario)
        VALUES(%s,%s,1,'1',500,500) RETURNING id_estimacion_analisis_precio_unitario""", (estimacion, apu))
    sql_write(db, "UPDATE obras.t_estimacion SET estado='APROBADA' WHERE id_estimacion=%s", (estimacion,))
    linea = costos.crear_linea_base({'id_obra': 12, 'id_estimacion_base': estimacion}, TOKEN)['data']['id_control_costo']
    return linea, partida


def costo(linea, partida, categoria='MATERIAL', monto=50):
    return dict(id_control_costo=linea, id_partida_presupuestaria=partida, fecha=date.today(),
                concepto='Costo sintético', categoria=categoria, cantidad=1, costo_unitario=monto, monto=monto)


def salario_jornada():
    trabajadores.registrar_salario(12,77,dict(salario_diario=200,fecha_vigencia=date.today()),TOKEN)
    trabajadores.registrar_jornada(12,dict(id_usuario=77,fecha=date.today(),dias_trabajados='0.5'),TOKEN)


def plan():
    return dict(nombre='Cronograma de prueba', descripcion='', fecha_inicio='2026-01-01', fecha_fin='2026-12-31',
                actividades=[dict(clave='a', nombre='Excavación', tipo='ACTIVIDAD', descripcion='',
                                  fecha_inicio='2026-01-01', fecha_fin='2026-01-05', avance=0, dependencias=[])])


def test_cu32_cierre_real_y_consulta_http(db):
    linea, partida = presupuesto(db)
    costos.registrar_costo(costo(linea, partida), TOKEN)
    salario_jornada()
    http = client()
    jornadas = http.get('/api/control-costos/obras/12/mano-obra')
    assert jornadas.status_code == 200, jornadas.text
    assert Decimal(str(jornadas.json()['data']['jornadas'][0]['costo_calculado'])) == 100
    response = http.patch('/api/proyectos/12/estado', json={'estado_obra': 'FINALIZADO'})
    assert response.status_code == 200, response.text
    assert 'resumen_economico_final' not in response.json()
    response = http.get('/api/control-costos/obras/12/resumen?final=true')
    assert response.status_code == 200, response.text
    data = response.json()['data']
    assert Decimal(str(data['resumen']['costo_final_registrado'])) == 150
    assert Decimal(str(data['resumen']['presupuesto_revisado'])) == 500
    assert Decimal(str(data['desglose_por_categoria']['MANO_OBRA'])) == 100
    gastos.finalizar_obra(12, TOKEN)
    assert scalar(db, 'SELECT count(*) FROM obras.t_cu32_mano_obra_cierre') == 1
    jornada = http.post('/api/control-costos/obras/12/jornadas', json=dict(id_usuario=77,fecha=str(date.today()),dias_trabajados=1))
    assert jornada.status_code == 409, jornada.text


def test_cu32_rollback_estado_y_cierre_si_falta_base(db):
    salario_jornada()
    with pytest.raises(costos.ControlCostosError):
        gastos.finalizar_obra(12, TOKEN)
    assert scalar(db,'SELECT estado_obra FROM obras.t_obra WHERE id_obra=12') == 'EN_PROCESO'
    assert scalar(db,'SELECT count(*) FROM obras.t_cu32_mano_obra_cierre') == 0


def test_cu32_no_duplica_manual_y_jornadas(db):
    linea, partida = presupuesto(db)
    costos.registrar_costo(costo(linea, partida, 'MANO_OBRA', 100), TOKEN)
    salario_jornada()
    response = client().patch('/api/proyectos/12/estado', json={'estado_obra':'FINALIZADO'})
    assert response.status_code == 409, response.text
    assert scalar(db,'SELECT estado_obra FROM obras.t_obra WHERE id_obra=12') == 'EN_PROCESO'
    assert scalar(db,'SELECT count(*) FROM obras.t_cu32_mano_obra_cierre') == 0


def test_cu32_contratos_permisos_y_tenant(db):
    presupuesto(db)
    http = client()
    salario = http.post('/api/control-costos/obras/12/trabajadores/77/salarios',json=dict(salario_diario=200,fecha_vigencia=str(date.today())))
    assert salario.status_code == 201, salario.text
    payload = dict(id_usuario=77,fecha=str(date.today()),dias_trabajados=0.5)
    for _ in range(2):
        response = http.post('/api/control-costos/obras/12/jornadas',json=payload)
        assert response.status_code == 201, response.text
    assert scalar(db,'SELECT count(*) FROM obras.t_jornada_trabajador_obra') == 1
    assert http.post('/api/control-costos/obras/12/jornadas',json={**payload,'dias_trabajados':1.1}).status_code == 422
    other = client(199,6)
    assert other.get('/api/control-costos/obras/12/mano-obra').status_code == 404
    assert other.get('/api/control-costos/obras/12/resumen?final=true').status_code == 404
    assert other.post('/api/control-costos/obras/12/jornadas',json=payload).status_code == 409
    worker = client(77,5,'ELECTRICO')
    assert worker.get('/api/control-costos/obras/12/mano-obra').status_code == 403
    assert worker.post('/api/control-costos/obras/12/jornadas',json=payload).status_code == 403
    sql_write(db,"UPDATE obras.t_suscripcion_empresa SET estado='SUSPENDIDA' WHERE id_empresa=5")
    assert http.post('/api/control-costos/obras/12/jornadas',json=payload).status_code == 403


def test_cu32_instalacion_pendiente_conserva_cu17(db):
    linea, partida = presupuesto(db)
    sql_write(db,'ALTER TABLE obras.t_cu32_mano_obra_cierre RENAME TO t_cu32_mano_obra_cierre_ausente')
    try:
        result = costos.registrar_costo(costo(linea, partida, 'MANO_OBRA',100), TOKEN)
        assert result['success']
        response = client().patch('/api/proyectos/12/estado',json={'estado_obra':'FINALIZADO'})
        assert response.status_code == 503, response.text
        assert scalar(db,'SELECT estado_obra FROM obras.t_obra WHERE id_obra=12') == 'EN_PROCESO'
    finally:
        sql_write(db,'ALTER TABLE obras.t_cu32_mano_obra_cierre_ausente RENAME TO t_cu32_mano_obra_cierre')


def test_cu39_crud_permisos_tenant_version_y_auditoria(db):
    http = client()
    url = '/api/obras/12/cronogramas/'
    response = http.post(url,json=plan())
    assert response.status_code == 201, response.text
    cid = response.json()['data']['id_cronograma']
    target = url + str(cid)
    assert client(199,6).get(target).status_code == 404
    assert client(77,5,'ELECTRICO').get(target).status_code == 403
    changed = {**plan(), 'version':1, 'nombre':'Revisado'}
    assert http.put(target,json=changed).status_code == 200
    assert http.put(target,json=changed).status_code == 409
    assert http.get(target).json()['data']['nombre'] == 'Revisado'
    delays = http.get('/api/obras/12/cronogramas/retrasos?corte=2026-01-10')
    assert delays.status_code == 200, delays.text
    assert delays.json()['data'][0]['dias_retraso'] == 5
    assert http.delete(target+'?version=1').status_code == 409
    assert http.delete(target+'?version=2').status_code == 200
    assert scalar(db,"SELECT count(*) FROM obras.t_bitacora WHERE modulo='CRONOGRAMAS'") == 3


def test_cu39_escrituras_simultaneas_y_suscripcion(db):
    http = client()
    response = http.post('/api/obras/12/cronogramas/',json=plan())
    assert response.status_code == 201, response.text
    target = '/api/obras/12/cronogramas/' + str(response.json()['data']['id_cronograma'])
    barrier = Barrier(2)
    def write(nombre):
        barrier.wait(timeout=5)
        return client().put(target,json={**plan(),'version':1,'nombre':nombre}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(write,['A','B'])) == [200,409]
    sql_write(db,"UPDATE obras.t_suscripcion_empresa SET estado='SUSPENDIDA' WHERE id_empresa=5")
    assert http.post('/api/obras/12/cronogramas/',json=plan()).status_code == 403
    assert http.get(target).status_code == 200


def test_cu39_fallo_sql_revierte_cabecera_y_bitacora(db):
    sql_write(db,"""CREATE OR REPLACE FUNCTION obras.cu39_test_fallo() RETURNS trigger LANGUAGE plpgsql
        AS $$ BEGIN RAISE EXCEPTION 'Fallo de prueba sintético'; END $$;
        CREATE TRIGGER cu39_test_fallo BEFORE INSERT ON obras.t_cronograma_actividad
        FOR EACH ROW EXECUTE FUNCTION obras.cu39_test_fallo()""")
    try:
        response = client().post('/api/obras/12/cronogramas/',json=plan())
        assert response.status_code == 500
        assert scalar(db,'SELECT count(*) FROM obras.t_cronograma') == 0
        assert scalar(db,"SELECT count(*) FROM obras.t_bitacora WHERE modulo='CRONOGRAMAS'") == 0
    finally:
        sql_write(db,'DROP TRIGGER cu39_test_fallo ON obras.t_cronograma_actividad; DROP FUNCTION obras.cu39_test_fallo()')


def test_cu39_supervisor_solo_planifica_y_no_borra_cabecera(db):
    role = scalar(db,"SELECT id_rol FROM obras.t_rol WHERE nombre_rol='SUPERVISOR_OBRA'")
    sql_write(db,'UPDATE obras.t_usuario SET id_rol=%s WHERE id_usuario=77',(role,))
    created = client().post('/api/obras/12/cronogramas/',json=plan())
    assert created.status_code == 201, created.text
    target = '/api/obras/12/cronogramas/' + str(created.json()['data']['id_cronograma'])
    supervisor = client(77,5,'SUPERVISOR_OBRA')
    assert supervisor.get(target).status_code == 200
    assert supervisor.post('/api/obras/12/cronogramas/',json=plan()).status_code == 403
    assert supervisor.put(target,json={**plan(),'version':1}).status_code == 403
    response = supervisor.put(target+'/planificacion',json={'version':1,'actividades':plan()['actividades']})
    assert response.status_code == 200, response.text
    assert supervisor.delete(target+'?version=2').status_code == 403
    assert client().get(target).json()['data']['nombre'] == plan()['nombre']


def test_cu39_instalacion_pendiente_responde_503(db):
    sql_write(db,'ALTER TABLE obras.t_cronograma RENAME TO t_cronograma_ausente')
    try:
        response = client().get('/api/obras/12/cronogramas/')
        assert response.status_code == 503, response.text
        assert 'migración' in response.json()['detail']
    finally:
        sql_write(db,'ALTER TABLE obras.t_cronograma_ausente RENAME TO t_cronograma')


def test_fabrica_real_registra_ambos_casos_sin_reemplazar_rutas(db):
    from app import create_app
    jwt = security.create_access_token(99,'test_99','ADMINISTRADOR_EMPRESA',5,'Pruebas','Actor sintético',None)
    http = TestClient(create_app(),headers={'Authorization':'Bearer '+jwt},raise_server_exceptions=False)
    for url in ['/api/obras/12/cronogramas/','/api/control-costos/obras/12/mano-obra']:
        response = http.get(url)
        assert response.status_code == 200, response.text
    response = http.get('/api/control-costos/obras/12/resumen?final=true')
    assert response.status_code == 409, response.text
