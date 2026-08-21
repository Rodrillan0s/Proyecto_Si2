# app/repos/empresas_repo.py
from app.config import Config

def get_all_empresas(db):
    query = f"""
        SELECT id_empresa, nombre_empresa, nit, estado, created_at 
        FROM {Config.SCHEMA}.empresa
        ORDER BY id_empresa ASC
    """
    return db.execute_query(query, fetchall=True)

def insert_empresa(db, nombre_empresa, nit, estado):
    query = f"""
        INSERT INTO {Config.SCHEMA}.empresa (nombre_empresa, nit, estado)
        VALUES (%s, %s, %s)
    """
    return db.execute_query(query, (nombre_empresa, nit, estado))

def delete_empresa(db, id_empresa):
    query = f"DELETE FROM {Config.SCHEMA}.empresa WHERE id_empresa = %s"
    return db.execute_query(query, (id_empresa,))

def update_empresa_dynamic(db, id_empresa, fields, params):
    set_clause = ", ".join(fields)
    query = f"""
        UPDATE {Config.SCHEMA}.empresa
        SET {set_clause}
        WHERE id_empresa = %s
    """
    return db.execute_query(query, tuple(params + [id_empresa]))