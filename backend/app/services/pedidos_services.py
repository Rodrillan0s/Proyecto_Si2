# app/services/pedidos_services.py
from app.repos import pedidos_repos, fidelizacion_repos
from app.classes.postgre import PostgreSQL
from app.services import fidelizacion_services

def obtener_catalogo(id_empresa):
    if not id_empresa:
        return {'success': False, 'message': 'ID de empresa es requerido.'}, 400
        
    db = PostgreSQL()
    try:
        db.create_connection()
        result = pedidos_repos.get_catalogo_insumos(db, int(id_empresa))
        
        data = []
        if result and db.cur.description:
            columns = [column[0] for column in db.cur.description]
            for row in result:
                row_dict = dict(zip(columns, row))
                row_dict['precio_unitario'] = float(row_dict['precio_unitario']) if row_dict['precio_unitario'] else 0.0
                row_dict['stock_actual'] = float(row_dict['stock_actual']) if row_dict['stock_actual'] else 0.0
                data.append(row_dict)
                
        return {'success': True, 'catalogo': data}, 200
    except Exception as e:
        print(f'[ERROR obtener_catalogo] {str(e)}')
        return {'success': False, 'message': f'Error interno: {str(e)}'}, 500
    finally:
        db.close_connection()

def registrar_pedido(data):
    id_cliente = data.get('id_cliente')
    id_supervisor = data.get('id_supervisor_admin') 
    id_empresa = data.get('id_empresa')
    detalles = data.get('detalles', []) 
    
    if not all([id_cliente, id_supervisor, id_empresa]) or len(detalles) == 0:
        return {'success': False, 'message': 'Faltan datos obligatorios o el carrito está vacío.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        
        # 1. Calcular precios reales desde bodega y evaluar fidelizacion
        detalles_calculados = []
        subtotal_original = 0.0
        for item in detalles:
            id_prod = item['id_producto']
            cant = float(item['cantidad'])
            producto = pedidos_repos.get_producto_para_pedido(db, id_prod, id_empresa)
            if not producto:
                raise Exception(f"Producto ID {id_prod} no existe para la empresa indicada.")
            precio_real = float(producto[1])
            stock_actual = float(producto[2])
            if stock_actual < cant:
                raise Exception(f"Stock insuficiente para el producto ID {id_prod}. Disponible: {stock_actual}")
            subtotal_original += cant * precio_real
            detalles_calculados.append({
                'id_producto': id_prod,
                'cantidad': cant,
                'precio_real': precio_real
            })

        descuento = fidelizacion_services.evaluar_descuento(
            db, id_cliente, id_empresa, subtotal_original, 'PEDIDO_INSUMO'
        )
        monto_total = descuento['monto_final']
        factor_descuento = (monto_total / subtotal_original) if subtotal_original > 0 else 1
        
        # 2. Insertar cabecera de la Transacción
        row_id = pedidos_repos.insert_transaccion_cabecera(
            db,
            tipo_transaccion='PEDIDO_INSUMO',
            monto_total=monto_total,
            id_cliente=id_cliente,
            id_supervisor_admin=id_supervisor,
            id_empresa=id_empresa
        )
        
        if not row_id:
            raise Exception("No se pudo generar el número de transacción.")
            
        nro_transaccion = row_id[0]
        
        # 3. Procesar cada producto del carrito con precio final descontado
        for item in detalles_calculados:
            id_prod = item['id_producto']
            cant = item['cantidad']
            precio = round(item['precio_real'] * factor_descuento, 2)

            pedidos_repos.insert_detalle_venta(db, cant, precio, nro_transaccion, id_prod)
            
            # Descontar stock
            pedidos_repos.update_stock_bodega(db, cant, id_prod)

        if descuento['descuento_total'] > 0:
            fidelizacion_repos.insert_descuento_transaccion(db, {
                'nro_transaccion': nro_transaccion,
                'id_cliente': id_cliente,
                'id_nivel': descuento['id_nivel'],
                'id_regla': descuento['id_regla'],
                'subtotal_original': descuento['subtotal_original'],
                'porcentaje_descuento': descuento['porcentaje_descuento'],
                'descuento_total': descuento['descuento_total'],
                'monto_final': descuento['monto_final']
            })
            
        # 4. Registrar en bitácora el pedido
        db.insert_log(f"GENERÓ UN PEDIDO POR {monto_total} Bs (Transacción: {nro_transaccion})", id_supervisor)
        
        # 5. Confirmar transacción completa (Atomicidad)
        db.conn.commit()
            
        return {
            'success': True, 
            'message': 'Pedido registrado exitosamente.', 
            'nro_transaccion': nro_transaccion,
            'monto_total': monto_total,
            'subtotal_original': descuento['subtotal_original'],
            'descuento_total': descuento['descuento_total'],
            'porcentaje_descuento': descuento['porcentaje_descuento'],
            'nivel_fidelizacion': descuento['nivel']
        }, 201

    except Exception as e:
        if db.conn:
            db.conn.rollback() # Si un solo producto falla el stock, deshacemos TODO
        print(f'[ERROR Pedido] {str(e)}')
        return {'success': False, 'message': f'Error al procesar el pedido: {str(e)}'}, 500
    finally:
        db.close_connection()

def obtener_historial(id_cliente):
    db = PostgreSQL()
    try:
        db.create_connection()
        result = pedidos_repos.get_historial_pedidos(db, id_cliente)
        data = []
        if result and db.cur.description:
            columns = [c[0] for c in db.cur.description]
            for row in result:
                row_dict = dict(zip(columns, row))
                row_dict['fecha_hora'] = row_dict['fecha_hora'].strftime('%Y-%m-%d %H:%M')
                row_dict['monto_total'] = float(row_dict['monto_total'])
                data.append(row_dict)
        return {'success': True, 'listado': data}, 200
    except Exception as e:
        print(f'[ERROR obtener_historial] {str(e)}')
        return {'success': False, 'message': f'Error: {str(e)}'}, 500
    finally:
        db.close_connection()

def obtener_detalle(nro_transaccion):
    db = PostgreSQL()
    try:
        db.create_connection()
        result = pedidos_repos.get_detalle_pedido(db, nro_transaccion)
        detalle_columns = [c[0] for c in db.cur.description] if db.cur.description else []
        descuento = pedidos_repos.get_descuento_pedido(db, nro_transaccion)
        data = []
        if result and detalle_columns:
            for row in result:
                row_dict = dict(zip(detalle_columns, row))
                row_dict['precio_venta'] = float(row_dict['precio_venta'])
                data.append(row_dict)
        descuento_data = None
        if descuento:
            descuento_data = {
                'subtotal_original': float(descuento[0]),
                'porcentaje_descuento': float(descuento[1]),
                'descuento_total': float(descuento[2]),
                'monto_final': float(descuento[3]),
                'nivel_fidelizacion': descuento[4] or 'SIN NIVEL'
            }
        return {'success': True, 'detalles': data, 'descuento': descuento_data}, 200
    except Exception as e:
        print(f'[ERROR obtener_detalle] {str(e)}')
        return {'success': False, 'message': f'Error: {str(e)}'}, 500
    finally:
        db.close_connection()
