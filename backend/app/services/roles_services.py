# app/services/roles_services.py
from app.repos import roles_repos
from app.classes.postgre import PostgreSQL

def fetch_roles() -> tuple[dict, int]:
    db = PostgreSQL()
    try:
        db.create_connection()
        data = roles_repos.get_all_roles(db)

        return {
            'success': True,
            'message': 'Roles obtenidos exitosamente.',
            'list_roles': data
        }, 200
    except Exception as e:
        print(f'ERROR en fetch_roles: {e}')
        return {'success': False, 'message': f'ERROR: {str(e)}'}, 500
    finally:
        db.close_connection()


def create_new_role(data: dict, admin_id: int) -> tuple[dict, int]:
    nombre_rol = data.get('nombre_rol')
    accion = 'CREAR NUEVO ROL'

    if not nombre_rol or str(nombre_rol).strip() == '':
        return {'success': False, 'message': 'Debe ingresar el nombre del rol.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()

        if roles_repos.exist_role(db, nombre_rol):
            return {'success': False, 'message': 'El rol ya se encuentra registrado.'}, 404
        
        insert_result = roles_repos.insert_new_role(db, nombre_rol)

        if insert_result and insert_result > 0:
            db.insert_log(accion, admin_id)
            db.conn.commit() # Confirmamos inserción y log
            return {'success': True, 'message': 'Rol registrado Exitosamente.'}, 200
            
        raise Exception('Ocurrio un problema al registrar el rol.')
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def update_role(data: dict, admin_id: int) -> tuple[dict, int]:
    id_rol = data.get("id")
    nombre_rol = data.get("nombre_rol")

    if not id_rol or not nombre_rol or str(nombre_rol).strip() == '': 
        return {'success': False, 'message': 'Debe enviar el ID y el nuevo nombre del rol.'}, 400

    nombre_rol = str(nombre_rol).upper().strip()
    accion = f"ACTUALIZACIÓN DE ROL ID {id_rol} A: {nombre_rol}"

    db = PostgreSQL()
    try:
        db.create_connection()

        update_result = roles_repos.update_role_name(db, id_rol, nombre_rol)        
        if update_result and update_result > 0:
            db.insert_log(accion=accion, id_user=admin_id)
            db.conn.commit() # Confirmamos actualización y log
            return {'success': True, 'message': 'Rol actualizado exitosamente.'}, 200
            
        return {'success': False, 'message': 'Rol no encontrado o el nombre es idéntico al actual.'}, 404

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'ERROR en update_role: {e}')
        return {'success': False, 'message': f'ERROR: {str(e)}'}, 500
    finally:
        db.close_connection()


def remove_role(data: dict, admin_id: int) -> tuple[dict, int]:
    id_rol = data.get("id")

    if not id_rol: 
        return {'success': False, 'message': 'Debe seleccionar un rol para eliminar.'}, 400

    if int(id_rol) == 1:
        return {'success': False, 'message': 'Acción bloqueada: No se puede eliminar el rol raíz del sistema.'}, 403
        
    accion = f"ELIMINACIÓN DE ROL ID: {id_rol}"

    db = PostgreSQL()
    try:
        db.create_connection()

        delete_result = roles_repos.delete_role(db, id_rol)
        
        if delete_result and delete_result > 0:
            db.insert_log(accion=accion, id_user=admin_id)
            db.conn.commit()
            return {'success': True, 'message': 'Rol eliminado exitosamente.'}, 200
            
        return {'success': False, 'message': 'Rol no encontrado.'}, 404

    except Exception as e:
        if db.conn:
            db.conn.rollback() # Limpia la transacción fallida por el error de FK
            
        print(f'ERROR en remove_role: {e}')
        error_msg = str(e).lower()
        
        # Validamos si es un error de integridad relacional (llaves foráneas)
        if "violates foreign key constraint" in error_msg or "llave foránea" in error_msg or "foreign key" in error_msg:
            return {'success': False, 'message': 'No se puede eliminar el rol porque hay usuarios asignados a él.'}, 409
            
        return {'success': False, 'message': f'ERROR: {str(e)}'}, 500
    finally:
        db.close_connection()