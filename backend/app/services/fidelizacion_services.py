from app.repos import fidelizacion_repos
from app.classes.postgre import PostgreSQL

def _validar_id_empresa(id_empresa):
    if not id_empresa or str(id_empresa).lower() == 'null':
        return None, {'success': False, 'message': 'ID de empresa requerido.'}, 400
    try:
        return int(id_empresa), None, None
    except (ValueError, TypeError):
        return None, {'success': False, 'message': 'ID de empresa inválido.'}, 400

def _to_float(value):
    return float(value) if value is not None else 0.0

def _format_nivel(row_dict):
    row_dict['min_monto_acumulado'] = _to_float(row_dict.get('min_monto_acumulado'))
    row_dict['porcentaje_descuento'] = _to_float(row_dict.get('porcentaje_descuento'))
    row_dict['monto_max_descuento'] = _to_float(row_dict.get('monto_max_descuento')) if row_dict.get('monto_max_descuento') is not None else None
    row_dict['vigencia_desde'] = row_dict['vigencia_desde'].strftime('%Y-%m-%d') if row_dict.get('vigencia_desde') else ''
    row_dict['vigencia_hasta'] = row_dict['vigencia_hasta'].strftime('%Y-%m-%d') if row_dict.get('vigencia_hasta') else ''
    return row_dict

def _normalizar_payload(data):
    payload = dict(data)
    if payload.get('monto_max_descuento') == '':
        payload['monto_max_descuento'] = None
    if payload.get('vigencia_desde') == '':
        payload['vigencia_desde'] = None
    if payload.get('vigencia_hasta') == '':
        payload['vigencia_hasta'] = None
    return payload

def listar_niveles(id_empresa):
    id_val, err, status = _validar_id_empresa(id_empresa)
    if err:
        return err, status

    db = PostgreSQL()
    try:
        db.create_connection()
        result = fidelizacion_repos.get_niveles(db, id_val)
        data = []
        if result and db.cur.description:
            columns = [c[0] for c in db.cur.description]
            for row in result:
                data.append(_format_nivel(dict(zip(columns, row))))
        return {'success': True, 'niveles': data}, 200
    except Exception as e:
        print(f'[ERROR listar_niveles] {str(e)}')
        return {'success': False, 'message': f'Error interno: {str(e)}'}, 500
    finally:
        db.close_connection()

def crear_nivel(data, id_usuario):
    data = _normalizar_payload(data)
    required = ['nombre_nivel', 'min_transacciones', 'min_monto_acumulado', 'prioridad', 'id_empresa', 'porcentaje_descuento']
    if not all(data.get(k) not in [None, ''] for k in required):
        return {'success': False, 'message': 'Faltan datos obligatorios.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        row_id = fidelizacion_repos.insert_nivel(db, data)
        if not row_id:
            raise Exception('No se pudo crear el nivel.')
        id_nivel = row_id[0]
        fidelizacion_repos.upsert_regla(db, id_nivel, data)
        db.insert_log(f'CREÓ NIVEL DE FIDELIZACIÓN {data.get("nombre_nivel")}', id_usuario)
        db.conn.commit()
        return {'success': True, 'message': 'Nivel registrado correctamente.', 'id_nivel': id_nivel}, 201
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'[ERROR crear_nivel] {str(e)}')
        return {'success': False, 'message': f'Error al crear nivel: {str(e)}'}, 500
    finally:
        db.close_connection()

def actualizar_nivel(id_nivel, data, id_usuario):
    data = _normalizar_payload(data)
    required = ['nombre_nivel', 'min_transacciones', 'min_monto_acumulado', 'prioridad', 'estado', 'porcentaje_descuento']
    if not all(data.get(k) not in [None, ''] for k in required):
        return {'success': False, 'message': 'Faltan datos obligatorios.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        fidelizacion_repos.update_nivel(db, id_nivel, data)
        if data.get('id_regla'):
            fidelizacion_repos.update_regla(db, data.get('id_regla'), data)
        else:
            fidelizacion_repos.upsert_regla(db, id_nivel, data)
        db.insert_log(f'ACTUALIZÓ NIVEL DE FIDELIZACIÓN #{id_nivel}', id_usuario)
        db.conn.commit()
        return {'success': True, 'message': 'Nivel actualizado correctamente.'}, 200
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'[ERROR actualizar_nivel] {str(e)}')
        return {'success': False, 'message': f'Error al actualizar nivel: {str(e)}'}, 500
    finally:
        db.close_connection()

def desactivar_nivel(id_nivel, id_usuario):
    db = PostgreSQL()
    try:
        db.create_connection()
        fidelizacion_repos.deactivate_nivel(db, id_nivel)
        db.insert_log(f'DESACTIVÓ NIVEL DE FIDELIZACIÓN #{id_nivel}', id_usuario)
        db.conn.commit()
        return {'success': True, 'message': 'Nivel desactivado correctamente.'}, 200
    except Exception as e:
        if db.conn:
            db.conn.rollback()
        print(f'[ERROR desactivar_nivel] {str(e)}')
        return {'success': False, 'message': f'Error al desactivar nivel: {str(e)}'}, 500
    finally:
        db.close_connection()

def evaluar_descuento(db, id_cliente, id_empresa, subtotal_original, tipo_transaccion='PEDIDO_INSUMO'):
    historial = fidelizacion_repos.get_historial_cliente(db, id_cliente, id_empresa)
    total_transacciones = int(historial[0]) if historial else 0
    monto_acumulado = _to_float(historial[1]) if historial else 0.0
    niveles = fidelizacion_repos.get_niveles_activos(db, id_empresa)

    for nivel in niveles or []:
        id_nivel, nombre_nivel, min_transacciones, min_monto, _prioridad, id_regla, tipo_regla, porcentaje, monto_max = nivel
        if tipo_regla != tipo_transaccion:
            continue
        cumple_transacciones = total_transacciones >= int(min_transacciones or 0)
        cumple_monto = monto_acumulado >= _to_float(min_monto)
        if not (cumple_transacciones or cumple_monto):
            continue

        porcentaje = _to_float(porcentaje)
        descuento_total = round(subtotal_original * porcentaje / 100, 2)
        if monto_max is not None:
            descuento_total = min(descuento_total, _to_float(monto_max))
        monto_final = round(max(subtotal_original - descuento_total, 0), 2)

        return {
            'aplica': True,
            'id_nivel': id_nivel,
            'id_regla': id_regla,
            'nivel': nombre_nivel,
            'total_transacciones': total_transacciones,
            'monto_acumulado': monto_acumulado,
            'porcentaje_descuento': porcentaje,
            'descuento_total': descuento_total,
            'monto_final': monto_final,
            'subtotal_original': round(subtotal_original, 2)
        }

    return {
        'aplica': False,
        'id_nivel': None,
        'id_regla': None,
        'nivel': 'SIN NIVEL',
        'total_transacciones': total_transacciones,
        'monto_acumulado': monto_acumulado,
        'porcentaje_descuento': 0.0,
        'descuento_total': 0.0,
        'monto_final': round(subtotal_original, 2),
        'subtotal_original': round(subtotal_original, 2)
    }

def listar_clientes(id_empresa):
    id_val, err, status = _validar_id_empresa(id_empresa)
    if err:
        return err, status

    db = PostgreSQL()
    try:
        db.create_connection()
        clientes = fidelizacion_repos.get_clientes_fidelizacion(db, id_val)
        cliente_columns = [c[0] for c in db.cur.description] if db.cur.description else []
        niveles = fidelizacion_repos.get_niveles_activos(db, id_val)
        data = []
        if clientes and cliente_columns:
            for row in clientes:
                cliente = dict(zip(cliente_columns, row))
                total = int(cliente.get('total_transacciones') or 0)
                monto = _to_float(cliente.get('monto_acumulado'))
                nivel_aplicado = 'SIN NIVEL'
                porcentaje = 0.0
                for nivel in niveles or []:
                    _id_nivel, nombre, min_trans, min_monto, _prioridad, _id_regla, _tipo, porc, _max = nivel
                    if total >= int(min_trans or 0) or monto >= _to_float(min_monto):
                        nivel_aplicado = nombre
                        porcentaje = _to_float(porc)
                        break
                cliente['monto_acumulado'] = monto
                cliente['nivel_fidelizacion'] = nivel_aplicado
                cliente['porcentaje_descuento'] = porcentaje
                data.append(cliente)
        return {'success': True, 'clientes': data}, 200
    except Exception as e:
        print(f'[ERROR listar_clientes_fidelizacion] {str(e)}')
        return {'success': False, 'message': f'Error interno: {str(e)}'}, 500
    finally:
        db.close_connection()
