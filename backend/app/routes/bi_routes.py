from flask import Blueprint, request, jsonify
from app.services import bi_services
from app.utils.security import decode_access_token
from functools import wraps

router = Blueprint('bi_routes', __name__)

def token_required(func):
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

def boss_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        rol = int(request.user_payload.get('id_rol', request.user_payload.get('role', 0)))
        # Asumiendo 1 = Admin, 2 = Gerente/Supervisor
        if rol not in [1, 2]:
            return jsonify({"success": False, "message": "Acceso denegado. Reportes exclusivos para gerencia."}), 403
        return func(*args, **kwargs)
    return wrapper

@router.route('/api/bi/dashboard', methods=['GET'])
@token_required
@boss_only
def get_dashboard():
    # Sacamos el id_empresa directo del token para evitar inyecciones
    id_empresa = request.user_payload.get('id_empresa', 1) 
    res, status = bi_services.obtener_dashboard_kpis(id_empresa)
    return jsonify(res), status