# app/repos/crm_repos.py
from app.config import Config

T_USER = Config.T_USER
T_ROL = Config.T_ROL
T_TRANSACCION = getattr(Config, 'T_TRANSACCION_COMERCIAL', 'transaccion_comercial')
CLIENT_ROLE_ID = getattr(Config, 'CLIENT_ROLE_ID', 4)

def get_all_crm_clients(db, id_empresa=None):
    query = f"""
        WITH resumen AS (
            SELECT 
                id_cliente,
                COUNT(*) AS total_transacciones,
                COALESCE(SUM(monto_total), 0) AS monto_total,
                MAX(fecha_hora) AS ultima_transaccion
            FROM {Config.SCHEMA}.{T_TRANSACCION}
            WHERE (%s IS NULL OR id_empresa = %s)
            GROUP BY id_cliente
        ),
        ultima AS (
            SELECT DISTINCT ON (id_cliente)
                id_cliente,
                nro_transaccion,
                tipo_transaccion,
                estado_transaccion,
                fecha_hora,
                monto_total
            FROM {Config.SCHEMA}.{T_TRANSACCION}
            WHERE (%s IS NULL OR id_empresa = %s)
            ORDER BY id_cliente, fecha_hora DESC, nro_transaccion DESC
        )
        SELECT
            u.id_usuario, u.user_name, u.documento_identidad, u.nombre_razon_social,
            u.direccion, u.correo, u.telefono, u.estado_cuenta, u.created_at,
            u.id_rol, r.nombre_rol AS rol, u.id_empresa,

            COALESCE(resumen.total_transacciones, 0) AS total_transacciones,
            COALESCE(resumen.monto_total, 0) AS monto_total,
            resumen.ultima_transaccion,

            ultima.nro_transaccion AS nro_ultima_transaccion,
            ultima.tipo_transaccion AS tipo_ultima_transaccion,
            ultima.estado_transaccion AS estado_ultima_transaccion,
            ultima.monto_total AS monto_ultima_transaccion

        FROM {Config.SCHEMA}.{T_USER} u
        INNER JOIN {Config.SCHEMA}.{T_ROL} r 
            ON r.id = u.id_rol
        LEFT JOIN resumen 
            ON resumen.id_cliente = u.id_usuario
        LEFT JOIN ultima 
            ON ultima.id_cliente = u.id_usuario
        WHERE 
            (
                u.id_rol = %s 
                OR UPPER(r.nombre_rol) LIKE '%%CLIENTE%%'
            )
            AND (%s IS NULL OR u.id_empresa = %s)
        ORDER BY 
            u.created_at DESC,
            u.id_usuario DESC
    """
    params = (
        id_empresa, id_empresa, id_empresa, id_empresa,
        CLIENT_ROLE_ID, id_empresa, id_empresa
    )
    return db.execute_query(query, params, fetchall=True)


def get_crm_client_by_id(db, id_usuario, id_empresa=None):
    query = f"""
        WITH resumen AS (
            SELECT 
                id_cliente,
                COUNT(*) AS total_transacciones,
                COALESCE(SUM(monto_total), 0) AS monto_total,
                MAX(fecha_hora) AS ultima_transaccion
            FROM {Config.SCHEMA}.{T_TRANSACCION}
            WHERE id_cliente = %s AND (%s IS NULL OR id_empresa = %s)
            GROUP BY id_cliente
        ),
        ultima AS (
            SELECT DISTINCT ON (id_cliente)
                id_cliente, nro_transaccion, tipo_transaccion,
                estado_transaccion, fecha_hora, monto_total
            FROM {Config.SCHEMA}.{T_TRANSACCION}
            WHERE id_cliente = %s AND (%s IS NULL OR id_empresa = %s)
            ORDER BY id_cliente, fecha_hora DESC, nro_transaccion DESC
        )
        SELECT
            u.id_usuario, u.user_name, u.documento_identidad, u.nombre_razon_social,
            u.direccion, u.correo, u.telefono, u.estado_cuenta, u.created_at,
            u.id_rol, r.nombre_rol AS rol, u.id_empresa,

            COALESCE(resumen.total_transacciones, 0) AS total_transacciones,
            COALESCE(resumen.monto_total, 0) AS monto_total,
            resumen.ultima_transaccion,

            ultima.nro_transaccion AS nro_ultima_transaccion,
            ultima.tipo_transaccion AS tipo_ultima_transaccion,
            ultima.estado_transaccion AS estado_ultima_transaccion,
            ultima.monto_total AS monto_ultima_transaccion

        FROM {Config.SCHEMA}.{T_USER} u
        INNER JOIN {Config.SCHEMA}.{T_ROL} r ON r.id = u.id_rol
        LEFT JOIN resumen ON resumen.id_cliente = u.id_usuario
        LEFT JOIN ultima ON ultima.id_cliente = u.id_usuario
        WHERE 
            u.id_usuario = %s
            AND (u.id_rol = %s OR UPPER(r.nombre_rol) LIKE '%%CLIENTE%%')
            AND (%s IS NULL OR u.id_empresa = %s)
        LIMIT 1
    """
    params = (
        id_usuario, id_empresa, id_empresa, id_usuario, id_empresa, id_empresa,
        id_usuario, CLIENT_ROLE_ID, id_empresa, id_empresa
    )
    return db.execute_query(query, params, fetchone=True)


def get_client_transactions(db, id_usuario, id_empresa=None, limit=50):
    query = f"""
        SELECT
            nro_transaccion, tipo_transaccion, estado_transaccion,
            fecha_hora, monto_total, id_cliente, id_supervisor_admin, id_empresa
        FROM {Config.SCHEMA}.{T_TRANSACCION}
        WHERE id_cliente = %s AND (%s IS NULL OR id_empresa = %s)
        ORDER BY fecha_hora DESC, nro_transaccion DESC
        LIMIT %s
    """
    return db.execute_query(query, (id_usuario, id_empresa, id_empresa, limit), fetchall=True)


def get_crm_general_stats(db, id_empresa=None):
    query = f"""
        SELECT
            COUNT(DISTINCT u.id_usuario) AS total_clientes,
            COUNT(DISTINCT CASE WHEN u.estado_cuenta = 'ACTIVO' THEN u.id_usuario END) AS clientes_activos,
            COUNT(DISTINCT CASE WHEN u.estado_cuenta <> 'ACTIVO' THEN u.id_usuario END) AS clientes_inactivos_sistema,
            COUNT(t.nro_transaccion) AS total_transacciones,
            COALESCE(SUM(t.monto_total), 0) AS monto_total_general,
            COALESCE(AVG(t.monto_total), 0) AS ticket_promedio
        FROM {Config.SCHEMA}.{T_USER} u
        INNER JOIN {Config.SCHEMA}.{T_ROL} r ON r.id = u.id_rol
        LEFT JOIN {Config.SCHEMA}.{T_TRANSACCION} t ON t.id_cliente = u.id_usuario
            AND (%s IS NULL OR t.id_empresa = %s)
        WHERE 
            (u.id_rol = %s OR UPPER(r.nombre_rol) LIKE '%%CLIENTE%%')
            AND (%s IS NULL OR u.id_empresa = %s)
    """
    params = (id_empresa, id_empresa, CLIENT_ROLE_ID, id_empresa, id_empresa)
    return db.execute_query(query, params, fetchone=True)