from app.config import Config

def get_empresa_usuario_db(db, id_usuario):
    query = f"""
        SELECT id_empresa
        FROM {Config.SCHEMA}.usuario
        WHERE id_usuario = %s
    """
    return db.execute_query(query, (id_usuario,), fetchone=True)


def check_terreno_exists_db(db, nro_lote):
    query = f"""
        SELECT 1
        FROM {Config.SCHEMA}.terreno
        WHERE nro_lote = %s
        LIMIT 1
    """
    return db.execute_query(query, (nro_lote,), fetchone=True)


def check_dispositivo_duplicate_db(db, codigo_dispositivo):
    query = f"""
        SELECT 1
        FROM {Config.SCHEMA}.dispositivo_iot
        WHERE codigo_dispositivo = %s
        LIMIT 1
    """
    return db.execute_query(query, (codigo_dispositivo,), fetchone=True)


def insert_dispositivo_db(db, codigo, nombre, tipo, estado, nro_lote, id_usuario, id_empresa):
    query = f"""
        INSERT INTO {Config.SCHEMA}.dispositivo_iot
        (codigo_dispositivo, nombre_dispositivo, tipo_dispositivo, estado, nro_lote, id_usuario, id_empresa)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (codigo, nombre, tipo, estado, nro_lote, id_usuario, id_empresa)
    return db.execute_query(query, params)


def get_dispositivos_db(db):
    query = f"""
        SELECT
            d.id_dispositivo,
            d.codigo_dispositivo,
            d.nombre_dispositivo,
            d.tipo_dispositivo,
            d.estado,
            d.fecha_vinculacion,
            d.nro_lote,
            t.nombre_sector,
            d.id_usuario,
            u.user_name AS responsable,
            d.id_empresa
        FROM {Config.SCHEMA}.dispositivo_iot d
        INNER JOIN {Config.SCHEMA}.terreno t ON t.nro_lote = d.nro_lote
        INNER JOIN {Config.SCHEMA}.usuario u ON u.id_usuario = d.id_usuario
        ORDER BY d.id_dispositivo DESC
    """
    return db.execute_query(query, fetchall=True)


def get_dispositivo_by_id_db(db, id_dispositivo):
    query = f"""
        SELECT
            d.id_dispositivo,
            d.codigo_dispositivo,
            d.nombre_dispositivo,
            d.tipo_dispositivo,
            d.estado,
            d.fecha_vinculacion,
            d.nro_lote,
            t.nombre_sector,
            d.id_usuario,
            u.user_name AS responsable,
            d.id_empresa
        FROM {Config.SCHEMA}.dispositivo_iot d
        INNER JOIN {Config.SCHEMA}.terreno t ON t.nro_lote = d.nro_lote
        INNER JOIN {Config.SCHEMA}.usuario u ON u.id_usuario = d.id_usuario
        WHERE d.id_dispositivo = %s
    """
    return db.execute_query(query, (id_dispositivo,), fetchone=True)


def update_dispositivo_estado_db(db, id_dispositivo, estado):
    query = f"""
        UPDATE {Config.SCHEMA}.dispositivo_iot
        SET estado = %s
        WHERE id_dispositivo = %s
    """
    return db.execute_query(query, (estado, id_dispositivo))