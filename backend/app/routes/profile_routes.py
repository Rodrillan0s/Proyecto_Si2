# app/routes/profile_routes.py
from functools import wraps
from flask import Blueprint, request, jsonify
from app.services import profile_services
from app.utils.security import decode_access_token

router = Blueprint('profile_routes', __name__)

def token_required(func):
    """Decorador genérico para validar sesión y extraer el user_id para el perfil"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Usuario No Autenticado."}), 401

        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)

        if not validation.get("success"):
            return jsonify({"success": False, "message": "Sesión inválida o expirada."}), 401

        request.user_payload = validation.get("payload", {})
        return func(*args, **kwargs)
    return wrapper

@router.route('/api/profile', methods=['GET'])
@token_required
def get_profile():
    # Soportamos tanto 'user_id' como 'id_usuario' dependiendo de cómo lo guardaste en el token
    user_id = request.user_payload.get('user_id', request.user_payload.get('id_usuario'))
    
    response_data, status_code = profile_services.fetch_profile_data(user_id)
    return jsonify(response_data), status_code

@router.route('/api/update-profile', methods=['PUT'])
@token_required
def update_profile():
    user_id = request.user_payload.get('user_id', request.user_payload.get('id_usuario'))
    data = request.get_json() or {}
    
    response_data, status_code = profile_services.modify_profile_data(data, user_id)
    return jsonify(response_data), status_code