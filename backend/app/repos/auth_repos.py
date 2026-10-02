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

        nombre_empresa = (data.get('nombre_empresa') or '').strip().upper()
        if nombre_empresa:
            empresa_res = db.execute_query(
                f"""SELECT id_empresa FROM {Config.SCHEMA}.t_empresa
                    WHERE UPPER(nombre_empresa) = %s ORDER BY id_empresa LIMIT 1;""",
                (nombre_empresa,), fetchone=True
            )
            if empresa_res:
                id_empresa = empresa_res[0]
            else:
                empresa_res = db.execute_query(
                    f"""INSERT INTO {Config.SCHEMA}.t_empresa (nombre_empresa)
                        VALUES (%s) RETURNING id_empresa;""",
                    (nombre_empresa,), fetchone=True
                )
                id_empresa = empresa_res[0]

            usuarios_empresa = db.execute_query(
                f"SELECT 1 FROM {Config.SCHEMA}.t_usuario WHERE id_empresa = %s LIMIT 1;",
                (id_empresa,), fetchone=True
            )
            rol_empresa = db.execute_query(
                f"""SELECT id_rol FROM {Config.SCHEMA}.t_rol
                    WHERE UPPER(nombre_rol) = 'ADMINISTRADOR_EMPRESA' LIMIT 1;""",
                fetchone=True
            )
            if not usuarios_empresa and rol_empresa:
                data['nro_rol'] = rol_empresa[0]
                db.execute_query(
                    f"""INSERT INTO {Config.SCHEMA}.t_rol_permiso (id_rol, id_permiso)
                        SELECT %s, id_permiso FROM {Config.SCHEMA}.t_permiso
                        ON CONFLICT DO NOTHING;""",
                    (rol_empresa[0],)
                )
        else:
            empresa_res = db.execute_query(
                f"""SELECT id_empresa FROM {Config.SCHEMA}.t_empresa
                    WHERE nombre_empresa = %s ORDER BY id_empresa LIMIT 1;""",
                ('CLIENTES SIN EMPRESA',), fetchone=True
            )
            if not empresa_res:
                raise ValueError("No existe la empresa técnica para clientes sin empresa.")
            id_empresa = empresa_res[0]
            rol_cliente = db.execute_query(
                f"""SELECT id_rol FROM {Config.SCHEMA}.t_rol
                    WHERE UPPER(nombre_rol) = 'CLIENTE' LIMIT 1;""",
                fetchone=True
            )
            if not rol_cliente:
                raise ValueError("No existe el rol CLIENTE.")
            data['nro_rol'] = rol_cliente[0]

        query_usuario = f"""
            INSERT INTO {Config.SCHEMA}.t_usuario (username, password, correo, id_persona, id_rol, id_empresa)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_usuario;
        """
        params_usuario = (
            data.get('nombre_usuario').upper(), data.get('password_hash'), data.get('correo'),
            id_persona, data.get('nro_rol'), id_empresa
        )
        resultado = db.execute_query(query_usuario, params_usuario, commit=True, fetchone=True)
        return resultado[0] if resultado else None
    except Exception as e:
        raise ValueError(f'ERROR: {str(e)}') 
    finally:
        if created:
            db.close_connection()