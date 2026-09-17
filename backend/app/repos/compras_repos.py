import json
from app.classes.postgres import PostgreSQL
from psycopg2 import errors


class ComprasRepoError(Exception):
    pass


def _row_to_orden_detalle_view(row):
    return {
        "id_orden_compra": row[0],
        "numero_orden": row[1],
        "fecha": str(row[2]) if row[2] else None,
        "observaciones": row[3],
        "estado": row[4],
        "id_empresa": row[5],
        "nombre_empresa": row[6],
        "id_proveedor": row[7],
        "proveedor_razon_social": row[8],
        "proveedor_nit": row[9],
        "id_usuario_solicitante": row[10],
        "nombre_solicitante": row[11],
        "subtotal": float(row[12]) if row[12] is not None else 0.0,
        "total": float(row[13]) if row[13] is not None else 0.0,
        "id_usuario_aprobacion": row[14],
        "nombre_aprobador": row[15],
        "fecha_aprobacion": row[16].isoformat() if row[16] else None,
        "observacion_aprobacion": row[17],
        "created_at": row[18].isoformat() if row[18] else None,
        "updated_at": row[19].isoformat() if row[19] else None
    }


def _row_to_orden_list_view(row):
    return {
        "id_orden_compra": row[0],
        "numero_orden": row[1],
        "fecha": str(row[2]) if row[2] else None,
        "observaciones": row[3],
        "estado": row[4],
        "id_empresa": row[5],
        "nombre_empresa": row[6],
        "id_proveedor": row[7],
        "proveedor_razon_social": row[8],
        "proveedor_nit": "",
        "id_usuario_solicitante": row[9],
        "nombre_solicitante": row[10],
        "subtotal": float(row[11]) if row[11] is not None else 0.0,
        "total": float(row[12]) if row[12] is not None else 0.0,
        "items_count": row[13],
        "items_recibidos_count": row[14],
        "created_at": row[15].isoformat() if row[15] else None,
        "updated_at": row[16].isoformat() if row[16] else None
    }


def _row_to_detalle(row):
    return {
        "id_detalle": row[0],
        "id_material": row[1],
        "codigo_material": row[2],
        "nombre_material": row[3],
        "unidad_medida": row[4],
        "cantidad_solicitada": float(row[5]) if row[5] is not None else 0.0,
        "precio_unitario": float(row[6]) if row[6] is not None else 0.0,
        "subtotal": float(row[7]) if row[7] is not None else 0.0,
        "cantidad_recibida": float(row[8]) if row[8] is not None else 0.0,
        "cantidad_pendiente": float(row[9]) if row[9] is not None else 0.0
    }


def _row_to_recepcion(row):
    return {
        "id_recepcion": row[0],
        "numero_recepcion": row[1],
        "fecha_recepcion": row[2].isoformat() if row[2] else None,
        "id_usuario_recepcion": row[3],
        "nombre_usuario_recepcion": row[4],
        "observaciones": row[5],
        "total_items": row[6],
        "total_cantidad_recibida": 0.0
    }


def crear_orden(id_empresa: int, id_proveedor: int, id_usuario: int, fecha: str, observaciones: str, detalles: list, enviar_aprobacion: bool = False) -> int:
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT obras.fn_registrar_orden_compra(%s::INT, %s::INT, %s::INT, %s::DATE, %s::TEXT, %s::VARCHAR, %s::JSONB);"
        estado = "PENDIENTE_APROBACION" if enviar_aprobacion else "BORRADOR"
        items_json = json.dumps([
            {
                "id_material": d["id_material"],
                "cantidad": d.get("cantidad", d.get("cantidad_solicitada")),
                "precio_unitario": d.get("precio_unitario", 0)
            }
            for d in detalles
        ])
        row = db.execute_query(
            sql,
            (id_empresa, id_proveedor, id_usuario, fecha, observaciones, estado, items_json),
            fetchone=True,
            commit=True
        )
        return row[0] if row else None
    except errors.RaiseException as exc:
        if db.conn:
            db.conn.rollback()
        raise ComprasRepoError(str(exc).replace("ERROR:  ", "").split("\n")[0].strip()) from exc
    finally:
        db.close_connection()


def cambiar_estado(id_orden: int, id_empresa: int, nuevo_estado: str) -> bool:
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT obras.fn_cambiar_estado_orden_compra(%s::INT, %s::INT, %s::VARCHAR);"
        row = db.execute_query(sql, (id_empresa, id_orden, nuevo_estado), fetchone=True, commit=True)
        return bool(row and row[0])
    except errors.RaiseException as exc:
        if db.conn:
            db.conn.rollback()
        raise ComprasRepoError(str(exc).replace("ERROR:  ", "").split("\n")[0].strip()) from exc
    finally:
        db.close_connection()


def aprobar_rechazar(id_orden: int, id_empresa: int, id_usuario: int, aprobar: bool, observacion: str = None) -> bool:
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT obras.fn_aprobar_rechazar_orden_compra(%s::INT, %s::INT, %s::INT, %s::BOOLEAN, %s::TEXT);"
        row = db.execute_query(sql, (id_empresa, id_orden, id_usuario, aprobar, observacion), fetchone=True, commit=True)
        return bool(row and row[0])
    except errors.RaiseException as exc:
        if db.conn:
            db.conn.rollback()
        raise ComprasRepoError(str(exc).replace("ERROR:  ", "").split("\n")[0].strip()) from exc
    finally:
        db.close_connection()


def obtener_detalles_orden_raw(id_orden: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT * FROM obras.fn_listar_detalles_orden_compra(%s::INT);"
        rows = db.execute_query(sql, (id_orden,), fetchall=True) or []
        return [_row_to_detalle(r) for r in rows]
    finally:
        db.close_connection()


def registrar_recepcion(id_orden: int, id_empresa: int, id_usuario: int, observaciones: str, detalles: list) -> int:
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT obras.fn_registrar_recepcion_compra(%s::INT, %s::INT, %s::INT, %s::TEXT, %s::JSONB);"
        items_json = json.dumps([
            {
                "id_detalle": d["id_detalle"],
                "cantidad": d.get("cantidad", d.get("cantidad_recibida"))
            }
            for d in detalles
        ])
        row = db.execute_query(sql, (id_empresa, id_orden, id_usuario, observaciones, items_json), fetchone=True, commit=True)
        return row[0] if row else None
    except errors.RaiseException as exc:
        if db.conn:
            db.conn.rollback()
        raise ComprasRepoError(str(exc).replace("ERROR:  ", "").split("\n")[0].strip()) from exc
    finally:
        db.close_connection()


def consultar_orden(id_orden: int, id_empresa: int = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        sql = "SELECT * FROM obras.fn_consultar_orden_compra(%s::INT, %s::INT);"
        row = db.execute_query(sql, (id_empresa, id_orden), fetchone=True)
        if not row:
            return None
        orden = _row_to_orden_detalle_view(row)

        # Detalles
        sql_detalles = "SELECT * FROM obras.fn_listar_detalles_orden_compra(%s::INT);"
        detalles_rows = db.execute_query(sql_detalles, (id_orden,), fetchall=True) or []
        orden["detalles"] = [_row_to_detalle(r) for r in detalles_rows]

        # Recepciones
        sql_recep = "SELECT * FROM obras.fn_listar_recepciones_orden(%s::INT);"
        recep_rows = db.execute_query(sql_recep, (id_orden,), fetchall=True) or []
        orden["recepciones"] = [_row_to_recepcion(r) for r in recep_rows]

        return orden
    finally:
        db.close_connection()


def listar_ordenes(id_empresa: int = None, q: str = None, estado: str = None, id_proveedor: int = None, page: int = 1, limit: int = 20):
    db = PostgreSQL()
    db.create_connection()
    try:
        offset = (page - 1) * limit
        sql = "SELECT * FROM obras.fn_listar_ordenes_compra(%s::INT, %s::VARCHAR, %s::VARCHAR, %s::INT, %s::INT, %s::INT);"
        rows = db.execute_query(
            sql,
            (id_empresa, q, estado, id_proveedor, limit, offset),
            fetchall=True
        ) or []

        if not rows:
            return [], 0

        total = rows[0][17]
        ordenes = [_row_to_orden_list_view(r) for r in rows]
        return ordenes, total
    finally:
        db.close_connection()
