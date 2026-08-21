# app/routes/cultivos_routes.py
from functools import wraps
from flask import Blueprint, request, jsonify
from app.services import cultivos_services
from app.utils.security import decode_access_token

router = Blueprint("cultivos_routes", __name__)

ALLOWED_ROLES = [1, 2]

def admin_or_supervisor_required(func):
    """Decorator para validar token y permitir solo Administrador o Supervisor"""
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
        role = payload.get("id_rol") or payload.get("role")

        try:
            role = int(role)
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "Rol inválido."}), 403

        if role not in ALLOWED_ROLES:
            return jsonify({"success": False, "message": "Acceso denegado. Solo Administrador o Supervisor."}), 403

        # Guardamos el payload para inyectar el user_id a los servicios
        request.user_payload = payload
        return func(*args, **kwargs)
    return wrapper


# ==========================================
# RUTAS RESTful (Conectan exacto con React)
# ==========================================

@router.route("/api/bodega", methods=["GET"])
@admin_or_supervisor_required
def get_cultivos():
    res, status = cultivos_services.get_cultivos_list()
    return jsonify(res), status


@router.route("/api/bodega", methods=["POST"])
@admin_or_supervisor_required
def add_cultivos():
    user_id = request.user_payload.get("user_id")
    res, status = cultivos_services.create_cultivo(request.get_json(), user_id)
    return jsonify(res), status


@router.route("/api/bodega/<int:id_producto>", methods=["PUT"])
@admin_or_supervisor_required
def update_cultivos(id_producto):
    data = request.get_json() or {}
    data["id_producto"] = id_producto 
    user_id = request.user_payload.get("user_id")
    
    res, status = cultivos_services.modify_cultivo(data, user_id)
    return jsonify(res), status


@router.route("/api/bodega/<int:id_producto>", methods=["DELETE"])
@admin_or_supervisor_required
def delete_cultivos(id_producto):
    user_id = request.user_payload.get("user_id")
    res, status = cultivos_services.remove_cultivo(id_producto, user_id)
    return jsonify(res), status


# ========================================================
# NUEVO CÓDIGO: RUTA PARA IMPORTACIÓN MASIVA
# ========================================================

@router.route("/api/bodega/import", methods=["POST"])
@admin_or_supervisor_required
def import_cultivos_bulk():
    """
    Endpoint que recibe una lista JSON de productos (parseada en el frontend 
    a partir de un archivo Excel/CSV) y los inserta de forma masiva.
    """
    data = request.get_json()
    user_id = request.user_payload.get("user_id")
    
    res, status = cultivos_services.import_cultivos(data, user_id)
    return jsonify(res), status