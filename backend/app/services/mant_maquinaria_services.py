# app/services/mant_maquinaria_services.py
from app.repos import mant_maquinaria_repos
from app.classes.postgre import PostgreSQL

TIPOS_MANT_VALIDOS = {'PREVENTIVO', 'CORRECTIVO', 'REVISION', 'EMERGENCIA'}

def _parse_registro(item):
    for campo in ('fecha_inicio', 'fecha_fin'):
        if item.get(campo):
            item[campo] = str(item[campo])
    return item


def fetch_historial_by_maquina(nro_maquina: int) -> tuple[dict, int]:
    db = PostgreSQL()
    try:
        db.create_connection()
        if not mant_maquinaria_repos.maquina_exists(db, nro_maquina):
            return {'success': False, 'message': 'La maquinaria no existe.'}, 404

        data = mant_maquinaria_repos.get_historial_by_maquina(db, nro_maquina)
        data = [_parse_registro(item) for item in data]
        return {'success': True, 'data': data}, 200
    except Exception as e:
        print(f'Error en fetch_historial_by_maquina: {e}')
        return {'success': False, 'message': f'Error del servidor: {str(e)}'}, 500
    finally:
        db.close_connection()


def fetch_all_historial() -> tuple[dict, int]:
    db = PostgreSQL()
    try:
        db.create_connection()
        data = mant_maquinaria_repos.get_all_historial(db)
        data = [_parse_registro(item) for item in data]
        return {'success': True, 'data': data}, 200
    except Exception as e:
        print(f'Error en fetch_all_historial: {e}')
        return {'success': False, 'message': f'Error del servidor: {str(e)}'}, 500
    finally:
        db.close_connection()


def register_mantenimiento(data: dict, supervisor_id: int) -> tuple[dict, int]:
    campos_requeridos = ['nro_maquina', 'tipo_mant', 'descripcion', 'fecha_inicio']
    for campo in campos_requeridos:
        if not data.get(campo):
            return {'success': False, 'message': f'El campo "{campo}" es obligatorio.'}, 400

    if data['tipo_mant'].upper() not in TIPOS_MANT_VALIDOS:
        return {'success': False, 'message': f'tipo_mant inválido. Valores aceptados: {", ".join(TIPOS_MANT_VALIDOS)}.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        if not mant_maquinaria_repos.maquina_exists(db, data.get('nro_maquina')):
            return {'success': False, 'message': 'La maquinaria no existe.'}, 404

        data['tipo_mant'] = data['tipo_mant'].upper()
        
        nro_orden = mant_maquinaria_repos.add_historial(db, data, supervisor_id)

        if not nro_orden:
            raise Exception('Ocurrió un error al registrar el mantenimiento.')

        db.insert_log(f"REGISTRÓ MANTENIMIENTO MAQUINARIA NRO: {data.get('nro_maquina')}", supervisor_id)
        db.conn.commit() # ¡Confirmamos todos los cambios juntos!

        return {'success': True, 'message': 'Mantenimiento registrado con éxito.', 'nro_orden': nro_orden}, 201
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'Error en register_mantenimiento: {e}')
        return {'success': False, 'message': f'Error al registrar: {str(e)}'}, 500
    finally:
        db.close_connection()


def modify_mantenimiento(nro_orden: int, data: dict, user_id: int) -> tuple[dict, int]:
    campos_requeridos = ['tipo_mant', 'descripcion', 'fecha_inicio']
    for campo in campos_requeridos:
        if not data.get(campo):
            return {'success': False, 'message': f'El campo "{campo}" es obligatorio.'}, 400

    if data['tipo_mant'].upper() not in TIPOS_MANT_VALIDOS:
        return {'success': False, 'message': f'tipo_mant inválido. Valores aceptados: {", ".join(TIPOS_MANT_VALIDOS)}.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        if not mant_maquinaria_repos.get_historial_by_id(db, nro_orden):
            return {'success': False, 'message': 'El registro de mantenimiento no existe.'}, 404

        data['tipo_mant'] = data['tipo_mant'].upper()
        
        # Actualizamos orden
        mant_maquinaria_repos.update_historial(db, nro_orden, data)

        # Actualizamos observaciones de maquinaria si corresponde
        if data.get('observaciones') is not None:
            mant_maquinaria_repos.update_detalle_maquina(db, nro_orden, data.get('observaciones'))

        db.insert_log(f"ACTUALIZÓ MANTENIMIENTO ORDEN NRO: {nro_orden}", user_id)
        db.conn.commit() # Confirmamos toda la actualización

        return {'success': True, 'message': 'Mantenimiento actualizado correctamente.'}, 200
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'Error en modify_mantenimiento: {e}')
        return {'success': False, 'message': f'Error al actualizar: {str(e)}'}, 500
    finally:
        db.close_connection()


def remove_mantenimiento(nro_orden: int, user_id: int) -> tuple[dict, int]:
    db = PostgreSQL()
    try:
        db.create_connection()
        if not mant_maquinaria_repos.get_historial_by_id(db, nro_orden):
            return {'success': False, 'message': 'El registro de mantenimiento no existe.'}, 404

        mant_maquinaria_repos.delete_historial(db, nro_orden)
        
        db.insert_log(f"ELIMINÓ MANTENIMIENTO ORDEN NRO: {nro_orden}", user_id)
        db.conn.commit() # Confirmamos la eliminación de ambas tablas y el log
        
        return {'success': True, 'message': 'Registro de mantenimiento eliminado correctamente.'}, 200
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'Error en remove_mantenimiento: {e}')
        return {'success': False, 'message': 'No se pudo eliminar el registro de mantenimiento.'}, 400
    finally:
        db.close_connection()