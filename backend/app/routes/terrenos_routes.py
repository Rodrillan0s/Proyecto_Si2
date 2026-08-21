# app/routes/terrenos_routes.py
from flask import Blueprint, request, jsonify
from app.services import terrenos_services
from app.utils.security import decode_access_token 

router = Blueprint('terrenos_routes', __name__)

# Decorador de seguridad 
def admin_required(func):
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'No autenticado'}), 401
            
        val = decode_access_token(auth.split(" ")[1])
        if not val['success'] or val['payload'].get('role') != 1:
            return jsonify({'success': False, 'message': 'Admin requerido'}), 403
            
        request.user_payload = val['payload'] # Guardamos el payload para usar el ID
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@router.route('/api/get-terrenos', methods=['GET'])
@admin_required
def get_terrenos():
    res, status = terrenos_services.get_terrenos_list()
    return jsonify(res), status

@router.route('/api/add-terreno', methods=['POST'])
@admin_required
def add_terreno():
    user_id = request.user_payload.get('user_id')
    res, status = terrenos_services.add_new_terreno(request.get_json(), user_id)
    return jsonify(res), status

@router.route('/api/update-terreno', methods=['POST'])
@admin_required
def update_terreno():
    res, status = terrenos_services.update_existing_terreno(request.get_json())
    return jsonify(res), status

@router.route('/api/delete-terreno', methods=['POST'])
@admin_required
def delete_terreno():
    nro_lote = request.get_json().get('nro_lote')
    res, status = terrenos_services.delete_existing_terreno(nro_lote)
    return jsonify(res), status


# ========================================================
# NUEVO CÓDIGO: RUTA PARA IMPORTACIÓN MASIVA DE TERRENOS
# ========================================================
@router.route('/api/import-terrenos', methods=['POST'])
@admin_required
def import_terrenos_bulk():
    """
    Endpoint que recibe una lista JSON de terrenos (parseada en el frontend 
    a partir de un archivo Excel/CSV) y los inserta masivamente.
    """
    data = request.get_json()
    user_id = request.user_payload.get('user_id')
    res, status = terrenos_services.import_terrenos_bulk(data, user_id)
    return jsonify(res), status