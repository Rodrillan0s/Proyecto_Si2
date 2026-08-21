from app.repos import empresas_repos
from app.classes.postgre import PostgreSQL

def get_empresas_list():
    db = PostgreSQL()
    try:
        db.create_connection()
        
        if not db.conn or not db.cur:
            raise RuntimeError('No se pudo establecer conexión con la base de datos')
        
        result = empresas_repos.get_all_empresas(db)
        
        data = []
        if result is not None and db.cur.description:
            columns = [column[0] for column in db.cur.description]
            for row in result:
                # Formateamos la fecha si existe para evitar errores de serialización JSON
                row_dict = dict(zip(columns, row))
                if 'created_at' in row_dict and row_dict['created_at']:
                    row_dict['created_at'] = row_dict['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                data.append(row_dict)
        
        return {
            'success': True,
            'message': 'Empresas obtenidas exitosamente.',
            'list_empresas': data
        }, 200
    except Exception as e:
        error_msg = f'Error al obtener empresas: {str(e)}'
        print(f'[ERROR] {error_msg}')
        return {'success': False, 'message': error_msg}, 500
    finally:
        db.close_connection()

def create_empresa(data):
    # Validar campos obligatorios
    if not data.get('nombre_empresa'):
        return {'success': False, 'message': 'El nombre de la empresa es obligatorio.'}, 400

    nombre_empresa = data.get('nombre_empresa').upper()
    nit = data.get('nit') # Puede ser None
    estado = data.get('estado', 'ACTIVO').upper()

    db = PostgreSQL()
    try:
        db.create_connection()
        
        ra = empresas_repos.insert_empresa(db, nombre_empresa, nit, estado)
        
        if ra and ra > 0:
            db.conn.commit() # Confirmar inserción
            return {'success': True, 'message': 'Empresa registrada exitosamente.'}, 201
            
        raise Exception('Error al registrar la empresa en la base de datos.')
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()

def remove_empresa(id_empresa):
    if not id_empresa:
        return {'success': False, 'message': 'Debe proporcionar el ID de la empresa.'}, 400
        
    db = PostgreSQL()
    try:
        db.create_connection()
        ra = empresas_repos.delete_empresa(db, id_empresa)
        
        if ra and ra > 0:
            db.conn.commit() # Confirmar eliminación
            return {'success': True, 'message': 'Empresa eliminada correctamente.', 'filas': ra}, 200
            
        return {'success': False, 'message': 'Empresa no encontrada.'}, 404
    except Exception as e:
        if db.conn:
            db.conn.rollback() # Fundamental para que el error de llave foránea no rompa la sesión
            
        # Capturamos si hay error de llave foránea (intentar borrar empresa con datos)
        if "violates foreign key constraint" in str(e):
            return {'success': False, 'message': 'No se puede eliminar la empresa porque tiene datos (usuarios, órdenes) asociados.'}, 409
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()

def modify_empresa(data):
    id_empresa = data.get("id_empresa")
    if not id_empresa:
        return {'success': False, 'message': 'ID de empresa requerido.'}, 400

    fields, params = [], []
    mappings = {
        'nombre_empresa': 'nombre_empresa',
        'nit': 'nit',
        'estado': 'estado'
    }

    for key, column in mappings.items():
        if data.get(key) is not None:
            val = data.get(key)
            fields.append(f"{column} = %s")
            # Convertimos a mayúsculas para estandarizar
            params.append(val.upper() if isinstance(val, str) else val)

    if not fields:
        return {'success': False, 'message': 'No hay datos para actualizar.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        ra = empresas_repos.update_empresa_dynamic(db, id_empresa, fields, params)
        
        if ra and ra > 0:
            db.conn.commit() # Confirmar actualización
            return {'success': True, 'message': 'Empresa actualizada correctamente.'}, 200
            
        return {'success': False, 'message': 'Sin cambios o empresa no encontrada.'}, 404
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()