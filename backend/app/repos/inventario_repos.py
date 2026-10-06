from app.classes.postgres import PostgreSQL


def _row_to_dict(row, keys):
    if not row:
        return None
    return {k: (float(v) if hasattr(v, 'as_integer_ratio') else (str(v) if hasattr(v, 'isoformat') else v)) for k, v in zip(keys, row)}


def listar_stock_inventario(id_empresa: int, id_categoria: int = None, estado_stock: str = None, q: str = None, page: int = 1, limit: int = 50):
    db = PostgreSQL()
    db.create_connection()
    try:
        offset = (page - 1) * limit
        sql = "SELECT * FROM obras.fn_listar_inventario_empresa(%s, %s, %s, %s, %s, %s);"
        params = (id_empresa, id_categoria, estado_stock, q, limit, offset)
        rows = db.execute_query(sql, params, fetchall=True) or []
        keys = [
            "id_material", "codigo", "nombre_material", "descripcion",
            "id_categoria", "categoria_nombre", "id_unidad_medida", "unidad_nombre",
            "unidad_abreviatura", "precio", "stock_actual", "stock_minimo",
            "valor_total", "estado_stock", "id_empresa", "nombre_empresa", "total_count"
        ]
        if not rows:
            return [], 0
        total = rows[0][16]
        return [_row_to_dict(r, keys) for r in rows], total
    finally:
        db.close_connection()


def obtener_kpis(id_empresa: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT * FROM obras.fn_resumen_kpis_inventario(%s);"
        row = db.execute_query(sql, (id_empresa,), fetchone=True)
        keys = [
            "total_materiales", "total_con_stock", "total_sin_stock",
            "total_stock_bajo", "valor_total_inventario", "total_movimientos_mes"
        ]
        return _row_to_dict(row, keys)
    finally:
        db.close_connection()


def listar_movimientos(id_empresa: int, id_material: int = None, tipo_movimiento: str = None, page: int = 1, limit: int = 50):
    db = PostgreSQL()
    db.create_connection()
    try:
        offset = (page - 1) * limit
        sql = "SELECT * FROM obras.fn_listar_movimientos_almacen(%s, %s, %s, %s, %s);"
        params = (id_empresa, id_material, tipo_movimiento, limit, offset)
        rows = db.execute_query(sql, params, fetchall=True) or []
        keys = [
            "id_movimiento", "fecha_movimiento", "created_at", "tipo_movimiento",
            "cantidad_asignada", "id_material", "material_codigo", "material_nombre",
            "unidad_abreviatura", "id_orden_compra", "numero_orden", "id_recepcion",
            "numero_recepcion", "id_usuario", "nombre_usuario", "observaciones", "total_count"
        ]
        if not rows:
            return [], 0
        total = rows[0][16]
        return [_row_to_dict(r, keys) for r in rows], total
    finally:
        db.close_connection()


def registrar_ajuste(id_empresa: int, id_material: int, cantidad: float, tipo_movimiento: str, id_usuario: int, observaciones: str, stock_minimo: float = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT * FROM obras.fn_registrar_ajuste_inventario(%s, %s, %s, %s, %s, %s, %s);"
        params = (id_empresa, id_material, cantidad, tipo_movimiento, id_usuario, observaciones, stock_minimo)
        row = db.execute_query(sql, params, fetchone=True, commit=True)
        keys = ["id_material", "nuevo_stock", "stock_minimo", "id_movimiento"]
        return _row_to_dict(row, keys)
    finally:
        db.close_connection()
