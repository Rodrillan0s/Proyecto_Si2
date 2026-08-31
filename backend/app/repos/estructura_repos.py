from app.classes.postgres import PostgreSQL
import json


def obtener_contexto_nodo(id_estructura: int, id_obra: int, id_empresa: int = None):
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query(
            """
            SELECT e.id_estructura, e.tipo, u.id_unidad,
                   EXISTS (
                       SELECT 1
                       FROM obras.t_estructura_obra h
                       WHERE h.id_padre = e.id_estructura
                   ) AS tiene_hijos
            FROM obras.t_estructura_obra e
            JOIN obras.t_obra o ON o.id_obra = e.id_obra
            LEFT JOIN obras.t_unidad_construccion u
                   ON u.id_estructura = e.id_estructura
            WHERE e.id_estructura = %s
              AND e.id_obra = %s
              AND (o.id_empresa = %s OR %s IS NULL)
            """,
            (id_estructura, id_obra, id_empresa, id_empresa),
            fetchone=True
        )
        if not row:
            return None
        return {
            "id_estructura": row[0],
            "tipo": row[1],
            "id_unidad": row[2],
            "tiene_hijos": bool(row[3])
        }
    finally:
        db.close_connection()

def listar_estructura_fn(id_obra: int, id_empresa: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = "SELECT obras.fn_listar_estructura_obra(%s, %s);"
        res = db.execute_query(query, (id_obra, id_empresa), fetchone=True)
        if res and res[0]:
            return res[0] if isinstance(res[0], dict) else json.loads(res[0])
        return {"success": False, "error": "No se obtuvieron resultados."}
    finally:
        db.close_connection()

def registrar_estructura_fn(id_obra: int, id_padre: int, nombre: str, tipo: str, descripcion: str, orden: int, id_empresa: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = "SELECT obras.fn_registrar_estructura_obra(%s, %s, %s, %s, %s, %s, %s);"
        res = db.execute_query(query, (id_obra, id_padre, nombre, tipo, descripcion, orden, id_empresa), fetchone=True, commit=True)
        if res and res[0]:
            return res[0] if isinstance(res[0], dict) else json.loads(res[0])
        return {"success": False, "error": "No se pudo registrar el elemento."}
    finally:
        db.close_connection()

def actualizar_estructura_fn(id_estructura: int, id_obra: int, nombre: str, tipo: str, descripcion: str, orden: int, id_empresa: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = "SELECT obras.fn_actualizar_estructura_obra(%s, %s, %s, %s, %s, %s, %s);"
        res = db.execute_query(query, (id_estructura, id_obra, nombre, tipo, descripcion, orden, id_empresa), fetchone=True, commit=True)
        if res and res[0]:
            return res[0] if isinstance(res[0], dict) else json.loads(res[0])
        return {"success": False, "error": "No se pudo actualizar el elemento."}
    finally:
        db.close_connection()

def eliminar_estructura_fn(id_estructura: int, id_obra: int, id_empresa: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = "SELECT obras.fn_eliminar_estructura_obra(%s, %s, %s);"
        res = db.execute_query(query, (id_estructura, id_obra, id_empresa), fetchone=True, commit=True)
        if res and res[0]:
            return res[0] if isinstance(res[0], dict) else json.loads(res[0])
        return {"success": False, "error": "No se pudo eliminar el elemento."}
    finally:
        db.close_connection()

def reordenar_estructura_fn(id_estructura: int, id_obra: int, direccion: str, id_empresa: int = None) -> dict:
    db = PostgreSQL()
    db.create_connection()
    try:
        query = "SELECT obras.fn_reordenar_estructura_obra(%s, %s, %s, %s);"
        res = db.execute_query(query, (id_estructura, id_obra, direccion, id_empresa), fetchone=True, commit=True)
        if res and res[0]:
            return res[0] if isinstance(res[0], dict) else json.loads(res[0])
        return {"success": False, "error": "No se pudo reordenar el elemento."}
    finally:
        db.close_connection()
