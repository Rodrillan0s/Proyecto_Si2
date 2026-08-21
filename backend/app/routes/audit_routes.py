# app/routes/audit_routes.py
from functools import wraps
from flask import Blueprint, jsonify, request
from app.services import audit_services
from app.utils.security import decode_access_token

router = Blueprint('audit_routes', __name__)

def admin_required(func):
    """Decorador para verificar que solo el Administrador (Rol 1) vea la auditoría."""
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
        rol = int(payload.get('role', payload.get('id_rol', 0)))

        if rol != 1:
            return jsonify({
                'success': False, 
                'message': 'Acceso denegado. Se requieren permisos de Administrador.'
            }), 403
            
        request.user_payload = payload
        return func(*args, **kwargs)
    return wrapper

@router.route('/api/get-bitacora', methods=['GET'])
@admin_required
def get_bitacora():
    response_data, status_code = audit_services.fetch_audit_logs()
    return jsonify(response_data), status_code