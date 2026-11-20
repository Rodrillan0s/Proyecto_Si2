"""Configuración y política de módulos sin BD o proveedores externos."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.services import planes_services as service, suscripcion_policy as policy
from app.services.planes_catalog import MODULOS, modulo_ruta
from app.routes.suscripcion_routes import router
from app.utils.security import verificar_token

ADMIN={'nro_usuario':1,'nombre_rol':'ADMINISTRADOR','id_empresa':1}
EMPRESA={'nro_usuario':3,'nombre_rol':'ADMINISTRADOR_EMPRESA','id_empresa':3}


def datos():
    return dict(version=1,nombre='Básico',descripcion='Plan de prueba',modulos=list(MODULOS),
        limite_usuarios=5,limite_obras=2,consultas_ia_mes=25,nivel_reportes='TODOS',
        exportar_reportes=True,automatizar_reportes=False)


@pytest.fixture
def memoria(monkeypatch):
    actual={'codigo':'BASICO',**datos()}
    empresas=[{'id_empresa':3,'nombre_empresa':'La Roca','estado':'ACTIVA','usuarios_activos':4,'obras_activas':3}]
    @contextmanager
    def transaction(): yield Mock()
    monkeypatch.setattr(service.repo,'transaccion',transaction)
    monkeypatch.setattr(service.repo,'obtener',lambda *args,**kwargs: deepcopy(actual))
    monkeypatch.setattr(service.repo,'empresas',lambda *args: deepcopy(empresas))
    guardar=Mock(side_effect=lambda cur,codigo,valores:{'codigo':codigo,**valores,'version':2})
    historial=Mock()
    monkeypatch.setattr(service.repo,'guardar',guardar)
    monkeypatch.setattr(service.repo,'historial_insertar',historial)
    return actual,empresas,guardar,historial


def test_previsualizacion_identifica_empresas_y_modulos_sin_escribir(memoria):
    actual,empresas,guardar,historial=memoria
    cambio=datos(); cambio['modulos'].remove('crm')
    vista=service.configurar(ADMIN,'BASICO',cambio)
    assert vista['total_empresas']==1 and vista['modulos_retirados']==[{'codigo':'crm','nombre':MODULOS['crm']}]
    assert vista['empresas_sobre_cupo'][0]['id_empresa']==3
    guardar.assert_not_called(); historial.assert_not_called()


def test_guardado_confirmado_registra_actor_y_snapshots(memoria):
    actual,empresas,guardar,historial=memoria
    vista=service.configurar(ADMIN,'BASICO',datos())
    nuevo=service.configurar(ADMIN,'BASICO',datos(),vista['confirmacion'])
    assert nuevo['version']==2
    assert historial.call_args.args[2]==ADMIN['nro_usuario']
    assert historial.call_args.args[3]['version']==1
    assert historial.call_args.args[4]['version']==2


@pytest.mark.parametrize('alteracion',['configuracion','empresas','version'])
def test_rechaza_preview_obsoleta_o_contenido_cambiado(memoria,alteracion):
    actual,empresas,guardar,historial=memoria
    vista=service.configurar(ADMIN,'BASICO',datos())
    cambio=datos()
    if alteracion=='configuracion': cambio['limite_obras']=50
    if alteracion=='empresas': empresas.append({'id_empresa':8,'nombre_empresa':'Nueva','usuarios_activos':1,'obras_activas':1})
    if alteracion=='version': actual['version']=2
    with pytest.raises(HTTPException) as error: service.configurar(ADMIN,'BASICO',cambio,vista['confirmacion'])
    assert error.value.status_code==409
    guardar.assert_not_called(); historial.assert_not_called()


@pytest.mark.parametrize('cambio',[
    {'modulos':['modulo_inventado']},{'modulos':['crm','crm']},{'limite_usuarios':0},
    {'limite_obras':1.5},{'consultas_ia_mes':-1},{'consultas_ia_mes':0},
    {'modulos':['crm'],'consultas_ia_mes':0}, {'exportar_reportes':False,'automatizar_reportes':True},
    {'nivel_reportes':'NINGUNO'}, {'nombre':'   '},
])
def test_validacion_de_configuraciones_inconsistentes(cambio):
    with pytest.raises(HTTPException) as error: service.validar(datos()|cambio)
    assert error.value.status_code==422


def test_ia_puede_habilitarse_en_basico_con_cupo_configurable(monkeypatch):
    fila={**datos(),'codigo_plan':'BASICO','estado':'ACTIVA','fecha_inicio':date(2020,1,1),'fecha_fin':None}
    monkeypatch.setattr(policy,'obtener',lambda *args:fila)
    assert policy.capacidades(fila)['ia_habilitada']
    policy.exigir_funcion(3,'ia')
    fila['modulos'].remove('ia')
    assert not policy.capacidades(fila)['ia_habilitada']
    with pytest.raises(HTTPException): policy.exigir_funcion(3,'ia')


@pytest.mark.parametrize('ruta,modulo',[
    ('/api/crm/clientes','crm'),('/crm/clientes/7','crm'),('/ai/consulta','ia'),
    ('/api/inventario/ajuste','inventario'),('/inventario/ajuste','inventario'),
    ('/api/proyectos/3/presupuestos/4','presupuestos'),('/api/proyectos/3/costos-ejecutados','control_costos'),
    ('/api/proyectos/3/avances/','avances'),('/api/proyectos/3/estructuras/','obras'),
    ('/api/estimaciones/analisis_precio_unitario','presupuestos'),('/api/ordenes-trabajo/','ordenes_trabajo'),
    ('/api/roles/4','usuarios'),('/api/voz/transcribir','ia')])
def test_rutas_y_aliases_quedan_en_solo_lectura_por_modulo(monkeypatch,ruta,modulo):
    assert modulo_ruta(ruta)==modulo
    fila={**datos(),'codigo_plan':'BASICO','estado':'ACTIVA','fecha_inicio':date(2020,1,1),'fecha_fin':None}
    fila['modulos'].remove(modulo)
    monkeypatch.setattr(policy,'obtener',lambda *args:fila)
    monkeypatch.setattr(policy.repo,'obtener_usuario',lambda _: {**EMPRESA,'estado':'ACTIVO'})
    with pytest.raises(HTTPException) as error: policy.proteger_http(EMPRESA,'POST',ruta)
    assert 'SUSCRIPCION_MODULO' in error.value.detail
    policy.proteger_http(EMPRESA,'GET',ruta)


def test_reportes_retirados_conservan_historial_pero_no_generacion(monkeypatch):
    fila=datos(); fila['modulos'].remove('reportes')
    monkeypatch.setattr(policy,'obtener',lambda *args:fila)
    ctx=SimpleNamespace(rol='ADMINISTRADOR_EMPRESA',empresa=3)
    policy.exigir_reporte(ctx,'stock',lectura=True)
    with pytest.raises(HTTPException): policy.exigir_reporte(ctx,'stock')
    with pytest.raises(HTTPException): policy.exigir_funcion(3,'automatizar')


def test_empresa_no_puede_configurar_ni_ver_historial_global(memoria):
    with pytest.raises(HTTPException) as error: service.configurar(EMPRESA,'BASICO',datos())
    assert error.value.status_code==403
    app=FastAPI(); app.include_router(router)
    app.dependency_overrides[verificar_token]=lambda: EMPRESA
    with TestClient(app) as client:
        assert client.get('/api/suscripciones/configuracion/modulos').status_code==403
        assert client.post('/api/suscripciones/planes/BASICO/previsualizar',json=datos()).status_code==403
        assert client.put('/api/suscripciones/planes/BASICO',json=datos()|{'confirmacion':'a'*64}).status_code==403
        assert client.get('/api/suscripciones/planes/BASICO/historial').status_code==403


def test_guardado_sin_revision_confirmada_rechazado_por_contrato():
    app=FastAPI(); app.include_router(router)
    app.dependency_overrides[verificar_token]=lambda: ADMIN
    with TestClient(app) as client:
        assert client.put('/api/suscripciones/planes/BASICO',json=datos()).status_code==422


def test_operaciones_actuales_de_negocio_tienen_modulo_registrado(monkeypatch):
    from app import create_app
    monkeypatch.setenv('BACKUP_ENABLED','false')
    caminos=create_app().openapi()['paths']
    excepciones=('/api/auth','/api/perfil','/api/suscripciones','/api/pagos','/api/backup','/api/empresas','/api/ws')
    for camino,operaciones in caminos.items():
        if set(operaciones)&{'post','put','patch','delete'} and not camino.startswith(excepciones):
            assert modulo_ruta(camino) in MODULOS, camino


def test_empresa_sin_suscripcion_no_falla_al_listar_modulos():
    caps=policy.capacidades({'codigo_plan':None,'modulos':None})
    assert caps['estado_efectivo']=='SIN_PLAN' and caps['solo_lectura']
    assert len(caps['modulos_solo_lectura'])==len(MODULOS)
