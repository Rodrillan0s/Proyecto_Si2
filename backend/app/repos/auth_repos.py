from app.classes.postgres import PostgreSQL
from app.config import Config
import json

def obtener_usuario_por_login_sp(identificador: str, db: PostgreSQL = None):
    created = False
    if db is None:
        db = PostgreSQL()
        db.create_connection()
        created = True
    try:
        query = "SELECT obras.sp_login_usuario(%s);"
        resultado = db.execute_query(query, (identificador,), commit=True, fetchone=True)
        if resultado and resultado[0]:
            res_dict = resultado[0]
            if isinstance(res_dict, str):
                res_dict = json.loads(res_dict)
            return res_dict
        return {"success": False, "error": "Error al conectar con la base de datos."}
    except Exception as e:
        raise ValueError(f'ERROR: {str(e)}') 
    finally:
        if created:
            db.close_connection()

def registrar_intento_fallido_sp(id_usuario: int, db: PostgreSQL = None):
    created = False
    if db is None:
        db = PostgreSQL()
        db.create_connection()
        created = True
    try:
        query = "SELECT obras.sp_registrar_intento_fallido(%s);"
        resultado = db.execute_query(query, (id_usuario,), commit=True, fetchone=True)
        if resultado and resultado[0]:
            res_dict = resultado[0]
            if isinstance(res_dict, str):
                res_dict = json.loads(res_dict)
            return res_dict
        return None
    except Exception as e:
        raise ValueError(f'ERROR: {str(e)}')
    finally:
        if created:
            db.close_connection()

def login_exitoso_sp(id_usuario: int, dispositivo_hash: str, db: PostgreSQL = None):
    created = False
    if db is None:
        db = PostgreSQL()
        db.create_connection()
        created = True
    try:
        query = "SELECT obras.sp_login_exitoso(%s, %s);"
        db.execute_query(query, (id_usuario, dispositivo_hash), commit=True)
    except Exception as e:
        raise ValueError(f'ERROR: {str(e)}')
    finally:
        if created:
            db.close_connection()

def existe_persona_por_ci(ci: str, db: PostgreSQL = None):
    created = False
    if db is None:
        db = PostgreSQL()
        db.create_connection()
        created = True
    try:
        query = f"SELECT 1 FROM {Config.SCHEMA}.t_persona WHERE ci = %s;"
        result = db.execute_query(query, (ci,), fetchone=True)
        if result:
            return True
        return False
    except Exception as e:
        raise ValueError(f'ERROR: {str(e)}') 
    finally:
        if created:
            db.close_connection()

def existe_nombre_usuario(nombre_usuario: str, db: PostgreSQL = None):
    created = False
    if db is None:
        db = PostgreSQL()
        db.create_connection()
        created = True
    try:
        query = f"SELECT 1 FROM {Config.SCHEMA}.t_usuario WHERE UPPER(username) = %s;"
        result = db.execute_query(query, (nombre_usuario,), fetchone=True)
        if result:
            return True
        return False
    except Exception as e:
        raise ValueError(f'ERROR: {str(e)}') 
    finally:
        if created:
            db.close_connection()

def registrar_usuario_bd(data: dict, persona_existe: bool, db: PostgreSQL = None):
    created = False
    if db is None:
        db = PostgreSQL()
        db.create_connection()
        created = True
    try:
        if not persona_existe:
            query_persona = f"""
                INSERT INTO {Config.SCHEMA}.t_persona (ci, nombre_completo, telefono, direccion)
                VALUES (%s, %s, %s, %s)
                RETURNING id_persona;
            """
            params_persona = (
                data.get('ci'), data.get('nombre_completo').upper(), data.get('telefono'), 
                data.get('direccion')
            )
            persona_res = db.execute_query(query_persona, params_persona, fetchone=True)
            id_persona = persona_res[0] if persona_res else None
        else:
            query_get_id = f"SELECT id_persona FROM {Config.SCHEMA}.t_persona WHERE ci = %s;"
            id_res = db.execute_query(query_get_id, (data.get('ci'),), fetchone=True)
            id_persona = id_res[0] if id_res else None

        if not id_persona:
            raise ValueError("No se pudo obtener o registrar la persona.")

        query_usuario = f"""
            INSERT INTO {Config.SCHEMA}.t_usuario (username, password, correo, id_persona, id_rol, id_empresa)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_usuario;
        """
        params_usuario = (
            data.get('nombre_usuario').upper(), data.get('password_hash'), data.get('correo'),
            id_persona, data.get('nro_rol'), data.get('id_empresa')
        )
        resultado = db.execute_query(query_usuario, params_usuario, commit=True, fetchone=True)
        return resultado[0] if resultado else None
    except Exception as e:
        raise ValueError(f'ERROR: {str(e)}') 
    finally:
        if created:
            db.close_connection()