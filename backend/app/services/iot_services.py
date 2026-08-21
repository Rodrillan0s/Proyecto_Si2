from app.classes.postgre import PostgreSQL
from app.repos import iot_repos

def rows_to_dicts(db, rows):
    data = []
    if rows is not None and db.cur.description:
        columns = [column[0] for column in db.cur.description]
        for row in rows:
            data.append(dict(zip(columns, row)))
    return data


def row_to_dict(db, row):
    if not row or not db.cur.description:
        return None
    columns = [column[0] for column in db.cur.description]
    return dict(zip(columns, row))


def registrar_dispositivo(data, id_usuario):
    required = ['codigo_dispositivo', 'nombre_dispositivo', 'nro_lote']

    for field in required:
        if not data.get(field):
            return {'success': False, 'message': f'Falta el campo: {field}'}, 400

    codigo = str(data.get('codigo_dispositivo')).strip().upper()
    nombre = str(data.get('nombre_dispositivo')).strip().upper()
    tipo = str(data.get('tipo_dispositivo', 'TELEMETRIA')).strip().upper()
    estado = str(data.get('estado', 'ACTIVO')).strip().upper()
    nro_lote = data.get('nro_lote')

    db = PostgreSQL()

    try:
        db.create_connection()

        if iot_repos.check_dispositivo_duplicate_db(db, codigo):
            return {'success': False, 'message': 'El código del dispositivo ya está registrado.'}, 409

        if not iot_repos.check_terreno_exists_db(db, nro_lote):
            return {'success': False, 'message': 'El terreno o parcela no existe.'}, 404

        empresa_row = iot_repos.get_empresa_usuario_db(db, id_usuario)
        id_empresa = empresa_row[0] if empresa_row else None

        ra = iot_repos.insert_dispositivo_db(
            db,
            codigo,
            nombre,
            tipo,
            estado,
            nro_lote,
            id_usuario,
            id_empresa
        )

        if ra and ra > 0:
            db.insert_log(
                accion=f'VINCULACION DE DISPOSITIVO IOT {codigo} AL LOTE {nro_lote}',
                id_user=id_usuario
            )
            return {'success': True, 'message': 'Dispositivo IoT vinculado correctamente.'}, 201

        raise Exception('No se pudo registrar el dispositivo IoT.')

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def listar_dispositivos():
    db = PostgreSQL()

    try:
        db.create_connection()
        rows = iot_repos.get_dispositivos_db(db)
        data = rows_to_dicts(db, rows)

        return {'success': True, 'dispositivos': data}, 200

    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def obtener_dispositivo(id_dispositivo):
    if not id_dispositivo:
        return {'success': False, 'message': 'id_dispositivo requerido.'}, 400

    db = PostgreSQL()

    try:
        db.create_connection()
        row = iot_repos.get_dispositivo_by_id_db(db, id_dispositivo)
        data = row_to_dict(db, row)

        if not data:
            return {'success': False, 'message': 'Dispositivo no encontrado.'}, 404

        return {'success': True, 'dispositivo': data}, 200

    except Exception as e:
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()


def cambiar_estado_dispositivo(data):
    id_dispositivo = data.get('id_dispositivo')
    estado = data.get('estado')

    if not id_dispositivo:
        return {'success': False, 'message': 'id_dispositivo requerido.'}, 400

    if not estado:
        return {'success': False, 'message': 'estado requerido.'}, 400

    estado = str(estado).strip().upper()

    db = PostgreSQL()

    try:
        db.create_connection()
        ra = iot_repos.update_dispositivo_estado_db(db, id_dispositivo, estado)

        if ra and ra > 0:
            db.conn.commit()
            return {'success': True, 'message': 'Estado del dispositivo actualizado.'}, 200

        return {'success': False, 'message': 'Dispositivo no encontrado o sin cambios.'}, 404

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        return {'success': False, 'message': str(e)}, 500
    finally:
        db.close_connection()