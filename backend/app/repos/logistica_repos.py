from app.config import Config

def get_pedidos_pendientes_ruta(db, id_empresa):
    query = f"""
        SELECT tc.nro_transaccion, tc.fecha_hora, tc.monto_total,
               tc.estado_transaccion, u.nombre_razon_social AS cliente,
               u.direccion, u.telefono
        FROM {Config.SCHEMA}.{Config.T_TRANSACCION_COMERCIAL} tc
        INNER JOIN {Config.SCHEMA}.{Config.T_USER} u ON u.id_usuario = tc.id_cliente
        WHERE tc.id_empresa = %s
          AND tc.estado_transaccion = 'PENDIENTE'
          AND tc.tipo_transaccion = 'PEDIDO_INSUMO'
          AND NOT EXISTS (
              SELECT 1 FROM {Config.SCHEMA}.{Config.T_RUTA} r
              WHERE r.id_transaccion = tc.nro_transaccion
                AND r.estado != 'CANCELADA'
          )
        ORDER BY tc.fecha_hora ASC
    """
    return db.execute_query(query, (id_empresa,), fetchall=True)

def get_choferes_disponibles(db, id_empresa):
    query = f"""
        SELECT id_usuario, user_name, nombre_razon_social, telefono
        FROM {Config.SCHEMA}.{Config.T_USER}
        WHERE id_rol = {Config.EMPLOYEE_ROLE_ID}
          AND id_empresa = %s
          AND estado_cuenta = 'ACTIVO'
        ORDER BY nombre_razon_social ASC
    """
    return db.execute_query(query, (id_empresa,), fetchall=True)

def insert_ruta(db, id_transaccion, id_chofer, id_empresa, origen, destino, fecha_entrega_estimada):
    query = f"""
        INSERT INTO {Config.SCHEMA}.{Config.T_RUTA}
        (id_transaccion, id_chofer, id_empresa, origen, destino, fecha_entrega_estimada)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id_ruta
    """
    return db.execute_query(query, (id_transaccion, id_chofer, id_empresa, origen, destino, fecha_entrega_estimada), fetchone=True)

def update_estado_transaccion(db, nro_transaccion, estado):
    query = f"""
        UPDATE {Config.SCHEMA}.{Config.T_TRANSACCION_COMERCIAL}
        SET estado_transaccion = %s
        WHERE nro_transaccion = %s
    """
    return db.execute_query(query, (estado, nro_transaccion))

def get_rutas_by_empresa(db, id_empresa, estado=None):
    query = f"""
        SELECT r.id_ruta, r.id_transaccion, r.id_chofer, r.id_empresa,
               r.origen, r.destino, r.fecha_asignacion,
               r.fecha_entrega_estimada, r.fecha_entrega_real,
               r.estado, r.observaciones, r.url_evidencia_imagen, r.url_evidencia_audio,
               u.nombre_razon_social AS chofer_nombre, u.user_name AS chofer_usuario,
               tc.nro_transaccion, tc.monto_total, cl.nombre_razon_social AS cliente_nombre
        FROM {Config.SCHEMA}.{Config.T_RUTA} r
        INNER JOIN {Config.SCHEMA}.{Config.T_USER} u ON u.id_usuario = r.id_chofer
        INNER JOIN {Config.SCHEMA}.{Config.T_TRANSACCION_COMERCIAL} tc ON tc.nro_transaccion = r.id_transaccion
        INNER JOIN {Config.SCHEMA}.{Config.T_USER} cl ON cl.id_usuario = tc.id_cliente
        WHERE r.id_empresa = %s
    """
    params = [id_empresa]
    if estado:
        query += " AND r.estado = %s"
        params.append(estado)
    query += " ORDER BY r.fecha_asignacion DESC"
    return db.execute_query(query, tuple(params), fetchall=True)

def get_rutas_by_chofer(db, id_chofer, estado=None):
    query = f"""
        SELECT r.id_ruta, r.id_transaccion, r.id_chofer, r.id_empresa,
               r.origen, r.destino, r.fecha_asignacion,
               r.fecha_entrega_estimada, r.fecha_entrega_real,
               r.estado, r.observaciones, r.url_evidencia_imagen, r.url_evidencia_audio,
               tc.nro_transaccion, tc.monto_total,
               cl.nombre_razon_social AS cliente_nombre, cl.direccion AS cliente_direccion,
               cl.telefono AS cliente_telefono
        FROM {Config.SCHEMA}.{Config.T_RUTA} r
        INNER JOIN {Config.SCHEMA}.{Config.T_TRANSACCION_COMERCIAL} tc ON tc.nro_transaccion = r.id_transaccion
        INNER JOIN {Config.SCHEMA}.{Config.T_USER} cl ON cl.id_usuario = tc.id_cliente
        WHERE r.id_chofer = %s
    """
    params = [id_chofer]
    if estado:
        query += " AND r.estado = %s"
        params.append(estado)
    query += " ORDER BY r.fecha_asignacion DESC"
    return db.execute_query(query, tuple(params), fetchall=True)

def get_ruta_by_id(db, id_ruta):
    query = f"""
        SELECT r.id_ruta, r.id_transaccion, r.id_chofer, r.id_empresa,
               r.origen, r.destino, r.fecha_asignacion,
               r.fecha_entrega_estimada, r.fecha_entrega_real,
               r.estado, r.observaciones, r.url_evidencia_imagen, r.url_evidencia_audio,
               u.nombre_razon_social AS chofer_nombre, u.user_name AS chofer_usuario,
               tc.nro_transaccion, tc.monto_total, tc.fecha_hora AS pedido_fecha,
               cl.nombre_razon_social AS cliente_nombre, cl.direccion AS cliente_direccion,
               cl.telefono AS cliente_telefono
        FROM {Config.SCHEMA}.{Config.T_RUTA} r
        INNER JOIN {Config.SCHEMA}.{Config.T_USER} u ON u.id_usuario = r.id_chofer
        INNER JOIN {Config.SCHEMA}.{Config.T_TRANSACCION_COMERCIAL} tc ON tc.nro_transaccion = r.id_transaccion
        INNER JOIN {Config.SCHEMA}.{Config.T_USER} cl ON cl.id_usuario = tc.id_cliente
        WHERE r.id_ruta = %s
    """
    return db.execute_query(query, (id_ruta,), fetchone=True)

def confirmar_entrega_ruta(db, id_ruta, observaciones, url_evidencia_imagen, url_evidencia_audio):
    query = f"""
        UPDATE {Config.SCHEMA}.{Config.T_RUTA}
        SET estado = 'ENTREGADA',
            observaciones = %s,
            url_evidencia_imagen = %s,
            url_evidencia_audio = %s,
            fecha_entrega_real = CURRENT_TIMESTAMP
        WHERE id_ruta = %s
    """
    return db.execute_query(query, (observaciones, url_evidencia_imagen, url_evidencia_audio, id_ruta))

def get_id_transaccion_by_ruta(db, id_ruta):
    query = f"""
        SELECT id_transaccion FROM {Config.SCHEMA}.{Config.T_RUTA}
        WHERE id_ruta = %s
    """
    return db.execute_query(query, (id_ruta,), fetchone=True)

def cancelar_ruta_db(db, id_ruta):
    query = f"""
        UPDATE {Config.SCHEMA}.{Config.T_RUTA}
        SET estado = 'CANCELADA'
        WHERE id_ruta = %s AND estado = 'ASIGNADA'
    """
    return db.execute_query(query, (id_ruta,))
