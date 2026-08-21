# app/routes/empresas_routes.py
from flask import Blueprint, request, jsonify
from app.services import empresas_services
from app.utils.security import decode_access_token

router = Blueprint('empresas_routes', __name__)

def admin_required(func):
    """Decorator para validar token y rol de admin (Super Admin)"""
    def wrapper(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'success': False, 'message': 'No autenticado'}), 401
            
            token = auth_header.split(" ")[1]
            validation = decode_access_token(token)
            
            if not validation.get('success'):
                return jsonify({'success': False, 'message': 'Token inválido'}), 401
            
            payload = validation.get('payload', {})
            rol = int(payload.get('role', 0))
            
            # Solo rol 1 (Administrador principal) puede gestionar empresas
            if rol != 1:
                return jsonify({'success': False, 'message': 'Acceso denegado. Se requiere privilegios de Super Administrador.'}), 403
            
            return func(*args, **kwargs)
        except Exception as e:
            print(f'[ERROR en decorador admin_required] {str(e)}')
            return jsonify({'success': False, 'message': f'Error de autenticación: {str(e)}'}), 401
    
    wrapper.__name__ = func.__name__
    return wrapper

@router.route('/api/get-empresas', methods=['GET'])
@admin_required
def get_empresas():
    res, status = empresas_services.get_empresas_list()
    return jsonify(res), status

@router.route('/api/add-empresa', methods=['POST'])
@admin_required
def add_empresa():
    res, status = empresas_services.create_empresa(request.get_json())
    return jsonify(res), status

@router.route('/api/update-empresa', methods=['POST'])
@admin_required
def update_empresa():
    res, status = empresas_services.modify_empresa(request.get_json())
    return jsonify(res), status

@router.route('/api/delete-empresa', methods=['POST'])
@admin_required
def delete_empresa():
    id_empresa = request.get_json().get('id_empresa')
    res, status = empresas_services.remove_empresa(id_empresa)
    return jsonify(res), status