from decimal import Decimal, InvalidOperation
from app.repos import inventario_repos, bitacora_repos


class InventarioError(ValueError):
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
        raise InventarioError("El usuario no pertenece a ninguna empresa.", 403)
    return value


def _usuario(token):
    user_id = token.get("id_usuario") or token.get("nro_usuario") or token.get("sub")
    if not user_id:
        raise InventarioError("No se pudo identificar al usuario desde el token.", 401)
    try:
        return int(user_id)
    except (ValueError, TypeError):
        raise InventarioError("ID de usuario inválido en el token.", 401)


def _log(token, accion, detalle, ip="unknown"):
    try:
        bitacora_repos.registrar(token, accion, detalle, ip)
    except Exception:
        pass


def listar_stock(token, id_categoria=None, estado_stock=None, q=None, page=1, limit=50, id_empresa=None):
    id_empresa_target = _empresa(token, id_empresa, obligatorio=False)
    if not id_empresa_target:
        raise InventarioError("Se requiere especificar una empresa para listar el inventario.")

    if page < 1 or limit < 1 or limit > 100:
        raise InventarioError("Paginación inválida (limit 1-100, page >= 1).")

    rows, total = inventario_repos.listar_stock_inventario(
        id_empresa=id_empresa_target,
        id_categoria=int(id_categoria) if id_categoria else None,
        estado_stock=estado_stock.strip().upper() if estado_stock else None,
        q=q.strip() if q else None,
        page=page,
        limit=limit
    )
    return {
        "success": True,
        "data": rows,
        "total": total,
        "page": page,
        "limit": limit
    }


def obtener_kpis(token, id_empresa=None):
    id_empresa_target = _empresa(token, id_empresa, obligatorio=False)
    if not id_empresa_target:
        raise InventarioError("Se requiere especificar una empresa para obtener métricas de inventario.")

    kpis = inventario_repos.obtener_kpis(id_empresa=id_empresa_target)
    return {
        "success": True,
        "data": kpis
    }


def listar_movimientos(token, id_material=None, tipo_movimiento=None, page=1, limit=50, id_empresa=None):
    id_empresa_target = _empresa(token, id_empresa, obligatorio=False)
    if not id_empresa_target:
        raise InventarioError("Se requiere especificar una empresa para consultar el kardex.")

    if page < 1 or limit < 1 or limit > 100:
        raise InventarioError("Paginación inválida (limit 1-100, page >= 1).")

    rows, total = inventario_repos.listar_movimientos(
        id_empresa=id_empresa_target,
        id_material=int(id_material) if id_material else None,
        tipo_movimiento=tipo_movimiento.strip().upper() if tipo_movimiento else None,
        page=page,
        limit=limit
    )
    return {
        "success": True,
        "data": rows,
        "total": total,
        "page": page,
        "limit": limit
    }


def registrar_ajuste(data: dict, token, ip: str = "unknown"):
    id_empresa_target = _empresa(token, data.get("id_empresa"), obligatorio=True)
    id_usuario = _usuario(token)

    id_material = data.get("id_material")
    if not id_material:
        raise InventarioError("El campo 'id_material' es obligatorio.")
    try:
        id_material = int(id_material)
    except (ValueError, TypeError):
        raise InventarioError("El 'id_material' debe ser un entero.")

    tipo_movimiento = str(data.get("tipo_movimiento") or "").strip().upper()
    if tipo_movimiento not in {"ENTRADA_AJUSTE", "SALIDA_AJUSTE", "AJUSTE_INVENTARIO"}:
        raise InventarioError("Tipo de movimiento no válido. Debe ser ENTRADA_AJUSTE, SALIDA_AJUSTE o AJUSTE_INVENTARIO.")

    try:
        cantidad = Decimal(str(data.get("cantidad", 0)).strip())
        if cantidad <= 0:
            raise InventarioError("La cantidad del ajuste debe ser mayor a 0.")
    except (InvalidOperation, ValueError, TypeError):
        raise InventarioError("La cantidad debe ser un número válido.")

    observaciones = str(data.get("observaciones") or "").strip()
    if not observaciones:
        raise InventarioError("Debe ingresar una justificación u observación para el ajuste.")

    stock_minimo = None
    if "stock_minimo" in data and data.get("stock_minimo") is not None and str(data.get("stock_minimo")).strip() != "":
        try:
            stock_minimo = Decimal(str(data.get("stock_minimo")).strip())
            if stock_minimo < 0:
                raise InventarioError("El stock mínimo no puede ser negativo.")
        except (InvalidOperation, ValueError, TypeError):
            raise InventarioError("El stock mínimo debe ser un número válido.")

    try:
        resultado = inventario_repos.registrar_ajuste(
            id_empresa=id_empresa_target,
            id_material=id_material,
            cantidad=float(cantidad),
            tipo_movimiento=tipo_movimiento,
            id_usuario=id_usuario,
            observaciones=observaciones,
            stock_minimo=float(stock_minimo) if stock_minimo is not None else None
        )
    except Exception as exc:
        msg = str(exc)
        if "ERROR:" in msg:
            msg = msg.split("ERROR:")[-1].split("CONTEXT:")[0].strip()
        raise InventarioError(msg, 400)

    _log(
        token,
        "AJUSTE_INVENTARIO",
        f"Ajuste de inventario en material ID {id_material}: {tipo_movimiento} por {cantidad}. Obs: {observaciones}",
        ip
    )

    return {
        "success": True,
        "message": "Ajuste de inventario registrado correctamente.",
        "data": resultado
    }
