from app.classes.postgres import PostgreSQL
from app.config import Config

# --- LEER USUARIOS ---
def obtener_todos_los_usuarios(id_empresa=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"""
            SELECT 
                a.id_usuario, b.ci, a.username, a.id_empresa, d.nombre_empresa,
                b.nombre_completo, a.correo, b.telefono, b.direccion,
                c.nombre_rol, a.id_rol
            FROM {Config.SCHEMA}.t_usuario a
            LEFT JOIN {Config.SCHEMA}.t_persona b ON a.id_persona = b.id_persona
            LEFT JOIN {Config.SCHEMA}.t_rol c ON a.id_rol = c.id_rol
            LEFT JOIN {Config.SCHEMA}.t_empresa d ON d.id_empresa = a.id_empresa
            WHERE (%s IS NULL OR a.id_empresa = %s);
        """
        resultados = db.execute_query(query, (id_empresa, id_empresa), fetchall=True)
        
        usuarios = []
        if resultados:
            for r in resultados:
                usuarios.append({
                    "nro_usuario": r[0], "ci": r[1], "nombre_usuario": r[2],
                    "estado": "ACTIVO", "id_empresa": r[3], "nombre_empresa": r[4],
                    "nombre_completo": r[5],
                    "correo": r[6], "telefono": r[7], "direccion": r[8],
                    "nombre_rol": r[9], "nro_rol": r[10]
                })
        return usuarios
    finally:
        db.close_connection()

# --- CREAR USUARIO ---
def crear_usuario_db(datos_persona, datos_usuario):
    db = PostgreSQL()
    db.create_connection()
    try:
        #INSERTAR DATOS PERSONA
        query_persona = f"""
            INSERT INTO {Config.SCHEMA}.t_persona (ci, nombre_completo, telefono, direccion)
            VALUES (%s, %s, %s, %s)
            RETURNING id_persona;
        """
        persona = db.execute_query(query_persona, datos_persona, fetchone=True)

        #INSERTAR DATOS USUARIO
        query_usuario = f"""
            INSERT INTO {Config.SCHEMA}.t_usuario (username, password, correo, id_persona, id_rol, id_empresa)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_usuario;
        """
        id_empresa = datos_usuario[5]
        if id_empresa is None:
            empresa_res = db.execute_query(
                f"""SELECT id_empresa FROM {Config.SCHEMA}.t_empresa
                    WHERE nombre_empresa = %s ORDER BY id_empresa LIMIT 1;""",
                ('CLIENTES SIN EMPRESA',), fetchone=True
            )
            if not empresa_res:
                raise ValueError("No existe la empresa técnica para clientes sin empresa.")
            id_empresa = empresa_res[0]

        datos_usuario = (datos_usuario[0], datos_usuario[1], datos_usuario[2], persona[0], datos_usuario[4], id_empresa)
        resultado = db.execute_query(query_usuario, datos_usuario, fetchone=True, commit=True)
        
        return resultado[0] if resultado else None
    finally:
        db.close_connection()

# --- ACTUALIZAR USUARIO ---
def actualizar_usuario_db(nro_usuario, ci, datos_persona, datos_usuario, cambiar_password=False):
    db = PostgreSQL()
    db.create_connection()
    try:
        query_persona = f"""
            UPDATE {Config.SCHEMA}.t_persona
            SET nombre_completo = %s, telefono = %s, direccion = %s
            WHERE ci = %s;
        """
        db.execute_query(query_persona, datos_persona + (ci,))

        if cambiar_password:
            query_usuario = f"""
                UPDATE {Config.SCHEMA}.t_usuario
                SET username = %s, password = %s, correo = %s, id_rol = %s, id_empresa = %s
                WHERE id_usuario = %s;
            """
        else:
            query_usuario = f"""
                UPDATE {Config.SCHEMA}.t_usuario
                SET username = %s, correo = %s, id_rol = %s, id_empresa = %s
                WHERE id_usuario = %s;
            """
        
        db.execute_query(query_usuario, datos_usuario + (nro_usuario,), commit=True)
        return True
    finally:
        db.close_connection()

# --- ELIMINAR USUARIO ---
def eliminar_usuario_db(nro_usuario: int, id_empresa=None):
    db = PostgreSQL()
    db.create_connection()
    try:
        query = f"DELETE FROM {Config.SCHEMA}.t_usuario WHERE id_usuario = %s AND (%s IS NULL OR id_empresa = %s);"
        filas = db.execute_query(query, (nro_usuario, id_empresa, id_empresa), commit=True)
        return filas > 0
    finally:
        db.close_connection()