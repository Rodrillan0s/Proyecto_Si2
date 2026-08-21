# app/routes/campanias_routes.py
from flask import Blueprint, request, jsonify
from app.services import campanias_services
from app.utils.security import decode_access_token

router = Blueprint('campanias_routes', __name__)

def admin_required(func):
    """Decorator para validar token y rol de admin"""
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

@router.route('/api/get-campanias', methods=['GET'])
@admin_required
def get_campanias():
    response_data, status_code = campanias_services.fetch_campanias()
    return jsonify(response_data), status_code

@router.route('/api/add-campania', methods=['POST'])
@admin_required
def add_campania():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Cuerpo de petición inválido o vacío'}), 400

    admin_id = request.user_payload.get('user_id')
    response_data, status_code = campanias_services.create_campania(data, admin_id)
    return jsonify(response_data), status_code

@router.route('/api/update-campania', methods=['POST'])
@admin_required
def update_campania():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Cuerpo de petición vacío.'}), 400

    admin_id = request.user_payload.get('user_id')
    response, status_code = campanias_services.update_existing_campania(data, admin_id)
    return jsonify(response), status_code

@router.route('/api/delete-campania', methods=['POST'])
@admin_required
def delete_campania():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Cuerpo de petición vacío.'}), 400

    admin_id = request.user_payload.get('user_id')
    response, status_code = campanias_services.remove_campania(data, admin_id)
    return jsonify(response), status_code