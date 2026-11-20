"""Pruebas aisladas: no conectan ni escriben en PostgreSQL."""
from datetime import date
from unittest.mock import Mock
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from app.routes import suscripcion_routes as routes
from app.services import suscripcion_services as service
from app.utils.security import verificar_token

ADMIN = {'nro_usuario': 1, 'nombre_rol': 'ADMINISTRADOR', 'id_empresa': 1}
EMPRESA = {'nro_usuario': 10, 'nombre_rol': 'ADMINISTRADOR_EMPRESA', 'id_empresa': 3}
VALIDO = {'codigo_plan': 'PROFESIONAL', 'estado': 'ACTIVA', 'fecha_inicio': '2026-10-24', 'fecha_fin': None}


def test_empresa_no_puede_asignar_ni_su_propio_plan(monkeypatch):
    escritura = Mock()
    monkeypatch.setattr(service.repo, 'asignar', escritura)
    with pytest.raises(HTTPException) as error:
        service.asignar(EMPRESA, 3, VALIDO)
    assert error.value.status_code == 403
    escritura.assert_not_called()


@pytest.mark.parametrize('usuario,token,solicitada', [
    ({'id_empresa': 3, 'estado': 'ACTIVO'}, EMPRESA, 4),
    ({'id_empresa': 4, 'estado': 'ACTIVO'}, EMPRESA, None),
    ({'id_empresa': 3, 'estado': 'INACTIVO'}, EMPRESA, None),
    (None, EMPRESA, None),
    ({'id_empresa': 3, 'estado': 'ACTIVO'}, {**EMPRESA, 'id_empresa': None}, None),
])
def test_contextos_no_autorizados(monkeypatch, usuario, token, solicitada):
    monkeypatch.setattr(service.repo, 'obtener_usuario', lambda _: usuario)
    lectura = Mock()
    monkeypatch.setattr(service.repo, 'listar_suscripciones', lectura)
    with pytest.raises(HTTPException) as error:
        service.consultar(token, solicitada)
    assert error.value.status_code == 403
    lectura.assert_not_called()


def test_usuario_consulta_solo_su_empresa(monkeypatch):
    monkeypatch.setattr(service.repo, 'obtener_usuario', lambda _: {'id_empresa': 3, 'estado': 'ACTIVO'})
    lectura = Mock(return_value=[{'id_empresa': 3, 'codigo_plan': 'PROFESIONAL', 'estado': 'ACTIVA', 'fecha_inicio': date(2026,10,24)}])
    monkeypatch.setattr(service.repo, 'listar_suscripciones', lectura)
    assert service.consultar(EMPRESA)['codigo_plan'] == 'PROFESIONAL'
    lectura.assert_called_once_with(3)


@pytest.mark.parametrize('cambios', [
    {'fecha_fin': '2026-10-01'}, {'fecha_inicio': 'invalida'}, {'estado': 'PAGADA'},
])
def test_validacion_antes_de_escribir(monkeypatch, cambios):
    escritura = Mock()
    monkeypatch.setattr(service.repo, 'asignar', escritura)
    with pytest.raises(HTTPException) as error:
        service.asignar(ADMIN, 3, {**VALIDO, **cambios})
    assert error.value.status_code == 400
    escritura.assert_not_called()


def test_asignacion_manual_con_actor_y_fechas(monkeypatch):
    escritura = Mock(return_value=True)
    monkeypatch.setattr(service.repo, 'asignar', escritura)
    monkeypatch.setattr(service.repo, 'listar_suscripciones', lambda _: [{'id_empresa': 3}])
    assert service.asignar(ADMIN, 3, VALIDO)['id_empresa'] == 3
    args = escritura.call_args.args
    assert args[0] == 3 and args[2] == ADMIN['nro_usuario']
    assert args[1]['fecha_inicio'] == date(2026, 10, 24)


def test_plan_inexistente_y_empresa_inexistente(monkeypatch):
    monkeypatch.setattr(service.repo, 'asignar', Mock(side_effect=ValueError('Plan inexistente')))
    with pytest.raises(HTTPException) as error:
        service.asignar(ADMIN, 3, VALIDO)
    assert error.value.status_code == 400
    monkeypatch.setattr(service.repo, 'asignar', Mock(return_value=False))
    with pytest.raises(HTTPException) as error:
        service.asignar(ADMIN, 99999, VALIDO)
    assert error.value.status_code == 404


def test_rutas_protegen_listado_historial_y_escritura():
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[verificar_token] = lambda: EMPRESA
    with TestClient(app) as client:
        assert client.get('/api/suscripciones/empresas').status_code == 403
        assert client.get('/api/suscripciones/empresas/3/historial').status_code == 403
        assert client.put('/api/suscripciones/empresas/3', json=VALIDO).status_code == 403


def test_ruta_valida_contrato_y_requiere_autenticacion():
    app = FastAPI()
    app.include_router(routes.router)
    with TestClient(app) as client:
        assert client.get('/api/suscripciones/planes').status_code in (401, 403)
        app.dependency_overrides[verificar_token] = lambda: ADMIN
        assert client.put('/api/suscripciones/empresas/3', json={**VALIDO, 'fecha_inicio': 'ayer'}).status_code == 422
