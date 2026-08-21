# app/services/profile_services.py
from werkzeug.security import generate_password_hash
from app.repos import profile_repos
from app.classes.postgre import PostgreSQL

def fetch_profile_data(user_id: int) -> tuple[dict, int]:
    db = PostgreSQL()
    try:
        db.create_connection()
        
        data = profile_repos.get_profile_data(db, user_id)

        if not data:
            return {'success': False, 'message': 'Perfil de usuario no encontrado.'}, 404

        return {
            'success': True,
            'message': 'Datos de Perfil Obtenidos Exitosamente.',
            'data': data
        }, 200

    except Exception as e:
        print(f'ERROR en fetch_profile_data: {e}')
        return {'success': False, 'message': f'ERROR: {str(e)}'}, 500
        
    finally:
        db.close_connection()


def modify_profile_data(data: dict, user_id: int) -> tuple[dict, int]:
    db = PostgreSQL()
    try:
        db.create_connection()
        
        new_pw_hash = None
        # Si el usuario quiere cambiar su contraseña, la validamos y encriptamos
        if data.get('newPassword'):
            if data.get('newPassword') != data.get('confirmPassword'):
                return {'success': False, 'message': 'Las nuevas contraseñas no coinciden.'}, 400
            new_pw_hash = generate_password_hash(password=data.get('newPassword'), method='pbkdf2:sha256')

        result = profile_repos.update_profile_data(db, user_id, data, new_pw_hash)

        if result and result > 0:
            accion = "ACTUALIZÓ SU PERFIL Y CONTRASEÑA" if new_pw_hash else "ACTUALIZÓ SU PERFIL"
            db.insert_log(accion, user_id)
            db.conn.commit()
            return {'success': True, 'message': 'Perfil actualizado correctamente.'}, 200

        return {'success': False, 'message': 'No hubo cambios o ocurrió un problema al actualizar tu usuario.'}, 400

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'ERROR en modify_profile_data: {e}')
        return {'success': False, 'message': f'Error al actualizar: {str(e)}'}, 500
        
    finally:
        db.close_connection()