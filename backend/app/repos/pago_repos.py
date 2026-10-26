"""Persistencia de CU37. No contiene reglas de Stripe ni de autorización."""
from calendar import monthrange
from contextlib import contextmanager
from datetime import date, timedelta

from psycopg2.extras import RealDictCursor

from app.classes.postgres import PostgreSQL


PAGO_PUBLICO = """id_pago,id_empresa,codigo_plan,version_precio,monto_menor,moneda,
    periodo_meses,estado,tipo_aplicacion,stripe_checkout_session_id,
    stripe_payment_intent_id,stripe_evento_confirmacion_id,stripe_checkout_url,stripe_receipt_url,
    stripe_payment_status,stripe_livemode,checkout_expira_en,iniciado_por,
    verificado_por,id_historial_suscripcion,error_codigo,error_detalle,
    creado_en,actualizado_en,confirmado_en,aplicado_en"""


class PagoNoEncontrado(RuntimeError):
    pass


class PagoConflicto(RuntimeError):
    pass


def _sumar_meses(valor, meses):
    indice = valor.month - 1 + meses
    anio = valor.year + indice // 12
    mes = indice % 12 + 1
    return date(anio, mes, min(valor.day, monthrange(anio, mes)[1]))


def calcular_aplicacion(suscripcion, pago, hoy):
    """Regla pura usada dentro de la transacción bloqueada."""
    meses = pago['periodo_meses']
    mismo_plan = suscripcion['codigo_plan'] == pago['codigo_plan']
    if not mismo_plan:
        return 'CAMBIO_PLAN', hoy, _sumar_meses(hoy, meses) - timedelta(days=1)
    if suscripcion['estado'] != 'ACTIVA':
        return 'CONTRATACION', hoy, _sumar_meses(hoy, meses) - timedelta(days=1)
    fin = suscripcion.get('fecha_fin')
    nuevo_fin = _sumar_meses(fin, meses) if fin and fin >= hoy else _sumar_meses(hoy, meses) - timedelta(days=1)
    return 'RENOVACION', suscripcion['fecha_inicio'], nuevo_fin


@contextmanager
def conexion():
    db = PostgreSQL()
    db.create_connection()
    try:
        with db.conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        db.conn.commit()
    finally:
        db.close_connection()


def listar_planes_comerciales():
    with conexion() as cur:
        cur.execute("""
            SELECT p.codigo,p.nombre,p.descripcion,pc.precio_menor,pc.moneda,
                   pc.periodo_meses,pc.version AS version_precio
            FROM obras.t_plan_suscripcion p
            JOIN obras.t_plan_precio_saas pc ON pc.codigo_plan=p.codigo
            WHERE pc.activo=true
            ORDER BY p.orden
        """)
        return [dict(row) for row in cur.fetchall()]


def obtener_usuario(id_usuario):
    with conexion() as cur:
        cur.execute("""
            SELECT u.id_usuario,u.id_empresa,u.estado,r.nombre_rol
            FROM obras.t_usuario u
            LEFT JOIN obras.t_rol r USING(id_rol)
            WHERE u.id_usuario=%s
        """, (id_usuario,))
        row = cur.fetchone()
        return dict(row) if row else None


def obtener_precio(codigo_plan):
    with conexion() as cur:
        cur.execute("""
            SELECT p.codigo,p.nombre,p.descripcion,pc.precio_menor,pc.moneda,
                   pc.periodo_meses,pc.version AS version_precio
            FROM obras.t_plan_suscripcion p
            JOIN obras.t_plan_precio_saas pc ON pc.codigo_plan=p.codigo
            WHERE p.codigo=%s AND pc.activo=true
        """, (codigo_plan,))
        row = cur.fetchone()
        return dict(row) if row else None


def existe_suscripcion(id_empresa):
    with conexion() as cur:
        cur.execute('SELECT 1 FROM obras.t_suscripcion_empresa WHERE id_empresa=%s', (id_empresa,))
        return cur.fetchone() is not None


def obtener_pago_por_idempotencia(idempotency_key):
    with conexion() as cur:
        cur.execute(f"SELECT {PAGO_PUBLICO} FROM obras.t_pago_suscripcion WHERE idempotency_key=%s",
                    (idempotency_key,))
        row = cur.fetchone()
        return dict(row) if row else None


def crear_pago_pendiente(id_empresa, precio, idempotency_key, iniciado_por):
    """Inserta una vez. Devuelve (pago, creado) ante carreras de la misma clave."""
    with conexion() as cur:
        cur.execute(f"""
            INSERT INTO obras.t_pago_suscripcion
                (id_empresa,codigo_plan,version_precio,monto_menor,moneda,
                 periodo_meses,estado,idempotency_key,checkout_expira_en,iniciado_por)
            VALUES (%s,%s,%s,%s,%s,%s,'PENDIENTE',%s,
                    CURRENT_TIMESTAMP + INTERVAL '35 minutes',%s)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING {PAGO_PUBLICO}
        """, (id_empresa, precio['codigo'], precio['version_precio'],
              precio['precio_menor'], precio['moneda'], precio['periodo_meses'],
              idempotency_key, iniciado_por))
        row = cur.fetchone()
        if row:
            return dict(row), True
        cur.execute(f"SELECT {PAGO_PUBLICO} FROM obras.t_pago_suscripcion WHERE idempotency_key=%s",
                    (idempotency_key,))
        return dict(cur.fetchone()), False


def guardar_checkout(id_pago, checkout):
    with conexion() as cur:
        cur.execute(f"""
            UPDATE obras.t_pago_suscripcion
            SET stripe_checkout_session_id=%s,stripe_checkout_url=%s,
                stripe_payment_status=%s,stripe_livemode=%s,checkout_expira_en=%s,
                error_codigo=NULL,error_detalle=NULL,actualizado_en=CURRENT_TIMESTAMP
            WHERE id_pago=%s AND estado='PENDIENTE'
              AND (stripe_checkout_session_id IS NULL OR stripe_checkout_session_id=%s)
            RETURNING {PAGO_PUBLICO}
        """, (checkout['session_id'], checkout['url'], checkout['payment_status'],
              checkout['livemode'], checkout['expires_at'], id_pago, checkout['session_id']))
        row = cur.fetchone()
        return dict(row) if row else None


def registrar_error_checkout(id_pago, codigo, detalle):
    with conexion() as cur:
        cur.execute("""
            UPDATE obras.t_pago_suscripcion
            SET error_codigo=%s,error_detalle=%s,actualizado_en=CURRENT_TIMESTAMP
            WHERE id_pago=%s AND estado='PENDIENTE'
        """, (codigo, detalle[:1000], id_pago))


def obtener_pago(id_pago):
    with conexion() as cur:
        cur.execute(f"SELECT {PAGO_PUBLICO} FROM obras.t_pago_suscripcion WHERE id_pago=%s", (id_pago,))
        row = cur.fetchone()
        return dict(row) if row else None


def listar_pagos_empresa(id_empresa):
    with conexion() as cur:
        cur.execute("""
            SELECT pg.id_pago,pg.codigo_plan,pl.nombre AS nombre_plan,
                   pg.monto_menor,pg.moneda,pg.estado,pg.creado_en AS fecha,
                   pg.confirmado_en,
                   pg.stripe_checkout_session_id,pg.stripe_payment_intent_id,
                   pg.stripe_checkout_url,pg.stripe_receipt_url
            FROM obras.t_pago_suscripcion pg
            JOIN obras.t_plan_suscripcion pl ON pl.codigo=pg.codigo_plan
            WHERE pg.id_empresa=%s
            ORDER BY pg.creado_en DESC,pg.id_pago DESC
        """, (id_empresa,))
        return [dict(row) for row in cur.fetchall()]


def obtener_comprobante(id_pago):
    with conexion() as cur:
        cur.execute("""
            SELECT pg.id_pago,pg.id_empresa,pg.codigo_plan,
                   pl.nombre AS nombre_plan,pg.monto_menor,pg.moneda,
                   pg.estado,pg.confirmado_en,pg.stripe_checkout_session_id,
                   pg.stripe_payment_intent_id,pg.stripe_receipt_url
            FROM obras.t_pago_suscripcion pg
            JOIN obras.t_plan_suscripcion pl ON pl.codigo=pg.codigo_plan
            WHERE pg.id_pago=%s
        """, (id_pago,))
        row = cur.fetchone()
        return dict(row) if row else None


def obtener_pago_por_sesion(session_id):
    with conexion() as cur:
        cur.execute(f"SELECT {PAGO_PUBLICO} FROM obras.t_pago_suscripcion WHERE stripe_checkout_session_id=%s",
                    (session_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def actualizar_pago_pendiente(session_id, payment_status):
    with conexion() as cur:
        cur.execute(f"""
            UPDATE obras.t_pago_suscripcion
            SET stripe_payment_status=%s,actualizado_en=CURRENT_TIMESTAMP
            WHERE stripe_checkout_session_id=%s AND estado='PENDIENTE'
            RETURNING {PAGO_PUBLICO}
        """, (payment_status, session_id))
        row = cur.fetchone()
        return dict(row) if row else obtener_pago_por_sesion(session_id)


def marcar_pago_terminal(session_id, evento_id, estado, payment_status):
    if estado not in ('FALLIDO', 'CANCELADO'):
        raise ValueError('Estado terminal de pago inválido.')
    with conexion() as cur:
        cur.execute('''SELECT * FROM obras.t_pago_suscripcion
                       WHERE stripe_checkout_session_id=%s FOR UPDATE''', (session_id,))
        pago = cur.fetchone()
        if not pago:
            raise PagoNoEncontrado('No existe un pago para la sesión Stripe.')
        pago = dict(pago)
        if pago['estado'] == 'CONFIRMADO' or pago['estado'] in ('FALLIDO', 'CANCELADO'):
            return pago
        codigo = 'STRIPE_ASYNC_PAYMENT_FAILED' if estado == 'FALLIDO' else 'STRIPE_CHECKOUT_EXPIRED'
        detalle = 'Stripe informó que el pago falló.' if estado == 'FALLIDO' else 'La sesión de Checkout expiró.'
        cur.execute(f"""UPDATE obras.t_pago_suscripcion
            SET estado=%s,stripe_evento_confirmacion_id=%s,stripe_payment_status=%s,
                error_codigo=%s,error_detalle=%s,actualizado_en=CURRENT_TIMESTAMP
            WHERE id_pago=%s RETURNING {PAGO_PUBLICO}
        """, (estado, evento_id, payment_status, codigo, detalle, pago['id_pago']))
        return dict(cur.fetchone())


def _validar_confirmacion(pago, confirmacion):
    metadata = confirmacion.get('metadata') or {}
    metadata_pi = confirmacion.get('payment_intent_metadata') or {}
    esperado = {
        'id_pago': str(pago['id_pago']),
        'id_empresa': str(pago['id_empresa']),
        'codigo_plan': pago['codigo_plan'],
        'version_precio': str(pago['version_precio']),
    }
    if confirmacion.get('session_id') != pago['stripe_checkout_session_id']:
        raise PagoConflicto('La sesión Stripe no coincide con el pago local.')
    if str(confirmacion.get('client_reference_id')) != str(pago['id_pago']):
        raise PagoConflicto('La referencia de Stripe no coincide con el pago local.')
    if any(str(metadata.get(clave)) != valor for clave, valor in esperado.items()):
        raise PagoConflicto('La metadata de Checkout no coincide con el pago local.')
    if any(str(metadata_pi.get(clave)) != valor for clave, valor in esperado.items()):
        raise PagoConflicto('La metadata del PaymentIntent no coincide con el pago local.')
    if confirmacion.get('amount_total') != pago['monto_menor']:
        raise PagoConflicto('El monto de Checkout no coincide con el pago local.')
    if confirmacion.get('payment_intent_amount_received') != pago['monto_menor']:
        raise PagoConflicto('El monto recibido por Stripe no coincide con el pago local.')
    moneda = pago['moneda'].lower()
    if ((confirmacion.get('currency') or '').lower() != moneda
            or (confirmacion.get('payment_intent_currency') or '').lower() != moneda):
        raise PagoConflicto('La moneda de Stripe no coincide con el pago local.')
    payment_intent = confirmacion.get('payment_intent_id')
    if not isinstance(payment_intent, str) or not payment_intent.startswith('pi_'):
        raise PagoConflicto('Stripe no informó un PaymentIntent válido.')
    if pago.get('stripe_payment_intent_id') not in (None, payment_intent):
        raise PagoConflicto('El PaymentIntent no coincide con el registrado previamente.')
    if (confirmacion.get('payment_status') != 'paid'
            or confirmacion.get('payment_intent_status') != 'succeeded'
            or confirmacion.get('livemode') is not False):
        raise PagoConflicto('Stripe no confirma un pago exitoso en modo prueba.')


def aplicar_pago_confirmado(id_pago, confirmacion, evento_id=None, verificado_por=None):
    with conexion() as cur:
        cur.execute('SELECT * FROM obras.t_pago_suscripcion WHERE id_pago=%s FOR UPDATE', (id_pago,))
        pago = cur.fetchone()
        if not pago:
            raise PagoNoEncontrado('Pago no encontrado.')
        pago = dict(pago)
        if pago['estado'] == 'CONFIRMADO' and pago.get('id_historial_suscripcion'):
            return pago, False
        if pago['estado'] != 'PENDIENTE':
            raise PagoConflicto('El pago ya se encuentra en un estado terminal.')
        _validar_confirmacion(pago, confirmacion)

        cur.execute('''SELECT id_empresa,codigo_plan,estado,fecha_inicio,fecha_fin
                       FROM obras.t_suscripcion_empresa WHERE id_empresa=%s FOR UPDATE''',
                    (pago['id_empresa'],))
        suscripcion = cur.fetchone()
        if not suscripcion:
            raise PagoNoEncontrado('La suscripción asociada ya no existe.')
        suscripcion = dict(suscripcion)
        cur.execute("SELECT (CURRENT_TIMESTAMP AT TIME ZONE 'America/La_Paz')::date AS hoy")
        hoy = cur.fetchone()['hoy']
        tipo, fecha_inicio, fecha_fin = calcular_aplicacion(suscripcion, pago, hoy)
        actor = verificado_por or pago.get('iniciado_por')

        cur.execute('''UPDATE obras.t_suscripcion_empresa
            SET codigo_plan=%s,estado='ACTIVA',fecha_inicio=%s,fecha_fin=%s,
                actualizado_por=%s,actualizado_en=CURRENT_TIMESTAMP
            WHERE id_empresa=%s
        ''', (pago['codigo_plan'], fecha_inicio, fecha_fin, actor, pago['id_empresa']))
        cur.execute('''INSERT INTO obras.t_suscripcion_historial
            (id_empresa,codigo_plan,estado,fecha_inicio,fecha_fin,id_actor,origen)
            VALUES (%s,%s,'ACTIVA',%s,%s,%s,'PAGO_STRIPE') RETURNING id
        ''', (pago['id_empresa'], pago['codigo_plan'], fecha_inicio, fecha_fin, actor))
        historial_id = cur.fetchone()['id']
        cur.execute(f"""UPDATE obras.t_pago_suscripcion
            SET estado='CONFIRMADO',tipo_aplicacion=%s,
                stripe_payment_intent_id=%s,stripe_evento_confirmacion_id=%s,
                stripe_receipt_url=%s,stripe_payment_status=%s,stripe_livemode=false,
                verificado_por=%s,id_historial_suscripcion=%s,
                error_codigo=NULL,error_detalle=NULL,confirmado_en=CURRENT_TIMESTAMP,
                aplicado_en=CURRENT_TIMESTAMP,actualizado_en=CURRENT_TIMESTAMP
            WHERE id_pago=%s RETURNING {PAGO_PUBLICO}
        """, (tipo, confirmacion['payment_intent_id'], evento_id,
              confirmacion.get('receipt_url'), confirmacion['payment_status'],
              verificado_por, historial_id, pago['id_pago']))
        return dict(cur.fetchone()), True

