# app/routes/crm_routes.py
from functools import wraps
from flask import Blueprint, request, jsonify,current_app
from app.services import crm_services
from app.utils.security import decode_access_token

router = Blueprint('crm_routes', __name__)

def crm_required(func):
    """
    Permite acceso a Admin (1) y Supervisor (2).
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'No autenticado'}), 401

        token = auth_header.split(" ")[1]
        validation = decode_access_token(token)

        if not validation.get('success'):
            return jsonify({'success': False, 'message': 'Token inválido'}), 401

        payload = validation.get('payload', {})
        rol = int(
            payload.get('role') or payload.get('rol') or payload.get('id_rol') or 0
        )

        if rol not in [1, 2]:
            return jsonify({
                'success': False,
                'message': 'Acceso denegado. Se requiere ser Admin o Supervisor.'
            }), 403

        kwargs['payload_token'] = payload
        return func(*args, **kwargs)
    return wrapper


@router.route('/api/crm/clientes', methods=['GET'])
@crm_required
def get_crm_clientes(payload_token=None):
    categoria = request.args.get('categoria')
    search = request.args.get('search')
    estado = request.args.get('estado')

    res, status = crm_services.get_clients_list(
        categoria=categoria,
        search=search,
        estado=estado,
        payload_token=payload_token
    )
    return jsonify(res), status


@router.route('/api/crm/clientes/<int:id_usuario>', methods=['GET'])
@crm_required
def get_crm_cliente_detalle(id_usuario, payload_token=None):
    res, status = crm_services.get_client_detail(
        id_usuario=id_usuario,
        payload_token=payload_token
    )
    return jsonify(res), status


@router.route('/api/crm/clientes/<int:id_usuario>/transacciones', methods=['GET'])
@crm_required
def get_crm_cliente_transacciones(id_usuario, payload_token=None):
    res, status = crm_services.get_client_transactions_service(
        id_usuario=id_usuario,
        payload_token=payload_token
    )
    return jsonify(res), status


@router.route('/api/crm/estadisticas', methods=['GET'])
@crm_required
def get_crm_estadisticas(payload_token=None):
    res, status = crm_services.get_crm_stats(payload_token=payload_token)
    return jsonify(res), status


@router.route('/api/crm/categorias', methods=['GET'])
@crm_required
def get_crm_categorias(payload_token=None):
    res, status = crm_services.get_categories()
    return jsonify(res), status


@router.route('/api/crm/health', methods=['GET'])
def crm_health():
    return jsonify({
        "success": True,
        "message": "CRM real conectado a base de datos.",
        "module": "CRM Clientes"
    }), 200

@router.route('/api/crm/notificaciones/enviar', methods=['POST'])
@crm_required
def enviar_notificacion_crm(payload_token=None):
    data = request.get_json()
    
    socketio_instance = current_app.socketio 
    
    res, status = crm_services.procesar_envio_notificaciones(data, socketio_instance)
    return jsonify(res), status