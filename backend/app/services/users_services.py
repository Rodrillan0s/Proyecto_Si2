# app/services/users_service.py
from werkzeug.security import generate_password_hash
from app.repos import users_repos, auth_repos # Utilizamos los repos ya refactorizados
from app.classes.postgre import PostgreSQL

def get_users_list(id_empresa=None):
    db = PostgreSQL()
    try:
        db.create_connection()
        
        # Pasamos db
        result = users_repos.get_all_users(db, id_empresa)
        
        data = []
        if result is not None and db.cur.description:
            columns = [column[0] for column in db.cur.description]
            for row in result:
                data.append(dict(zip(columns, row)))
        
        return {
            'success': True,
            'message': 'Usuarios obtenidos exitosamente.',
            'list_users': data
        }, 200
    except Exception as e:
        error_msg = f'Error al obtener usuarios: {str(e)}'
        print(f'[ERROR] {error_msg}')
        return {'success': False, 'message': error_msg}, 500
    finally:
        db.close_connection()


def create_user(data):
    required_fields = ['user', 'doc', 'name', 'mail', 'number', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return {'success': False, 'message': f'Falta el campo: {field}'}, 400

    user_name = data.get('user').upper()
    doc = data.get('doc')
    name = data.get('name').upper()
    mail = data.get('mail').lower()
    password_hash = generate_password_hash(data.get('password'), method='pbkdf2:sha256')
    id_role = data.get('id_role', 4)    
    id_empresa = data.get('id_empresa')

    db = PostgreSQL()
    try:
        db.create_connection()
        
        # Pasamos db a auth_repos
        if auth_repos.check_user_exists(db, doc, mail, user_name):
            return {'success': False, 'message': 'El usuario ya existe.'}, 409

        ra = auth_repos.insert_user(
            db, user_name, doc, name, mail, data.get('number'), 
            data.get('dir').upper() if data.get('dir') else None, 
            password_hash, id_role, id_empresa
        )
        
        if ra and ra > 0:
            db.conn.commit() # Confirmamos los cambios
            return {'success': True, 'message': 'Usuario agregado exitosamente.'}, 201
            
        raise Exception('Error al insertar el usuario en base de datos.')
    except Exception as e:
        if db.conn:
            db.conn.rollback() # Revertimos si hay error
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def remove_user(username):
    if not username:
        return {'success': False, 'message': 'Debe seleccionar un usuario.'}, 400
        
    db = PostgreSQL()
    try:
        db.create_connection()
        ra = users_repos.delete_user_by_username(db, username)
        
        if ra and ra > 0:
            db.conn.commit() # Confirmamos el Delete
            return {'success': True, 'message': 'Usuario eliminado.', 'filas': ra}, 200
            
        return {'success': False, 'message': 'Usuario no encontrado.'}, 404
    except Exception as e:
        if db.conn:
            db.conn.rollback() # Revertimos en caso de fallo de integridad referencial
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def modify_user(data):
    username = data.get("user")
    if not username:
        return {'success': False, 'message': 'Usuario requerido.'}, 400

    fields, params = [], []
    mappings = {
        'doc': 'documento_identidad',
        'name': 'nombre_razon_social',
        'mail': 'correo',
        'number': 'telefono',
        'dir': 'direccion',
        'id_role': 'id_rol',
        'id_empresa': 'id_empresa'
    }

    for key, column in mappings.items():
        if data.get(key) is not None:
            val = data.get(key)
            fields.append(f"{column} = %s")
            params.append(val.upper() if isinstance(val, str) and key != 'mail' else val.lower() if key == 'mail' else val)

    if data.get('password'):
        fields.append("password_hash = %s")
        params.append(generate_password_hash(data.get('password'), method='pbkdf2:sha256'))

    if not fields:
        return {'success': False, 'message': 'No hay datos para actualizar.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        ra = users_repos.update_user_dynamic(db, username.upper(), fields, params)
        
        if ra and ra > 0:
            db.conn.commit() # Confirmamos el Update
            return {'success': True, 'message': 'Usuario actualizado.'}, 200
            
        return {'success': False, 'message': 'Sin cambios o usuario no encontrado.'}, 404
    except Exception as e:
        if db.conn:
            db.conn.rollback() # Revertimos si hay error
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def get_employees_list(id_empresa=None):
    db = PostgreSQL()
    try:
        db.create_connection()
        result = users_repos.get_all_employees(db, id_empresa)
        
        data = []
        if result:
            columns = ['id_usuario', 'user_name', 'nombre_razon_social', 'id_empresa']
            for row in result:
                data.append(dict(zip(columns, row)))
        
        return {
            'success': True,
            'list_empleados': data
        }, 200
    except Exception as e:
        return {'success': False, 'message': f'Error: {str(e)}'}, 500
    finally:
        db.close_connection()


# ========================================================
# NUEVO CÓDIGO: SERVICIO PARA IMPORTACIÓN MASIVA
# ========================================================
def import_users(data_list):
    """
    Recibe una lista de diccionarios (datos parseados de CSV/Excel en el frontend)
    e inserta los usuarios válidos masivamente.
    """
    if not data_list or not isinstance(data_list, list):
        return {"success": False, "message": "El formato enviado debe ser una lista de registros."}, 400

    db = PostgreSQL()
    importados = 0
    errores = []

    try:
        db.create_connection()

        for idx, item in enumerate(data_list):
            try:
                # El front puede enviar las llaves de varias formas (ej: 'user' o 'user_name')
                user_val = item.get('user') or item.get('user_name')
                doc_val = item.get('doc') or item.get('documento_identidad')
                name_val = item.get('name') or item.get('nombre_razon_social')
                mail_val = item.get('mail') or item.get('correo')
                number_val = item.get('number') or item.get('telefono')
                password_val = item.get('password')

                if not user_val or not doc_val or not name_val or not mail_val or not number_val or not password_val:
                    errores.append(f"Fila {idx+1}: Faltan campos obligatorios.")
                    continue
                
                # Normalizamos datos
                user_name = str(user_val).strip().upper()
                doc_str = str(doc_val).strip()
                name_str = str(name_val).strip().upper()
                mail_str = str(mail_val).strip().lower()
                password_hash = generate_password_hash(str(password_val), method='pbkdf2:sha256')
                
                # Valores opcionales / foráneos
                id_role = item.get('id_role', item.get('id_rol', 4))
                id_empresa = item.get('id_empresa')
                direction = item.get('dir') or item.get('direccion')
                direction = str(direction).strip().upper() if direction else None

                # Verificamos si existe antes de insertar (evita romper la transacción)
                if auth_repos.check_user_exists(db, doc_str, mail_str, user_name):
                    errores.append(f"Fila {idx+1} ({user_name}): El usuario, documento o correo ya existe.")
                    continue

                # Insertamos en base de datos
                ra = auth_repos.insert_user(
                    db, user_name, doc_str, name_str, mail_str, str(number_val), 
                    direction, password_hash, int(id_role), id_empresa
                )

                if ra and ra > 0:
                    importados += 1
                else:
                    errores.append(f"Fila {idx+1} ({user_name}): Fallo al insertar.")

            except Exception as e:
                errores.append(f"Fila {idx+1}: Error inesperado - {str(e)}")

        # Si al menos un registro se importó, hacemos commit
        if importados > 0:
            db.conn.commit()

        # Construir mensaje de respuesta
        mensaje = f"Importación finalizada. {importados} usuarios agregados exitosamente."
        if errores:
            mensaje += f" Se omitieron {len(errores)} filas con errores."

        return {
            "success": True if importados > 0 else False,
            "message": mensaje,
            "importados": importados,
            "errores": errores
        }, 201 if importados > 0 else 400

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {"success": False, "message": f"Error crítico en importación: {str(e)}"}, 500
    finally:
        db.close_connection()