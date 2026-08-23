from app.classes.postgres import PostgreSQL
from app.config import Config

# --- LEER ROLES ---
def obtener_todos_los_roles(empresa=False):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT id_rol, nombre_rol
            FROM {Config.SCHEMA}.t_rol
            {"WHERE id_rol NOT IN (1, 2)" if empresa else ""}
            ORDER BY id_rol ASC;
        """
        resultados = db.execute_query(query, fetchall=True)
        
        roles = []
        if resultados:
            for r in resultados:
                roles.append({
                    "nro_rol": r[0],
                    "nombre_rol": r[1]
                })
        return roles
    finally:
        db.close_connection()

# --- CREAR ROL ---
def crear_rol_db(nombre_rol, descripcion):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            INSERT INTO {Config.SCHEMA}.t_rol (nombre_rol)
            VALUES (%s)
            RETURNING id_rol;
        """
        resultado = db.execute_query(query, (nombre_rol,), fetchone=True, commit=True)
        return resultado[0] if resultado else None
    finally:
        db.close_connection()

# --- ACTUALIZAR ROL ---
def actualizar_rol_db(nro_rol, nombre_rol, descripcion):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            UPDATE {Config.SCHEMA}.t_rol
            SET nombre_rol = %s
            WHERE id_rol = %s;
        """
        filas_afectadas = db.execute_query(query, (nombre_rol, nro_rol), commit=True)
        return filas_afectadas > 0
    finally:
        db.close_connection()

# --- ELIMINAR ROL (Borrado Físico) ---
def eliminar_rol_db(nro_rol: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"DELETE FROM {Config.SCHEMA}.t_rol WHERE id_rol = %s;"
        filas_afectadas = db.execute_query(query, (nro_rol,), commit=True)
        return filas_afectadas > 0
    finally:
        db.close_connection()