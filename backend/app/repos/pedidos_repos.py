# app/repos/pedidos_repos.py
from app.config import Config

def get_catalogo_insumos(db, id_empresa):
    query = f"""
        SELECT id_producto, nombre_producto, categoria, unidad_medida, precio_unitario, stock_actual 
        FROM {Config.SCHEMA}.bodega
        WHERE id_empresa = %s 
          AND stock_actual > 0 
          AND categoria IN ('FERTILIZANTE', 'SEMILLA')
        ORDER BY nombre_producto ASC
    """
    return db.execute_query(query, (id_empresa,), fetchall=True)

def verificar_stock(db, id_producto):
    query = f"SELECT stock_actual FROM {Config.SCHEMA}.bodega WHERE id_producto = %s"
    resultado = db.execute_query(query, (id_producto,), fetchone=True)
    return float(resultado[0]) if resultado else 0.0

def get_producto_para_pedido(db, id_producto, id_empresa):
    query = f"""
        SELECT id_producto, precio_unitario, stock_actual
        FROM {Config.SCHEMA}.bodega
        WHERE id_producto = %s AND id_empresa = %s
    """
    return db.execute_query(query, (id_producto, id_empresa), fetchone=True)

def insert_transaccion_cabecera(db, tipo_transaccion, monto_total, id_cliente, id_supervisor_admin, id_empresa):
    query = f"""
        INSERT INTO {Config.SCHEMA}.transaccion_comercial 
        (tipo_transaccion, estado_transaccion, monto_total, id_cliente, id_supervisor_admin, id_empresa)
        VALUES (%s, 'PENDIENTE', %s, %s, %s, %s)
        RETURNING nro_transaccion
    """
    return db.execute_query(query, (tipo_transaccion, monto_total, id_cliente, id_supervisor_admin, id_empresa), fetchone=True)

def insert_detalle_venta(db, cantidad, precio_venta, nro_transaccion, id_producto):
    query = f"""
        INSERT INTO {Config.SCHEMA}.detalle_venta 
        (cantidad, precio_venta, nro_transaccion, id_producto)
        VALUES (%s, %s, %s, %s)
    """
    return db.execute_query(query, (cantidad, precio_venta, nro_transaccion, id_producto))

def update_stock_bodega(db, cantidad, id_producto):
    query = f"""
        UPDATE {Config.SCHEMA}.bodega 
        SET stock_actual = stock_actual - %s 
        WHERE id_producto = %s
    """
    return db.execute_query(query, (cantidad, id_producto))

def get_historial_pedidos(db, id_cliente):
    query = f"""SELECT nro_transaccion, fecha_hora, monto_total, estado_transaccion 
                FROM {Config.SCHEMA}.transaccion_comercial 
                WHERE id_cliente = %s ORDER BY fecha_hora DESC"""
    return db.execute_query(query, (id_cliente,), fetchall=True)

def get_detalle_pedido(db, nro_transaccion):
    query = f"""SELECT b.nombre_producto, d.cantidad, d.precio_venta 
                FROM {Config.SCHEMA}.detalle_venta d
                JOIN {Config.SCHEMA}.bodega b ON d.id_producto = b.id_producto
                WHERE d.nro_transaccion = %s"""
    return db.execute_query(query, (nro_transaccion,), fetchall=True)

def get_descuento_pedido(db, nro_transaccion):
    query = f"""
        SELECT d.subtotal_original, d.porcentaje_descuento, d.descuento_total,
               d.monto_final, n.nombre_nivel AS nivel_fidelizacion
        FROM {Config.SCHEMA}.{Config.T_DESCUENTO_TRANSACCION} d
        LEFT JOIN {Config.SCHEMA}.{Config.T_NIVEL_FIDELIZACION} n ON n.id_nivel = d.id_nivel
        WHERE d.nro_transaccion = %s
    """
    return db.execute_query(query, (nro_transaccion,), fetchone=True)
