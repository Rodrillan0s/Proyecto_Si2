# app/routes/mant_maquinaria_routes.py
from functools import wraps
from flask import Blueprint, request, jsonify
from app.services import mant_maquinaria_services
from app.utils.security import decode_access_token

router = Blueprint('mant_maquinaria_routes', __name__)

def auth_required(func):
    """Decorator para validar token y obtener usuario"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Usuario No Autenticado."}), 401

        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)

        if not validation.get("success"):
            return jsonify({"success": False, "message": "Sesión inválida."}), 401

        request.user_payload = validation.get("payload", {})
        return func(*args, **kwargs)
    return wrapper

@router.route('/api/mantenimiento', methods=['GET'])
@auth_required
def get_all_historial():
    response, status = mant_maquinaria_services.fetch_all_historial()
    return jsonify(response), status

@router.route('/api/maquinaria/<int:nro_maquina>/mantenimiento', methods=['GET'])
@auth_required
def get_historial_by_maquina(nro_maquina):
    response, status = mant_maquinaria_services.fetch_historial_by_maquina(nro_maquina)
    return jsonify(response), status

@router.route('/api/mantenimiento', methods=['POST'])
@auth_required
def add_mantenimiento():
    data = request.get_json()
    user_id = request.user_payload.get('user_id', request.user_payload.get('id_usuario'))
    
    response, status = mant_maquinaria_services.register_mantenimiento(data, user_id)
    return jsonify(response), status

@router.route('/api/mantenimiento/<int:nro_orden>', methods=['PUT'])
@auth_required
def update_mantenimiento(nro_orden):
    data = request.get_json()
    user_id = request.user_payload.get('user_id', request.user_payload.get('id_usuario'))
    
    response, status = mant_maquinaria_services.modify_mantenimiento(nro_orden, data, user_id)
    return jsonify(response), status

@router.route('/api/mantenimiento/<int:nro_orden>', methods=['DELETE'])
@auth_required
def delete_mantenimiento(nro_orden):
    user_id = request.user_payload.get('user_id', request.user_payload.get('id_usuario'))
    
    response, status = mant_maquinaria_services.remove_mantenimiento(nro_orden, user_id)
    return jsonify(response), status