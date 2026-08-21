# app/repos/auth_repos.py
from app.config import Config

def check_user_exists(db, doc, mail, user_name):
    check_query = f"""
        SELECT 1
        FROM {Config.SCHEMA}.{Config.T_USER}
        WHERE DOCUMENTO_IDENTIDAD=%s OR CORREO=%s 
        OR USER_NAME=%s
        LIMIT 1
    """
    check_params = (doc, mail, user_name)
    return db.execute_query(check_query, check_params, fetchone=True)


def insert_user(db, user, doc, name, mail, number, direction, password_hash, id_role=4, id_empresa=None):
    if direction:
        insert_query = f"""
            INSERT INTO {Config.SCHEMA}.{Config.T_USER} 
            (USER_NAME,PASSWORD_HASH,DOCUMENTO_IDENTIDAD,NOMBRE_RAZON_SOCIAL,DIRECCION,CORREO,TELEFONO,ID_ROL,ID_EMPRESA)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        params = (user, password_hash, doc, name, direction, mail, number, id_role, id_empresa)
    else:
        insert_query = f"""
            INSERT INTO {Config.SCHEMA}.{Config.T_USER} 
            (USER_NAME,PASSWORD_HASH,DOCUMENTO_IDENTIDAD,NOMBRE_RAZON_SOCIAL,CORREO,TELEFONO,ID_ROL,ID_EMPRESA)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """
        params = (user, password_hash, doc, name, mail, number, id_role, id_empresa)

    # Nota importante: Eliminamos commit=True, el commit lo hará el Servicio
    return db.execute_query(query=insert_query, params=params)


def get_user_id_by_username(db, username):
    query = f"""
        SELECT id_usuario
        FROM {Config.SCHEMA}.{Config.T_USER}
        WHERE user_name=%s
    """
    return db.execute_query(query=query, params=(username,), fetchone=True)


def extract_login_user(db, user_input):
    query = f"""
        SELECT ID_USUARIO, USER_NAME, PASSWORD_HASH, NOMBRE_RAZON_SOCIAL, CORREO, ID_ROL, ESTADO_CUENTA, ID_EMPRESA
        FROM {Config.SCHEMA}.{Config.T_USER}
        WHERE UPPER(CORREO) = %s OR USER_NAME = %s
    """
    params = (user_input, user_input)
    return db.execute_query(query=query, params=params, fetchone=True)