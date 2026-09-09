import re

from app.repos import bitacora_repos, proveedor_repos


# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────
ESTADOS = {"ACTIVO", "INACTIVO"}
PROHIBIDOS_EDICION = {"id_proveedor", "id_empresa", "estado", "created_at"}
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ─────────────────────────────────────────────────────────────────────────────
# Excepción del módulo
# ─────────────────────────────────────────────────────────────────────────────
class ProveedorError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _empresa(token):
    value = token.get("id_empresa")
    if not value:
        raise ProveedorError("El token no identifica una empresa.", 403)
    return value


def _str(data, key, label, obligatorio=True, max_len=None):
    val = str(data.get(key) or "").strip()
    if obligatorio and not val:
        raise ProveedorError(f"{label} es obligatorio/a.")
    if max_len and len(val) > max_len:
        raise ProveedorError(f"{label} no puede superar {max_len} caracteres.")
    return val or None


def _log(token, accion, descripcion, ip):
    bitacora_repos.registrar_bitacora(
        token.get("nro_usuario"), "PROVEEDORES", accion, descripcion, ip, "EXITOSO"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Validación de payload
# ─────────────────────────────────────────────────────────────────────────────
def _validar(data, creando):
    if not isinstance(data, dict):
        raise ProveedorError("El cuerpo debe ser un objeto válido.")

    if not creando:
        invalidos = PROHIBIDOS_EDICION.intersection(data)
        if invalidos:
            raise ProveedorError(
                "No se permite modificar: " + ", ".join(sorted(invalidos)) + "."
            )

    result = {}
    result["nombre"]   = _str(data, "nombre",   "El nombre/razón social", max_len=200)
    result["nit"]      = _str(data, "nit",       "El NIT",                 max_len=50)
    result["telefono"] = _str(data, "telefono",  "El teléfono", obligatorio=False, max_len=30)
    result["contacto"] = _str(data, "contacto",  "El contacto", obligatorio=False, max_len=150)
    result["direccion"]= _str(data, "direccion", "La dirección",obligatorio=False)

    email = _str(data, "email", "El email", obligatorio=False, max_len=150)
    if email and not _EMAIL_RE.match(email):
        raise ProveedorError("El formato del correo electrónico no es válido.")
    result["email"] = email

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Casos de uso
# ─────────────────────────────────────────────────────────────────────────────
def registrar(data, token, ip="unknown"):
    clean = _validar(data, True)
    try:
        id_proveedor = proveedor_repos.crear(_empresa(token), clean)
    except proveedor_repos.ProveedorConflictError as exc:
        raise ProveedorError(str(exc), 409)
    _log(token, "REGISTRAR_PROVEEDOR", f"Proveedor {id_proveedor} registrado.", ip)
    return {
        "success": True,
        "id_proveedor": id_proveedor,
        "message": "Proveedor registrado exitosamente.",
    }


def modificar(id_proveedor, data, token, ip="unknown"):
    id_empresa = _empresa(token)
    if not proveedor_repos.obtener(id_empresa, id_proveedor):
        raise ProveedorError("Proveedor no encontrado.", 404)
    clean = _validar(data, False)
    try:
        saved = proveedor_repos.actualizar(id_empresa, id_proveedor, clean)
    except proveedor_repos.ProveedorConflictError as exc:
        raise ProveedorError(str(exc), 409)
    if not saved:
        raise ProveedorError("Proveedor no encontrado.", 404)
    _log(token, "MODIFICAR_PROVEEDOR", f"Proveedor {id_proveedor} modificado.", ip)
    return {"success": True, "message": "Proveedor actualizado exitosamente."}


def listar(token, q=None, estado=None, page=1, limit=20):
    if estado:
        estado = estado.upper()
        if estado not in ESTADOS:
            raise ProveedorError("Estado inválido. Use ACTIVO o INACTIVO.")
    if page < 1 or limit < 1 or limit > 100:
        raise ProveedorError("Paginación inválida; limit debe estar entre 1 y 100.")
    rows, total = proveedor_repos.listar(
        _empresa(token),
        q.strip() if q else None,
        estado,
        page,
        limit,
    )
    return {
        "success": True,
        "data": rows,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
        },
    }


def detalle(id_proveedor, token):
    data = proveedor_repos.obtener(_empresa(token), id_proveedor)
    if not data:
        raise ProveedorError("Proveedor no encontrado.", 404)
    return {"success": True, "data": data}


def cambiar_estado(id_proveedor, estado, token, ip="unknown"):
    estado = str(estado or "").strip().upper()
    if estado not in ESTADOS:
        raise ProveedorError("Estado inválido.")
    id_empresa = _empresa(token)
    if not proveedor_repos.cambiar_estado(id_empresa, id_proveedor, estado):
        raise ProveedorError("Proveedor no encontrado.", 404)
    accion = "DESACTIVAR_PROVEEDOR" if estado == "INACTIVO" else "REACTIVAR_PROVEEDOR"
    _log(token, accion, f"Proveedor {id_proveedor} cambiado a {estado}.", ip)
    return {"success": True, "message": "Estado actualizado exitosamente."}


def listar_materiales(id_proveedor, token):
    id_empresa = _empresa(token)
    if not proveedor_repos.obtener(id_empresa, id_proveedor):
        raise ProveedorError("Proveedor no encontrado.", 404)
    data = proveedor_repos.listar_materiales_de_proveedor(id_proveedor, id_empresa)
    return {"success": True, "data": data}


def asociar_materiales(id_proveedor, ids_material, token, ip="unknown"):
    """
    Asocia una lista de materiales al proveedor.
    Valida que cada material exista en la empresa.
    Devuelve cuántas asociaciones nuevas se crearon.
    """
    if not isinstance(ids_material, list) or len(ids_material) == 0:
        raise ProveedorError("Debe proporcionar al menos un id_material.")

    id_empresa = _empresa(token)
    if not proveedor_repos.obtener(id_empresa, id_proveedor):
        raise ProveedorError("Proveedor no encontrado.", 404)

    nuevas = 0
    for id_mat in ids_material:
        try:
            id_mat = int(id_mat)
        except (TypeError, ValueError):
            raise ProveedorError(f"ID de material inválido: {id_mat}.")
        if not proveedor_repos.material_existe(id_mat, id_empresa):
            raise ProveedorError(f"Material {id_mat} no encontrado.", 404)
        if proveedor_repos.asociar_material(id_proveedor, id_mat):
            nuevas += 1

    _log(
        token,
        "ASOCIAR_MATERIALES_PROVEEDOR",
        f"Proveedor {id_proveedor}: {nuevas} material(es) asociado(s).",
        ip,
    )
    return {
        "success": True,
        "nuevas_asociaciones": nuevas,
        "message": f"{nuevas} material(es) asociado(s) correctamente.",
    }


def desasociar_material(id_proveedor, id_material, token, ip="unknown"):
    id_empresa = _empresa(token)
    if not proveedor_repos.obtener(id_empresa, id_proveedor):
        raise ProveedorError("Proveedor no encontrado.", 404)
    if not proveedor_repos.material_existe(id_material, id_empresa):
        raise ProveedorError("Material no encontrado.", 404)
    if not proveedor_repos.desasociar_material(id_proveedor, id_material):
        raise ProveedorError("La asociación no existe.", 404)
    _log(
        token,
        "DESASOCIAR_MATERIAL_PROVEEDOR",
        f"Proveedor {id_proveedor}: material {id_material} desasociado.",
        ip,
    )
    return {"success": True, "message": "Material desasociado correctamente."}
