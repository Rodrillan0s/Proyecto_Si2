from flask import Blueprint, request, jsonify
from app.services import iot_services
from app.utils.decorators import admin_or_supervisor_required

router = Blueprint('iot_routes', __name__)

@router.route('/api/iot/dispositivos', methods=['GET'])
@admin_or_supervisor_required
def get_dispositivos():
    res, status = iot_services.listar_dispositivos()
    return jsonify(res), status


@router.route('/api/iot/dispositivos/<int:id_dispositivo>', methods=['GET'])
@admin_or_supervisor_required
def get_dispositivo(id_dispositivo):
    res, status = iot_services.obtener_dispositivo(id_dispositivo)
    return jsonify(res), status


@router.route('/api/iot/dispositivos', methods=['POST'])
@admin_or_supervisor_required
def add_dispositivo():
    user_id = request.user_payload.get('user_id')
    res, status = iot_services.registrar_dispositivo(request.get_json(), user_id)
    return jsonify(res), status


@router.route('/api/iot/dispositivos/estado', methods=['PATCH'])
@admin_or_supervisor_required
def update_estado_dispositivo():
    res, status = iot_services.cambiar_estado_dispositivo(request.get_json())
    return jsonify(res), status