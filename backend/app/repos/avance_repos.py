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


def listar_avances_fn(id_obra: int, id_empresa: int, id_unidad: int = None) -> dict:
    """Invoca fn_listar_avances_obra y retorna el historial completo."""
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"SELECT {Config.SCHEMA}.fn_listar_avances_obra(%s, %s, %s);"
        return _json_result(
            db.execute_query(query, (id_obra, id_empresa, id_unidad), fetchone=True),
            "Error al obtener los avances de obra.",
        )
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
