from app.config import Config

def get_kpis_financieros(db, id_empresa):
    # Suma de ingresos por transacciones confirmadas
    query = f"""
        SELECT 
            COALESCE(SUM(monto_total), 0) AS ingresos_totales,
            COUNT(nro_transaccion) AS total_ventas
        FROM {Config.SCHEMA}.transaccion_comercial 
        -- WHERE id_empresa = %s AND estado_transaccion IN ('CONFIRMADO', 'FINALIZADA')
    """
    return db.execute_query(query, (id_empresa,), fetchone=True)

def get_kpis_operativos(db, id_empresa):
    # Conteo de órdenes de trabajo agrupadas por estado
    query = f"""
        SELECT estado, COUNT(*) AS cantidad 
        FROM {Config.SCHEMA}.orden_trabajo 
        -- WHERE id_empresa = %s 
        GROUP BY estado
    """
    return db.execute_query(query, (id_empresa,), fetchall=True)

def get_kpis_inventario(db, id_empresa):
    # Productos con stock por debajo del mínimo y valoración total del almacén
    query = f"""
        SELECT 
            COUNT(CASE WHEN stock_actual <= stock_minimo THEN 1 END) AS alertas_stock,
            COALESCE(SUM(stock_actual * precio_unitario), 0) AS valor_inventario
        FROM {Config.SCHEMA}.bodega 
        -- WHERE id_empresa = %s
    """
    return db.execute_query(query, (id_empresa,), fetchone=True)

def get_kpis_agricolas(db, id_empresa):
    # Hectáreas totales y hectáreas activas
    query = f"""
        SELECT 
            COALESCE(SUM(tamano_hectareas), 0) AS hectareas_totales,
            COALESCE(SUM(CASE WHEN estado = 'ACTIVO' THEN tamano_hectareas ELSE 0 END), 0) AS hectareas_activas
        FROM {Config.SCHEMA}.terreno 
        -- WHERE id_empresa = %s
    """
    return db.execute_query(query, (id_empresa,), fetchone=True)

def get_kpis_maquinaria(db, id_empresa):
    # Estado de la flota
    query = f"""
        SELECT estado, COUNT(*) as cantidad
        FROM {Config.SCHEMA}.maquinaria
        -- WHERE id_empresa = %s
        GROUP BY estado
    """
    return db.execute_query(query, (id_empresa,), fetchall=True)