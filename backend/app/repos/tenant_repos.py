from app.classes.postgres import PostgreSQL
from app.config import Config

# --- LEER EMPRESAS ---
def obtener_todas_las_empresas():
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT id_empresa, nombre_empresa, nit, descripcion
            FROM {Config.SCHEMA}.t_empresa
            ORDER BY id_empresa ASC;
        """
        resultados = db.execute_query(query, fetchall=True)
        
        empresas = []
        if resultados:
            for r in resultados:
                empresas.append({
                    "id_empresa": r[0],
                    "nombre_empresa": r[1],
                    "nit": r[2],
                    "descripcion": r[3],
                    "estado": "ACTIVO"
                })
        return empresas
    finally:
        db.close_connection()

# --- CREAR EMPRESA ---
def crear_empresa_db(nombre_empresa, nit=None, descripcion=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            INSERT INTO {Config.SCHEMA}.t_empresa (nombre_empresa, nit, descripcion)
            VALUES (%s, %s, %s)
            RETURNING id_empresa;
        """
        resultado = db.execute_query(query, (nombre_empresa, nit, descripcion), fetchone=True, commit=True)
        return resultado[0] if resultado else None
    finally:
        db.close_connection()

# --- ACTUALIZAR EMPRESA ---
def actualizar_empresa_db(id_empresa, nombre_empresa, nit=None, descripcion=None, estado=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            UPDATE {Config.SCHEMA}.t_empresa
            SET nombre_empresa = %s,
                nit = %s,
                descripcion = %s
            WHERE id_empresa = %s;
        """
        filas_afectadas = db.execute_query(query, (nombre_empresa, nit, descripcion, id_empresa), commit=True)
        return filas_afectadas > 0
    finally:
        db.close_connection()

# --- ELIMINAR EMPRESA (Borrado Físico Completo) ---
def eliminar_empresa_db(id_empresa: int):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"DELETE FROM {Config.SCHEMA}.t_empresa WHERE id_empresa = %s;"
        # Guardamos cuántas filas se borraron realmente
        filas_afectadas = db.execute_query(query, (id_empresa,), commit=True)
        return filas_afectadas > 0
    finally:
        db.close_connection()