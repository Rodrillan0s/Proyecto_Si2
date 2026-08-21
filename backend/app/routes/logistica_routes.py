from flask import Blueprint, request, jsonify
from app.services import logistica_services
from app.utils.decorators import admin_or_supervisor_required, token_required

router = Blueprint('logistica_routes', __name__)

# ── CU43: Planificar ruta logística (Admin/Supervisor) ──

@router.route('/api/logistica/pedidos-pendientes', methods=['GET'])
@admin_or_supervisor_required
def get_pedidos_pendientes():
    id_empresa = request.user_payload.get('id_empresa') or request.args.get('id_empresa')
    res, status = logistica_services.listar_pedidos_pendientes(id_empresa)
    return jsonify(res), status

@router.route('/api/logistica/choferes', methods=['GET'])
@admin_or_supervisor_required
def get_choferes():
    id_empresa = request.user_payload.get('id_empresa') or request.args.get('id_empresa')
    res, status = logistica_services.listar_choferes(id_empresa)
    return jsonify(res), status

@router.route('/api/logistica/rutas', methods=['GET'])
@admin_or_supervisor_required
def get_rutas():
    id_empresa = request.user_payload.get('id_empresa') or request.args.get('id_empresa')
    estado = request.args.get('estado')
    res, status = logistica_services.listar_rutas(id_empresa, estado)
    return jsonify(res), status

@router.route('/api/logistica/rutas', methods=['POST'])
@admin_or_supervisor_required
def create_ruta():
    data = request.get_json()
    data['id_empresa'] = data.get('id_empresa') or request.user_payload.get('id_empresa')
    id_usuario = request.user_payload.get('user_id')
    res, status = logistica_services.crear_ruta(data, id_usuario)
    return jsonify(res), status

# ── CU44: Confirmar entrega (Chofer/Repartidor) ──

@router.route('/api/logistica/mis-rutas', methods=['GET'])
@token_required
def get_mis_rutas():
    id_chofer = request.user_payload.get('user_id')
    estado = request.args.get('estado')
    res, status = logistica_services.obtener_mis_rutas(id_chofer, estado)
    return jsonify(res), status

@router.route('/api/logistica/rutas/<int:id_ruta>', methods=['GET'])
@token_required
def get_ruta_detail(id_ruta):
    res, status = logistica_services.obtener_detalle_ruta(id_ruta)
    return jsonify(res), status

@router.route('/api/logistica/rutas/<int:id_ruta>/confirmar-entrega', methods=['POST'])
@token_required
def confirmar_entrega(id_ruta):
    data = request.get_json() or {}
    id_usuario = request.user_payload.get('user_id')
    res, status = logistica_services.confirmar_entrega(id_ruta, data, id_usuario)
    return jsonify(res), status

@router.route('/api/logistica/rutas/<int:id_ruta>/cancelar', methods=['POST'])
@admin_or_supervisor_required
def cancelar_ruta(id_ruta):
    id_usuario = request.user_payload.get('user_id')
    res, status = logistica_services.cancelar_ruta(id_ruta, id_usuario)
    return jsonify(res), status
