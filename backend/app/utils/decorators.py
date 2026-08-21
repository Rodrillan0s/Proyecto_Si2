from functools import wraps
from flask import request, jsonify
from app.utils.security import decode_access_token

def token_required(func):
    """Valida que el usuario tenga un token válido (Cualquier rol)"""
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


def admin_required(func):
    """Valida que el usuario sea exclusivamente Administrador (Rol 1)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'Usuario No Autenticado.'}), 401
        
        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)
        
        if not validation.get('success'):
            return jsonify({'success': False, 'message': 'Token inválido o expirado.'}), 401
            
        payload = validation.get('payload', {})
        rol = int(payload.get('role') or payload.get('id_rol') or payload.get('rol') or 0)
        
        if rol != 1:
            return jsonify({
                'success': False, 
                'message': 'Acceso denegado. Se requieren permisos de Administrador.'
            }), 403
            
        request.user_payload = payload
        return func(*args, **kwargs)
    return wrapper


def admin_or_supervisor_required(func):
    """Valida que el usuario sea Administrador (1) o Supervisor (2)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "No autenticado."}), 401

        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)

        if not validation.get("success"):
            return jsonify({"success": False, "message": "Token inválido o expirado."}), 401

        payload = validation.get("payload", {})
        rol = int(payload.get('role') or payload.get('id_rol') or payload.get('rol') or 0)

        if rol not in [1, 2]:
            return jsonify({
                "success": False, 
                "message": "Acceso denegado. Solo Administrador o Supervisor."
            }), 403

        request.user_payload = payload
        return func(*args, **kwargs)
    return wrapper