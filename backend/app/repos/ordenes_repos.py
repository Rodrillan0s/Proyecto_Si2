# app/repos/ordenes_repos.py
from app.config import Config

def get_work_orders_db(db, employee_id=None):
    query = f"""
        SELECT 
            o.nro_orden, o.tipo_trabajo, o.fecha_inicio, o.fecha_fin,
            o.estado, o.id_campana, o.id_supervisor, us.user_name AS supervisor_username,
            o.id_empleado, ue.user_name AS empleado_username,
            o.reporte_texto, o.url_imagen, o.url_audio
        FROM {Config.SCHEMA}.{Config.T_ORDEN} o
        LEFT JOIN {Config.SCHEMA}.{Config.T_USER} us ON us.id_usuario = o.id_supervisor
        LEFT JOIN {Config.SCHEMA}.{Config.T_USER} ue ON ue.id_usuario = o.id_empleado
    """
    params = ()
    if employee_id:
        query += " WHERE o.id_empleado = %s"
        params = (employee_id,)
        
    query += " ORDER BY o.nro_orden DESC"
    return db.execute_query(query, params, fetchall=True)

def insert_work_order_db(db, tipo, f_inicio, f_fin, id_campana, id_sup):
    query = f"""
        INSERT INTO {Config.SCHEMA}.{Config.T_ORDEN} 
        (tipo_trabajo, fecha_inicio, fecha_fin, estado, id_campana, id_supervisor)
        VALUES (%s, %s, %s, 'PENDIENTE', %s, %s)
    """
    params = (tipo, f_inicio, f_fin, id_campana, id_sup)
    return db.execute_query(query, params)

def assign_employee_db(db, nro_orden, id_empleado):
    query = f"UPDATE {Config.SCHEMA}.{Config.T_ORDEN} SET id_empleado = %s WHERE nro_orden = %s"
    return db.execute_query(query, (id_empleado, nro_orden))

def delete_work_order_db(db, nro_orden):
    query = f"DELETE FROM {Config.SCHEMA}.{Config.T_ORDEN} WHERE nro_orden = %s"
    return db.execute_query(query, (nro_orden,))

def update_orden_empleado_db(db, nro_orden, id_empleado, estado, reporte, url_img, url_audio):
    query = f"""
        UPDATE {Config.SCHEMA}.{Config.T_ORDEN}
        SET estado = %s,
            reporte_texto = %s,
            url_imagen = %s,
            url_audio = %s
        WHERE nro_orden = %s AND id_empleado = %s
    """
    params = (estado, reporte, url_img, url_audio, nro_orden, id_empleado)
    return db.execute_query(query, params)