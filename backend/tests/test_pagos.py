"""CU37 Fase 1: pruebas aisladas, sin PostgreSQL ni llamadas a Stripe."""
from copy import deepcopy
from datetime import date, datetime, timezone
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.routes import pago_routes
from app.repos import pago_repos
from app.services import pago_services as service
from app.services import suscripcion_policy
from app.services.payments import stripe_gateway
from app.utils.security import verificar_token


EMPRESA = {'nro_usuario': 30, 'nombre_rol': 'ADMINISTRADOR_EMPRESA', 'id_empresa': 3}
OTRA_EMPRESA = {'nro_usuario': 40, 'nombre_rol': 'ADMINISTRADOR_EMPRESA', 'id_empresa': 4}
ADMIN = {'nro_usuario': 1, 'nombre_rol': 'ADMINISTRADOR', 'id_empresa': 1}
TRABAJADOR = {'nro_usuario': 31, 'nombre_rol': 'TRABAJADOR', 'id_empresa': 3}
CLAVE = 'checkout-prueba-0001'


@pytest.fixture
def memoria(monkeypatch):
    pagos = {}
    llamadas = {'stripe': 0, 'precio_insertado': None}
    usuarios = {
        30: {'id_usuario': 30, 'id_empresa': 3, 'estado': 'ACTIVO', 'nombre_rol': 'ADMINISTRADOR_EMPRESA'},
        40: {'id_usuario': 40, 'id_empresa': 4, 'estado': 'ACTIVO', 'nombre_rol': 'ADMINISTRADOR_EMPRESA'},
        1: {'id_usuario': 1, 'id_empresa': 1, 'estado': 'ACTIVO', 'nombre_rol': 'ADMINISTRADOR'},
        31: {'id_usuario': 31, 'id_empresa': 3, 'estado': 'ACTIVO', 'nombre_rol': 'TRABAJADOR'},
    }
    precio = {
        'codigo': 'PROFESIONAL', 'nombre': 'Profesional', 'descripcion': 'Plan de prueba',
        'precio_menor': 15900, 'moneda': 'BOB', 'periodo_meses': 1, 'version_precio': 7,
    }

    monkeypatch.setattr(service.repo, 'obtener_usuario', lambda usuario: deepcopy(usuarios.get(usuario)))
    monkeypatch.setattr(service.repo, 'listar_planes_comerciales', lambda: [deepcopy(precio)])
    monkeypatch.setattr(service.repo, 'obtener_precio', lambda codigo: deepcopy(precio) if codigo == 'PROFESIONAL' else None)
    monkeypatch.setattr(service.repo, 'existe_suscripcion', lambda empresa: empresa in (3, 4))
    monkeypatch.setattr(service.repo, 'obtener_pago_por_idempotencia', lambda clave: deepcopy(pagos.get(clave)))

    def crear_pago(empresa, valor, clave, actor):
        llamadas['precio_insertado'] = deepcopy(valor)
        if clave in pagos:
            return deepcopy(pagos[clave]), False
        pago = {
            'id_pago': len(pagos) + 1, 'id_empresa': empresa, 'codigo_plan': valor['codigo'],
            'version_precio': valor['version_precio'], 'monto_menor': valor['precio_menor'],
            'moneda': valor['moneda'], 'periodo_meses': valor['periodo_meses'],
            'estado': 'PENDIENTE', 'stripe_checkout_session_id': None,
            'stripe_checkout_url': None,
            'checkout_expira_en': datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc),
            'iniciado_por': actor,
        }
        pagos[clave] = pago
        return deepcopy(pago), True

    def guardar_checkout(id_pago, checkout):
        clave = next(k for k, p in pagos.items() if p['id_pago'] == id_pago)
        pagos[clave].update({
            'stripe_checkout_session_id': checkout['session_id'],
            'stripe_checkout_url': checkout['url'],
            'checkout_expira_en': checkout['expires_at'],
            'stripe_payment_status': checkout['payment_status'],
            'stripe_livemode': checkout['livemode'],
        })
        return deepcopy(pagos[clave])

    def checkout(pago, plan, clave):
        llamadas['stripe'] += 1
        assert pago['monto_menor'] == 15900 and pago['moneda'] == 'BOB'
        assert plan['version_precio'] == 7 and clave == CLAVE
        return {
            'session_id': 'cs_test_fase1', 'url': 'https://checkout.stripe.test/fase1',
            'expires_at': datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc),
            'payment_status': 'unpaid', 'livemode': False,
        }

    monkeypatch.setattr(service.repo, 'crear_pago_pendiente', crear_pago)
    monkeypatch.setattr(service.repo, 'guardar_checkout', guardar_checkout)
    monkeypatch.setattr(service.repo, 'registrar_error_checkout', Mock())
    monkeypatch.setattr(service.repo, 'obtener_pago', lambda pago_id: next((deepcopy(p) for p in pagos.values() if p['id_pago'] == pago_id), None))
    monkeypatch.setattr(service.stripe_gateway, 'crear_checkout', checkout)
    return pagos, llamadas, precio


def test_crea_pago_pendiente_con_snapshot_de_precio(memoria):
    pagos, llamadas, precio = memoria
    resultado = service.iniciar_checkout(EMPRESA, 'profesional', CLAVE)
    pago = pagos[CLAVE]
    assert resultado == {
        'id_pago': 1, 'estado': 'PENDIENTE',
        'checkout_url': 'https://checkout.stripe.test/fase1',
        'checkout_expira_en': datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc),
    }
    assert pago['id_empresa'] == EMPRESA['id_empresa']
    assert (pago['monto_menor'], pago['moneda'], pago['periodo_meses'], pago['version_precio']) == (15900, 'BOB', 1, 7)
    assert llamadas['precio_insertado'] == precio
    assert llamadas['stripe'] == 1


def test_reintento_idempotente_reutiliza_pago_y_checkout(memoria):
    pagos, llamadas, _ = memoria
    primero = service.iniciar_checkout(EMPRESA, 'PROFESIONAL', CLAVE)
    segundo = service.iniciar_checkout(EMPRESA, 'PROFESIONAL', CLAVE)
    assert primero == segundo
    assert len(pagos) == 1
    assert llamadas['stripe'] == 1


def test_clave_no_puede_reutilizarse_para_otro_tenant_o_plan(memoria):
    service.iniciar_checkout(EMPRESA, 'PROFESIONAL', CLAVE)
    with pytest.raises(HTTPException) as error:
        service.iniciar_checkout(OTRA_EMPRESA, 'PROFESIONAL', CLAVE)
    assert error.value.status_code == 409
    with pytest.raises(HTTPException) as error:
        service.iniciar_checkout(EMPRESA, 'BASICO', CLAVE)
    assert error.value.status_code == 409


def test_consulta_respeta_tenant_y_admin_global(memoria):
    service.iniciar_checkout(EMPRESA, 'PROFESIONAL', CLAVE)
    assert service.consultar_pago(EMPRESA, 1)['id_empresa'] == 3
    assert service.consultar_pago(ADMIN, 1)['id_empresa'] == 3
    with pytest.raises(HTTPException) as error:
        service.consultar_pago(OTRA_EMPRESA, 1)
    assert error.value.status_code == 403


def comprobante_hu126(**cambios):
    datos = {
        'id_pago': 20, 'id_empresa': 3, 'codigo_plan': 'PROFESIONAL',
        'nombre_plan': 'Profesional', 'monto_menor': 24900, 'moneda': 'BOB',
        'estado': 'CONFIRMADO',
        'confirmado_en': datetime(2026, 10, 25, 19, 0, tzinfo=timezone.utc),
        'stripe_checkout_session_id': 'cs_test_hu126',
        'stripe_payment_intent_id': 'pi_hu126',
        'stripe_receipt_url': 'https://pay.stripe.com/receipts/test-hu126',
    }
    datos.update(cambios)
    return datos


def test_historial_propio_filtra_por_empresa_autenticada(memoria, monkeypatch):
    esperado = [{
        'id_pago': 20, 'codigo_plan': 'PROFESIONAL', 'nombre_plan': 'Profesional',
        'monto_menor': 24900, 'moneda': 'BOB', 'estado': 'CONFIRMADO',
        'fecha': datetime(2026, 10, 25, 18, 0, tzinfo=timezone.utc),
        'stripe_checkout_session_id': 'cs_test_hu126',
        'stripe_payment_intent_id': 'pi_hu126',
        'stripe_checkout_url': 'https://checkout.stripe.com/test-hu126',
        'stripe_receipt_url': 'https://pay.stripe.com/receipts/test-hu126',
    }]
    listar = Mock(return_value=esperado)
    monkeypatch.setattr(service.repo, 'listar_pagos_empresa', listar)
    assert service.listar_pagos_mi_empresa(EMPRESA) == esperado
    listar.assert_called_once_with(3)


def test_historial_rechaza_roles_sin_ambito_empresa(memoria, monkeypatch):
    listar = Mock(side_effect=AssertionError('No debe listar pagos para este rol.'))
    monkeypatch.setattr(service.repo, 'listar_pagos_empresa', listar)
    with pytest.raises(HTTPException) as error:
        service.listar_pagos_mi_empresa(ADMIN)
    assert error.value.status_code == 403
    listar.assert_not_called()


def test_comprobante_devuelve_proyeccion_solicitada(memoria, monkeypatch):
    monkeypatch.setattr(service.repo, 'obtener_comprobante', lambda _: comprobante_hu126())
    resultado = service.consultar_comprobante(EMPRESA, 20)
    assert resultado == {
        'id_pago': 20, 'codigo_plan': 'PROFESIONAL', 'nombre_plan': 'Profesional',
        'monto_menor': 24900, 'moneda': 'BOB', 'estado': 'CONFIRMADO',
        'confirmado_en': datetime(2026, 10, 25, 19, 0, tzinfo=timezone.utc),
        'stripe_checkout_session_id': 'cs_test_hu126',
        'stripe_payment_intent_id': 'pi_hu126',
        'stripe_receipt_url': 'https://pay.stripe.com/receipts/test-hu126',
    }
    assert 'id_empresa' not in resultado


def test_administrador_puede_consultar_cualquier_comprobante(memoria, monkeypatch):
    monkeypatch.setattr(
        service.repo, 'obtener_comprobante',
        lambda _: comprobante_hu126(id_empresa=4, id_pago=21),
    )
    assert service.consultar_comprobante(ADMIN, 21)['id_pago'] == 21


def test_comprobante_de_otra_empresa_devuelve_403(memoria, monkeypatch):
    monkeypatch.setattr(
        service.repo, 'obtener_comprobante',
        lambda _: comprobante_hu126(id_empresa=4),
    )
    with pytest.raises(HTTPException) as error:
        service.consultar_comprobante(EMPRESA, 20)
    assert error.value.status_code == 403


def test_rutas_hu126_exponen_historial_y_comprobante(memoria, monkeypatch):
    historial = Mock(return_value=[])
    comprobante = Mock(return_value={'id_pago': 20})
    monkeypatch.setattr(service, 'listar_pagos_mi_empresa', historial)
    monkeypatch.setattr(service, 'consultar_comprobante', comprobante)
    app = FastAPI()
    app.include_router(pago_routes.router)
    app.dependency_overrides[verificar_token] = lambda: EMPRESA
    with TestClient(app) as client:
        respuesta_historial = client.get('/api/pagos/mi-empresa')
        respuesta_comprobante = client.get('/api/pagos/20/comprobante')
    assert respuesta_historial.status_code == 200
    assert respuesta_comprobante.status_code == 200
    historial.assert_called_once_with(EMPRESA)
    comprobante.assert_called_once_with(EMPRESA, 20)


def test_roles_y_body_no_permiten_alterar_datos_comerciales(memoria):
    with pytest.raises(HTTPException) as error:
        service.iniciar_checkout(ADMIN, 'PROFESIONAL', CLAVE)
    assert error.value.status_code == 403
    with pytest.raises(HTTPException) as error:
        service.consultar_pago(TRABAJADOR, 1)
    assert error.value.status_code == 403

    app = FastAPI()
    app.include_router(pago_routes.router)
    app.dependency_overrides[verificar_token] = lambda: EMPRESA
    with TestClient(app) as client:
        respuesta = client.post('/api/pagos/checkout-sessions', headers={'Idempotency-Key': CLAVE}, json={
            'codigo_plan': 'PROFESIONAL', 'id_empresa': 99, 'monto_menor': 1, 'moneda': 'USD',
        })
        assert respuesta.status_code == 422


def test_ruta_checkout_rechaza_roles_distintos_de_empresa(memoria):
    app = FastAPI()
    app.include_router(pago_routes.router)
    app.dependency_overrides[verificar_token] = lambda: ADMIN
    with TestClient(app) as client:
        assert client.post('/api/pagos/checkout-sessions', headers={'Idempotency-Key': CLAVE},
                           json={'codigo_plan': 'PROFESIONAL'}).status_code == 403


def test_pagos_es_cuidado_de_cuenta_aun_en_solo_lectura(memoria, monkeypatch):
    escritura = Mock(side_effect=AssertionError('No debe consultar vigencia para iniciar una renovación.'))
    monkeypatch.setattr(suscripcion_policy, 'exigir_escritura', escritura)
    monkeypatch.setattr(suscripcion_policy.repo, 'obtener_usuario', lambda _: {
        'id_empresa': 3, 'estado': 'ACTIVO', 'nombre_rol': 'ADMINISTRADOR_EMPRESA',
    })
    suscripcion_policy.proteger_http(EMPRESA, 'POST', '/api/pagos/checkout-sessions')
    escritura.assert_not_called()


def test_gateway_crea_exclusivamente_checkout_de_prueba(monkeypatch):
    capturado = {}

    class Session:
        @staticmethod
        def create(**kwargs):
            capturado.update(kwargs)
            return {
                'id': 'cs_test_gateway', 'url': 'https://checkout.stripe.test/gateway',
                'livemode': False, 'payment_status': 'unpaid', 'expires_at': 1792960200,
            }

    monkeypatch.setattr(stripe_gateway, '_stripe_module', lambda: SimpleNamespace(
        checkout=SimpleNamespace(Session=Session)))
    monkeypatch.setattr(stripe_gateway.Config, 'STRIPE_SECRET_KEY', 'sk_test_sin_valor_real')
    monkeypatch.setattr(stripe_gateway.Config, 'STRIPE_SUCCESS_URL', 'https://example.test/exito')
    monkeypatch.setattr(stripe_gateway.Config, 'STRIPE_CANCEL_URL', 'https://example.test/cancelado')
    pago = {
        'id_pago': 8, 'id_empresa': 3, 'codigo_plan': 'PROFESIONAL',
        'version_precio': 7, 'monto_menor': 15900, 'moneda': 'BOB',
        'checkout_expira_en': datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc),
    }
    resultado = stripe_gateway.crear_checkout(
        pago, {'nombre': 'Profesional', 'descripcion': 'Plan'}, CLAVE)
    assert resultado['session_id'] == 'cs_test_gateway' and resultado['livemode'] is False
    assert capturado['line_items'][0]['price_data']['unit_amount'] == 15900
    assert capturado['line_items'][0]['price_data']['currency'] == 'bob'
    assert capturado['metadata']['id_empresa'] == '3'
    assert capturado['expires_at'] == 1792958400
    assert 'payment_method_types' not in capturado


def test_gateway_rechaza_clave_live(monkeypatch):
    monkeypatch.setattr(stripe_gateway, '_stripe_module', lambda: SimpleNamespace())
    monkeypatch.setattr(stripe_gateway.Config, 'STRIPE_SECRET_KEY', 'sk_live_prohibida')
    monkeypatch.setattr(stripe_gateway.Config, 'STRIPE_SUCCESS_URL', 'https://example.test/exito')
    monkeypatch.setattr(stripe_gateway.Config, 'STRIPE_CANCEL_URL', 'https://example.test/cancelado')
    with pytest.raises(stripe_gateway.StripeGatewayError) as error:
        stripe_gateway.crear_checkout({}, {}, CLAVE)
    assert error.value.codigo == 'STRIPE_TEST_REQUERIDO'


def test_gateway_configura_store_tls_una_sola_vez(monkeypatch):
    inyectar = Mock()
    monkeypatch.setattr(stripe_gateway, '_TLS_CONFIGURADO', False)
    monkeypatch.setitem(sys.modules, 'truststore', SimpleNamespace(inject_into_ssl=inyectar))
    stripe_gateway._configurar_tls()
    stripe_gateway._configurar_tls()
    inyectar.assert_called_once_with()


def test_gateway_convierte_metadata_de_stripe_object_v16():
    class StripeObjectV16:
        def _to_dict_recursive(self):
            return {
                'id_pago': '4', 'id_empresa': '4',
                'codigo_plan': 'PROFESIONAL', 'version_precio': '1',
            }

    assert stripe_gateway._diccionario(StripeObjectV16()) == {
        'id_pago': '4', 'id_empresa': '4',
        'codigo_plan': 'PROFESIONAL', 'version_precio': '1',
    }


def confirmacion_pago(**cambios):
    datos = {
        'session_id': 'cs_test_hu125', 'livemode': False, 'payment_status': 'paid',
        'amount_total': 24900, 'currency': 'bob', 'client_reference_id': '10',
        'metadata': {'id_pago': '10', 'id_empresa': '3', 'codigo_plan': 'PROFESIONAL', 'version_precio': '1'},
        'payment_intent_id': 'pi_hu125', 'payment_intent_status': 'succeeded',
        'payment_intent_amount_received': 24900, 'payment_intent_currency': 'bob',
        'payment_intent_metadata': {
            'id_pago': '10', 'id_empresa': '3', 'codigo_plan': 'PROFESIONAL', 'version_precio': '1',
        },
        'receipt_url': 'https://pay.stripe.com/receipts/test',
    }
    datos.update(cambios)
    return datos


def pago_hu125(**cambios):
    datos = {
        'id_pago': 10, 'id_empresa': 3, 'codigo_plan': 'PROFESIONAL',
        'version_precio': 1, 'monto_menor': 24900, 'moneda': 'BOB',
        'periodo_meses': 1, 'estado': 'PENDIENTE', 'tipo_aplicacion': None,
        'stripe_checkout_session_id': 'cs_test_hu125', 'stripe_payment_intent_id': None,
        'id_historial_suscripcion': None,
    }
    datos.update(cambios)
    return datos


def test_webhook_firmado_confirma_una_vez(monkeypatch):
    pago = pago_hu125()
    session = {'id': 'cs_test_hu125', 'livemode': False, 'payment_status': 'paid'}
    monkeypatch.setattr(service.stripe_gateway, 'construir_evento', lambda payload, firma: {
        'id': 'evt_test_hu125', 'tipo': 'checkout.session.completed', 'objeto': session,
    })
    monkeypatch.setattr(service.stripe_gateway, 'confirmar_desde_evento', lambda _: confirmacion_pago())
    monkeypatch.setattr(service.repo, 'obtener_pago_por_sesion', lambda _: deepcopy(pago))
    aplicaciones = []

    def aplicar(id_pago, confirmacion, evento_id=None, verificado_por=None):
        aplicaciones.append((id_pago, evento_id, verificado_por))
        if pago['estado'] == 'CONFIRMADO':
            return deepcopy(pago), False
        pago.update(estado='CONFIRMADO', tipo_aplicacion='RENOVACION', id_historial_suscripcion=50)
        return deepcopy(pago), True

    monkeypatch.setattr(service.repo, 'aplicar_pago_confirmado', aplicar)
    primero = service.procesar_webhook(b'evento', 'firma')
    segundo = service.procesar_webhook(b'evento', 'firma')
    assert primero['estado'] == 'CONFIRMADO' and primero['aplicado'] is True
    assert segundo['estado'] == 'CONFIRMADO' and segundo['aplicado'] is False
    assert aplicaciones == [(10, 'evt_test_hu125', None), (10, 'evt_test_hu125', None)]


@pytest.mark.parametrize(('tipo', 'estado'), [
    ('checkout.session.async_payment_failed', 'FALLIDO'),
    ('checkout.session.expired', 'CANCELADO'),
])
def test_webhook_fallido_o_expirado_no_aplica_cu33(monkeypatch, tipo, estado):
    pago = pago_hu125()
    monkeypatch.setattr(service.stripe_gateway, 'construir_evento', lambda payload, firma: {
        'id': f'evt_{estado.lower()}', 'tipo': tipo,
        'objeto': {'id': 'cs_test_hu125', 'livemode': False, 'payment_status': 'unpaid'},
    })
    monkeypatch.setattr(service.repo, 'obtener_pago_por_sesion', lambda _: deepcopy(pago))
    aplicar = Mock(side_effect=AssertionError('No debe modificar CU33.'))
    monkeypatch.setattr(service.repo, 'aplicar_pago_confirmado', aplicar)
    monkeypatch.setattr(service.repo, 'marcar_pago_terminal', lambda session, evento, nuevo, status: {
        **pago, 'estado': nuevo,
    })
    resultado = service.procesar_webhook(b'evento', 'firma')
    assert resultado['estado'] == estado and resultado['aplicado'] is False
    aplicar.assert_not_called()


def test_verificacion_admin_y_tenant_propietario_consultan_stripe(monkeypatch):
    pago = pago_hu125()
    usuarios = {
        1: {'id_usuario': 1, 'id_empresa': 1, 'estado': 'ACTIVO', 'nombre_rol': 'ADMINISTRADOR'},
        30: {'id_usuario': 30, 'id_empresa': 3, 'estado': 'ACTIVO', 'nombre_rol': 'ADMINISTRADOR_EMPRESA'},
    }
    monkeypatch.setattr(service.repo, 'obtener_usuario', lambda nro: usuarios[nro])
    monkeypatch.setattr(service.repo, 'obtener_pago', lambda _: deepcopy(pago))
    consultar = Mock(return_value=confirmacion_pago())
    monkeypatch.setattr(service.stripe_gateway, 'consultar_checkout', consultar)
    monkeypatch.setattr(service.repo, 'aplicar_pago_confirmado', lambda *args: (
        {**pago, 'estado': 'CONFIRMADO', 'tipo_aplicacion': 'RENOVACION'}, True))
    resultado = service.verificar_pago(ADMIN, 10)
    assert resultado == {'id_pago': 10, 'estado': 'CONFIRMADO', 'tipo_aplicacion': 'RENOVACION', 'aplicado': True}
    resultado_tenant = service.verificar_pago(EMPRESA, 10)
    assert resultado_tenant['estado'] == 'CONFIRMADO'
    assert consultar.call_count == 2


def test_verificacion_tenant_rechaza_pago_de_otra_empresa_antes_de_stripe(monkeypatch):
    pago = {**pago_hu125(), 'id_empresa': 4}
    monkeypatch.setattr(service.repo, 'obtener_usuario', lambda _: {
        'id_usuario': 30, 'id_empresa': 3, 'estado': 'ACTIVO', 'nombre_rol': 'ADMINISTRADOR_EMPRESA',
    })
    monkeypatch.setattr(service.repo, 'obtener_pago', lambda _: deepcopy(pago))
    consultar = Mock(side_effect=AssertionError('No debe consultar Stripe para otro tenant.'))
    monkeypatch.setattr(service.stripe_gateway, 'consultar_checkout', consultar)
    with pytest.raises(HTTPException) as error:
        service.verificar_pago(EMPRESA, 10)
    assert error.value.status_code == 403
    consultar.assert_not_called()


def test_validacion_stripe_contrasta_snapshot_completo():
    pago_repos._validar_confirmacion(pago_hu125(), confirmacion_pago())
    with pytest.raises(pago_repos.PagoConflicto):
        pago_repos._validar_confirmacion(pago_hu125(), confirmacion_pago(amount_total=1))


def test_reglas_renovacion_contratacion_y_cambio_plan():
    hoy = date(2026, 10, 25)
    pago = pago_hu125()
    renovacion = pago_repos.calcular_aplicacion({
        'codigo_plan': 'PROFESIONAL', 'estado': 'ACTIVA',
        'fecha_inicio': date(2026, 9, 25), 'fecha_fin': date(2026, 11, 24),
    }, pago, hoy)
    abierta = pago_repos.calcular_aplicacion({
        'codigo_plan': 'PROFESIONAL', 'estado': 'ACTIVA',
        'fecha_inicio': date(2026, 9, 25), 'fecha_fin': None,
    }, pago, hoy)
    contratacion = pago_repos.calcular_aplicacion({
        'codigo_plan': 'PROFESIONAL', 'estado': 'CANCELADA',
        'fecha_inicio': date(2026, 9, 25), 'fecha_fin': date(2026, 10, 24),
    }, pago, hoy)
    cambio = pago_repos.calcular_aplicacion({
        'codigo_plan': 'BASICO', 'estado': 'ACTIVA',
        'fecha_inicio': date(2026, 9, 25), 'fecha_fin': date(2026, 11, 24),
    }, pago, hoy)
    assert renovacion == ('RENOVACION', date(2026, 9, 25), date(2026, 12, 24))
    assert abierta == ('RENOVACION', date(2026, 9, 25), date(2026, 11, 24))
    assert contratacion == ('CONTRATACION', hoy, date(2026, 11, 24))
    assert cambio == ('CAMBIO_PLAN', hoy, date(2026, 11, 24))


def test_gateway_verifica_firma_y_rechaza_evento_live(monkeypatch):
    construct = Mock(return_value={
        'id': 'evt_test_firma', 'type': 'checkout.session.completed', 'livemode': False,
        'data': {'object': {'id': 'cs_test_hu125'}},
    })
    monkeypatch.setattr(stripe_gateway, '_stripe_module', lambda: SimpleNamespace(
        Webhook=SimpleNamespace(construct_event=construct)))
    monkeypatch.setattr(stripe_gateway.Config, 'STRIPE_WEBHOOK_SECRET', 'whsec_sin_valor_real')
    evento = stripe_gateway.construir_evento(b'payload', 't=1,v1=firma')
    assert evento['id'] == 'evt_test_firma'
    construct.assert_called_once_with(payload=b'payload', sig_header='t=1,v1=firma', secret='whsec_sin_valor_real')
    construct.return_value = {**construct.return_value, 'livemode': True}
    with pytest.raises(stripe_gateway.StripeGatewayError) as error:
        stripe_gateway.construir_evento(b'payload', 't=1,v1=firma')
    assert error.value.codigo == 'STRIPE_TEST_REQUERIDO'


def test_rutas_webhook_y_verificacion_admin(monkeypatch):
    app = FastAPI()
    app.include_router(pago_routes.router)
    app.dependency_overrides[verificar_token] = lambda: ADMIN
    webhook = Mock(return_value={'recibido': True, 'estado': 'PENDIENTE'})
    verificar = Mock(return_value={
        'id_pago': 10, 'estado': 'CONFIRMADO', 'tipo_aplicacion': 'RENOVACION', 'aplicado': True,
    })
    monkeypatch.setattr(service, 'procesar_webhook', webhook)
    monkeypatch.setattr(service, 'verificar_pago', verificar)
    with TestClient(app) as client:
        respuesta_webhook = client.post(
            '/api/pagos/webhooks/stripe', content=b'{"id":"evt_test"}',
            headers={'Stripe-Signature': 't=1,v1=firma', 'Content-Type': 'application/json'},
        )
        respuesta_verificacion = client.post('/api/pagos/10/verificar')
    assert respuesta_webhook.status_code == 200
    assert respuesta_verificacion.status_code == 200
    webhook.assert_called_once_with(b'{"id":"evt_test"}', 't=1,v1=firma')
    verificar.assert_called_once_with(ADMIN, 10)


def test_ruta_verificacion_acepta_administrador_empresa(monkeypatch):
    app = FastAPI()
    app.include_router(pago_routes.router)
    app.dependency_overrides[verificar_token] = lambda: EMPRESA
    verificar = Mock(return_value={
        'id_pago': 10, 'estado': 'CONFIRMADO', 'tipo_aplicacion': 'RENOVACION', 'aplicado': True,
    })
    monkeypatch.setattr(service, 'verificar_pago', verificar)
    with TestClient(app) as client:
        respuesta = client.post('/api/pagos/10/verificar')
    assert respuesta.status_code == 200
    verificar.assert_called_once_with(EMPRESA, 10)

