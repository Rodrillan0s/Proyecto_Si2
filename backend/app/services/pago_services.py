"""Casos de uso de CU37 Fase 1."""
from fastapi import HTTPException

from app.repos import pago_repos as repo
from app.services.payments import stripe_gateway


ROLES_CONSULTA = {'ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA'}
EVENTOS_STRIPE = {
    'checkout.session.completed',
    'checkout.session.async_payment_succeeded',
    'checkout.session.async_payment_failed',
    'checkout.session.expired',
}


def _usuario_actual(token):
    usuario = repo.obtener_usuario(token.get('nro_usuario'))
    if (not usuario or usuario.get('estado') != 'ACTIVO'
            or usuario.get('id_empresa') != token.get('id_empresa')
            or usuario.get('nombre_rol') != token.get('nombre_rol')):
        raise HTTPException(403, 'Su cuenta o contexto de empresa cambió. Inicie sesión nuevamente.')
    return usuario


def listar_planes(token):
    _usuario_actual(token)
    return repo.listar_planes_comerciales()


def _validar_clave(clave):
    clave = (clave or '').strip()
    if not 8 <= len(clave) <= 255 or any(c in clave for c in '\r\n'):
        raise HTTPException(422, 'Envía Idempotency-Key de 8 a 255 caracteres.')
    return clave


def _validar_reutilizacion(pago, empresa, codigo_plan):
    if pago['id_empresa'] != empresa or pago['codigo_plan'] != codigo_plan:
        raise HTTPException(409, 'La clave de idempotencia ya fue utilizada con otra operación.')


def _respuesta_checkout(pago):
    return {
        'id_pago': pago['id_pago'],
        'estado': pago['estado'],
        'checkout_url': pago.get('stripe_checkout_url'),
        'checkout_expira_en': pago.get('checkout_expira_en'),
    }


def iniciar_checkout(token, codigo_plan, idempotency_key):
    usuario = _usuario_actual(token)
    if usuario['nombre_rol'] != 'ADMINISTRADOR_EMPRESA':
        raise HTTPException(403, 'Solo el administrador de empresa puede iniciar el pago de su suscripción.')
    empresa = usuario.get('id_empresa')
    if not empresa:
        raise HTTPException(403, 'No tiene un contexto de empresa válido.')
    codigo_plan = (codigo_plan or '').strip().upper()
    clave = _validar_clave(idempotency_key)

    existente = repo.obtener_pago_por_idempotencia(clave)
    if existente:
        _validar_reutilizacion(existente, empresa, codigo_plan)
        if existente.get('stripe_checkout_session_id') or existente.get('estado') != 'PENDIENTE':
            return _respuesta_checkout(existente)

    precio = repo.obtener_precio(codigo_plan)
    if not precio:
        raise HTTPException(409, 'El plan no tiene una configuración comercial activa.')
    if not repo.existe_suscripcion(empresa):
        raise HTTPException(409, 'La empresa no tiene una suscripción de CU33 disponible para asociar el pago.')

    if existente:
        pago = existente
    else:
        pago, _ = repo.crear_pago_pendiente(empresa, precio, clave, usuario['id_usuario'])
        _validar_reutilizacion(pago, empresa, codigo_plan)
        if pago.get('stripe_checkout_session_id'):
            return _respuesta_checkout(pago)

    try:
        checkout = stripe_gateway.crear_checkout(pago, precio, clave)
    except stripe_gateway.StripeGatewayError as exc:
        repo.registrar_error_checkout(pago['id_pago'], exc.codigo, exc.mensaje)
        raise HTTPException(503, exc.mensaje)

    actualizado = repo.guardar_checkout(pago['id_pago'], checkout)
    if not actualizado:
        raise HTTPException(409, 'El pago cambió mientras se creaba la sesión. Consulte su estado antes de reintentar.')
    return _respuesta_checkout(actualizado)


def consultar_pago(token, id_pago):
    usuario = _usuario_actual(token)
    if usuario['nombre_rol'] not in ROLES_CONSULTA:
        raise HTTPException(403, 'No tiene permisos para consultar pagos de suscripción.')
    pago = repo.obtener_pago(id_pago)
    if not pago:
        raise HTTPException(404, 'Pago no encontrado.')
    if usuario['nombre_rol'] != 'ADMINISTRADOR' and pago['id_empresa'] != usuario['id_empresa']:
        raise HTTPException(403, 'No puede consultar pagos de otra empresa.')
    return pago


def listar_pagos_mi_empresa(token):
    usuario = _usuario_actual(token)
    if usuario['nombre_rol'] != 'ADMINISTRADOR_EMPRESA':
        raise HTTPException(403, 'Solo el administrador de empresa puede consultar su historial de pagos.')
    empresa = usuario.get('id_empresa')
    if not empresa:
        raise HTTPException(403, 'No tiene un contexto de empresa válido.')
    return repo.listar_pagos_empresa(empresa)


def consultar_comprobante(token, id_pago):
    usuario = _usuario_actual(token)
    if usuario['nombre_rol'] not in ROLES_CONSULTA:
        raise HTTPException(403, 'No tiene permisos para consultar comprobantes de pago.')
    comprobante = repo.obtener_comprobante(id_pago)
    if not comprobante:
        raise HTTPException(404, 'Pago no encontrado.')
    if (usuario['nombre_rol'] != 'ADMINISTRADOR'
            and comprobante['id_empresa'] != usuario['id_empresa']):
        raise HTTPException(403, 'No puede consultar comprobantes de otra empresa.')
    return {
        'id_pago': comprobante['id_pago'],
        'codigo_plan': comprobante['codigo_plan'],
        'nombre_plan': comprobante['nombre_plan'],
        'monto_menor': comprobante['monto_menor'],
        'moneda': comprobante['moneda'],
        'estado': comprobante['estado'],
        'confirmado_en': comprobante.get('confirmado_en'),
        'stripe_checkout_session_id': comprobante.get('stripe_checkout_session_id'),
        'stripe_payment_intent_id': comprobante.get('stripe_payment_intent_id'),
        'stripe_receipt_url': comprobante.get('stripe_receipt_url'),
    }


def _valor(objeto, nombre, defecto=None):
    if isinstance(objeto, dict):
        return objeto.get(nombre, defecto)
    return getattr(objeto, nombre, defecto)


def _traducir_error_repo(exc):
    if isinstance(exc, repo.PagoNoEncontrado):
        raise HTTPException(404, str(exc))
    if isinstance(exc, repo.PagoConflicto):
        raise HTTPException(409, str(exc))
    raise exc


def _aplicar_confirmacion(pago, confirmacion, evento_id=None, verificado_por=None):
    try:
        resultado, aplicado = repo.aplicar_pago_confirmado(
            pago['id_pago'], confirmacion, evento_id, verificado_por)
    except (repo.PagoNoEncontrado, repo.PagoConflicto) as exc:
        _traducir_error_repo(exc)
    return {'id_pago': resultado['id_pago'], 'estado': resultado['estado'],
            'tipo_aplicacion': resultado.get('tipo_aplicacion'), 'aplicado': aplicado}


def procesar_webhook(payload, firma):
    try:
        evento = stripe_gateway.construir_evento(payload, firma)
    except stripe_gateway.StripeGatewayError as exc:
        raise HTTPException(400, exc.mensaje)
    if evento['tipo'] not in EVENTOS_STRIPE:
        return {'recibido': True, 'ignorado': True, 'tipo': evento['tipo']}

    session = evento['objeto']
    session_id = _valor(session, 'id')
    if (not isinstance(session_id, str) or not session_id.startswith('cs_test_')
            or _valor(session, 'livemode') is not False):
        raise HTTPException(400, 'La sesión del evento no pertenece al modo prueba.')
    pago = repo.obtener_pago_por_sesion(session_id)
    if not pago:
        raise HTTPException(404, 'No existe un pago local para la sesión Stripe.')

    if evento['tipo'] == 'checkout.session.async_payment_failed':
        try:
            resultado = repo.marcar_pago_terminal(
                session_id, evento['id'], 'FALLIDO', _valor(session, 'payment_status') or 'unpaid')
        except (repo.PagoNoEncontrado, repo.PagoConflicto) as exc:
            _traducir_error_repo(exc)
        return {'recibido': True, 'id_pago': resultado['id_pago'], 'estado': resultado['estado'], 'aplicado': False}

    if evento['tipo'] == 'checkout.session.expired':
        try:
            resultado = repo.marcar_pago_terminal(
                session_id, evento['id'], 'CANCELADO', _valor(session, 'payment_status') or 'unpaid')
        except (repo.PagoNoEncontrado, repo.PagoConflicto) as exc:
            _traducir_error_repo(exc)
        return {'recibido': True, 'id_pago': resultado['id_pago'], 'estado': resultado['estado'], 'aplicado': False}

    if _valor(session, 'payment_status') != 'paid':
        repo.actualizar_pago_pendiente(session_id, _valor(session, 'payment_status') or 'unpaid')
        return {'recibido': True, 'id_pago': pago['id_pago'], 'estado': 'PENDIENTE', 'aplicado': False}

    try:
        confirmacion = stripe_gateway.confirmar_desde_evento(session)
    except stripe_gateway.StripeGatewayError as exc:
        raise HTTPException(503, exc.mensaje)
    return {'recibido': True, **_aplicar_confirmacion(pago, confirmacion, evento['id'])}


def verificar_pago(token, id_pago):
    usuario = _usuario_actual(token)
    if usuario['nombre_rol'] not in ROLES_CONSULTA:
        raise HTTPException(403, 'No tiene permisos para verificar pagos.')
    pago = repo.obtener_pago(id_pago)
    if not pago:
        raise HTTPException(404, 'Pago no encontrado.')
    if (usuario['nombre_rol'] == 'ADMINISTRADOR_EMPRESA'
            and pago['id_empresa'] != usuario['id_empresa']):
        raise HTTPException(403, 'No puede verificar pagos de otra empresa.')
    if pago['estado'] not in ('PENDIENTE', 'CONFIRMADO'):
        raise HTTPException(409, 'El pago ya se encuentra en un estado terminal.')
    if not pago.get('stripe_checkout_session_id'):
        raise HTTPException(409, 'El pago no tiene una sesión Stripe para verificar.')
    try:
        confirmacion = stripe_gateway.consultar_checkout(pago['stripe_checkout_session_id'])
    except stripe_gateway.StripeGatewayError as exc:
        raise HTTPException(503, exc.mensaje)
    if (confirmacion.get('payment_status') != 'paid'
            or confirmacion.get('payment_intent_status') != 'succeeded'):
        raise HTTPException(409, 'Stripe todavía no confirma el pago como exitoso.')
    return _aplicar_confirmacion(pago, confirmacion, verificado_por=usuario['id_usuario'])

