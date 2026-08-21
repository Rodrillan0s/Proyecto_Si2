from flask import Blueprint, request, jsonify
from app.services import fidelizacion_services
from app.utils.decorators import admin_or_supervisor_required

router = Blueprint('fidelizacion_routes', __name__)

@router.route('/api/fidelizacion/niveles', methods=['GET'])
@admin_or_supervisor_required
def get_niveles():
    id_empresa = request.user_payload.get('id_empresa') or request.args.get('id_empresa')
    res, status = fidelizacion_services.listar_niveles(id_empresa)
    return jsonify(res), status

@router.route('/api/fidelizacion/niveles', methods=['POST'])
@admin_or_supervisor_required
def create_nivel():
    data = request.get_json() or {}
    data['id_empresa'] = data.get('id_empresa') or request.user_payload.get('id_empresa')
    id_usuario = request.user_payload.get('user_id')
    res, status = fidelizacion_services.crear_nivel(data, id_usuario)
    return jsonify(res), status

@router.route('/api/fidelizacion/niveles/<int:id_nivel>', methods=['PUT'])
@admin_or_supervisor_required
def update_nivel(id_nivel):
    data = request.get_json() or {}
    id_usuario = request.user_payload.get('user_id')
    res, status = fidelizacion_services.actualizar_nivel(id_nivel, data, id_usuario)
    return jsonify(res), status

@router.route('/api/fidelizacion/niveles/<int:id_nivel>', methods=['DELETE'])
@admin_or_supervisor_required
def delete_nivel(id_nivel):
    id_usuario = request.user_payload.get('user_id')
    res, status = fidelizacion_services.desactivar_nivel(id_nivel, id_usuario)
    return jsonify(res), status

@router.route('/api/fidelizacion/clientes', methods=['GET'])
@admin_or_supervisor_required
def get_clientes_fidelizacion():
    id_empresa = request.user_payload.get('id_empresa') or request.args.get('id_empresa')
    res, status = fidelizacion_services.listar_clientes(id_empresa)
    return jsonify(res), status
