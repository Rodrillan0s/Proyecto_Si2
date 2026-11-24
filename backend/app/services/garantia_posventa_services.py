"""
Servicio CU42 – Garantías Inmobiliarias y Servicio Posventa (HU161–HU168).

Reglas de negocio acordadas:
- Catálogo extensible de categorías (HU164), sin clasificación automática ni alteración
  de la descripción original del cliente.
- Estados iniciales (HU166): REGISTRADA -> CLASIFICADA -> ASIGNADA -> EN_ATENCION -> RESUELTA -> CERRADA.
  Sin RECHAZADA (pendiente de aprobación) y sin forzar pasos artificialmente cuando el
  flujo operativo avanza directo a asignación o atención.
- Todo cambio relevante queda trazado en obras.t_posventa_seguimiento.
- id_garantia es opcional en solicitudes (HU163); sin duraciones estándar ni reglas de
  cobertura inventadas.
- Aislamiento estricto multi-tenant derivado exclusivamente del JWT.
"""
from datetime import date, datetime

from app.repos import bitacora_repos, crm_repos, garantia_posventa_repos as repo
from app.utils.security import es_admin_sistema, obtener_permisos_rol


CATEGORIAS_POSVENTA = (
    "ESTRUCTURAL",
    "INSTALACION_ELECTRICA",
    "INSTALACION_SANITARIA",
    "ACABADOS",
    "CARPINTERIA",
    "IMPERMEABILIZACION",
    "OTRO",
)

ESTADOS_POSVENTA = (
    "REGISTRADA",
    "CLASIFICADA",
    "ASIGNADA",
    "EN_ATENCION",
    "RESUELTA",
    "CERRADA",
)

# Máquina de estados hacia adelante sin forzar pasos intermedios innecesarios
# ni permitir retrocesos o cierres arbitrarios sin atención.
TRANSICIONES_POSVENTA = {
    "REGISTRADA": {"CLASIFICADA", "ASIGNADA", "EN_ATENCION"},
    "CLASIFICADA": {"ASIGNADA", "EN_ATENCION"},
    "ASIGNADA": {"EN_ATENCION"},
    "EN_ATENCION": {"RESUELTA"},
    "RESUELTA": {"CERRADA"},
    "CERRADA": set(),
}

ROLES_GESTION_POSVENTA = {
    "ADMINISTRADOR",
    "ADMINISTRADOR_EMPRESA",
    "JEFE DE OBRA",
    "JEFE_DE_OBRA",
    "SUPERVISOR",
    "SUPERVISOR_OBRA",
}


class PosventaError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _rol(token: dict) -> str:
    return str(token.get("nombre_rol") or "").strip().upper()


def _es_gestion(token: dict) -> bool:
    if es_admin_sistema(token):
        return True
    rol = _rol(token)
    if rol in ROLES_GESTION_POSVENTA:
        return True
    permisos = obtener_permisos_rol(token.get("nombre_rol"))
    return "Modificar_obras" in permisos or "Modificar_clientes" in permisos


def _empresa_token(token: dict) -> int | None:
    if es_admin_sistema(token):
        return None
    emp = token.get("id_empresa")
    if not emp:
        raise PosventaError("El token no identifica una empresa autorizada.", 403)
    return int(emp)


def _entero_positivo(valor, etiqueta: str) -> int:
    try:
        parsed = int(valor)
    except (TypeError, ValueError):
        raise PosventaError(f"{etiqueta} debe ser un entero positivo.")
    if parsed <= 0:
        raise PosventaError(f"{etiqueta} debe ser un entero positivo.")
    return parsed


def _texto(valor, etiqueta: str, obligatorio: bool = True, max_len: int | None = None) -> str:
    val = str(valor or "").strip()
    if obligatorio and not val:
        raise PosventaError(f"{etiqueta} es obligatorio/a.")
    if max_len and len(val) > max_len:
        raise PosventaError(f"{etiqueta} no puede superar {max_len} caracteres.")
    return val


def _parse_date(valor, etiqueta: str, obligatorio: bool = True) -> date | None:
    if valor is None or str(valor).strip() == "":
        if obligatorio:
            raise PosventaError(f"{etiqueta} es obligatoria.")
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    try:
        return datetime.strptime(str(valor).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        raise PosventaError(f"{etiqueta} debe tener formato YYYY-MM-DD.")


def _log(token: dict, accion: str, descripcion: str, ip: str = "unknown"):
    try:
        bitacora_repos.registrar_bitacora(
            id_usuario=token.get("nro_usuario"),
            modulo="POSVENTA",
            accion=accion,
            descripcion=descripcion,
            ip=ip or "unknown",
            estado="EXITOSO",
        )
    except Exception:
        pass


def _cliente_desde_token(token: dict) -> tuple[int, int, int]:
    if _rol(token) != "CLIENTE":
        raise PosventaError("Operación exclusiva del rol CLIENTE.", 403)
    id_usuario = _entero_positivo(token.get("nro_usuario"), "Usuario autenticado")
    id_empresa = _entero_positivo(token.get("id_empresa"), "Empresa autenticada")
    id_cliente = crm_repos.obtener_id_cliente_por_usuario_empresa(id_usuario, id_empresa)
    if id_cliente is None:
        raise PosventaError("El usuario autenticado no tiene un cliente CRM asociado.", 404)
    return id_cliente, id_usuario, id_empresa


# ─────────────────────────────────────────────────────────────────────────────
# HU161 – REGISTRAR GARANTÍAS INMOBILIARIAS
# ─────────────────────────────────────────────────────────────────────────────
def registrar_garantia(data: dict, token: dict, ip: str = "unknown") -> dict:
    if not _es_gestion(token):
        raise PosventaError("No tiene permisos para registrar garantías inmobiliarias.", 403)
    if not isinstance(data, dict):
        raise PosventaError("El cuerpo de la solicitud es inválido.")

    id_unidad = _entero_positivo(data.get("id_unidad"), "El identificador de unidad")
    unidad = repo.obtener_unidad_con_empresa(id_unidad)
    if not unidad:
        raise PosventaError("La unidad inmobiliaria no existe.", 404)

    emp_token = _empresa_token(token)
    if emp_token is not None and int(unidad["id_empresa"]) != emp_token:
        raise PosventaError("No puede registrar garantías sobre unidades de otra empresa.", 403)

    codigo = _texto(data.get("codigo"), "El código", obligatorio=False, max_len=50) or None
    tipo_garantia = _texto(data.get("tipo_garantia"), "El tipo de garantía", max_len=80)
    descripcion = _texto(data.get("descripcion"), "La descripción de la garantía", max_len=4000)
    fecha_inicio = _parse_date(data.get("fecha_inicio"), "La fecha de inicio", obligatorio=True)
    fecha_fin = _parse_date(data.get("fecha_fin"), "La fecha de fin", obligatorio=False)
    if fecha_fin is not None and fecha_fin < fecha_inicio:
        raise PosventaError("La fecha de fin no puede ser anterior a la fecha de inicio.")
    observaciones = _texto(data.get("observaciones"), "Las observaciones", obligatorio=False, max_len=2000) or None

    id_usuario = _entero_positivo(token.get("nro_usuario"), "Usuario autenticado")
    garantia = repo.crear_garantia(
        id_empresa=int(unidad["id_empresa"]),
        id_unidad=id_unidad,
        codigo=codigo,
        tipo_garantia=tipo_garantia,
        descripcion=descripcion,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        observaciones=observaciones,
        id_usuario_registro=id_usuario,
    )
    _log(token, "REGISTRAR_GARANTIA", f"Garantía #{garantia['id_garantia']} registrada en unidad {id_unidad}.", ip)
    return {"success": True, "data": garantia}


# ─────────────────────────────────────────────────────────────────────────────
# HU162 – CONSULTAR GARANTÍAS INMOBILIARIAS
# ─────────────────────────────────────────────────────────────────────────────
def listar_garantias(token: dict, id_unidad: int | None = None) -> dict:
    if id_unidad is not None:
        id_unidad = _entero_positivo(id_unidad, "El identificador de unidad")

    if _rol(token) == "CLIENTE":
        id_cliente, _, id_empresa = _cliente_desde_token(token)
        if id_unidad is not None and not crm_repos.validar_unidad_asociada_cliente(id_cliente, id_unidad):
            raise PosventaError("La unidad no está asociada a su cuenta de cliente.", 403)
        datos = repo.listar_garantias(id_empresa=id_empresa, id_unidad=id_unidad, id_cliente=id_cliente)
        return {"success": True, "data": datos}

    emp_token = _empresa_token(token)
    if id_unidad is not None and emp_token is not None:
        unidad = repo.obtener_unidad_con_empresa(id_unidad)
        if not unidad or int(unidad["id_empresa"]) != emp_token:
            raise PosventaError("Unidad no encontrada en su empresa.", 404)

    datos = repo.listar_garantias(id_empresa=emp_token, id_unidad=id_unidad)
    return {"success": True, "data": datos}


# ─────────────────────────────────────────────────────────────────────────────
# HU163 – REGISTRAR SOLICITUDES DE POSVENTA (CLIENTE)
# ─────────────────────────────────────────────────────────────────────────────
def registrar_solicitud_posventa(data: dict, token: dict, ip: str = "unknown") -> dict:
    if not isinstance(data, dict):
        raise PosventaError("El cuerpo de la solicitud es inválido.")

    id_cliente, id_usuario, id_empresa = _cliente_desde_token(token)
    id_unidad = _entero_positivo(data.get("id_unidad"), "El identificador de unidad")

    unidad = repo.obtener_unidad_con_empresa(id_unidad)
    if not unidad or int(unidad["id_empresa"]) != id_empresa:
        raise PosventaError("La unidad inmobiliaria no existe o pertenece a otra empresa.", 403)

    if not crm_repos.validar_unidad_asociada_cliente(id_cliente, id_unidad):
        raise PosventaError("El cliente no tiene acceso autorizado a la unidad indicada.", 403)

    id_garantia = None
    if data.get("id_garantia") not in (None, ""):
        id_garantia = _entero_positivo(data.get("id_garantia"), "El identificador de garantía")
        garantia = repo.obtener_garantia_por_id(id_garantia, id_empresa=id_empresa)
        if not garantia or int(garantia["id_unidad"]) != id_unidad:
            raise PosventaError("La garantía indicada no corresponde a esta unidad o empresa.", 400)

    titulo = _texto(data.get("titulo"), "El título de la solicitud", max_len=200)
    descripcion = _texto(data.get("descripcion"), "La descripción del problema", max_len=4000)

    id_solicitud = repo.crear_solicitud_posventa(
        id_empresa=id_empresa,
        id_unidad=id_unidad,
        id_cliente=id_cliente,
        id_garantia=id_garantia,
        titulo=titulo,
        descripcion=descripcion,
        id_usuario_creacion=id_usuario,
    )
    repo.registrar_seguimiento(
        id_solicitud_posventa=id_solicitud,
        id_usuario=id_usuario,
        accion="REGISTRO",
        estado_anterior=None,
        estado_nuevo="REGISTRADA",
        observacion="Solicitud de posventa registrada por el cliente.",
    )
    _log(token, "REGISTRAR_SOLICITUD_POSVENTA", f"Solicitud posventa #{id_solicitud} en unidad {id_unidad}.", ip)
    detalle = repo.obtener_solicitud_por_id(id_solicitud, id_empresa=id_empresa)
    return {"success": True, "id_solicitud_posventa": id_solicitud, "data": detalle}


# ─────────────────────────────────────────────────────────────────────────────
# HU164 – CLASIFICAR SOLICITUDES DE POSVENTA
# ─────────────────────────────────────────────────────────────────────────────
def clasificar_solicitud(id_solicitud: int, data: dict, token: dict, ip: str = "unknown") -> dict:
    if not _es_gestion(token):
        raise PosventaError("No tiene permisos para clasificar solicitudes de posventa.", 403)
    if not isinstance(data, dict):
        raise PosventaError("El cuerpo de la solicitud es inválido.")

    emp_token = _empresa_token(token)
    actual = repo.obtener_solicitud_por_id(id_solicitud, id_empresa=emp_token)
    if not actual:
        raise PosventaError("Solicitud de posventa no encontrada.", 404)
    if actual["estado"] == "CERRADA":
        raise PosventaError("No se puede clasificar una solicitud cerrada.", 409)

    categoria = _texto(data.get("categoria"), "La categoría", max_len=50).upper()
    if categoria not in CATEGORIAS_POSVENTA:
        raise PosventaError(
            f"Categoría inválida. Valores permitidos: {', '.join(CATEGORIAS_POSVENTA)}."
        )

    observacion = _texto(data.get("observacion"), "La observación", obligatorio=False, max_len=1000)
    estado_anterior = actual["estado"]
    nuevo_estado = "CLASIFICADA" if estado_anterior == "REGISTRADA" else estado_anterior

    repo.actualizar_clasificacion(id_solicitud, categoria, nuevo_estado)
    repo.registrar_seguimiento(
        id_solicitud_posventa=id_solicitud,
        id_usuario=_entero_positivo(token.get("nro_usuario"), "Usuario"),
        accion="CLASIFICACION",
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        observacion=observacion or f"Solicitud clasificada en categoría {categoria}.",
    )
    _log(token, "CLASIFICAR_POSVENTA", f"Solicitud #{id_solicitud} clasificada como {categoria}.", ip)
    return {
        "success": True,
        "data": repo.obtener_solicitud_por_id(id_solicitud, id_empresa=emp_token),
    }


# ─────────────────────────────────────────────────────────────────────────────
# HU165 – ASIGNAR RESPONSABLES DE ATENCIÓN
# ─────────────────────────────────────────────────────────────────────────────
def asignar_responsable(id_solicitud: int, data: dict, token: dict, ip: str = "unknown") -> dict:
    if not _es_gestion(token):
        raise PosventaError("No tiene permisos para asignar responsables de posventa.", 403)
    if not isinstance(data, dict):
        raise PosventaError("El cuerpo de la solicitud es inválido.")

    emp_token = _empresa_token(token)
    actual = repo.obtener_solicitud_por_id(id_solicitud, id_empresa=emp_token)
    if not actual:
        raise PosventaError("Solicitud de posventa no encontrada.", 404)
    if actual["estado"] in {"RESUELTA", "CERRADA"}:
        raise PosventaError("No se puede asignar responsable a una solicitud resuelta o cerrada.", 409)

    id_responsable = _entero_positivo(data.get("id_responsable"), "El identificador de responsable")
    responsable = repo.obtener_usuario_activo_empresa(id_responsable, int(actual["id_empresa"]))
    if not responsable:
        raise PosventaError("El responsable debe ser un usuario activo perteneciente a la misma empresa.", 403)
    if str(responsable["nombre_rol"] or "").strip().upper() == "CLIENTE":
        raise PosventaError("No se puede asignar un usuario con rol CLIENTE como responsable de atención.", 400)

    estado_anterior = actual["estado"]
    nuevo_estado = "ASIGNADA" if estado_anterior in {"REGISTRADA", "CLASIFICADA"} else estado_anterior
    observacion = _texto(data.get("observacion"), "La observación", obligatorio=False, max_len=1000)

    repo.actualizar_asignacion(id_solicitud, id_responsable, nuevo_estado)
    repo.registrar_seguimiento(
        id_solicitud_posventa=id_solicitud,
        id_usuario=_entero_positivo(token.get("nro_usuario"), "Usuario"),
        accion="ASIGNACION",
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        observacion=observacion or f"Responsable asignado: {responsable['nombre_completo']}.",
    )
    _log(token, "ASIGNAR_POSVENTA", f"Solicitud #{id_solicitud} asignada a usuario {id_responsable}.", ip)
    return {
        "success": True,
        "data": repo.obtener_solicitud_por_id(id_solicitud, id_empresa=emp_token),
    }


# ─────────────────────────────────────────────────────────────────────────────
# HU166 – GESTIONAR ATENCIÓN DE SOLICITUDES DE POSVENTA
# ─────────────────────────────────────────────────────────────────────────────
def gestionar_atencion(id_solicitud: int, data: dict, token: dict, ip: str = "unknown") -> dict:
    if not isinstance(data, dict):
        raise PosventaError("El cuerpo de la solicitud es inválido.")
    if _rol(token) == "CLIENTE":
        raise PosventaError("El rol CLIENTE no puede gestionar estados de atención posventa.", 403)

    emp_token = _empresa_token(token)
    actual = repo.obtener_solicitud_por_id(id_solicitud, id_empresa=emp_token)
    if not actual:
        raise PosventaError("Solicitud de posventa no encontrada.", 404)

    id_usuario = _entero_positivo(token.get("nro_usuario"), "Usuario")
    es_responsable_asignado = actual.get("id_responsable") is not None and int(actual["id_responsable"]) == id_usuario
    if not _es_gestion(token) and not es_responsable_asignado:
        raise PosventaError("No tiene permisos para gestionar la atención de esta solicitud.", 403)

    observacion = _texto(data.get("observacion"), "La observación de atención", max_len=4000)
    estado_anterior = actual["estado"]
    nuevo_estado_raw = data.get("estado")

    if nuevo_estado_raw is not None and str(nuevo_estado_raw).strip() != "":
        nuevo_estado = str(nuevo_estado_raw).strip().upper()
        if nuevo_estado not in ESTADOS_POSVENTA:
            raise PosventaError(f"Estado inválido. Permitidos: {', '.join(ESTADOS_POSVENTA)}.")
        if nuevo_estado != estado_anterior:
            permitidos = TRANSICIONES_POSVENTA.get(estado_anterior, set())
            if nuevo_estado not in permitidos:
                raise PosventaError(
                    f"Transición no permitida de {estado_anterior} a {nuevo_estado}.", 409
                )
            repo.actualizar_estado(id_solicitud, nuevo_estado)
            accion = "CAMBIO_ESTADO"
        else:
            accion = "ATENCION"
    else:
        nuevo_estado = estado_anterior
        accion = "ATENCION"

    repo.registrar_seguimiento(
        id_solicitud_posventa=id_solicitud,
        id_usuario=id_usuario,
        accion=accion,
        estado_anterior=estado_anterior,
        estado_nuevo=nuevo_estado,
        observacion=observacion,
    )
    _log(
        token,
        "ATENCION_POSVENTA",
        f"Solicitud #{id_solicitud}: {estado_anterior} -> {nuevo_estado}.",
        ip,
    )
    detalle = repo.obtener_solicitud_por_id(id_solicitud, id_empresa=emp_token)
    detalle["seguimiento"] = repo.listar_seguimiento_solicitud(id_solicitud)
    return {"success": True, "data": detalle}


# ─────────────────────────────────────────────────────────────────────────────
# HU167 – CONSULTAR SEGUIMIENTO DE SOLICITUDES DE POSVENTA
# ─────────────────────────────────────────────────────────────────────────────
def listar_solicitudes(
    token: dict,
    id_unidad: int | None = None,
    estado: str | None = None,
    categoria: str | None = None,
) -> dict:
    if id_unidad is not None:
        id_unidad = _entero_positivo(id_unidad, "El identificador de unidad")
    if estado:
        estado = estado.strip().upper()
        if estado not in ESTADOS_POSVENTA:
            raise PosventaError("Estado de filtro inválido.")
    if categoria:
        categoria = categoria.strip().upper()
        if categoria not in CATEGORIAS_POSVENTA:
            raise PosventaError("Categoría de filtro inválida.")

    if _rol(token) == "CLIENTE":
        id_cliente, _, id_empresa = _cliente_desde_token(token)
        datos = repo.listar_solicitudes(
            id_empresa=id_empresa,
            id_cliente=id_cliente,
            id_unidad=id_unidad,
            estado=estado,
            categoria=categoria,
        )
        return {"success": True, "data": datos}

    emp_token = _empresa_token(token)
    id_resp = None if _es_gestion(token) else _entero_positivo(token.get("nro_usuario"), "Usuario")
    datos = repo.listar_solicitudes(
        id_empresa=emp_token,
        id_unidad=id_unidad,
        estado=estado,
        categoria=categoria,
        id_responsable=id_resp,
    )
    return {"success": True, "data": datos}


def obtener_seguimiento_solicitud(id_solicitud: int, token: dict) -> dict:
    if _rol(token) == "CLIENTE":
        id_cliente, _, id_empresa = _cliente_desde_token(token)
        solicitud = repo.obtener_solicitud_por_id(id_solicitud, id_empresa=id_empresa)
        if not solicitud or int(solicitud["id_cliente"]) != id_cliente:
            raise PosventaError("Solicitud de posventa no encontrada.", 404)
    else:
        emp_token = _empresa_token(token)
        solicitud = repo.obtener_solicitud_por_id(id_solicitud, id_empresa=emp_token)
        if not solicitud:
            raise PosventaError("Solicitud de posventa no encontrada.", 404)
        id_usuario = _entero_positivo(token.get("nro_usuario"), "Usuario")
        if not _es_gestion(token) and solicitud.get("id_responsable") != id_usuario:
            raise PosventaError("No tiene permisos para consultar esta solicitud.", 403)

    solicitud["seguimiento"] = repo.listar_seguimiento_solicitud(id_solicitud)
    return {"success": True, "data": solicitud}


# ─────────────────────────────────────────────────────────────────────────────
# HU168 – CONSULTAR HISTORIAL DE GARANTÍAS Y ATENCIONES POR UNIDAD
# ─────────────────────────────────────────────────────────────────────────────
def consultar_historial_unidad(id_unidad: int, token: dict) -> dict:
    id_unidad = _entero_positivo(id_unidad, "El identificador de unidad")
    unidad = repo.obtener_unidad_con_empresa(id_unidad)
    if not unidad:
        raise PosventaError("Unidad inmobiliaria no encontrada.", 404)

    if _rol(token) == "CLIENTE":
        id_cliente, _, id_empresa = _cliente_desde_token(token)
        if int(unidad["id_empresa"]) != id_empresa or not crm_repos.validar_unidad_asociada_cliente(id_cliente, id_unidad):
            raise PosventaError("No tiene acceso autorizado al historial de esta unidad.", 403)
        garantias = repo.listar_garantias(id_empresa=id_empresa, id_unidad=id_unidad, id_cliente=id_cliente)
        solicitudes = repo.listar_solicitudes(id_empresa=id_empresa, id_cliente=id_cliente, id_unidad=id_unidad)
    else:
        emp_token = _empresa_token(token)
        if emp_token is not None and int(unidad["id_empresa"]) != emp_token:
            raise PosventaError("La unidad pertenece a otra empresa.", 403)
        id_emp_real = int(unidad["id_empresa"])
        garantias = repo.listar_garantias(id_empresa=id_emp_real, id_unidad=id_unidad)
        solicitudes = repo.listar_solicitudes(id_empresa=id_emp_real, id_unidad=id_unidad)

    for sol in solicitudes:
        sol["seguimiento"] = repo.listar_seguimiento_solicitud(sol["id_solicitud_posventa"])

    return {
        "success": True,
        "data": {
            "unidad": unidad,
            "garantias": garantias,
            "solicitudes": solicitudes,
        },
    }
