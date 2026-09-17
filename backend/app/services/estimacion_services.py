from app.repos import estimacion_repos, bitacora_repos


FORBIDDEN_TYPES = {'EQUIPO', 'HERRAMIENTA', 'MAQUINARIA'}


def _empresa(token):
    value = token.get('id_empresa')
    if not value and token.get('nombre_rol') == 'ADMINISTRADOR':
        raise ValueError('Seleccione una empresa activa para operar estimaciones.')
    if not value:
        raise ValueError('El ID de la empresa es obligatorio.')
    return int(value)


def _log(token, action, description, ip):
    bitacora_repos.registrar_bitacora(token.get('nro_usuario'), 'ESTIMACIONES_APU', action, description, ip, 'EXITOSO')


def list_apu(token, filters):
    return {'success': True, 'data': estimacion_repos.list_apu(_empresa(token), filters.get('id_obra'), filters.get('tipo_analisis_precio_unitario'), filters.get('calidad'), filters.get('activo', True))}


def get_apu(id_apu, token):
    result = estimacion_repos.get_apu(id_apu, _empresa(token))
    if not result:
        raise ValueError('La partida no existe o no pertenece a su empresa.')
    return {'success': True, 'data': result}


def create_apu(data, token, ip):
    empresa = _empresa(token)
    if data.get('tipo_analisis_precio_unitario') == 'ACABADO' and data.get('calidad') not in ('NORMAL', 'LUJO'):
        raise ValueError('Los acabados requieren calidad NORMAL o LUJO.')
    if data.get('tipo_analisis_precio_unitario') != 'ACABADO':
        data['calidad'] = None
    result = estimacion_repos.create_apu(data, empresa)
    if not result:
        raise ValueError('No se pudo crear la partida.')
    _log(token, 'CREAR_APU', f"Partida creada: {data.get('nombre')}", ip)
    return {'success': True, 'data': {'id_analisis_precio_unitario': result['id_analisis_precio_unitario']}}


def update_apu(id_apu, data, token, ip):
    empresa = _empresa(token)
    if data.get('tipo_insumo') in FORBIDDEN_TYPES:
        raise ValueError('Las herramientas, equipos y maquinaria no forman parte de una APU.')
    result = estimacion_repos.update_apu(id_apu, data, empresa)
    if not result:
        raise ValueError('La partida no existe o no pertenece a su empresa.')
    _log(token, 'ACTUALIZAR_APU', f'Partida {id_apu} actualizada.', ip)
    return {'success': True, 'data': result}


def create_insumo(id_apu, data, token, ip):
    empresa = _empresa(token)
    tipo = str(data.get('tipo_insumo', '')).upper()
    if tipo in FORBIDDEN_TYPES:
        raise ValueError('Las herramientas, equipos y maquinaria están prohibidas en las APUs.')
    if tipo not in ('MATERIAL', 'MANO_OBRA', 'OTRO'):
        raise ValueError('El tipo de insumo no es válido.')
    for field in ('nombre', 'id_unidad_medida', 'cantidad', 'precio_unitario'):
        if data.get(field) is None:
            raise ValueError(f'El campo {field} es obligatorio.')
    result = estimacion_repos.create_insumo(id_apu, data, empresa)
    if not result:
        raise ValueError('La partida no existe o no pertenece a su empresa.')
    _log(token, 'CREAR_INSUMO_APU', f'Insumo agregado a la partida {id_apu}.', ip)
    return {'success': True, 'data': result}


def list_insumos(id_apu, token):
    return {'success': True, 'data': estimacion_repos.list_insumos(id_apu, _empresa(token))}


def create_estimacion(data, token, ip):
    result = estimacion_repos.create_estimacion(data, _empresa(token))
    if not result:
        raise ValueError('La obra no existe o no pertenece a su empresa.')
    _log(token, 'CREAR_ESTIMACION', f"Estimación creada: {data.get('nombre')}", ip)
    return {'success': True, 'data': result}


def get_estimacion(id_estimacion, token):
    result = estimacion_repos.get_estimacion(id_estimacion, _empresa(token))
    if not result:
        raise ValueError('La estimación no existe o no pertenece a su empresa.')
    return {'success': True, 'data': result}


def list_estimaciones(token, id_obra=None):
    return {'success': True, 'data': estimacion_repos.list_estimaciones(_empresa(token), id_obra)}


def update_estimacion(id_estimacion, data, token, ip):
    if data.get('estado') == 'APROBADA':
        data = {**data, 'estado': 'APROBADA'}
    result = estimacion_repos.update_estimacion(id_estimacion, data, _empresa(token))
    if not result:
        raise ValueError('La estimación no existe o no pertenece a su empresa.')
    _log(token, 'ACTUALIZAR_ESTIMACION', f'Estimación {id_estimacion} actualizada.', ip)
    return {'success': True, 'data': result}


def add_estimacion_apu(id_estimacion, data, token, ip):
    result = estimacion_repos.add_estimacion_apu(id_estimacion, data, _empresa(token))
    if not result:
        raise ValueError('La estimación o la partida no existe, o ya fue agregada.')
    _log(token, 'AGREGAR_APU_ESTIMACION', f'APU agregada a estimación {id_estimacion}.', ip)
    return {'success': True, 'data': result}


def approve_estimacion(id_estimacion, token, ip):
    result = estimacion_repos.approve_estimacion(id_estimacion, _empresa(token))
    if not result:
        raise ValueError('La estimación no existe o no pertenece a su empresa.')
    _log(token, 'APROBAR_ESTIMACION', f'Estimación {id_estimacion} aprobada.', ip)
    return {'success': True, 'data': result}