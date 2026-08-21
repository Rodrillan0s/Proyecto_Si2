# app/repos/terrenos_repos.py
from app.config import Config

def get_all_terrenos_db(db):
    query = f"""
        SELECT T.NRO_LOTE, T.NOMBRE_SECTOR, T.TAMANO_HECTAREAS, 
               T.LATITUD, T.LONGITUD, T.ID_USUARIO AS ID, U.USER_NAME AS PROPIETARIO
        FROM {Config.SCHEMA}.{Config.T_TERRENO} T
        INNER JOIN {Config.SCHEMA}.{Config.T_USER} U ON U.ID_USUARIO = T.ID_USUARIO
    """
    return db.execute_query(query, fetchall=True)


def check_duplicate_terreno(db, nombre_sector, id_usuario):
    query = f"""
        SELECT 1 FROM {Config.SCHEMA}.{Config.T_TERRENO}
        WHERE nombre_sector = %s AND id_usuario = %s LIMIT 1
    """
    return db.execute_query(query, (nombre_sector, id_usuario), fetchone=True)


def insert_terreno_db(db, nombre_sector, tamano, lat, lon, id_user):
    query = f"""
        INSERT INTO {Config.SCHEMA}.{Config.T_TERRENO}
        (nombre_sector, tamano_hectareas, latitud, longitud, id_usuario)
        VALUES (%s, %s, %s, %s, %s)
    """
    return db.execute_query(query, (nombre_sector, tamano, lat, lon, id_user))


def update_terreno_dynamic_db(db, nro_lote, fields, params):
    set_clause = ", ".join(fields)
    query = f"UPDATE {Config.SCHEMA}.{Config.T_TERRENO} SET {set_clause} WHERE nro_lote = %s"
    return db.execute_query(query, tuple(params + [nro_lote]))


def delete_terreno_db(db, nro_lote):
    query = f"DELETE FROM {Config.SCHEMA}.{Config.T_TERRENO} WHERE nro_lote = %s"
    return db.execute_query(query, (nro_lote,))

# ========================================================
# NOTA: Para la importación masiva de terrenos
# reutilizaremos insert_terreno_db desde el servicio.
# ========================================================