# app/repos/users_repos.py
from app.config import Config

def get_all_users(db, id_empresa=None):
    query = f"""
        SELECT a.id_usuario, a.user_name, a.documento_identidad, a.nombre_razon_social, a.telefono, b.nombre_rol as rol, a.id_empresa,
        a.correo as mail
        FROM {Config.SCHEMA}.{Config.T_USER} a
        INNER JOIN {Config.SCHEMA}.{Config.T_ROL} b ON b.id = a.id_rol
    """
    params = []
    
    # Condicional Multi-tenant
    if id_empresa:
        query += " WHERE a.id_empresa = %s"
        params.append(id_empresa)
        
    return db.execute_query(query, tuple(params) if params else None, fetchall=True)


def delete_user_by_username(db, username):
    query = f"DELETE FROM {Config.SCHEMA}.{Config.T_USER} WHERE user_name = %s"
    # Quitamos commit=True, lo hará el servicio
    return db.execute_query(query, (username,))


def update_user_dynamic(db, username, fields, params):
    set_clause = ", ".join(fields)
    query = f"""
        UPDATE {Config.SCHEMA}.{Config.T_USER}
        SET {set_clause}
        WHERE user_name = %s
    """
    # Quitamos commit=True, lo hará el servicio
    return db.execute_query(query, tuple(params + [username]))


def get_all_employees(db, id_empresa=None):
    query = f"""
        SELECT id_usuario, user_name, nombre_razon_social, id_empresa
        FROM {Config.SCHEMA}.{Config.T_USER}
        WHERE id_rol = 3
    """
    params = []
    
    # Condicional Multi-tenant: usamos AND porque ya hay un WHERE
    if id_empresa:
        query += " AND id_empresa = %s"
        params.append(id_empresa)
        
    return db.execute_query(query, tuple(params) if params else None, fetchall=True)

# ========================================================
# NOTA: Para la importación masiva de usuarios 
# reutilizaremos auth_repos.insert_user desde el servicio.
# ========================================================