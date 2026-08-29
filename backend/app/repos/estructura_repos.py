from app.classes.postgres import PostgreSQL
import json

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
