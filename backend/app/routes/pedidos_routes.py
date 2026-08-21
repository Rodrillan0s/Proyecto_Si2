# app/routes/pedidos_routes.py
from flask import Blueprint, request, jsonify
from app.services import pedidos_services
from app.utils.security import decode_access_token # Asumiendo que crearemos un decorador propio si lo necesitas
from functools import wraps

router = Blueprint('pedidos_routes', __name__)

# Definimos el decorador aquí para no depender de cruce de importaciones con rutas
def token_required(func):
    """Decorador genérico para validar sesión"""
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

@router.route('/api/insumos/catalogo', methods=['GET'])
@token_required 
def get_catalogo():
    id_empresa = request.args.get('id_empresa')
    res, status = pedidos_services.obtener_catalogo(id_empresa)
    return jsonify(res), status

@router.route('/api/pedidos/crear', methods=['POST'])
@token_required 
def crear_pedido():
    # Podemos inyectar el id del supervisor directo desde el token si quieres, 
    # o seguir usando el que mandas en el JSON
    data = request.get_json()
    if not data.get('id_supervisor_admin'):
        data['id_supervisor_admin'] = request.user_payload.get('user_id', request.user_payload.get('id_usuario'))
        
    res, status = pedidos_services.registrar_pedido(data)
    return jsonify(res), status

@router.route('/api/pedidos/historial', methods=['GET'])
@token_required
def get_historial():
    id_usuario = request.args.get('id_usuario')
    res, status = pedidos_services.obtener_historial(id_usuario)
    return jsonify(res), status

@router.route('/api/pedidos/detalle', methods=['GET'])
@token_required
def get_detalle():
    nro_transaccion = request.args.get('nro_transaccion')
    res, status = pedidos_services.obtener_detalle(nro_transaccion)
    return jsonify(res), status