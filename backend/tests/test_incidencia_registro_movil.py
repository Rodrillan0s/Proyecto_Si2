"""Registro móvil CU19: autorización API y tenant, sin BD real."""
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes import incidencia_routes as routes
from app.services import incidencia_services as svc
from app.utils.security import verificar_token


@pytest.fixture
def caso(monkeypatch):
    actor = dict(nombre_rol='ELECTRICO', nro_usuario=14, id_empresa=1)
    detalle = dict(id_incidencia=20, id_obra=5, id_usuario_registro=14,
                   estado='ABIERTA', id_responsable=None, titulo='Falla eléctrica')
    repo = Mock()
    repo.obtener_empresa_obra.return_value = 1
    repo.trabajador_en_obra.return_value = True
    repo.crear.return_value = 20
    repo.obtener_estado_actual.return_value = ('ABIERTA', None)
    repo.obtener_detalle.return_value = detalle
    repo.listar_ordenes_trabajo_incidencia.return_value = []
    repo.obras_registro.return_value = [dict(id_obra=5, nombre='Green Tower', codigo='GT')]
    monkeypatch.setattr(svc, 'incidencia_repos', repo)
    monkeypatch.setattr(svc, 'bitacora_repos', Mock())
    monkeypatch.setattr('app.utils.security.obtener_permisos_rol', lambda rol: set())
    monkeypatch.setattr('app.classes.postgres.PostgreSQL.create_connection',
                        lambda *args: pytest.fail('No conectar a BD real'))
    app = FastAPI()
    app.include_router(routes.router, prefix='/api/incidencias')
    app.dependency_overrides[verificar_token] = lambda: actor
    with TestClient(app) as client:
        yield client, actor, detalle, repo


BODY = dict(id_obra=5, id_unidad=None, titulo='Falla eléctrica',
            descripcion='Segundo piso', prioridad='ALTA', ubicacion='Segundo piso')


@pytest.mark.parametrize('rol', ['ELECTRICO', 'PLOMERO', 'MAESTROALBAÑIL', 'ALBAÑIL'])
def test_registro_y_detalle_sin_acciones_administrativas(caso, rol):
    client, actor, detalle, repo = caso
    actor['nombre_rol'] = rol
    assert client.get('/api/incidencias/obras-registro').json()['data'][0]['id_obra'] == 5
    assert client.post('/api/incidencias/', json={**BODY, 'id_responsable':14,
                       'estado':'CERRADA', 'id_empresa':2}).status_code == 201
    repo.crear.assert_called_once_with(5, None, 14, 'Falla eléctrica', 'Segundo piso', 'ALTA', 'Segundo piso')
    repo.crear_seguimiento.assert_called_once_with(20, 14, None, 'ABIERTA', 'Incidencia registrada.')
    respuesta = client.get('/api/incidencias/20')
    assert respuesta.status_code == 200
    assert respuesta.json()['data']['estado'] == 'ABIERTA'
    assert respuesta.json()['data']['id_responsable'] is None
    for estado in ['EN_PROCESO', 'PENDIENTE_VALIDACION', 'RESUELTA', 'CERRADA']:
        assert client.patch('/api/incidencias/20/estado', json={'estado':estado}).status_code == 403
    assert client.patch('/api/incidencias/20/responsable', json={'id_responsable':14}).status_code == 403
    detalle['id_usuario_registro'] = 15
    assert client.get('/api/incidencias/20').status_code == 403


def test_obra_manipulada_otro_tenant_y_sin_pertenencia(caso):
    client, actor, detalle, repo = caso
    repo.obtener_empresa_obra.return_value = None
    assert client.post('/api/incidencias/', json={**BODY, 'id_obra':999, 'id_empresa':2}).status_code == 404
    repo.obtener_empresa_obra.assert_called_with(999, 1)
    repo.obtener_empresa_obra.return_value = 1
    repo.trabajador_en_obra.return_value = False
    assert client.post('/api/incidencias/', json=BODY).status_code == 403
    repo.crear.assert_not_called()


def test_cliente_sin_permiso_no_registra(caso):
    client, actor, detalle, repo = caso
    actor['nombre_rol'] = 'CLIENTE'
    assert client.post('/api/incidencias/', json=BODY).status_code == 403


def test_listado_propios_y_asignados_sin_confiar_en_filtro(caso):
    client, actor, detalle, repo = caso
    repo.listar.return_value = ([detalle], 1)
    assert client.get('/api/incidencias/').status_code == 200
    assert repo.listar.call_args.kwargs == {'id_usuario_visible':14}
    assert client.get('/api/incidencias/?id_responsable=999').status_code == 200
    assert repo.listar.call_args.args[6] == 14


def test_sql_obras_exige_tenant_pertenencia_y_usuario_activo(monkeypatch):
    from app.repos import incidencia_repos
    db = Mock()
    db.execute_query.return_value = [(5, 'GT', 'Green Tower')]
    monkeypatch.setattr(incidencia_repos, 'PostgreSQL', lambda: db)
    assert incidencia_repos.trabajador_en_obra(5, 14, 1)
    sql, params = db.execute_query.call_args.args
    assert params == (1, 1, 14, 14)
    for fragmento in ['o.id_empresa = %s', 't_obra_usuario', 'u.id_usuario = %s',
                       'u.id_empresa = o.id_empresa', "u.estado = 'ACTIVO'"]:
        assert fragmento in sql
    assert not incidencia_repos.trabajador_en_obra(999, 14, 1)


def test_sql_listado_propios_no_elimina_filtro_empresa(monkeypatch):
    from app.repos import incidencia_repos
    db = Mock()
    db.execute_query.side_effect = [(0,), []]
    monkeypatch.setattr(incidencia_repos, 'PostgreSQL', lambda: db)
    incidencia_repos.listar(id_empresa=1, id_usuario_visible=14)
    for llamada in db.execute_query.call_args_list:
        sql, params = llamada.args
        assert '(i.id_usuario_registro = %s OR i.id_responsable = %s)' in sql
        assert 'o.id_empresa = %s' in sql
        assert params[:3] == (14, 14, 1)


@pytest.mark.parametrize('rol', ['ELECTRICO', 'PLOMERO', 'MAESTROALBAÑIL', 'ALBAÑIL'])
def test_registrador_adjunta_y_consulta_sin_ser_responsable(caso, monkeypatch, tmp_path, rol):
    client, actor, detalle, repo = caso
    actor['nombre_rol'] = rol
    monkeypatch.setattr(svc, '_upload_root', lambda: str(tmp_path))
    repo.crear_evidencia.return_value = 7
    repo.listar_evidencias.return_value = [dict(id_evidencia=7, id_usuario=14)]
    base = '/api/incidencias/20'
    assert client.post('/api/incidencias/', json=BODY).status_code == 201
    assert client.get(base).status_code == 200
    assert client.post(base+'/evidencias', files={'archivo':('foto.jpg', b'foto', 'image/jpeg')}).status_code == 201
    assert repo.crear_evidencia.call_args.args[:2] == (20, 14)
    assert client.get(base+'/evidencias').json()['data'][0]['id_evidencia'] == 7
    ruta = next((tmp_path / '20').iterdir())
    repo.obtener_evidencia.return_value = dict(ruta_archivo=str(ruta), nombre_archivo='foto.jpg', tipo_mime='image/jpeg')
    assert client.get(base+'/evidencias/7/archivo').content == b'foto'
    assert detalle['id_responsable'] is None
    # Carlos recibe la responsabilidad; Jhon conserva solo su acceso de registrador.
    detalle.update(id_responsable=15, estado='ASIGNADA')
    repo.obtener_estado_actual.return_value = ('ASIGNADA', 15)
    assert client.get(base).status_code == 200
    assert client.get(base+'/evidencias').status_code == 200
    assert client.post(base+'/evidencias', files={'archivo':('foto.jpg', b'foto', 'image/jpeg')}).status_code == 201
    for estado in ['EN_PROCESO', 'PENDIENTE_VALIDACION', 'RESUELTA', 'CERRADA']:
        assert client.patch(base+'/estado', json={'estado':estado}).status_code == 403
    assert client.patch(base+'/responsable', json={'id_responsable':14}).status_code == 403
    assert client.put(base, json=BODY).status_code == 403
    assert client.put(base+'/ordenes-trabajo', json={'ordenes':[1]}).status_code == 403
    assert client.post(base+'/seguimiento', json={'observacion':'Avance'}).status_code == 403
    actor['nro_usuario'] = 15
    repo.cambiar_estado.return_value = True
    assert client.post(base+'/evidencias', files={'archivo':('foto.jpg', b'foto', 'image/jpeg')}).status_code == 201
    assert client.patch(base+'/estado', json={'estado':'EN_PROCESO'}).status_code == 200
    repo.obtener_estado_actual.return_value = ('EN_PROCESO', 15)
    assert client.patch(base+'/estado', json={'estado':'PENDIENTE_VALIDACION'}).status_code == 200
    repo.asignar_responsable.assert_not_called()
    repo.reemplazar_ordenes_trabajo.assert_not_called()


@pytest.mark.parametrize('empresa,usuario,status', [(1,16,403), (2,14,404)])
def test_evidencia_rechaza_ajeno_y_otro_tenant(caso, empresa, usuario, status):
    client, actor, detalle, repo = caso
    actor.update(id_empresa=empresa, nro_usuario=usuario)
    repo.obtener_estado_actual.side_effect = lambda i, e: ('ABIERTA', None) if e == 1 else (None, None)
    base = '/api/incidencias/20'
    for path in [base, base+'/evidencias', base+'/evidencias/7/archivo']:
        assert client.get(path).status_code == status
    assert client.post(base+'/evidencias', files={'archivo':('foto.jpg', b'foto', 'image/jpeg')}).status_code == status
    repo.obtener_estado_actual.assert_called_with(20, empresa)
    repo.crear_evidencia.assert_not_called()


def test_registrador_conserva_validaciones_archivo_y_cierre(caso):
    client, actor, detalle, repo = caso
    base = '/api/incidencias/20/evidencias'
    for contenido, tipo in [(b'', 'image/jpeg'), (b'foto', 'application/pdf'),
                             (b'x' * (svc.MAX_EVIDENCIA_BYTES + 1), 'image/jpeg')]:
        assert client.post(base, files={'archivo':('foto.jpg', contenido, tipo)}).status_code == 400
    repo.obtener_estado_actual.return_value = ('CERRADA', None)
    assert client.post(base, files={'archivo':('foto.jpg', b'foto', 'image/jpeg')}).status_code == 400
    repo.crear_evidencia.assert_not_called()


@pytest.mark.parametrize('valida,status', [(True, 201), (False, 400)])
def test_registro_unidad_real_y_rechazo_otra_obra(caso, valida, status):
    client, actor, detalle, repo = caso
    repo.unidad_pertenece_a_obra.return_value = valida
    assert client.post('/api/incidencias/', json={**BODY, 'id_unidad': 7}).status_code == status
    repo.unidad_pertenece_a_obra.assert_called_once_with(7, 5)
    if valida:
        assert repo.crear.call_args.args[:3] == (5, 7, 14)
    else:
        repo.crear.assert_not_called()


@pytest.mark.parametrize('rol', ['ELECTRICO', 'PLOMERO', 'ALBAÑIL', 'MAESTROALBAÑIL'])
def test_unidades_registro_limitadas_a_obra_activa(caso, monkeypatch, rol):
    from app.routes import unidad_routes
    from app.services import unidad_services
    client, actor, detalle, repo = caso
    actor['nombre_rol'] = rol
    client.app.include_router(unidad_routes.router)
    listar = Mock(return_value={'success': True, 'data': [{'id_unidad': 7, 'codigo': 'UNI-000007'}]})
    monkeypatch.setattr(unidad_services, 'listar_unidades', listar)
    assert client.get('/api/proyectos/5/unidades/').status_code == 200
    repo.obras_registro.assert_called_with(1, 14)
    listar.assert_called_once_with(5, actor)
    assert client.get('/api/proyectos/6/unidades/').status_code == 403
    actor['id_empresa'] = 2
    repo.obras_registro.return_value = []
    assert client.get('/api/proyectos/5/unidades/').status_code == 403
    repo.obras_registro.assert_called_with(2, 14)
    actor['id_empresa'] = None
    assert client.get('/api/proyectos/5/unidades/').status_code == 403
    actor.update(id_empresa=1, nro_usuario=None)
    assert client.get('/api/proyectos/5/unidades/').status_code == 403
    actor.update(nro_usuario=14, nombre_rol='CLIENTE')
    assert client.get('/api/proyectos/5/unidades/').status_code == 403
    actor['nombre_rol'] = rol
    for method, path in [('GET', '/api/proyectos/5/unidades/7'),
                         ('POST', '/api/proyectos/5/unidades/'),
                         ('PUT', '/api/proyectos/5/unidades/7'),
                         ('DELETE', '/api/proyectos/5/unidades/7')]:
        assert client.request(method, path, json={}).status_code == 403
    assert listar.call_count == 1
