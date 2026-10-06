"""CU19 atención: API aislada, sin conexiones ni escrituras a BD real."""
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes import incidencia_routes as routes
from app.services import incidencia_services as svc
from app.utils.security import verificar_token


@pytest.fixture
def escenario(monkeypatch, tmp_path):
    incidencia = dict(id_incidencia=10, id_obra=5, titulo="Filtración segundo piso",
                      obra_nombre="Green Tower", estado="ABIERTA", id_responsable=None,
                      fecha_inicio_atencion=None, fecha_fin_atencion=None)
    ot = dict(orden_nro=5, responsable="CARLOS", estado="EN_PROCESO")
    actor = dict(nro_usuario=12, id_empresa=1, nombre_rol="JEFE DE OBRA")
    permisos = {"JEFE DE OBRA": {"Visualizar_incidencias", "Modificar_incidencias", "Asignar_incidencias"},
                "SUPERVISOR": {"Cerrar_incidencias", "Modificar_incidencias", "Visualizar_incidencias"}, "ELECTRICO": set(), "PLOMERO": set()}
    monkeypatch.setattr("app.utils.security.obtener_permisos_rol", lambda rol: permisos.get(rol, set()))
    # Fail immediately if any code tries to connect to a real database.
    monkeypatch.setattr("app.classes.postgres.PostgreSQL.create_connection",
                        lambda *args: pytest.fail("No se permite conectar a BD en estas pruebas"))
    repo = Mock()
    def visible(i, empresa):
        return i == 10 and empresa in (None, 1)
    repo.obtener_detalle.side_effect = lambda i, e: dict(incidencia) if visible(i, e) else None
    repo.obtener_estado_actual.side_effect = lambda i, e: (incidencia['estado'], incidencia['id_responsable']) if visible(i, e) else (None, None)
    repo.obtener_empresa_incidencia.return_value = 1
    repo.usuario_pertenece_a_empresa.return_value = True
    repo.obtener_usuarios_asignables.return_value = [dict(nro_usuario=14, nombre_rol="ELECTRICO")]
    def asignar(i, empresa, usuario, estado):
        incidencia.update(id_responsable=usuario, estado=estado)
        return True
    repo.asignar_responsable.side_effect = asignar
    def cambiar(i, empresa, previo, nuevo, responsable):
        assert visible(i, empresa) and incidencia['estado'] == previo
        assert responsable is None or responsable == incidencia['id_responsable']
        incidencia['estado'] = nuevo
        if nuevo == 'EN_PROCESO':
            incidencia['fecha_inicio_atencion'] = incidencia['fecha_inicio_atencion'] or datetime.now(timezone.utc)
            incidencia['fecha_fin_atencion'] = None
        if nuevo == 'PENDIENTE_VALIDACION': incidencia['fecha_fin_atencion'] = datetime.now(timezone.utc)
        return True
    repo.cambiar_estado.side_effect = cambiar
    repo.crear_seguimiento.return_value = 1
    def evidencia(i, usuario, ruta, nombre, tipo, tamano):
        repo.obtener_evidencia.return_value = dict(
            ruta_archivo=str(tmp_path / str(i) / ruta.replace('\\', '/').split('/')[-1]),
            nombre_archivo=nombre, tipo_mime=tipo)
        return 1
    repo.crear_evidencia.side_effect = evidencia
    repo.listar_seguimiento.return_value = []
    repo.listar_evidencias.return_value = []
    repo.listar_ordenes_trabajo_incidencia.side_effect = lambda i: [dict(ot)]
    repo.listar.side_effect = lambda *args, **kwargs: ([dict(incidencia)] if args[6] == 14 or kwargs.get('id_usuario_visible') == 14 else [], 1 if args[6] == 14 or kwargs.get('id_usuario_visible') == 14 else 0)
    monkeypatch.setattr(svc, "incidencia_repos", repo)
    monkeypatch.setattr(svc, "bitacora_repos", Mock())
    monkeypatch.setattr(svc, "_upload_root", lambda: str(tmp_path))
    app = FastAPI()
    app.include_router(routes.router, prefix="/api/incidencias")
    app.dependency_overrides[verificar_token] = lambda: dict(actor)
    with TestClient(app) as client:
        yield client, actor, incidencia, ot, repo


def jhon(actor):
    actor.update(nro_usuario=14, nombre_rol="ELECTRICO", id_empresa=1)


def test_green_tower_flujo_completo_y_ot_intacta(escenario):
    client, actor, inc, ot, repo = escenario
    base = '/api/incidencias/10'
    assert client.patch(base+'/responsable', json={'id_responsable':14}).status_code == 200
    jhon(actor)
    assert client.get(base).json()['data']['id_responsable'] == 14
    assert client.patch(base+'/estado', json={'estado':'EN_PROCESO', 'fecha_inicio_atencion':'1900-01-01'}).status_code == 200
    inicio = inc['fecha_inicio_atencion']
    assert client.post(base+'/seguimiento', json={'observacion':'Atendiendo filtración'}).status_code == 201
    assert client.post(base+'/evidencias', files={'archivo':('foto.jpg', b'foto', 'image/jpeg')}).status_code == 201
    assert client.get(base+'/seguimiento').status_code == 200
    assert client.get(base+'/evidencias').status_code == 200
    assert client.get(base+'/evidencias/1/archivo').content == b'foto'
    assert client.patch(base+'/estado', json={'estado':'PENDIENTE_VALIDACION', 'fecha_fin_atencion':'1900-01-01'}).status_code == 200
    assert inc['estado'] == 'PENDIENTE_VALIDACION'
    assert client.patch(base+'/estado', json={'estado':'RESUELTA'}).status_code == 403
    actor.update(nro_usuario=12, nombre_rol='JEFE DE OBRA')
    assert client.patch(base+'/estado', json={'estado':'RESUELTA'}).status_code == 200
    jhon(actor)
    assert inc['fecha_inicio_atencion'] == inicio
    assert inc['fecha_fin_atencion'] >= inicio
    assert inc['id_responsable'] == 14
    assert client.patch(base+'/estado', json={'estado':'CERRADA'}).status_code == 403
    assert client.patch(base+'/responsable', json={'id_responsable':15}).status_code == 403
    assert client.put(base+'/ordenes-trabajo', json={'ordenes':[5]}).status_code == 403
    actor.update(nro_usuario=20, nombre_rol='SUPERVISOR')
    assert client.patch(base+'/estado', json={'estado':'CERRADA'}).status_code == 200
    assert ot == dict(orden_nro=5, responsable='CARLOS', estado='EN_PROCESO')
    repo.reemplazar_ordenes_trabajo.assert_not_called()
    # Todas las mutaciones del flujo son de incidencia/seguimiento/evidencia.
    assert {c[0] for c in repo.mock_calls} <= {
        'obtener_estado_actual', 'obtener_empresa_incidencia', 'usuario_pertenece_a_empresa',
        'obtener_detalle', 'obtener_usuarios_asignables', 'asignar_responsable',
        'crear_seguimiento', 'listar_ordenes_trabajo_incidencia', 'cambiar_estado',
        'crear_evidencia', 'listar_seguimiento', 'listar_evidencias', 'obtener_evidencia'}


@pytest.mark.parametrize('empresa,esperado', [(1,403),(2,404)])
@pytest.mark.parametrize('operacion', ['detalle','inicio','fin','seguimiento','foto','listar_fotos','archivo','leer_seguimiento','ot_afectadas'])
def test_ajeno_o_otro_tenant_rechazado(escenario, empresa, esperado, operacion):
    client, actor, inc, ot, repo = escenario
    inc.update(id_responsable=14, estado='EN_PROCESO' if operacion=='fin' else 'ASIGNADA')
    actor.update(nro_usuario=15, id_empresa=empresa, nombre_rol='PLOMERO')
    base='/api/incidencias/10'
    if operacion=='detalle': res=client.get(base)
    elif operacion in ('inicio','fin'): res=client.patch(base+'/estado', json={'estado':'EN_PROCESO' if operacion=='inicio' else 'PENDIENTE_VALIDACION'})
    elif operacion=='seguimiento': res=client.post(base+'/seguimiento', json={'observacion':'Intento ajeno'})
    elif operacion=='foto': res=client.post(base+'/evidencias', files={'archivo':('foto.jpg',b'foto','image/jpeg')})
    elif operacion=='listar_fotos': res=client.get(base+'/evidencias')
    elif operacion=='leer_seguimiento': res=client.get(base+'/seguimiento')
    elif operacion=='ot_afectadas': res=client.get(base+'/ordenes-trabajo')
    else: res=client.get(base+'/evidencias/1/archivo')
    assert res.status_code == esperado
    repo.cambiar_estado.assert_not_called()
    repo.crear_seguimiento.assert_not_called()
    repo.crear_evidencia.assert_not_called()


def test_listado_no_confia_en_responsable_cliente(escenario):
    client, actor, inc, ot, repo = escenario
    jhon(actor)
    client.get('/api/incidencias/?id_responsable=15&id_empresa=2')
    assert repo.listar.call_args.args[0] == 1
    assert repo.listar.call_args.args[6] == 14


@pytest.mark.parametrize('rol', ['ELECTRICO', 'PLOMERO', 'MAESTROALBAÑIL', 'ALBAÑIL'])
def test_roles_campo_solo_listan_propias_y_leen_ot_sin_modificar(escenario, rol):
    client, actor, inc, ot, repo = escenario
    actor.update(nro_usuario=14, nombre_rol=rol, id_empresa=1)
    inc.update(id_responsable=14, estado='ASIGNADA')
    respuesta = client.get('/api/incidencias/')
    assert respuesta.status_code == 200
    assert all(i['id_responsable'] == 14 for i in respuesta.json()['data'])
    assert repo.listar.call_args.args[0] == 1
    assert repo.listar.call_args.kwargs['id_usuario_visible'] == 14
    assert client.get('/api/incidencias/10/ordenes-trabajo').json()['data'] == [ot]
    assert client.put('/api/incidencias/10/ordenes-trabajo', json={'ordenes':[]}).status_code == 403
    repo.reemplazar_ordenes_trabajo.assert_not_called()


@pytest.mark.parametrize('rol', ['ADMINISTRADOR','JEFE DE OBRA'])
def test_administrativos_conservan_consulta_y_aportes(escenario, rol):
    client, actor, inc, ot, repo = escenario
    actor['nombre_rol']=rol
    inc.update(id_responsable=14, estado='ASIGNADA')
    assert client.get('/api/incidencias/10').status_code == 200
    assert client.post('/api/incidencias/10/seguimiento', json={'observacion':'Supervisión'}).status_code == 201
    assert client.post('/api/incidencias/10/evidencias', files={'archivo':('foto.jpg',b'foto','image/jpeg')}).status_code == 201
    # Incluso un administrador ajeno no inicia por el responsable.
    assert client.patch('/api/incidencias/10/estado', json={'estado':'EN_PROCESO'}).status_code == 403


def test_sin_jwt_no_accede():
    app=FastAPI()
    app.include_router(routes.router, prefix='/api/incidencias')
    with TestClient(app) as client:
        assert client.get('/api/incidencias/10').status_code in (401,403)


def test_responsable_con_mismo_id_en_otro_tenant_no_accede(escenario):
    client, actor, inc, ot, repo = escenario
    inc.update(id_responsable=14, estado='ASIGNADA')
    jhon(actor)
    actor['id_empresa']=2
    assert client.get('/api/incidencias/10').status_code == 404
    assert client.patch('/api/incidencias/10/estado', json={'estado':'EN_PROCESO'}).status_code == 404


@pytest.mark.parametrize('rol', ['JEFE DE OBRA', 'SUPERVISOR', 'ADMINISTRADOR'])
def test_validar_rechazar_y_volver_a_finalizar(escenario, rol):
    client, actor, inc, ot, repo = escenario
    inc.update(estado='PENDIENTE_VALIDACION', id_responsable=14,
               fecha_inicio_atencion=datetime.now(timezone.utc), fecha_fin_atencion=datetime.now(timezone.utc))
    inicio = inc['fecha_inicio_atencion']
    actor.update(nro_usuario=12, nombre_rol=rol)
    base='/api/incidencias/10/estado'
    assert client.patch(base, json={'estado':'EN_PROCESO'}).status_code == 200
    assert inc['fecha_inicio_atencion'] == inicio
    assert inc['fecha_fin_atencion'] is None
    jhon(actor)
    assert client.patch(base, json={'estado':'RESUELTA'}).status_code == 403
    assert client.patch(base, json={'estado':'PENDIENTE_VALIDACION'}).status_code == 200
    fin = inc['fecha_fin_atencion']
    actor.update(nro_usuario=12, nombre_rol=rol)
    assert client.patch(base, json={'estado':'RESUELTA'}).status_code == 200
    assert inc['id_responsable'] == 14 and inc['fecha_fin_atencion'] == fin
    jhon(actor)
    assert client.patch(base, json={'estado':'PENDIENTE_VALIDACION'}).status_code == 400
    assert ot == dict(orden_nro=5, responsable='CARLOS', estado='EN_PROCESO')
    repo.reemplazar_ordenes_trabajo.assert_not_called()


@pytest.mark.parametrize('rol', ['ELECTRICO','PLOMERO','MAESTROALBA\u00d1IL','ALBA\u00d1IL'])
@pytest.mark.parametrize('destino', ['RESUELTA','EN_PROCESO'])
def test_trabajador_no_valida_ni_rechaza(escenario, rol, destino):
    client, actor, inc, ot, repo = escenario
    inc.update(estado='PENDIENTE_VALIDACION', id_responsable=14)
    actor.update(nro_usuario=14, nombre_rol=rol)
    assert client.patch('/api/incidencias/10/estado', json={'estado':destino}).status_code == 403
    repo.cambiar_estado.assert_not_called()


@pytest.mark.parametrize('destino', ['RESUELTA','EN_PROCESO'])
def test_otro_tenant_no_valida(escenario, destino):
    client, actor, inc, ot, repo = escenario
    inc.update(estado='PENDIENTE_VALIDACION', id_responsable=14)
    actor.update(id_empresa=2, nombre_rol='JEFE DE OBRA')
    assert client.patch('/api/incidencias/10/estado', json={'estado':destino}).status_code == 404
    repo.cambiar_estado.assert_not_called()
