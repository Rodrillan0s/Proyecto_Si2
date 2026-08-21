# app/repos/cultivos_repos.py
from app.config import Config

T_BODEGA = "bodega"

def get_all_cultivos(db):
    query = f"""
        SELECT 
            id_producto, nombre_producto, categoria, unidad_medida,
            precio_unitario, stock_actual, stock_minimo
        FROM {Config.SCHEMA}.{T_BODEGA}
        ORDER BY id_producto DESC
    """
    return db.execute_query(query, fetchall=True)


def insert_cultivo(db, nombre_producto, categoria, unidad_medida, precio_unitario, stock_actual, stock_minimo):
    query = f"""
        INSERT INTO {Config.SCHEMA}.{T_BODEGA}
        (nombre_producto, categoria, unidad_medida, precio_unitario, stock_actual, stock_minimo)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        nombre_producto, categoria, unidad_medida, 
        precio_unitario, stock_actual, stock_minimo
    )
    return db.execute_query(query, params)


def delete_cultivo_by_id(db, id_producto):
    query = f"""
        DELETE FROM {Config.SCHEMA}.{T_BODEGA}
        WHERE id_producto = %s
    """
    return db.execute_query(query, (id_producto,))


def update_cultivo_dynamic(db, id_producto, fields, params):
    set_clause = ", ".join(fields)
    query = f"""
        UPDATE {Config.SCHEMA}.{T_BODEGA}
        SET {set_clause}
        WHERE id_producto = %s
    """
    return db.execute_query(query, tuple(params + [id_producto]))

# ========================================================
# NOTA: Para la importación masiva reutilizaremos la 
# función insert_cultivo iterándola desde el servicio.
# ========================================================