# app/services/campanias_services.py
from app.repos import campanias_repos
from app.classes.postgre import PostgreSQL

def fetch_campanias() -> tuple[dict, int]:
    db = PostgreSQL()
    try:
        db.create_connection()
        data = campanias_repos.get_all_campanias(db)

        return {
            'success': True,
            'message': 'Campañas de cultivo obtenidas Exitosamente.',
            'list_campanias': data
        }, 200

    except Exception as e:
        print(f'ERROR en fetch_campanias: {e}')
        return {'success': False, 'message': f'ERROR: {str(e)}'}, 500
    finally:
        db.close_connection()

def create_campania(data: dict, admin_id: int) -> tuple[dict, int]:
    required_fields = [
        'nombre_campana', 'variedad', 'fecha_siembra',
        'fecha_cosecha', 'estado', 'rendimiento_estimado', 'nro_lote'
    ]

    for field in required_fields:
        if field not in data or str(data[field]).strip() == '':
            return {'success': False, 'message': f'Debe Ingresar Todos los Campos Requeridos. Falta: {field}'}, 400

    nombre_campana       = data.get('nombre_campana').upper()
    variedad             = data.get('variedad').upper()
    fecha_siembra        = data.get('fecha_siembra')
    fecha_cosecha        = data.get('fecha_cosecha')
    estado               = data.get('estado').upper()
    rendimiento_estimado = data.get('rendimiento_estimado')
    rendimiento_real     = data.get('rendimiento_real') # Puede ser None
    nro_lote             = data.get('nro_lote')

    accion = f"REGISTRO DE NUEVA CAMPAÑA: {nombre_campana} EN LOTE #{nro_lote}"

    db = PostgreSQL()
    try:
        db.create_connection()

        if campanias_repos.check_campania_exists(db, nombre_campana, nro_lote):
            return {'success': False, 'message': 'Ya existe una campaña con ese nombre registrada en el mismo lote.'}, 409

        ra = campanias_repos.insert_campania(
            db, nombre_campana, variedad, fecha_siembra, fecha_cosecha, 
            estado, rendimiento_estimado, rendimiento_real, nro_lote
        )

        if ra and ra > 0:
            db.insert_log(accion=accion, id_user=admin_id)
            db.conn.commit() # Confirmamos ambos: inserción y log
            return {'success': True, 'message': 'Campaña de cultivo agregada exitosamente.'}, 201

        raise Exception('Hubo un problema al registrar la campaña en la base de datos.')

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'ERROR en create_campania: {e}')
        return {'success': False, 'message': f'ERROR: {str(e)}'}, 500
    finally:
        db.close_connection()

def update_existing_campania(data: dict, admin_id: int) -> tuple[dict, int]:
    id_campana = data.get('id_campana')
    if not id_campana:
        return {'success': False, 'message': 'Debe enviar el id_campana de la campaña.'}, 400

    update_fields = []
    update_params = []

    fields_to_process = {
        'nombre_campana': True,  
        'variedad': True,
        'fecha_siembra': False,
        'fecha_cosecha': False,
        'estado': True,
        'rendimiento_estimado': False,
        'rendimiento_real': False,
        'nro_lote': False
    }

    for field, to_upper in fields_to_process.items():
        val = data.get(field)
        
        if field == 'rendimiento_real':
            if val is not None:
                update_fields.append(f"{field} = %s")
                update_params.append(val)
        elif val:
            update_fields.append(f"{field} = %s")
            update_params.append(val.upper() if to_upper else val)

    if not update_fields:
        return {'success': False, 'message': 'No se enviaron datos nuevos para actualizar.'}, 400

    update_params.append(id_campana)
    set_clause = ", ".join(update_fields)

    db = PostgreSQL()
    try:
        db.create_connection()
        result = campanias_repos.update_campania_data(db, set_clause, update_params)

        if result and result > 0:
            db.insert_log(f"ACTUALIZÓ CAMPAÑA ID: {id_campana}", admin_id)
            db.conn.commit()
            return {
                'success': True,
                'message': 'Campaña de cultivo actualizada exitosamente.',
                'filas_afectadas': result
            }, 200

        return {'success': False, 'message': 'Campaña no encontrada o los datos son idénticos a los actuales.'}, 404

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f"Error en update_existing_campania: {e}")
        return {'success': False, 'message': f"ERROR: {str(e)}"}, 500
    finally:
        db.close_connection()

def remove_campania(data: dict, admin_id: int) -> tuple[dict, int]:
    id_campana = data.get('id_campana')
    if not id_campana:
        return {'success': False, 'message': 'Debe enviar el id_campana de la campaña.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        filas_afectadas = campanias_repos.delete_campania_from_db(db, id_campana)

        if filas_afectadas and filas_afectadas > 0:
            db.insert_log(f"ELIMINÓ CAMPAÑA ID: {id_campana}", admin_id)
            db.conn.commit()
            return {
                'success': True, 
                'message': 'Campaña de cultivo eliminada exitosamente.',
                'filas_afectadas': filas_afectadas
            }, 200

        return {'success': False, 'message': 'Campaña No Encontrada.'}, 404

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f"Error en remove_campania: {e}")
        return {'success': False, 'message': f"ERROR: {str(e)}"}, 500
    finally:
        db.close_connection()