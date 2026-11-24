"""
Repositorio CU18 – Avances de Obra
Acceso a datos para registrar y consultar avances de obra.
Patrón: llamadas directas a PostgreSQL siguiendo las convenciones del proyecto.
"""
from app.classes.postgres import PostgreSQL
from app.config import Config
import json


def _json_result(row, default_error: str) -> dict:
    if row and row[0]:
        return row[0] if isinstance(row[0], dict) else json.loads(row[0])
    return {"success": False, "error": default_error}


def registrar_avance_fn(
    id_obra: int,
    id_unidad: int,
    id_empresa: int,
    porcentaje: float,
    fecha_registro,
    observacion: str,
    id_usuario: int,
) -> dict:
    """Invoca fn_registrar_avance_obra y retorna el resultado."""
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.fn_registrar_avance_obra(%s, %s, %s, %s, %s, %s, %s);"
        params = (id_obra, id_unidad, id_empresa, porcentaje, fecha_registro, observacion, id_usuario)
        return _json_result(
            db.execute_query(query, params, fetchone=True, commit=True),
            "No se pudo registrar el avance de obra.",
        )
    finally:
        db.close_connection()


def listar_avances_fn(id_obra: int, id_empresa: int, estado: str = None) -> dict:
    """Invoca fn_listar_avances_obra y retorna la bitácora de órdenes con estado y cuadrillas."""
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.fn_listar_avances_obra(%s, %s, %s);"
        return _json_result(
            db.execute_query(query, (id_obra, id_empresa, estado), fetchone=True),
            "Error al obtener los avances de obra.",
        )
    finally:
        db.close_connection()


def listar_avance_fisico_unidad_cliente(
    id_cliente: int,
    id_unidad: int,
    id_obra: int,
    id_empresa: int,
) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT a.id_avance, a.id_obra, a.id_unidad, a.porcentaje_avance,
                   u.estado AS estado_unidad, a.fecha_registro, a.observacion
            FROM {Config.SCHEMA}.t_avance_obra a
            INNER JOIN {Config.SCHEMA}.t_unidad_construccion u
                ON u.id_unidad = a.id_unidad
            INNER JOIN {Config.SCHEMA}.t_estructura_obra e
                ON e.id_estructura = u.id_estructura
            INNER JOIN {Config.SCHEMA}.t_obra o
                ON o.id_obra = e.id_obra
               AND o.id_obra = a.id_obra
            INNER JOIN {Config.SCHEMA}.t_crm_cliente c
                ON c.id_cliente = %s
               AND c.id_empresa = %s
               AND c.tipo_cliente = 'CLIENTE'
            WHERE a.id_unidad = %s
              AND a.id_obra = %s
              AND o.id_empresa = %s
              AND EXISTS (
                  SELECT 1
                  FROM {Config.SCHEMA}.t_crm_cliente_unidad cu
                  WHERE cu.id_cliente = c.id_cliente
                    AND cu.id_unidad = u.id_unidad
              )
            ORDER BY a.fecha_registro DESC, a.created_at DESC;
        """
        rows = db.execute_query(
            query,
            (id_cliente, id_empresa, id_unidad, id_obra, id_empresa),
            fetchall=True,
        ) or []
        return {
            "success": True,
            "data": [
                {
                    "id_avance": row[0],
                    "id_obra": row[1],
                    "id_unidad": row[2],
                    "porcentaje_avance": float(row[3]),
                    "estado_unidad": row[4],
                    "fecha_registro": row[5].isoformat() if row[5] else None,
                    "observacion": row[6],
                }
                for row in rows
            ],
        }
    finally:
        db.close_connection()


def resumen_avances_fn(id_obra: int, id_empresa: int) -> dict:
    """Invoca fn_resumen_avances_obra para obtener el resumen de avance global."""
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.fn_resumen_avances_obra(%s, %s);"
        return _json_result(
            db.execute_query(query, (id_obra, id_empresa), fetchone=True),
            "Error al calcular el resumen de avances.",
        )
    finally:
        db.close_connection()


def eliminar_avance_fn(id_avance: int, id_obra: int, id_empresa: int) -> dict:
    """Invoca fn_eliminar_avance_obra."""
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.fn_eliminar_avance_obra(%s, %s, %s);"
        return _json_result(
            db.execute_query(query, (id_avance, id_obra, id_empresa), fetchone=True, commit=True),
            "No se pudo eliminar el avance.",
        )
    finally:
        db.close_connection()
