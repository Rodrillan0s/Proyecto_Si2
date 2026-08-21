# app/routes/roles_routes.py
from flask import Blueprint, request, jsonify
from app.services import roles_services
from app.utils.security import decode_access_token

router = Blueprint('roles_routes', __name__)

def admin_required(func):
    """Decorator para validar token y rol de admin en roles"""
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'Usuario No Autenticado.'}), 401
        
        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)
        
        if not validation.get('success'):
            return jsonify({'success': False, 'message': 'Usuario No Autenticado.'}), 401
            
        payload = validation.get('payload', {})
        rol = int(payload.get('role', 0))
        
        if rol != 1:
            return jsonify({'success': False, 'message': 'Acceso denegado. Se requieren permisos de Administrador.'}), 403
            
        request.user_payload = payload
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@router.route('/api/get-roles', methods=['GET'])
@admin_required
def get_roles():
   response_data, status_code = roles_services.fetch_roles()
   return jsonify(response_data), status_code

@router.route('/api/add-roles', methods=['POST'])
@admin_required
def add_roles():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Solicitud Invalida'}), 400
    
    admin_id = request.user_payload.get('user_id')
    response_data, status_code = roles_services.create_new_role(data, admin_id)
    return jsonify(response_data), status_code

@router.route('/api/update-roles', methods=['POST'])  
@admin_required
def update_roles():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No se enviaron datos en la petición.'}), 400

    admin_id = request.user_payload.get('user_id')
    response_data, status_code = roles_services.update_role(data, admin_id)
    return jsonify(response_data), status_code

@router.route('/api/delete-roles', methods=['POST'])
@admin_required
def delete_roles():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No se enviaron datos en la petición.'}), 400

    admin_id = request.user_payload.get('user_id')
    response_data, status_code = roles_services.remove_role(data, admin_id)
    return jsonify(response_data), status_code