# app/routes/users_routes.py
from flask import Blueprint, request, jsonify
from app.services import users_services
from app.utils.security import decode_access_token

router = Blueprint('users_routes', __name__)

def admin_required(func):
    """Decorator para validar token y rol de admin"""
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'No autenticado'}), 401
        
        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)
        
        payload = validation.get('payload', {})
        rol = int(payload.get('role', payload.get('role', 0)))
        
        if not validation['success'] or rol != 1:
            return jsonify({'success': False, 'message': 'Acceso denegado (Admin Requerido)'}), 403
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

def boss_required(func):
    """Valida que sea Admin (1) o Supervisor (2) para ver la lista de empleados"""
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'No autenticado'}), 401
        
        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)
        
        if not validation['success']:
            return jsonify({'success': False, 'message': 'Token inválido'}), 401
            
        payload = validation.get('payload', {})
        rol = int(payload.get('role', payload.get('role', 0)))
        
        if rol not in [1, 2]:
            return jsonify({'success': False, 'message': 'Acceso denegado. Se requiere ser Admin o Supervisor.'}), 403
            
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@router.route('/api/get-users', methods=['GET'])
@admin_required
def get_users():
    id_empresa = request.args.get('id_empresa')
    res, status = users_services.get_users_list(id_empresa)
    return jsonify(res), status

@router.route('/api/add-users', methods=['POST'])
@admin_required
def add_users():
    res, status = users_services.create_user(request.get_json())
    return jsonify(res), status

@router.route('/api/delete-users', methods=['POST'])
@admin_required
def delete_users():
    username = request.get_json().get('user')
    res, status = users_services.remove_user(username)
    return jsonify(res), status

@router.route('/api/update-users', methods=['POST'])
@admin_required
def update_users():
    res, status = users_services.modify_user(request.get_json())
    return jsonify(res), status

@router.route('/api/get-empleados', methods=['GET'])
@boss_required
def get_empleados():
    id_empresa = request.args.get('id_empresa')
    res, status = users_services.get_employees_list(id_empresa)
    return jsonify(res), status

# ========================================================
# NUEVO CÓDIGO: RUTA PARA IMPORTACIÓN MASIVA DE USUARIOS
# ========================================================
@router.route('/api/import-users', methods=['POST'])
@admin_required
def import_users_bulk():
    """
    Endpoint que recibe una lista JSON de usuarios (parseada en el frontend 
    a partir de un archivo Excel/CSV) y los inserta de forma masiva.
    """
    data = request.get_json()
    res, status = users_services.import_users(data)
    return jsonify(res), status