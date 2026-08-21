# app/routes/ordenes_routes.py
from flask import Blueprint, request, jsonify
from app.services import ordenes_services
from app.utils.security import decode_access_token

router = Blueprint('ordenes_routes', __name__)

def token_required(func):
    """Valida token y extrae el payload. Bloquea solo al Rol 4 (Cliente)."""
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'No autenticado'}), 401
        
        val = decode_access_token(auth.split(" ")[1])
        if not val['success']:
            return jsonify({'success': False, 'message': 'Token inválido'}), 401
            
        payload = val.get('payload', {})
        rol = int(payload.get('id_rol', payload.get('role', 0)))
        
        if rol == 4:
            return jsonify({'success': False, 'message': 'Acceso denegado. Rol no autorizado.'}), 403
            
        request.user_payload = payload
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def boss_only(func):
    """Decorador adicional: Solo permite el paso a Admin (1) y Supervisor (2)."""
    def wrapper(*args, **kwargs):
        rol = int(request.user_payload.get('id_rol', request.user_payload.get('role', 0)))
        if rol not in [1, 2]:
            return jsonify({
                'success': False, 
                'message': 'Acceso denegado. Solo Administradores o Supervisores pueden realizar esta acción.'
            }), 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@router.route('/api/get-ordenes', methods=['GET'])
@token_required
def get_ordenes():
    user_id = request.user_payload.get('id_usuario', request.user_payload.get('user_id'))
    role_id = int(request.user_payload.get('id_rol', request.user_payload.get('role', 0)))
    res, status = ordenes_services.get_ordenes_logic(user_id, role_id)
    return jsonify(res), status

@router.route('/api/add-orden', methods=['POST'])
@token_required
@boss_only
def add_orden():
    sup_id = request.user_payload.get('id_usuario', request.user_payload.get('user_id'))
    res, status = ordenes_services.create_work_order(request.get_json(), sup_id)
    return jsonify(res), status

@router.route('/api/assign-responsible', methods=['POST'])
@token_required
@boss_only
def assign_responsible():
    sup_id = request.user_payload.get('id_usuario', request.user_payload.get('user_id'))
    res, status = ordenes_services.assign_responsible_to_order(request.get_json(), sup_id)
    return jsonify(res), status

@router.route('/api/delete-orden', methods=['POST'])
@token_required
@boss_only
def delete_orden():
    sup_id = request.user_payload.get('id_usuario', request.user_payload.get('user_id'))
    res, status = ordenes_services.remove_work_order(request.get_json(), sup_id)
    return jsonify(res), status

@router.route('/api/update-mi-orden', methods=['POST'])
@token_required
def update_mi_orden():
    employee_id = request.user_payload.get('id_usuario', request.user_payload.get('user_id'))
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Cuerpo de petición vacío.'}), 400
        
    res, status = ordenes_services.update_work_order_by_employee(data, employee_id)
    return jsonify(res), status

