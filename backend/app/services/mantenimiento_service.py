from ..repositories import mantenimiento_repo
from ..config import db

def registrar_mantenimiento(data, user_id):
    nro_maquina = data.get('nro_maquina')
    fecha = data.get('fecha_mantenimiento')
    tipo = data.get('tipo_mantenimiento') # Ej: PREVENTIVO o CORRECTIVO
    descripcion = data.get('descripcion')
    costo = data.get('costo', 0.0)

    # Validamos que los datos obligatorios estén presentes
    if not nro_maquina or not fecha or not tipo or not descripcion:
        return {'success': False, 'message': 'Faltan datos obligatorios (máquina, fecha, tipo o descripción).'}, 400

    try:
        db.create_connection()
        ra = mantenimiento_repo.insert_mantenimiento_db(nro_maquina, fecha, tipo.upper(), descripcion.upper(), costo, user_id)
        
        if ra > 0:
            # Opcional: Registramos en la bitácora
            db.insert_log(f"REGISTRÓ MANTENIMIENTO PARA MÁQUINA: {nro_maquina}", user_id)
            return {'success': True, 'message': 'Historial de mantenimiento registrado exitosamente.'}, 201
            
        return {'success': False, 'message': 'No se pudo registrar el mantenimiento.'}, 500
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()

def obtener_historial_maquina(nro_maquina):
    if not nro_maquina:
         return {'success': False, 'message': 'Debe proveer el número de máquina.'}, 400

    try:
        db.create_connection()
        result = mantenimiento_repo.get_historial_mantenimiento_db(nro_maquina)
        
        data = []
        if result is not None and db.cur.description:
            columns = [column[0] for column in db.cur.description]
            for row in result:
                data.append(dict(zip(columns, row)))

        return {
            'success': True,
            'message': 'Historial obtenido exitosamente.',
            'historial': data
        }, 200
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()