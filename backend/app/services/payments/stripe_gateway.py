"""Adaptador mínimo de Stripe Checkout. CU37 está restringido a Test Mode."""
from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import threading

from app.config import Config


_TLS_CONFIGURADO = False
_TLS_LOCK = threading.Lock()


class StripeGatewayError(RuntimeError):
    def __init__(self, codigo, mensaje):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


def _configurar_tls():
    """Integra las CA confiables del sistema sin relajar la validación TLS."""
    global _TLS_CONFIGURADO
    if _TLS_CONFIGURADO:
        return
    with _TLS_LOCK:
        if _TLS_CONFIGURADO:
            return
        try:
            import truststore
            truststore.inject_into_ssl()
        except ImportError as exc:
            raise StripeGatewayError(
                'STRIPE_CA_NO_DISPONIBLE',
                'No está disponible el almacén seguro de certificados para Stripe.',
            ) from exc
        _TLS_CONFIGURADO = True


def _stripe_module():
    _configurar_tls()
    try:
        import stripe
        return stripe
    except ImportError as exc:
        raise StripeGatewayError('STRIPE_SDK_NO_DISPONIBLE', 'El SDK de Stripe no está instalado.') from exc


def _configuracion():
    secret = _clave_secreta()
    success_url = (Config.STRIPE_SUCCESS_URL or '').strip()
    cancel_url = (Config.STRIPE_CANCEL_URL or '').strip()
    if not success_url or not cancel_url:
        raise StripeGatewayError('STRIPE_URLS_REQUERIDAS', 'Configure las URL de éxito y cancelación de Stripe.')
    return secret, success_url, cancel_url


def _clave_secreta():
    secret = (Config.STRIPE_SECRET_KEY or '').strip()
    if not secret.startswith('sk_test_'):
        raise StripeGatewayError('STRIPE_TEST_REQUERIDO', 'Stripe debe configurarse con una clave secreta de prueba.')
    return secret


def _valor(objeto, nombre, defecto=None):
    if isinstance(objeto, dict):
        return objeto.get(nombre, defecto)
    return getattr(objeto, nombre, defecto)


def _diccionario(objeto):
    if objeto is None:
        return {}
    if isinstance(objeto, Mapping):
        return dict(objeto)
    for nombre in ('to_dict_recursive', '_to_dict_recursive'):
        convertir = getattr(objeto, nombre, None)
        if callable(convertir):
            convertido = convertir()
            return dict(convertido) if isinstance(convertido, Mapping) else {}
    try:
        return dict(objeto)
    except (TypeError, ValueError):
        return {}


def construir_evento(payload, firma):
    stripe = _stripe_module()
    secreto = (Config.STRIPE_WEBHOOK_SECRET or '').strip()
    if not secreto:
        raise StripeGatewayError('STRIPE_WEBHOOK_NO_CONFIGURADO', 'El secreto del webhook de Stripe no está configurado.')
    try:
        evento = stripe.Webhook.construct_event(payload=payload, sig_header=firma, secret=secreto)
    except Exception as exc:
        raise StripeGatewayError('STRIPE_FIRMA_INVALIDA', 'La firma del webhook de Stripe no es válida.') from exc
    if _valor(evento, 'livemode') is not False:
        raise StripeGatewayError('STRIPE_TEST_REQUERIDO', 'El evento no pertenece al modo prueba.')
    evento_id = _valor(evento, 'id')
    tipo = _valor(evento, 'type')
    datos = _valor(_valor(evento, 'data', {}), 'object')
    if not evento_id or not tipo or datos is None:
        raise StripeGatewayError('STRIPE_EVENTO_INVALIDO', 'El evento de Stripe está incompleto.')
    return {'id': evento_id, 'tipo': tipo, 'objeto': datos}


def _normalizar_confirmacion(session, payment_intent=None):
    session_id = _valor(session, 'id')
    if (not isinstance(session_id, str) or not session_id.startswith('cs_test_')
            or _valor(session, 'livemode') is not False):
        raise StripeGatewayError('STRIPE_TEST_REQUERIDO', 'La sesión no pertenece al modo prueba.')
    pi = payment_intent if payment_intent is not None else _valor(session, 'payment_intent')
    pi_id = _valor(pi, 'id') if not isinstance(pi, str) else pi
    metadata_pi = _diccionario(_valor(pi, 'metadata')) if not isinstance(pi, str) else {}
    charge = _valor(pi, 'latest_charge') if not isinstance(pi, str) else None
    receipt_url = _valor(charge, 'receipt_url') if charge and not isinstance(charge, str) else None
    return {
        'session_id': session_id,
        'livemode': False,
        'payment_status': _valor(session, 'payment_status'),
        'amount_total': _valor(session, 'amount_total'),
        'currency': _valor(session, 'currency'),
        'client_reference_id': _valor(session, 'client_reference_id'),
        'metadata': _diccionario(_valor(session, 'metadata')),
        'payment_intent_id': pi_id,
        'payment_intent_status': _valor(pi, 'status') if not isinstance(pi, str) else None,
        'payment_intent_amount_received': _valor(pi, 'amount_received') if not isinstance(pi, str) else None,
        'payment_intent_currency': _valor(pi, 'currency') if not isinstance(pi, str) else None,
        'payment_intent_metadata': metadata_pi,
        'receipt_url': receipt_url,
    }


def consultar_checkout(session_id):
    if not isinstance(session_id, str) or not session_id.startswith('cs_test_'):
        raise StripeGatewayError('STRIPE_TEST_REQUERIDO', 'La sesión local no pertenece al modo prueba.')
    stripe = _stripe_module()
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            api_key=_clave_secreta(),
            expand=['payment_intent.latest_charge'],
        )
    except Exception as exc:
        raise StripeGatewayError('STRIPE_VERIFICACION_ERROR', 'Stripe no pudo verificar la sesión de pago.') from exc
    return _normalizar_confirmacion(session)


def confirmar_desde_evento(session):
    stripe = _stripe_module()
    payment_intent = _valor(session, 'payment_intent')
    payment_intent_id = _valor(payment_intent, 'id') if not isinstance(payment_intent, str) else payment_intent
    if not payment_intent_id:
        raise StripeGatewayError('STRIPE_PAYMENT_INTENT_REQUERIDO', 'Stripe no informó el PaymentIntent del pago.')
    try:
        payment_intent = stripe.PaymentIntent.retrieve(
            payment_intent_id,
            api_key=_clave_secreta(),
            expand=['latest_charge'],
        )
    except Exception as exc:
        raise StripeGatewayError('STRIPE_VERIFICACION_ERROR', 'Stripe no pudo verificar el PaymentIntent.') from exc
    return _normalizar_confirmacion(session, payment_intent)


def crear_checkout(pago, plan, idempotency_key):
    stripe = _stripe_module()
    secret, success_url, cancel_url = _configuracion()
    expires_at = pago.get('checkout_expira_en')
    if not isinstance(expires_at, datetime):
        raise StripeGatewayError(
            'STRIPE_EXPIRACION_REQUERIDA',
            'El pago no tiene una expiración estable para crear Checkout.',
        )
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    metadata = {
        'id_pago': str(pago['id_pago']),
        'id_empresa': str(pago['id_empresa']),
        'codigo_plan': pago['codigo_plan'],
        'version_precio': str(pago['version_precio']),
    }
    stripe_key = 'cu37-' + hashlib.sha256(idempotency_key.encode('utf-8')).hexdigest()
    try:
        session = stripe.checkout.Session.create(
            api_key=secret,
            idempotency_key=stripe_key,
            mode='payment',
            client_reference_id=str(pago['id_pago']),
            metadata=metadata,
            payment_intent_data={'metadata': metadata},
            line_items=[{
                'quantity': 1,
                'price_data': {
                    'currency': pago['moneda'].lower(),
                    'unit_amount': pago['monto_menor'],
                    'product_data': {
                        'name': f"Plan {plan['nombre']}",
                        'description': plan.get('descripcion') or 'Suscripción SaaS OBRATEC',
                    },
                },
            }],
            invoice_creation={'enabled': True},
            success_url=success_url,
            cancel_url=cancel_url,
            expires_at=int(expires_at.timestamp()),
        )
    except StripeGatewayError:
        raise
    except Exception as exc:
        raise StripeGatewayError('STRIPE_CHECKOUT_ERROR', 'Stripe no pudo crear la sesión de pago de prueba.') from exc

    session_id = _valor(session, 'id')
    livemode = _valor(session, 'livemode')
    url = _valor(session, 'url')
    if not isinstance(session_id, str) or not session_id.startswith('cs_test_') or livemode is not False:
        raise StripeGatewayError('STRIPE_TEST_REQUERIDO', 'Stripe devolvió una sesión que no pertenece al modo prueba.')
    if not url:
        raise StripeGatewayError('STRIPE_CHECKOUT_SIN_URL', 'Stripe no devolvió una URL de Checkout.')
    expiration = _valor(session, 'expires_at')
    if expiration:
        expires_at = datetime.fromtimestamp(int(expiration), timezone.utc)
    return {
        'session_id': session_id,
        'url': url,
        'expires_at': expires_at,
        'payment_status': _valor(session, 'payment_status', 'unpaid'),
        'livemode': False,
    }

