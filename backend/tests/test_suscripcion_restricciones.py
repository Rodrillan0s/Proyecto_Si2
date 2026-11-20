"""Política comercial aislada: no BD, proveedor, worker o envíos reales."""
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock
import pytest
from fastapi import HTTPException, FastAPI, Depends
from fastapi.testclient import TestClient
from app.services import suscripcion_policy as policy, suscripcion_services as subscriptions
from app.services import reportes_services as reports
from app.services.ai.ai_service import AIService
from app.services.reportes.contracts import Interpretation, AssistantRequest, ReportRequest
from app.utils import security
from app.classes.postgres import PostgreSQL

HOY = date(2026,10,24)
TOKEN = {'nro_usuario':10,'id_empresa':3,'nombre_rol':'ADMINISTRADOR_EMPRESA'}


def plan(codigo='BASICO', **extra):
    return dict(codigo_plan=codigo,estado='ACTIVA',fecha_inicio=HOY-timedelta(days=30),fecha_fin=None,modulos=list(policy.MODULOS),
        limite_usuarios={'BASICO':5,'PROFESIONAL':15,'EMPRESARIAL':50}[codigo],
        limite_obras={'BASICO':2,'PROFESIONAL':10,'EMPRESARIAL':30}[codigo],
        consultas_ia_mes=500 if codigo=='EMPRESARIAL' else 0,
        nivel_reportes='OPERATIVOS' if codigo=='BASICO' else 'TODOS',
        exportar_reportes=codigo!='BASICO',automatizar_reportes=codigo=='EMPRESARIAL') | extra


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setattr(policy,'hoy',lambda: HOY)
    monkeypatch.setattr(policy.repo,'obtener_usuario',lambda _: {**TOKEN,'estado':'ACTIVO'})
    obtener = Mock(return_value=plan())
    monkeypatch.setattr(policy.repo,'obtener_politica',obtener)
    return obtener


@pytest.mark.parametrize('dias,estado,lectura', [(0,'ACTIVA',False),(1,'GRACIA',False),(7,'GRACIA',False),(8,'VENCIDA',True)])
def test_fin_inclusivo_y_siete_dias_gracia(dias,estado,lectura):
    caps = policy.capacidades(plan(fecha_fin=HOY-timedelta(days=dias)),HOY)
    assert caps['estado_efectivo']==estado and caps['solo_lectura']==lectura


@pytest.mark.parametrize('fila,estado', [(None,'SIN_PLAN'),(plan(estado='SUSPENDIDA'),'SUSPENDIDA'),
    (plan(estado='CANCELADA'),'CANCELADA'),(plan(fecha_inicio=HOY+timedelta(days=1)),'PROGRAMADA')])
def test_estados_sin_escritura(fila,estado):
    caps=policy.capacidades(fila,HOY)
    assert caps['estado_efectivo']==estado and caps['solo_lectura']


@pytest.mark.parametrize('codigo', ['BASICO','PROFESIONAL'])
def test_ia_denegada_antes_del_proveedor_y_sin_reserva(entorno,monkeypatch,codigo):
    entorno.return_value=plan(codigo)
    reserva=Mock(); proveedor=Mock()
    monkeypatch.setattr(policy.repo,'reservar_ia',reserva)
    with pytest.raises(HTTPException) as error:
        with policy.consulta_ia(TOKEN): proveedor()
    assert error.value.status_code==403
    reserva.assert_not_called(); proveedor.assert_not_called()


def test_ia_reserva_una_consulta_por_solicitud_y_mes(entorno,monkeypatch):
    entorno.return_value=plan('EMPRESARIAL')
    reserva=Mock(return_value=True); liberar=Mock()
    monkeypatch.setattr(policy.repo,'reservar_ia',reserva); monkeypatch.setattr(policy.repo,'liberar_ia',liberar)
    with policy.consulta_ia(TOKEN): pass
    reserva.assert_called_once_with(3,date(2026,10,1)); liberar.assert_not_called()


def test_ia_no_supera_cupo_y_libera_reserva_en_fallo(entorno,monkeypatch):
    entorno.return_value=plan('EMPRESARIAL')
    reserva=Mock(return_value=False); liberar=Mock()
    monkeypatch.setattr(policy.repo,'reservar_ia',reserva); monkeypatch.setattr(policy.repo,'liberar_ia',liberar)
    with pytest.raises(HTTPException) as error:
        with policy.consulta_ia(TOKEN): pytest.fail('No debe invocar proveedor')
    assert error.value.status_code==429
    liberar.assert_not_called()
    reserva.return_value=True
    with pytest.raises(RuntimeError):
        with policy.consulta_ia(TOKEN): raise RuntimeError('Proveedor no disponible')
    liberar.assert_called_once_with(3,date(2026,10,1))


def test_ia_global_no_consume_cupo(entorno,monkeypatch):
    reserva=Mock(); monkeypatch.setattr(policy.repo,'reservar_ia',reserva)
    with policy.consulta_ia({**TOKEN,'nombre_rol':'ADMINISTRADOR'},4): pass
    reserva.assert_not_called()


def test_ia_rechaza_empresa_del_selector_no_autorizada(entorno):
    entorno.return_value=plan('EMPRESARIAL')
    with pytest.raises(HTTPException) as error:
        policy.autorizar_ia(TOKEN,4)
    assert error.value.status_code==403


@pytest.mark.parametrize('ruta', ['/api/crm/clientes','/crm/clientes','/api/compras/','/api/proyectos/','/api/usuarios/','/api/ai/consulta','/ai/consulta','/api/reportes/ejecuciones'])
def test_solo_lectura_bloquea_escrituras_y_aliases(entorno,ruta):
    entorno.return_value=plan(fecha_fin=HOY-timedelta(days=8))
    with pytest.raises(HTTPException) as error:
        policy.proteger_http(TOKEN,'POST',ruta)
    assert error.value.status_code==403
    policy.proteger_http(TOKEN,'GET',ruta)


@pytest.mark.parametrize('ruta', ['/api/auth/renovar','/api/perfil/','/api/perfil/cambiar-password','/api/suscripciones/mi-empresa'])
def test_solo_lectura_no_bloquea_cuenta(entorno,ruta):
    entorno.return_value=None
    policy.proteger_http(TOKEN,'PUT',ruta)


def test_inactivo_o_cambio_empresa_no_pueden_eludir_guard_con_jwt(entorno,monkeypatch):
    for usuario in ({**TOKEN,'estado':'INACTIVO'}, {**TOKEN,'id_empresa':4,'estado':'ACTIVO'}):
        monkeypatch.setattr(policy.repo,'obtener_usuario',lambda _: usuario)
        with pytest.raises(HTTPException): policy.proteger_http(TOKEN,'GET','/api/proyectos/')


@pytest.mark.parametrize('codigo,reporte,permitido', [('BASICO','stock',True),('BASICO','incidencias',True),
    ('BASICO','costos_periodo',False),('BASICO','saldo_comercial',False),('PROFESIONAL','costos_periodo',True),('EMPRESARIAL','saldo_comercial',True)])
def test_reportes_segun_plan(entorno,codigo,reporte,permitido):
    entorno.return_value=plan(codigo)
    assert policy.reporte_permitido(3,reporte)==permitido


def test_downgrade_conserva_lectura_reporte_historico_sin_exportar(entorno):
    ctx=SimpleNamespace(empresa=3,rol='ADMINISTRADOR_EMPRESA')
    policy.exigir_reporte(ctx,'saldo_comercial',lectura=True)
    with pytest.raises(HTTPException): policy.exigir_reporte(ctx,'saldo_comercial')
    with pytest.raises(HTTPException): policy.exigir_reporte(ctx,'saldo_comercial','Exportar_reportes',lectura=True)


def test_profesional_exporta_pero_no_automatiza(entorno):
    entorno.return_value=plan('PROFESIONAL')
    policy.exigir_funcion(3,'exportar')
    with pytest.raises(HTTPException): policy.exigir_funcion(3,'automatizar')


def test_tres_entradas_ia_bloqueadas_sin_abrir_reportes_ni_proveedor(entorno,monkeypatch):
    transaction=Mock(side_effect=AssertionError('No debe leer datos ni invocar IA'))
    monkeypatch.setattr(reports.repo,'transaction',transaction)
    for accion in (
        lambda: reports.assistant(TOKEN,AssistantRequest(texto='stock')),
        lambda: reports.interpretation(TOKEN,Interpretation(texto='stock',usar_ia=True)),
        lambda: AIService(provider=Mock()).consultar_crm('clientes',TOKEN),
    ):
        with pytest.raises(HTTPException) as error: accion()
        assert error.value.status_code==403
    transaction.assert_not_called()


def test_guard_ejecuta_antes_del_handler_que_captura_excepciones(entorno,monkeypatch):
    entorno.return_value=plan(estado='SUSPENDIDA')
    monkeypatch.setattr(security,'decode_access_token',lambda _: {'success':True,'payload':TOKEN})
    app=FastAPI(); handler=Mock()
    @app.post('/api/compras/')
    def comprar(token=Depends(security.verificar_token)):
        handler(); return {}
    with TestClient(app) as client:
        assert client.post('/api/compras/',headers={'Authorization':'Bearer prueba'}).status_code==403
    handler.assert_not_called()


def test_pool_no_toma_dos_conexiones_por_apertura(monkeypatch):
    pool=MagicMock(); pool.getconn.return_value.closed=0
    monkeypatch.setattr(PostgreSQL,'get_pool',classmethod(lambda cls: pool))
    db=PostgreSQL(); db.create_connection(); db.close_connection()
    assert pool.getconn.call_count==1 and pool.putconn.call_count==1


def test_handler_normaliza_cupo_de_sql_envuelto_por_rutas_legacy(monkeypatch):
    from app import create_app
    from app.services import users_services, obra_services
    monkeypatch.setenv('BACKUP_ENABLED','false')
    app=create_app()
    app.dependency_overrides[security.verificar_token]=lambda: {**TOKEN,'nombre_rol':'ADMINISTRADOR'}
    monkeypatch.setattr(users_services,'registrar_usuario',Mock(side_effect=RuntimeError('SUSCRIPCION_CUPO: Límite alcanzado.\nCONTEXT: SQL interno')))
    monkeypatch.setattr(obra_services,'registrar_obra',Mock(side_effect=ValueError('SUSCRIPCION_CUPO: Límite de obras alcanzado.')))
    with TestClient(app) as client:
        for path in ('/api/usuarios/','/api/proyectos/'):
            response=client.post(path,json={'ejemplo':True})
            assert response.status_code==409 and response.json()['code']=='SUSCRIPCION_CUPO'
            assert 'CONTEXT' not in response.text


def test_worker_no_envia_ni_encola_con_plan_suspendido(entorno,monkeypatch):
    from contextlib import contextmanager
    from app.services.reportes import worker
    entorno.return_value=plan('EMPRESARIAL',estado='SUSPENDIDA')
    @contextmanager
    def transaccion(*args,**kwargs): yield MagicMock()
    ctx=SimpleNamespace(empresa=3,rol='ADMINISTRADOR_EMPRESA',usuario=10)
    monkeypatch.setattr(worker.repo,'transaction',transaccion)
    monkeypatch.setattr(worker.repo,'get_execution',lambda *args: {'id_usuario':10,'id_empresa':3})
    monkeypatch.setattr(worker,'context',lambda *args: ctx)
    monkeypatch.setattr(reports,'context',lambda *args: ctx)
    correo=Mock(); completar=Mock(); insertar=Mock()
    monkeypatch.setattr(worker,'enviar_reporte',correo)
    monkeypatch.setattr(worker.repo,'complete_delivery',completar)
    monkeypatch.setattr(worker.repo,'insert_scheduled_execution',insertar)
    worker.deliver({'id':'envio','ejecucion':'reporte'})
    correo.assert_not_called()
    assert completar.call_args.args[1][0]=='FALLIDO'
    with pytest.raises(HTTPException): reports.queue_schedule(MagicMock(),{'id_usuario':10,'id_empresa':3},HOY)
    insertar.assert_not_called()


@pytest.mark.parametrize('valor', ['1',1])
def test_administrador_empresa_no_excluye_usuarios_del_cupo_asignando_rol_global(monkeypatch,valor):
    from app.services import users_services
    escritura=Mock(); monkeypatch.setattr(users_services.users_repos,'crear_usuario_db',escritura)
    with pytest.raises(ValueError,match='roles globales'):
        users_services.registrar_usuario({'nro_rol':valor,'ci':'Prueba','nombre_completo':'Prueba',
            'nombre_usuario':'prueba','password':'Prueba123!'},TOKEN)
    escritura.assert_not_called()


def test_perfil_disponible_no_permite_modificar_empresa_en_solo_lectura(entorno,monkeypatch):
    from app.services import profile_services as profile
    perfil=dict(id_empresa=3,ci='CI-PROPIO',nombre_rol='ADMINISTRADOR_EMPRESA',descripcion_empresa='Actual')
    monkeypatch.setattr(profile.profile_repos,'get_profile',lambda _: perfil)
    guardar=Mock(return_value={'success':True}); monkeypatch.setattr(profile.profile_repos,'update_profile',guardar)
    entorno.return_value=plan(estado='SUSPENDIDA')
    with pytest.raises(HTTPException):
        profile.actualizar_perfil_usuario(10,{'id_empresa':4,'descripcion_empresa':'Cambio'})
    guardar.assert_not_called()
    profile.actualizar_perfil_usuario(10,{'ci':'AJENO','id_empresa':4,'telefono':'123'})
    assert guardar.call_args.args[0]['id_empresa']==3
    assert guardar.call_args.args[0]['ci']=='CI-PROPIO'
