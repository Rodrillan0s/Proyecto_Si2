from app.repos import logistica_repos
from app.classes.postgre import PostgreSQL

def _validar_id_empresa(id_empresa):
    if not id_empresa:
        return None, {'success': False, 'message': 'ID de empresa requerido.'}, 400
    try:
        return int(id_empresa), None, None
    except (ValueError, TypeError):
        return None, {'success': False, 'message': 'ID de empresa inválido.'}, 400

def listar_pedidos_pendientes(id_empresa):
    id_val, err, status = _validar_id_empresa(id_empresa)
    if err:
        return err, status

    db = PostgreSQL()
    try:
        db.create_connection()
        result = logistica_repos.get_pedidos_pendientes_ruta(db, id_val)

        data = []
        if result and db.cur.description:
            columns = [c[0] for c in db.cur.description]
            for row in result:
                row_dict = dict(zip(columns, row))
                row_dict['fecha_hora'] = row_dict['fecha_hora'].strftime('%Y-%m-%d %H:%M') if row_dict['fecha_hora'] else ''
                row_dict['monto_total'] = float(row_dict['monto_total'])
                data.append(row_dict)

        return {'success': True, 'pedidos': data}, 200
    except Exception as e:
        print(f'[ERROR listar_pedidos_pendientes] {str(e)}')
        return {'success': False, 'message': f'Error interno: {str(e)}'}, 500
    finally:
        db.close_connection()

def listar_choferes(id_empresa):
    id_val, err, status = _validar_id_empresa(id_empresa)
    if err:
        return err, status

    db = PostgreSQL()
    try:
        db.create_connection()
        result = logistica_repos.get_choferes_disponibles(db, id_val)

        data = []
        if result and db.cur.description:
            columns = [c[0] for c in db.cur.description]
            for row in result:
                row_dict = dict(zip(columns, row))
                data.append(row_dict)

        return {'success': True, 'choferes': data}, 200
    except Exception as e:
        print(f'[ERROR listar_choferes] {str(e)}')
        return {'success': False, 'message': f'Error interno: {str(e)}'}, 500
    finally:
        db.close_connection()

def crear_ruta(data, id_usuario_logeado):
    id_transaccion = data.get('id_transaccion')
    id_chofer = data.get('id_chofer')
    id_empresa = data.get('id_empresa')
    origen = data.get('origen')
    destino = data.get('destino')
    fecha_entrega_estimada = data.get('fecha_entrega_estimada')

    if not all([id_transaccion, id_chofer, id_empresa, origen, destino, fecha_entrega_estimada]):
        return {'success': False, 'message': 'Todos los campos obligatorios deben estar completos.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()

        row_id = logistica_repos.insert_ruta(
            db, id_transaccion, id_chofer, id_empresa,
            origen, destino, fecha_entrega_estimada
        )

        if not row_id:
            raise Exception('No se pudo generar el ID de la ruta.')

        id_ruta = row_id[0]

        logistica_repos.update_estado_transaccion(db, id_transaccion, 'EN_RUTA')

        db.insert_log(f'CREÓ RUTA LOGÍSTICA #{id_ruta} para transacción #{id_transaccion}', id_usuario_logeado)

        db.conn.commit()

        return {
            'success': True,
            'message': 'Ruta logística registrada exitosamente.',
            'id_ruta': id_ruta
        }, 201

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'[ERROR crear_ruta] {str(e)}')
        return {'success': False, 'message': f'Error al crear la ruta: {str(e)}'}, 500
    finally:
        db.close_connection()

def listar_rutas(id_empresa, estado=None):
    id_val, err, status = _validar_id_empresa(id_empresa)
    if err:
        return err, status

    db = PostgreSQL()
    try:
        db.create_connection()
        result = logistica_repos.get_rutas_by_empresa(db, id_val, estado)

        data = []
        if result and db.cur.description:
            columns = [c[0] for c in db.cur.description]
            for row in result:
                row_dict = dict(zip(columns, row))
                row_dict['fecha_asignacion'] = row_dict['fecha_asignacion'].strftime('%Y-%m-%d %H:%M') if row_dict['fecha_asignacion'] else ''
                row_dict['fecha_entrega_estimada'] = row_dict['fecha_entrega_estimada'].strftime('%Y-%m-%d') if row_dict['fecha_entrega_estimada'] else ''
                row_dict['fecha_entrega_real'] = row_dict['fecha_entrega_real'].strftime('%Y-%m-%d %H:%M') if row_dict['fecha_entrega_real'] else ''
                row_dict['monto_total'] = float(row_dict['monto_total'])
                data.append(row_dict)

        return {'success': True, 'rutas': data}, 200
    except Exception as e:
        print(f'[ERROR listar_rutas] {str(e)}')
        return {'success': False, 'message': f'Error interno: {str(e)}'}, 500
    finally:
        db.close_connection()

def obtener_mis_rutas(id_chofer, estado=None):
    db = PostgreSQL()
    try:
        db.create_connection()
        result = logistica_repos.get_rutas_by_chofer(db, int(id_chofer), estado)

        data = []
        if result and db.cur.description:
            columns = [c[0] for c in db.cur.description]
            for row in result:
                row_dict = dict(zip(columns, row))
                row_dict['fecha_asignacion'] = row_dict['fecha_asignacion'].strftime('%Y-%m-%d %H:%M') if row_dict['fecha_asignacion'] else ''
                row_dict['fecha_entrega_estimada'] = row_dict['fecha_entrega_estimada'].strftime('%Y-%m-%d') if row_dict['fecha_entrega_estimada'] else ''
                row_dict['fecha_entrega_real'] = row_dict['fecha_entrega_real'].strftime('%Y-%m-%d %H:%M') if row_dict['fecha_entrega_real'] else ''
                row_dict['monto_total'] = float(row_dict['monto_total'])
                data.append(row_dict)

        return {'success': True, 'rutas': data}, 200
    except Exception as e:
        print(f'[ERROR obtener_mis_rutas] {str(e)}')
        return {'success': False, 'message': f'Error interno: {str(e)}'}, 500
    finally:
        db.close_connection()

def obtener_detalle_ruta(id_ruta):
    db = PostgreSQL()
    try:
        db.create_connection()
        result = logistica_repos.get_ruta_by_id(db, int(id_ruta))

        if not result:
            return {'success': False, 'message': 'Ruta no encontrada.'}, 404

        columns = [c[0] for c in db.cur.description]
        row_dict = dict(zip(columns, result))
        if row_dict.get('fecha_asignacion'):
            row_dict['fecha_asignacion'] = row_dict['fecha_asignacion'].strftime('%Y-%m-%d %H:%M')
        if row_dict.get('fecha_entrega_estimada'):
            row_dict['fecha_entrega_estimada'] = row_dict['fecha_entrega_estimada'].strftime('%Y-%m-%d')
        if row_dict.get('fecha_entrega_real'):
            row_dict['fecha_entrega_real'] = row_dict['fecha_entrega_real'].strftime('%Y-%m-%d %H:%M')
        if row_dict.get('monto_total'):
            row_dict['monto_total'] = float(row_dict['monto_total'])

        return {'success': True, 'ruta': row_dict}, 200
    except Exception as e:
        print(f'[ERROR obtener_detalle_ruta] {str(e)}')
        return {'success': False, 'message': f'Error interno: {str(e)}'}, 500
    finally:
        db.close_connection()

def confirmar_entrega(id_ruta, data, id_usuario_logeado):
    observaciones = data.get('observaciones', '')
    url_evidencia_imagen = data.get('url_evidencia_imagen')
    url_evidencia_audio = data.get('url_evidencia_audio')

    db = PostgreSQL()
    try:
        db.create_connection()

        logistica_repos.confirmar_entrega_ruta(
            db, id_ruta, observaciones, url_evidencia_imagen, url_evidencia_audio
        )

        row = logistica_repos.get_id_transaccion_by_ruta(db, id_ruta)
        if row:
            nro_transaccion = row[0]
            logistica_repos.update_estado_transaccion(db, nro_transaccion, 'ENTREGADO')

        db.insert_log(f'CONFIRMÓ ENTREGA de ruta #{id_ruta}', id_usuario_logeado)

        db.conn.commit()

        return {'success': True, 'message': 'Entrega confirmada exitosamente.'}, 200

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'[ERROR confirmar_entrega] {str(e)}')
        return {'success': False, 'message': f'Error al confirmar entrega: {str(e)}'}, 500
    finally:
        db.close_connection()

def cancelar_ruta(id_ruta, id_usuario_logeado):
    db = PostgreSQL()
    try:
        db.create_connection()

        logistica_repos.cancelar_ruta_db(db, id_ruta)

        row = logistica_repos.get_id_transaccion_by_ruta(db, id_ruta)
        if row:
            nro_transaccion = row[0]
            logistica_repos.update_estado_transaccion(db, nro_transaccion, 'PENDIENTE')

        db.insert_log(f'CANCELÓ ruta logística #{id_ruta}', id_usuario_logeado)
        db.conn.commit()

        return {'success': True, 'message': 'Ruta cancelada exitosamente.'}, 200

    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'[ERROR cancelar_ruta] {str(e)}')
        return {'success': False, 'message': f'Error al cancelar ruta: {str(e)}'}, 500
    finally:
        db.close_connection()
