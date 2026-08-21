# app/services/crm_services.py
from datetime import datetime
from decimal import Decimal

from app.repos import crm_repos
from app.classes.postgre import PostgreSQL

CATEGORIAS_CRM = ["VIP", "FRECUENTE", "REGULAR", "NUEVO", "INACTIVO"]

def _rows_to_dicts(db, result):
    """
    Transforma el resultado de la DB a diccionarios.
    Ahora recibe 'db' para acceder al cursor activo.
    """
    data = []
    if result is None: return data
    if not db.cur or not db.cur.description: return data

    columns = [column[0] for column in db.cur.description]

    if isinstance(result, list):
        for row in result:
            data.append(dict(zip(columns, row)))
    else:
        data.append(dict(zip(columns, result)))

    return data

def _to_float(value):
    if value is None: return 0.0
    if isinstance(value, Decimal): return float(value)
    try: return float(value)
    except Exception: return 0.0

def _serialize_datetime(value):
    if value is None: return None
    if isinstance(value, datetime): return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)

def _days_since(value):
    if value is None: return None
    if isinstance(value, str):
        try: value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except Exception: return None
    if isinstance(value, datetime):
        return (datetime.now() - value).days
    return None

def _get_id_empresa_from_payload(payload_token):
    if not payload_token: return None
    return payload_token.get("id_empresa") or payload_token.get("empresa") or payload_token.get("company_id")

def classify_client(cliente):
    estado = str(cliente.get("estado_cuenta") or "").upper()
    total_transacciones = int(cliente.get("total_transacciones") or 0)
    monto_total = _to_float(cliente.get("monto_total"))
    dias_creacion = _days_since(cliente.get("created_at"))
    dias_ultima = _days_since(cliente.get("ultima_transaccion"))

    if estado != "ACTIVO": return "INACTIVO"
    if total_transacciones == 0:
        if dias_creacion is not None and dias_creacion <= 30: return "NUEVO"
        return "INACTIVO"
    if dias_ultima is not None and dias_ultima > 90: return "INACTIVO"
    if dias_creacion is not None and dias_creacion <= 30 and total_transacciones <= 1: return "NUEVO"
    if monto_total >= 10000 or total_transacciones >= 8: return "VIP"
    if total_transacciones >= 4: return "FRECUENTE"
    
    return "REGULAR"

def _category_priority(categoria):
    priorities = {"VIP": 1, "FRECUENTE": 2, "REGULAR": 3, "NUEVO": 4, "INACTIVO": 5}
    return priorities.get(categoria, 99)

def _normalize_client(cliente):
    categoria = classify_client(cliente)
    return {
        "id_usuario": cliente.get("id_usuario"),
        "user_name": cliente.get("user_name"),
        "documento_identidad": cliente.get("documento_identidad"),
        "nombre_razon_social": cliente.get("nombre_razon_social"),
        "direccion": cliente.get("direccion"),
        "correo": cliente.get("correo"),
        "telefono": cliente.get("telefono"),
        "estado_cuenta": cliente.get("estado_cuenta"),
        "created_at": _serialize_datetime(cliente.get("created_at")),
        "id_rol": cliente.get("id_rol"),
        "rol": cliente.get("rol"),
        "id_empresa": cliente.get("id_empresa"),
        "total_transacciones": int(cliente.get("total_transacciones") or 0),
        "monto_total": _to_float(cliente.get("monto_total")),
        "ultima_transaccion": _serialize_datetime(cliente.get("ultima_transaccion")),
        "nro_ultima_transaccion": cliente.get("nro_ultima_transaccion"),
        "tipo_ultima_transaccion": cliente.get("tipo_ultima_transaccion"),
        "estado_ultima_transaccion": cliente.get("estado_ultima_transaccion"),
        "monto_ultima_transaccion": _to_float(cliente.get("monto_ultima_transaccion")),
        "dias_desde_ultima_transaccion": _days_since(cliente.get("ultima_transaccion")),
        "categoria_cliente": categoria,
        "prioridad_categoria": _category_priority(categoria),
    }

def _build_stats_from_clients(clientes):
    stats = {
        "total_clientes": len(clientes), "vip": 0, "frecuentes": 0, 
        "regulares": 0, "nuevos": 0, "inactivos": 0,
        "monto_total_general": 0, "transacciones_total": 0,
    }
    for cliente in clientes:
        categoria = cliente.get("categoria_cliente")
        stats["monto_total_general"] += _to_float(cliente.get("monto_total"))
        stats["transacciones_total"] += int(cliente.get("total_transacciones") or 0)
        
        if categoria == "VIP": stats["vip"] += 1
        elif categoria == "FRECUENTE": stats["frecuentes"] += 1
        elif categoria == "REGULAR": stats["regulares"] += 1
        elif categoria == "NUEVO": stats["nuevos"] += 1
        elif categoria == "INACTIVO": stats["inactivos"] += 1
    return stats


def get_clients_list(categoria=None, search=None, estado=None, payload_token=None):
    db = PostgreSQL()
    try:
        id_empresa = _get_id_empresa_from_payload(payload_token)
        db.create_connection()

        result = crm_repos.get_all_crm_clients(db, id_empresa=id_empresa)
        rows = _rows_to_dicts(db, result) # <- Pasamos db local
        clientes = [_normalize_client(row) for row in rows]

        if categoria:
            categoria = categoria.upper().strip()
            clientes = [c for c in clientes if str(c.get("categoria_cliente")).upper() == categoria]

        if estado:
            estado = estado.upper().strip()
            clientes = [c for c in clientes if str(c.get("estado_cuenta")).upper() == estado]

        if search:
            search = search.upper().strip()
            clientes = [
                c for c in clientes
                if search in str(c.get("nombre_razon_social") or "").upper()
                or search in str(c.get("user_name") or "").upper()
                or search in str(c.get("documento_identidad") or "").upper()
                or search in str(c.get("telefono") or "").upper()
                or search in str(c.get("correo") or "").upper()
            ]

        clientes = sorted(
            clientes, key=lambda c: (c.get("prioridad_categoria", 99), -_to_float(c.get("monto_total")))
        )

        return {
            "success": True, "message": "Clientes CRM obtenidos exitosamente.",
            "data": clientes, "list_clientes": clientes,
            "stats": _build_stats_from_clients(clientes), "categorias": CATEGORIAS_CRM,
        }, 200

    except Exception as e:
        return {"success": False, "message": f"Error al obtener clientes CRM: {str(e)}"}, 500
    finally:
        db.close_connection()


def get_client_detail(id_usuario, payload_token=None):
    db = PostgreSQL()
    try:
        id_empresa = _get_id_empresa_from_payload(payload_token)
        db.create_connection()

        result = crm_repos.get_crm_client_by_id(db, id_usuario=id_usuario, id_empresa=id_empresa)
        rows = _rows_to_dicts(db, result)

        if not rows:
            return {"success": False, "message": "Cliente no encontrado."}, 404

        cliente = _normalize_client(rows[0])

        trans_result = crm_repos.get_client_transactions(db, id_usuario=id_usuario, id_empresa=id_empresa, limit=20)
        trans_rows = _rows_to_dicts(db, trans_result)

        transacciones = []
        for row in trans_rows:
            transacciones.append({
                "nro_transaccion": row.get("nro_transaccion"),
                "tipo_transaccion": row.get("tipo_transaccion"),
                "estado_transaccion": row.get("estado_transaccion"),
                "fecha_hora": _serialize_datetime(row.get("fecha_hora")),
                "monto_total": _to_float(row.get("monto_total")),
                "id_cliente": row.get("id_cliente"),
                "id_supervisor_admin": row.get("id_supervisor_admin"),
                "id_empresa": row.get("id_empresa"),
            })

        cliente["transacciones"] = transacciones

        return {"success": True, "message": "Detalle de cliente obtenido exitosamente.", "data": cliente, "cliente": cliente}, 200

    except Exception as e:
        return {"success": False, "message": f"Error al obtener detalle del cliente: {str(e)}"}, 500
    finally:
        db.close_connection()


def get_client_transactions_service(id_usuario, payload_token=None):
    db = PostgreSQL()
    try:
        id_empresa = _get_id_empresa_from_payload(payload_token)
        db.create_connection()

        result = crm_repos.get_client_transactions(db, id_usuario=id_usuario, id_empresa=id_empresa, limit=50)
        rows = _rows_to_dicts(db, result)

        data = []
        for row in rows:
            data.append({
                "nro_transaccion": row.get("nro_transaccion"),
                "tipo_transaccion": row.get("tipo_transaccion"),
                "estado_transaccion": row.get("estado_transaccion"),
                "fecha_hora": _serialize_datetime(row.get("fecha_hora")),
                "monto_total": _to_float(row.get("monto_total")),
                "id_cliente": row.get("id_cliente"),
                "id_supervisor_admin": row.get("id_supervisor_admin"),
                "id_empresa": row.get("id_empresa"),
            })

        return {"success": True, "message": "Transacciones obtenidas.", "data": data, "list_transacciones": data}, 200

    except Exception as e:
        return {"success": False, "message": f"Error al obtener transacciones: {str(e)}"}, 500
    finally:
        db.close_connection()


def get_crm_stats(payload_token=None):
    db = PostgreSQL()
    try:
        id_empresa = _get_id_empresa_from_payload(payload_token)
        db.create_connection()

        result = crm_repos.get_crm_general_stats(db, id_empresa=id_empresa)
        rows = _rows_to_dicts(db, result)
        general_stats = rows[0] if rows else {}

        clientes_result = crm_repos.get_all_crm_clients(db, id_empresa=id_empresa)
        clientes_rows = _rows_to_dicts(db, clientes_result)
        clientes = [_normalize_client(row) for row in clientes_rows]
        
        category_stats = _build_stats_from_clients(clientes)

        response = {
            "total_clientes": int(general_stats.get("total_clientes") or 0),
            "clientes_activos": int(general_stats.get("clientes_activos") or 0),
            "clientes_inactivos_sistema": int(general_stats.get("clientes_inactivos_sistema") or 0),
            "total_transacciones": int(general_stats.get("total_transacciones") or 0),
            "monto_total_general": _to_float(general_stats.get("monto_total_general")),
            "ticket_promedio": _to_float(general_stats.get("ticket_promedio")),
            "vip": category_stats.get("vip", 0),
            "frecuentes": category_stats.get("frecuentes", 0),
            "regulares": category_stats.get("regulares", 0),
            "nuevos": category_stats.get("nuevos", 0),
            "inactivos": category_stats.get("inactivos", 0),
        }

        return {"success": True, "message": "Estadísticas obtenidas.", "data": response, "stats": response}, 200

    except Exception as e:
        return {"success": False, "message": f"Error al obtener estadísticas: {str(e)}"}, 500
    finally:
        db.close_connection()


def get_categories():
    return {
        "success": True, "categorias": CATEGORIAS_CRM,
        "reglas": {
            "VIP": "Monto total >= 10000 o 8+ transacciones.",
            "FRECUENTE": "4+ transacciones.",
            "REGULAR": "Cliente activo que no entra en otras categorías.",
            "NUEVO": "Cliente creado hace 30 días o menos y con máximo 1 transacción.",
            "INACTIVO": "Cuenta inactiva, sin transacciones o última transacción mayor a 90 días."
        }
    }, 200


def procesar_envio_notificaciones(data, socketio_instance):
    """
    Valida el payload del frontend y orquesta el envío por WebSockets.
    """
    clientes = data.get('clientes', [])
    asunto = data.get('asunto', '')
    mensaje = data.get('mensaje', '')
    canal = data.get('canal', 'CORREO')

    if not clientes or not isinstance(clientes, list):
        return {'success': False, 'message': 'Debe seleccionar al menos un cliente válido.'}, 400

    if not mensaje:
        return {'success': False, 'message': 'El mensaje de la notificación no puede estar vacío.'}, 400

    try:
        # Importamos la función de sockets que acabamos de crear
        from app.services.notificaciones_services import emitir_notificacion_masiva
        
        # 1. Ejecutar el broadcast por WebSockets
        emitir_notificacion_masiva(socketio_instance, clientes, asunto, mensaje, canal)
        
        # 2. OPCIONAL: Aquí podrías guardar el registro en PostgreSQL si tienes 
        # una tabla de "historial_notificaciones" usando tus repositorios.

        return {
            'success': True, 
            'message': f'Notificación lanzada exitosamente a {len(clientes)} clientes.'
        }, 200

    except Exception as e:
        print(f"[ERROR CRM NOTIFICACIONES]: {str(e)}")
        return {'success': False, 'message': 'Error interno al intentar emitir la notificación.'}, 500