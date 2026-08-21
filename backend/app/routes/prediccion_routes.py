# app/routes/prediccion_routes.py
from functools import wraps
from flask import Blueprint, request, jsonify
from app.services import prediccion_services
from app.utils.security import decode_access_token

router = Blueprint('prediccion_routes', __name__)

def auth_required(func):
    """Decorator genérico para validar token y obtener usuario"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "No autenticado."}), 401

        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)

        if not validation.get("success"):
            return jsonify({"success": False, "message": "Token inválido o expirado."}), 401

        # Inyectamos el payload para usar el user_id
        request.user_payload = validation.get("payload", {})
        return func(*args, **kwargs)
    return wrapper


# GET PREDICCIÓN DE RENDIMIENTO POR CAMPAÑA
@router.route('/api/prediccion/campana/<int:id_campana>', methods=['GET'])
@auth_required
def predecir_rendimiento_campana(id_campana):
    user_id = request.user_payload.get("user_id")
    response_data, status_code = prediccion_services.predecir_rendimiento(id_campana, user_id)
    return jsonify(response_data), status_code