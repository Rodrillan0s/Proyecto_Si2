# app/repos/maquinaria_repos.py
from app.config import Config

def get_all_maquinaria(db):
    query = f"""
        SELECT nro_maquina, tipo, modelo, placa, estado, kilometraje, 
               cant_tanque_comb, fecha_ult_mant, created_at
        FROM {Config.SCHEMA}.{Config.T_MAQUINA}
        ORDER BY nro_maquina ASC;
    """
    result = db.execute_query(query, fetchall=True)
    
    if not result:
        return []

    # Extraemos las columnas de la conexión activa 'db'
    columns = [desc[0] for desc in db.cur.description]
    return [dict(zip(columns, row)) for row in result]

def get_maquinaria_by_placa(db, placa, exclude_nro=None):
    query = f"SELECT nro_maquina FROM {Config.SCHEMA}.{Config.T_MAQUINA} WHERE placa = %s"
    params = [placa]
    
    if exclude_nro:
        query += " AND nro_maquina != %s"
        params.append(exclude_nro)
        
    return db.execute_query(query, tuple(params), fetchone=True)

def add_maquinaria(db, data):
    query = f"""
        INSERT INTO {Config.SCHEMA}.{Config.T_MAQUINA} 
        (tipo, modelo, placa, estado, kilometraje, cant_tanque_comb, fecha_ult_mant)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data.get('tipo'), data.get('modelo'), data.get('placa'),
        data.get('estado', 'DISPONIBLE'), data.get('kilometraje'),
        data.get('cant_tanque_comb'), data.get('fecha_ult_mant')
    )
    return db.execute_query(query, params)

def update_maquinaria(db, nro_maquina, data):
    query = f"""
        UPDATE {Config.SCHEMA}.{Config.T_MAQUINA} 
        SET tipo = %s, modelo = %s, placa = %s, estado = %s, 
            kilometraje = %s, cant_tanque_comb = %s, fecha_ult_mant = %s
        WHERE nro_maquina = %s;
    """
    params = (
        data.get('tipo'), data.get('modelo'), data.get('placa'),
        data.get('estado'), data.get('kilometraje'),
        data.get('cant_tanque_comb'), data.get('fecha_ult_mant'),
        nro_maquina
    )
    return db.execute_query(query, params)

def delete_maquinaria(db, nro_maquina):
    query = f"DELETE FROM {Config.SCHEMA}.{Config.T_MAQUINA} WHERE nro_maquina = %s;"
    return db.execute_query(query, (nro_maquina,))

# ========================================================
# NOTA: Para la importación masiva de maquinaria
# reutilizaremos add_maquinaria desde el servicio.
# ========================================================