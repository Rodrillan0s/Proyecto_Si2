from decimal import Decimal, InvalidOperation
from app.repos import compras_repos, bitacora_repos


class ComprasError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def _empresa(token, id_empresa_solicitada=None, obligatorio=True):
    from app.utils.security import es_admin_sistema
    if es_admin_sistema(token):
        if id_empresa_solicitada is not None and str(id_empresa_solicitada).strip() != "":
            try:
                return int(id_empresa_solicitada)
            except (ValueError, TypeError):
                pass
        if not obligatorio:
            return None
        return token.get("id_empresa") or 1
    value = token.get("id_empresa")
    if not value:
        raise ComprasError("El usuario no pertenece a ninguna empresa.", 403)
    return value


def _usuario(token):
    user_id = token.get("id_usuario") or token.get("nro_usuario") or token.get("sub")
    if not user_id:
        raise ComprasError("No se pudo identificar al usuario desde el token.", 401)
    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise ComprasError("ID de usuario inválido en el token.", 401)


def _log(token, accion, detalle, ip="unknown"):
    try:
        bitacora_repos.registrar(token, accion, detalle, ip)
    except Exception:
        pass


def listar_ordenes(token, estado=None, id_proveedor=None, fecha_desde=None, fecha_hasta=None, q=None, page=1, limit=20, id_empresa=None):
    id_empresa_target = _empresa(token, id_empresa, obligatorio=False)
    if page < 1 or limit < 1 or limit > 100:
        raise ComprasError("Paginación inválida (limit 1-100, page >= 1).")

    rows, total = compras_repos.listar_ordenes(
        id_empresa=id_empresa_target,
        q=q.strip() if q else None,
        estado=estado.strip().upper() if estado else None,
        id_proveedor=int(id_proveedor) if id_proveedor else None,
        page=page,
        limit=limit
    )
    return {
        "success": True,
        "data": rows,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0
        }
    }


def _empresa_de_orden(id_orden: int):
    from app.classes.postgres import PostgreSQL
    db = PostgreSQL()
    db.create_connection()
    try:
        row = db.execute_query("SELECT id_empresa FROM obras.t_orden_compra WHERE id_orden_compra = %s;", (id_orden,), fetchone=True)
        return row[0] if row else None
    finally:
        db.close_connection()


def detalle_orden(token, id_orden: int, id_empresa=None):
    if not id_empresa:
        id_empresa = _empresa_de_orden(id_orden)
    id_empresa_target = _empresa(token, id_empresa, obligatorio=False)
    orden = compras_repos.consultar_orden(id_orden, id_empresa_target)
    if not orden:
        raise ComprasError("Orden de compra no encontrada.", 404)
    return {"success": True, "data": orden}


def crear_orden(data: dict, token, ip="unknown"):
    id_empresa_solicitada = data.get("id_empresa")
    if not id_empresa_solicitada and data.get("detalles"):
        try:
            first_mat_id = int(data["detalles"][0].get("id_material"))
            from app.classes.postgres import PostgreSQL
            db = PostgreSQL()
            db.create_connection()
            try:
                row = db.execute_query(
                    "SELECT id_empresa FROM obras.t_material WHERE id_material = %s;",
                    (first_mat_id,),
                    fetchone=True
                )
                if row:
                    id_empresa_solicitada = row[0]
            finally:
                db.close_connection()
        except Exception:
            pass

    id_empresa = _empresa(token, id_empresa_solicitada)
    id_usuario = _usuario(token)

    id_proveedor = data.get("id_proveedor")
    if not id_proveedor:
        raise ComprasError("El proveedor es obligatorio.")

    detalles = data.get("detalles")
    if not detalles or not isinstance(detalles, list):
        raise ComprasError("Debe incluir al menos un material en la orden.")

    detalles_limpios = []
    for d in detalles:
        try:
            id_mat = int(d.get("id_material"))
            cant = Decimal(str(d.get("cantidad_solicitada", 0)))
            precio = Decimal(str(d.get("precio_unitario", 0)))
        except (ValueError, TypeError, InvalidOperation):
            raise ComprasError("Cantidades y precios de materiales deben ser numéricos válidos.")

        if cant <= 0:
            raise ComprasError("La cantidad solicitada debe ser mayor a 0.")
        if precio < 0:
            raise ComprasError("El precio unitario no puede ser negativo.")

        detalles_limpios.append({
            "id_material": id_mat,
            "cantidad_solicitada": float(cant),
            "precio_unitario": float(precio)
        })

    fecha = data.get("fecha")
    observaciones = data.get("observaciones")
    enviar_aprobacion = bool(data.get("enviar_aprobacion", False))

    try:
        id_orden = compras_repos.crear_orden(
            id_empresa=id_empresa,
            id_proveedor=int(id_proveedor),
            id_usuario=id_usuario,
            fecha=fecha,
            observaciones=observaciones,
            detalles=detalles_limpios,
            enviar_aprobacion=enviar_aprobacion
        )
    except compras_repos.ComprasRepoError as exc:
        raise ComprasError(str(exc), 400)

    _log(token, "CREAR_ORDEN_COMPRA", f"Orden de compra #{id_orden} creada.", ip)
    return {"success": True, "message": "Orden de compra creada exitosamente.", "id_orden_compra": id_orden}


def cambiar_estado(id_orden: int, data: dict, token, ip="unknown"):
    id_empresa = _empresa(token, data.get("id_empresa") or _empresa_de_orden(id_orden))
    nuevo_estado = (data.get("estado") or "").strip().upper()

    if nuevo_estado not in ("PENDIENTE_APROBACION", "CANCELADA"):
        raise ComprasError("Acción de estado no permitida a través de este endpoint.")

    try:
        ok = compras_repos.cambiar_estado(id_orden, id_empresa, nuevo_estado)
        if not ok:
            raise ComprasError("No se pudo actualizar el estado de la orden.")
    except compras_repos.ComprasRepoError as exc:
        raise ComprasError(str(exc), 400)

    _log(token, "CAMBIAR_ESTADO_OC", f"Orden #{id_orden} cambiada a estado {nuevo_estado}.", ip)
    return {"success": True, "message": f"Orden de compra actualizada a {nuevo_estado}."}


def aprobar_rechazar(id_orden: int, data: dict, token, ip="unknown"):
    id_empresa = _empresa(token, data.get("id_empresa") or _empresa_de_orden(id_orden))
    id_usuario = _usuario(token)
    accion = (data.get("accion") or "").strip().upper()

    if accion not in ("APROBADA", "RECHAZADA"):
        raise ComprasError("La acción debe ser 'APROBADA' o 'RECHAZADA'.")

    observacion = data.get("observacion")
    if accion == "RECHAZADA" and not observacion:
        raise ComprasError("Debe ingresar una observación al rechazar una orden de compra.")

    try:
        ok = compras_repos.aprobar_rechazar(
            id_orden=id_orden,
            id_empresa=id_empresa,
            id_usuario=id_usuario,
            aprobar=(accion == "APROBADA"),
            observacion=observacion
        )
        if not ok:
            raise ComprasError("No se pudo procesar la aprobación/rechazo de la orden.")
    except compras_repos.ComprasRepoError as exc:
        raise ComprasError(str(exc), 400)

    _log(token, f"OC_{accion}", f"Orden de compra #{id_orden} evaluada como {accion}.", ip)
    return {"success": True, "message": f"Orden de compra {accion.lower()} exitosamente."}


def registrar_recepcion(id_orden: int, data: dict, token, ip="unknown"):
    id_empresa = _empresa(token, data.get("id_empresa") or _empresa_de_orden(id_orden))
    id_usuario = _usuario(token)

    detalles = data.get("detalles")
    if not detalles or not isinstance(detalles, list):
        raise ComprasError("Debe incluir al menos un material a recibir.")

    detalles_actuales = compras_repos.obtener_detalles_orden_raw(id_orden)
    mat_to_detalle = {d["id_material"]: d["id_detalle"] for d in detalles_actuales}

    detalles_limpios = []
    for d in detalles:
        try:
            id_mat = int(d.get("id_material"))
            cant = Decimal(str(d.get("cantidad_recibida", d.get("cantidad", 0))))
        except (ValueError, TypeError, InvalidOperation):
            raise ComprasError("Cantidades recibidas deben ser numéricas válidas.")

        if cant <= 0:
            continue

        id_det = d.get("id_detalle") or mat_to_detalle.get(id_mat)
        if not id_det:
            raise ComprasError(f"El material ID {id_mat} no pertenece a los detalles de la orden de compra.")

        detalles_limpios.append({
            "id_detalle": id_det,
            "cantidad": float(cant)
        })

    if not detalles_limpios:
        raise ComprasError("Debe indicar al menos una cantidad recibida mayor a 0.")

    observaciones = data.get("observaciones")

    try:
        id_recepcion = compras_repos.registrar_recepcion(
            id_orden=id_orden,
            id_empresa=id_empresa,
            id_usuario=id_usuario,
            observaciones=observaciones,
            detalles=detalles_limpios
        )
    except compras_repos.ComprasRepoError as exc:
        raise ComprasError(str(exc), 400)

    _log(token, "RECEPCION_COMPRA", f"Recepción #{id_recepcion} registrada para orden #{id_orden}. Entrada de inventario generada.", ip)
    return {
        "success": True,
        "message": "Recepción registrada exitosamente y stock actualizado.",
        "id_recepcion": id_recepcion
    }
