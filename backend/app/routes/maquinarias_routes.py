# app/routes/maquinarias_routes.py
from flask import Blueprint, request, jsonify
from app.services import maquinarias_services
from app.utils.security import decode_access_token

router = Blueprint('maquinaria_routes', __name__)

def auth_required(func):
    """Decorator para validar token en el módulo de maquinaria"""
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'Usuario No Autenticado.'}), 401
        
        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)
        
        if not validation.get('success'):
            return jsonify({'success': False, 'message': 'Sesión inválida.'}), 401
            
        # Extraemos el payload completo en la petición
        request.user_payload = validation.get('payload', {})
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@router.route('/api/maquinaria', methods=['GET'])
@auth_required
def get_maquinaria():
    response, status = maquinarias_services.fetch_maquinaria()
    return jsonify(response), status

@router.route('/api/maquinaria', methods=['POST'])
@auth_required
def add_maquinaria():
    data = request.get_json()
    user_id = request.user_payload.get('user_id')
    response, status = maquinarias_services.register_maquinaria(data, user_id)
    return jsonify(response), status

@router.route('/api/maquinaria/<int:nro_maquina>', methods=['PUT'])
@auth_required
def update_maquinaria(nro_maquina):
    data = request.get_json()
    user_id = request.user_payload.get('user_id')
    response, status = maquinarias_services.modify_maquinaria(nro_maquina, data, user_id)
    return jsonify(response), status

@router.route('/api/maquinaria/<int:nro_maquina>', methods=['DELETE'])
@auth_required
def delete_maquinaria(nro_maquina):
    user_id = request.user_payload.get('user_id')
    response, status = maquinarias_services.remove_maquinaria(nro_maquina, user_id)
    return jsonify(response), status

# ========================================================
# NUEVO CÓDIGO: RUTA PARA IMPORTACIÓN MASIVA DE MAQUINARIA
# ========================================================
@router.route('/api/maquinaria/import', methods=['POST'])
@auth_required
def import_maquinaria_bulk():
    """
    Endpoint que recibe una lista JSON de maquinarias (parseada en el frontend 
    a partir de un archivo Excel/CSV) y las inserta masivamente.
    """
    data = request.get_json()
    user_id = request.user_payload.get('user_id')
    
    response, status = maquinarias_services.import_maquinaria_bulk(data, user_id)
    return jsonify(response), status