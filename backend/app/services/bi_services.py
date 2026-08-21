from app.repos import bi_repos
from app.classes.postgre import PostgreSQL

def obtener_dashboard_kpis(id_empresa):
    if not id_empresa:
        return {'success': False, 'message': 'ID de empresa requerido.'}, 400

    db = PostgreSQL()
    try:
        db.create_connection()
        
        # 1. Finanzas
        finanzas_bd = bi_repos.get_kpis_financieros(db, id_empresa)
        finanzas = {
            'ingresos_totales': float(finanzas_bd[0]) if finanzas_bd else 0.0,
            'total_ventas': int(finanzas_bd[1]) if finanzas_bd else 0
        }

        # 2. Operatividad (Órdenes)
        ordenes_bd = bi_repos.get_kpis_operativos(db, id_empresa)
        ordenes = {'PENDIENTE': 0, 'EN PROCESO': 0, 'FINALIZADA': 0}
        if ordenes_bd:
            for row in ordenes_bd:
                estado = row[0].upper() if row[0] else 'DESCONOCIDO'
                if estado in ordenes:
                    ordenes[estado] = int(row[1])

        # 3. Inventario
        inv_bd = bi_repos.get_kpis_inventario(db, id_empresa)
        inventario = {
            'alertas_stock_minimo': int(inv_bd[0]) if inv_bd else 0,
            'valoracion_total': float(inv_bd[1]) if inv_bd else 0.0
        }

        # 4. Agricultura y Tierra
        agro_bd = bi_repos.get_kpis_agricolas(db, id_empresa)
        agricultura = {
            'hectareas_totales': float(agro_bd[0]) if agro_bd else 0.0,
            'hectareas_activas': float(agro_bd[1]) if agro_bd else 0.0
        }

        # 5. Maquinaria
        maq_bd = bi_repos.get_kpis_maquinaria(db, id_empresa)
        maquinas = {'DISPONIBLE': 0, 'EN MANTENIMIENTO': 0, 'ALQUILADA': 0}
        if maq_bd:
            for row in maq_bd:
                estado_maq = row[0].upper() if row[0] else 'OTRO'
                maquinas[estado_maq] = int(row[1])

        # Consolidar Payload
        payload = {
            'finanzas': finanzas,
            'ordenes': ordenes,
            'inventario': inventario,
            'agricultura': agricultura,
            'maquinaria': maquinas
        }

        return {'success': True, 'data': payload}, 200

    except Exception as e:
        print(f"[ERROR BI Service]: {str(e)}")
        return {'success': False, 'message': 'Error al generar métricas de inteligencia de negocios.'}, 500
    finally:
        db.close_connection()