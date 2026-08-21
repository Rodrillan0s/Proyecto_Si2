from app.config import Config

def get_niveles(db, id_empresa):
    query = f"""
        SELECT n.id_nivel, n.nombre_nivel, n.descripcion, n.min_transacciones,
               n.min_monto_acumulado, n.prioridad, n.estado, n.id_empresa,
               r.id_regla, r.tipo_transaccion, r.porcentaje_descuento,
               r.monto_max_descuento, r.vigencia_desde, r.vigencia_hasta,
               r.estado AS estado_regla
        FROM {Config.SCHEMA}.{Config.T_NIVEL_FIDELIZACION} n
        LEFT JOIN {Config.SCHEMA}.{Config.T_REGLA_FIDELIZACION} r ON r.id_nivel = n.id_nivel
        WHERE n.id_empresa = %s
        ORDER BY n.prioridad DESC, n.id_nivel DESC
    """
    return db.execute_query(query, (id_empresa,), fetchall=True)

def insert_nivel(db, data):
    query = f"""
        INSERT INTO {Config.SCHEMA}.{Config.T_NIVEL_FIDELIZACION}
        (nombre_nivel, descripcion, min_transacciones, min_monto_acumulado,
         prioridad, estado, id_empresa)
        VALUES (%s, %s, %s, %s, %s, 'ACTIVO', %s)
        RETURNING id_nivel
    """
    return db.execute_query(query, (
        data.get('nombre_nivel'), data.get('descripcion'), data.get('min_transacciones'),
        data.get('min_monto_acumulado'), data.get('prioridad'), data.get('id_empresa')
    ), fetchone=True)

def update_nivel(db, id_nivel, data):
    query = f"""
        UPDATE {Config.SCHEMA}.{Config.T_NIVEL_FIDELIZACION}
        SET nombre_nivel = %s,
            descripcion = %s,
            min_transacciones = %s,
            min_monto_acumulado = %s,
            prioridad = %s,
            estado = %s
        WHERE id_nivel = %s
    """
    return db.execute_query(query, (
        data.get('nombre_nivel'), data.get('descripcion'), data.get('min_transacciones'),
        data.get('min_monto_acumulado'), data.get('prioridad'), data.get('estado'), id_nivel
    ))

def deactivate_nivel(db, id_nivel):
    query = f"""
        UPDATE {Config.SCHEMA}.{Config.T_NIVEL_FIDELIZACION}
        SET estado = 'INACTIVO'
        WHERE id_nivel = %s
    """
    return db.execute_query(query, (id_nivel,))

def upsert_regla(db, id_nivel, data):
    query = f"""
        INSERT INTO {Config.SCHEMA}.{Config.T_REGLA_FIDELIZACION}
        (id_nivel, tipo_transaccion, porcentaje_descuento, monto_max_descuento,
         vigencia_desde, vigencia_hasta, estado)
        VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVO')
    """
    return db.execute_query(query, (
        id_nivel,
        data.get('tipo_transaccion', 'PEDIDO_INSUMO'),
        data.get('porcentaje_descuento'),
        data.get('monto_max_descuento'),
        data.get('vigencia_desde'),
        data.get('vigencia_hasta')
    ))

def update_regla(db, id_regla, data):
    query = f"""
        UPDATE {Config.SCHEMA}.{Config.T_REGLA_FIDELIZACION}
        SET tipo_transaccion = %s,
            porcentaje_descuento = %s,
            monto_max_descuento = %s,
            vigencia_desde = %s,
            vigencia_hasta = %s,
            estado = %s
        WHERE id_regla = %s
    """
    return db.execute_query(query, (
        data.get('tipo_transaccion', 'PEDIDO_INSUMO'),
        data.get('porcentaje_descuento'),
        data.get('monto_max_descuento'),
        data.get('vigencia_desde'),
        data.get('vigencia_hasta'),
        data.get('estado', 'ACTIVO'),
        id_regla
    ))

def get_historial_cliente(db, id_cliente, id_empresa):
    query = f"""
        SELECT COUNT(*) AS total_transacciones,
               COALESCE(SUM(monto_total), 0) AS monto_acumulado
        FROM {Config.SCHEMA}.{Config.T_TRANSACCION_COMERCIAL}
        WHERE id_cliente = %s
          AND id_empresa = %s
          AND estado_transaccion != 'CANCELADA'
    """
    return db.execute_query(query, (id_cliente, id_empresa), fetchone=True)

def get_niveles_activos(db, id_empresa):
    query = f"""
        SELECT n.id_nivel, n.nombre_nivel, n.min_transacciones,
               n.min_monto_acumulado, n.prioridad,
               r.id_regla, r.tipo_transaccion, r.porcentaje_descuento,
               r.monto_max_descuento
        FROM {Config.SCHEMA}.{Config.T_NIVEL_FIDELIZACION} n
        INNER JOIN {Config.SCHEMA}.{Config.T_REGLA_FIDELIZACION} r ON r.id_nivel = n.id_nivel
        WHERE n.id_empresa = %s
          AND n.estado = 'ACTIVO'
          AND r.estado = 'ACTIVO'
          AND (r.vigencia_desde IS NULL OR r.vigencia_desde <= CURRENT_DATE)
          AND (r.vigencia_hasta IS NULL OR r.vigencia_hasta >= CURRENT_DATE)
        ORDER BY n.prioridad DESC
    """
    return db.execute_query(query, (id_empresa,), fetchall=True)

def get_clientes_fidelizacion(db, id_empresa):
    query = f"""
        SELECT u.id_usuario, u.user_name, u.nombre_razon_social, u.correo,
               u.telefono, u.estado_cuenta,
               COUNT(t.nro_transaccion) AS total_transacciones,
               COALESCE(SUM(t.monto_total), 0) AS monto_acumulado
        FROM {Config.SCHEMA}.{Config.T_USER} u
        LEFT JOIN {Config.SCHEMA}.{Config.T_TRANSACCION_COMERCIAL} t
          ON t.id_cliente = u.id_usuario
         AND t.id_empresa = u.id_empresa
         AND t.estado_transaccion != 'CANCELADA'
        WHERE u.id_rol = {Config.CLIENT_ROLE_ID}
          AND u.id_empresa = %s
        GROUP BY u.id_usuario, u.user_name, u.nombre_razon_social, u.correo,
                 u.telefono, u.estado_cuenta
        ORDER BY monto_acumulado DESC
    """
    return db.execute_query(query, (id_empresa,), fetchall=True)

def insert_descuento_transaccion(db, data):
    query = f"""
        INSERT INTO {Config.SCHEMA}.{Config.T_DESCUENTO_TRANSACCION}
        (nro_transaccion, id_cliente, id_nivel, id_regla, subtotal_original,
         porcentaje_descuento, descuento_total, monto_final)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    return db.execute_query(query, (
        data.get('nro_transaccion'), data.get('id_cliente'), data.get('id_nivel'),
        data.get('id_regla'), data.get('subtotal_original'), data.get('porcentaje_descuento'),
        data.get('descuento_total'), data.get('monto_final')
    ))
