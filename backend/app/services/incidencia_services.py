import os
import uuid

from app.repos import bitacora_repos, incidencia_repos


# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────
PRIORIDADES = {"BAJA", "MEDIA", "ALTA", "CRITICA"}
ESTADOS = {"ABIERTA", "ASIGNADA", "EN_PROCESO", "PENDIENTE_VALIDACION", "RESUELTA", "CERRADA"}

# Máquina de estados: no se permiten saltos arbitrarios (HU72).
TRANSICIONES = {
    "ABIERTA": {"ASIGNADA"},
    "ASIGNADA": {"EN_PROCESO"},
    "EN_PROCESO": {"PENDIENTE_VALIDACION"},
    "PENDIENTE_VALIDACION": {"RESUELTA", "EN_PROCESO"},
    "RESUELTA": {"CERRADA"},
    "CERRADA": set(),
}

# Transiciones reservadas al responsable asignado (verbo para mensajes).
ACCIONES_RESPONSABLE = {"EN_PROCESO": "iniciar", "PENDIENTE_VALIDACION": "finalizar"}

# Seguimiento por defecto cuando el cambio de estado no trae observación.
OBSERVACION_AUTOMATICA = {
    "EN_PROCESO": "Inicio de atención de la incidencia.",
    "PENDIENTE_VALIDACION": "Fin de atención: pendiente de validación.",
    "RESUELTA": "Resolución aprobada.",
}

MAX_ORDENES_TRABAJO = 100

ALLOWED_EVIDENCIA_MIME ={"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_EVIDENCIA_BYTES = 10 * 1024 * 1024  # 10 MB


# ─────────────────────────────────────────────────────────────────────────────
# Excepción del módulo
# ─────────────────────────────────────────────────────────────────────────────
class IncidenciaError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _empresa_id(token):
    """
    Nunca confía en id_empresa enviado por el cliente: siempre se obtiene del
    token de sesión. El administrador de plataforma (ADMINISTRADOR) recibe
    None para no filtrar por empresa (acceso global de solo lectura/soporte).
    """
    from app.utils.security import es_admin_sistema
    if es_admin_sistema(token):
        return None
    id_empresa = token.get("id_empresa")
    if not id_empresa:
        raise IncidenciaError("El token no identifica una empresa.", 403)
    return id_empresa


def _texto(value, label, obligatorio=True, max_len=None):
    val = str(value or "").strip()
    if obligatorio and not val:
        raise IncidenciaError(f"{label} es obligatorio/a.")
    if max_len and len(val) > max_len:
        raise IncidenciaError(f"{label} no puede superar {max_len} caracteres.")
    return val


def _prioridad(value):
    val = str(value or "").strip().upper()
    if val not in PRIORIDADES:
        raise IncidenciaError("La prioridad debe ser BAJA, MEDIA, ALTA o CRITICA.")
    return val


def _entero_positivo(value, label):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise IncidenciaError(f"{label} no es válido.")
    if parsed <= 0:
        raise IncidenciaError(f"{label} no es válido.")
    return parsed


def _tiene_permiso(token, nombre_permiso):
    from app.utils.security import es_admin_sistema, obtener_permisos_rol
    if es_admin_sistema(token):
        return True
    return nombre_permiso in obtener_permisos_rol(token.get("nombre_rol"))


def _es_usuario(token, id_usuario):
    """True si el usuario autenticado (JWT) es id_usuario."""
    try:
        return int(token.get("nro_usuario")) == int(id_usuario)
    except (TypeError, ValueError):
        return False


def es_trabajador(token):
    rol = str(token.get("nombre_rol") or "").upper().replace("Ñ", "N").replace("_", "").replace(" ", "")
    return rol in {"ELECTRICO", "PLOMERO", "MAESTROALBANIL", "ALBANIL"}


def autorizar_registro(token):
    if not es_trabajador(token) and not _tiene_permiso(token, "Registrar_incidencias"):
        raise IncidenciaError("No tiene permisos para registrar incidencias.", 403)
    _empresa_id(token)
    return token


def obras_registro(token):
    autorizar_registro(token)
    return {"success": True, "data": incidencia_repos.obras_registro(
        _empresa_id(token), token.get("nro_usuario") if es_trabajador(token) else None
    )}


def autorizar_atencion(id_incidencia, token, permiso=None, solo_responsable=False, permitir_registrador=False):
    """Autoriza esta incidencia después de validar su empresa mediante el JWT."""
    estado, responsable = incidencia_repos.obtener_estado_actual(id_incidencia, _empresa_id(token))
    if estado is None:
        raise IncidenciaError("Incidencia no encontrada.", 404)
    if _es_usuario(token, responsable):
        return token
    if not solo_responsable and permiso and _tiene_permiso(token, permiso):
        return token
    if not solo_responsable and (permitir_registrador or (permiso == "Visualizar_incidencias" and es_trabajador(token))):
        detalle = incidencia_repos.obtener_detalle(id_incidencia, _empresa_id(token))
        if detalle and _es_usuario(token, detalle.get("id_usuario_registro")):
            return token
    raise IncidenciaError("No tiene permisos para acceder a esta incidencia.", 403)


def _ot_label(orden_nro):
    return f"OT-{int(orden_nro):03d}"


def _log(token, accion, descripcion, ip):
    bitacora_repos.registrar_bitacora(
        token.get("nro_usuario"), "INCIDENCIAS", accion, descripcion, ip, "EXITOSO"
    )


def _upload_root():
    # backend/app/services/incidencia_services.py -> backend/
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(backend_dir, "uploads", "incidencias")
    os.makedirs(path, exist_ok=True)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# HU69 – Registrar incidencia
# ─────────────────────────────────────────────────────────────────────────────
def registrar(data, token, ip="unknown"):
    if not isinstance(data, dict):
        raise IncidenciaError("El cuerpo debe ser un objeto válido.")

    if data.get("id_obra") in (None, ""):
        raise IncidenciaError("El proyecto/obra es obligatorio.")
    id_obra = _entero_positivo(data.get("id_obra"), "El identificador del proyecto")

    id_empresa_token = _empresa_id(token)
    id_empresa_real = incidencia_repos.obtener_empresa_obra(id_obra, id_empresa_token)
    if id_empresa_real is None:
        raise IncidenciaError("El proyecto no existe o no pertenece a su empresa.", 404)
    if es_trabajador(token) and not incidencia_repos.trabajador_en_obra(
        id_obra, token.get("nro_usuario"), id_empresa_token
    ):
        raise IncidenciaError("No pertenece al personal activo de esta obra.", 403)

    id_unidad = data.get("id_unidad")
    if id_unidad not in (None, ""):
        id_unidad = _entero_positivo(id_unidad, "El identificador de la unidad")
        if not incidencia_repos.unidad_pertenece_a_obra(id_unidad, id_obra):
            raise IncidenciaError("La unidad no existe o no pertenece al proyecto indicado.")
    else:
        id_unidad = None

    titulo = _texto(data.get("titulo"), "El título", max_len=200)
    descripcion = _texto(data.get("descripcion"), "La descripción", max_len=4000)
    prioridad = _prioridad(data.get("prioridad"))
    ubicacion = _texto(data.get("ubicacion"), "La ubicación", obligatorio=False, max_len=255) or None

    # El cliente NO puede fijar el estado inicial ni las fechas de atención:
    # se ignora cualquier 'estado'/'fecha_*' recibido; siempre nace en ABIERTA
    # sin fechas de atención (se aplica en el repo/BD).
    id_usuario = token.get("nro_usuario")

    id_incidencia = incidencia_repos.crear(
        id_obra, id_unidad, id_usuario, titulo, descripcion, prioridad, ubicacion
    )
    incidencia_repos.crear_seguimiento(
        id_incidencia, id_usuario, None, "ABIERTA", "Incidencia registrada."
    )
    _log(token, "REGISTRAR_INCIDENCIA", f"Incidencia {id_incidencia} registrada en obra {id_obra}.", ip)
    return {
        "success": True,
        "id_incidencia": id_incidencia,
        "message": "Incidencia registrada exitosamente.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Listar / detalle
# ─────────────────────────────────────────────────────────────────────────────
def listar(token, id_obra=None, id_unidad=None, prioridad=None, estado=None,
           busqueda=None, id_responsable=None, page=1, limit=20):
    if page < 1 or limit < 1 or limit > 100:
        raise IncidenciaError("Paginación inválida; limit debe estar entre 1 y 100.")
    if prioridad:
        prioridad = prioridad.strip().upper()
        if prioridad not in PRIORIDADES:
            raise IncidenciaError("Prioridad inválida.")
    if estado:
        estado = estado.strip().upper()
        if estado not in ESTADOS:
            raise IncidenciaError("Estado inválido.")

    id_empresa = _empresa_id(token)
    propios = None
    if es_trabajador(token) and id_responsable is None and not _tiene_permiso(token, "Visualizar_incidencias"):
        propios = _entero_positivo(token.get("nro_usuario"), "El usuario autenticado")
    elif not _tiene_permiso(token, "Visualizar_incidencias"):
        id_responsable = _entero_positivo(token.get("nro_usuario"), "El usuario autenticado")
    opciones = {"id_usuario_visible": propios} if propios is not None else {}
    rows, total = incidencia_repos.listar(
        id_empresa, id_obra, id_unidad, prioridad, estado,
        busqueda.strip() if busqueda else None, id_responsable, page, limit, **opciones
    )
    return {
        "success": True,
        "data": rows,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit if total else 0,
        },
    }


def obtener(id_incidencia, token):
    id_empresa = _empresa_id(token)
    data = incidencia_repos.obtener_detalle(id_incidencia, id_empresa)
    if not data:
        raise IncidenciaError("Incidencia no encontrada.", 404)
    data["ordenes_trabajo"] = incidencia_repos.listar_ordenes_trabajo_incidencia(id_incidencia)
    return {"success": True, "data": data}


# ─────────────────────────────────────────────────────────────────────────────
# HU71 – Candidatos a responsable (para el selector del modal "Asignar
# responsable"). Nunca se filtra por id_empresa enviado por el cliente: se
# valida que la incidencia sea accesible para el token (igual que obtener())
# y luego se resuelve la empresa REAL vía incidencia -> obra -> empresa, la
# misma fuente de verdad que ya usa asignar_responsable() para validar el
# responsable al confirmar.
# ─────────────────────────────────────────────────────────────────────────────
def obtener_responsables(id_incidencia, token):
    id_empresa_token = _empresa_id(token)
    detalle = incidencia_repos.obtener_detalle(id_incidencia, id_empresa_token)
    if not detalle:
        raise IncidenciaError("Incidencia no encontrada.", 404)

    id_empresa_real = incidencia_repos.obtener_empresa_incidencia(id_incidencia)
    usuarios = incidencia_repos.obtener_usuarios_asignables(id_empresa_real, detalle["id_obra"])
    return {"success": True, "data": usuarios}


# ─────────────────────────────────────────────────────────────────────────────
# Modificar datos generales (título/descripción/prioridad)
# ─────────────────────────────────────────────────────────────────────────────
def actualizar(id_incidencia, data, token, ip="unknown"):
    id_empresa = _empresa_id(token)
    estado_actual, _ = incidencia_repos.obtener_estado_actual(id_incidencia, id_empresa)
    if estado_actual is None:
        raise IncidenciaError("Incidencia no encontrada.", 404)
    if estado_actual == "CERRADA":
        raise IncidenciaError("No se puede modificar una incidencia cerrada.")

    titulo = _texto(data.get("titulo"), "El título", max_len=200)
    descripcion = _texto(data.get("descripcion"), "La descripción", max_len=4000)
    prioridad = _prioridad(data.get("prioridad"))
    # La ubicación solo se modifica si el cliente envía el campo (si no, se conserva).
    actualizar_ubicacion = "ubicacion" in data
    ubicacion = _texto(data.get("ubicacion"), "La ubicación", obligatorio=False, max_len=255) or None

    if not incidencia_repos.actualizar(id_incidencia, id_empresa, titulo, descripcion, prioridad,
                                       actualizar_ubicacion, ubicacion):
        raise IncidenciaError("Incidencia no encontrada.", 404)

    _log(token, "MODIFICAR_INCIDENCIA", f"Incidencia {id_incidencia} modificada.", ip)
    return {"success": True, "message": "Incidencia actualizada exitosamente."}


# ─────────────────────────────────────────────────────────────────────────────
# HU71 – Asignar responsable
# ─────────────────────────────────────────────────────────────────────────────
def asignar_responsable(id_incidencia, data, token, ip="unknown"):
    if data.get("id_responsable") in (None, ""):
        raise IncidenciaError("El campo id_responsable es obligatorio.")
    id_responsable = _entero_positivo(data.get("id_responsable"), "El identificador del responsable")

    id_empresa_token = _empresa_id(token)
    estado_actual, _responsable_previo = incidencia_repos.obtener_estado_actual(id_incidencia, id_empresa_token)
    if estado_actual is None:
        raise IncidenciaError("Incidencia no encontrada.", 404)
    if estado_actual == "CERRADA":
        raise IncidenciaError("No se puede reasignar una incidencia cerrada.")

    # El responsable siempre se valida contra la empresa real de la incidencia,
    # nunca contra una empresa enviada por el cliente.
    id_empresa_real = incidencia_repos.obtener_empresa_incidencia(id_incidencia)
    if not incidencia_repos.usuario_pertenece_a_empresa(id_responsable, id_empresa_real):
        raise IncidenciaError("El responsable no existe o no pertenece a su empresa.", 404)

    detalle = incidencia_repos.obtener_detalle(id_incidencia, id_empresa_token)
    if not detalle:
        raise IncidenciaError("Incidencia no encontrada.", 404)
    candidatos = incidencia_repos.obtener_usuarios_asignables(id_empresa_real, detalle["id_obra"])
    if not any(u["nro_usuario"] == id_responsable for u in candidatos):
        raise IncidenciaError("El responsable no está activo, no pertenece a la obra de la incidencia o no tiene un rol de campo o supervisión permitido.", 404)

    # HU71: al asignar por primera vez, ABIERTA -> ASIGNADA. Una reasignación
    # posterior conserva el estado actual del flujo (no retrocede a ASIGNADA).
    nuevo_estado = "ASIGNADA" if estado_actual == "ABIERTA" else estado_actual

    if not incidencia_repos.asignar_responsable(id_incidencia, id_empresa_token, id_responsable, nuevo_estado):
        raise IncidenciaError("Incidencia no encontrada.", 404)

    observacion = f"Responsable {id_responsable} asignado."
    incidencia_repos.crear_seguimiento(
        id_incidencia, token.get("nro_usuario"), estado_actual, nuevo_estado, observacion
    )
    _log(token, "ASIGNAR_RESPONSABLE", f"Incidencia {id_incidencia}: responsable {id_responsable} asignado.", ip)
    return {"success": True, "message": "Responsable asignado exitosamente.", "estado": nuevo_estado}


# ─────────────────────────────────────────────────────────────────────────────
# HU72 / HU74 – Cambiar estado (incluye el cierre)
# ─────────────────────────────────────────────────────────────────────────────
def cambiar_estado(id_incidencia, data, token, ip="unknown"):
    estado_nuevo = str(data.get("estado") or "").strip().upper()
    if estado_nuevo not in ESTADOS:
        raise IncidenciaError("Estado inválido.")

    id_empresa = _empresa_id(token)
    estado_actual, id_responsable = incidencia_repos.obtener_estado_actual(id_incidencia, id_empresa)
    if estado_actual is None:
        raise IncidenciaError("Incidencia no encontrada.", 404)

    if estado_nuevo == estado_actual:
        raise IncidenciaError(f"La incidencia ya se encuentra en estado {estado_actual}.")

    permitidos = TRANSICIONES.get(estado_actual, set())
    if estado_nuevo not in permitidos:
        raise IncidenciaError(
            f"Transición de estado no permitida: {estado_actual} -> {estado_nuevo}."
        )
    if estado_nuevo == "ASIGNADA" and not id_responsable:
        raise IncidenciaError("Debe asignar un responsable antes de mover la incidencia a ASIGNADA.")

    if estado_nuevo == "CERRADA" and not _tiene_permiso(token, "Cerrar_incidencias"):
        raise IncidenciaError("No tiene permisos para cerrar incidencias.", 403)

    validando = estado_actual == "PENDIENTE_VALIDACION"
    if validando and not _tiene_permiso(token, "Modificar_incidencias"):
        raise IncidenciaError("No tiene permisos para validar la resolución.", 403)

    # Iniciar (ASIGNADA -> EN_PROCESO) y finalizar (EN_PROCESO -> PENDIENTE_VALIDACION) la
    # atención solo puede hacerlo el responsable asignado. Se verifica aquí y
    # además en el UPDATE condicional del repo (no se confía en el frontend).
    responsable_requerido = None
    if estado_nuevo in ACCIONES_RESPONSABLE and not validando:
        if not id_responsable:
            raise IncidenciaError("La incidencia no tiene un responsable asignado.")
        if not _es_usuario(token, id_responsable):
            raise IncidenciaError(
                f"Solo el responsable asignado puede {ACCIONES_RESPONSABLE[estado_nuevo]} la atención de la incidencia.",
                403,
            )
        responsable_requerido = id_responsable

    observacion = (
        str(data.get("observacion") or "").strip()
        or ("Resolución rechazada: continuar atención." if validando and estado_nuevo == "EN_PROCESO"
            else OBSERVACION_AUTOMATICA.get(estado_nuevo))
    )

    # Las fechas de inicio/fin de atención las genera el servidor dentro del
    # mismo UPDATE; cualquier fecha enviada por el cliente se ignora.
    if not incidencia_repos.cambiar_estado(
        id_incidencia, id_empresa, estado_actual, estado_nuevo, responsable_requerido
    ):
        raise IncidenciaError(
            "La incidencia fue modificada por otra operación. Recargue e intente nuevamente.", 409
        )

    incidencia_repos.crear_seguimiento(
        id_incidencia, token.get("nro_usuario"), estado_actual, estado_nuevo, observacion
    )

    accion = "CERRAR_INCIDENCIA" if estado_nuevo == "CERRADA" else "CAMBIAR_ESTADO_INCIDENCIA"
    _log(token, accion, f"Incidencia {id_incidencia}: {estado_actual} -> {estado_nuevo}.", ip)
    return {
        "success": True,
        "message": "Estado actualizado exitosamente.",
        "estado_anterior": estado_actual,
        "estado_nuevo": estado_nuevo,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Órdenes de trabajo afectadas (relación M:N incidencia <-> OT)
#
# Solo se leen datos de obras.t_orden_trabajo; el módulo de OT no se modifica.
# Una OT solo puede vincularse si pertenece a la MISMA obra de la incidencia y
# a la empresa REAL de la incidencia (incidencia -> obra -> empresa). Nunca se
# usa un id_empresa ni un id_obra enviados por el cliente.
# ─────────────────────────────────────────────────────────────────────────────
def _incidencia_accesible(id_incidencia, token):
    """Detalle de la incidencia si es accesible para el token (404 si no)."""
    detalle = incidencia_repos.obtener_detalle(id_incidencia, _empresa_id(token))
    if not detalle:
        raise IncidenciaError("Incidencia no encontrada.", 404)
    return detalle


def listar_ordenes_trabajo(id_incidencia, token):
    _incidencia_accesible(id_incidencia, token)
    data = incidencia_repos.listar_ordenes_trabajo_incidencia(id_incidencia)
    return {"success": True, "data": data}


def listar_ordenes_trabajo_disponibles(id_incidencia, token):
    detalle = _incidencia_accesible(id_incidencia, token)
    id_empresa_real = incidencia_repos.obtener_empresa_incidencia(id_incidencia)
    data = incidencia_repos.listar_ordenes_trabajo_obra(
        detalle["id_obra"], id_empresa_real, id_incidencia
    )
    return {"success": True, "data": data}


def _lista_ordenes(value):
    if not isinstance(value, list):
        raise IncidenciaError("El campo ordenes debe ser una lista de órdenes de trabajo.")
    if len(value) > MAX_ORDENES_TRABAJO:
        raise IncidenciaError(f"No se pueden vincular más de {MAX_ORDENES_TRABAJO} órdenes de trabajo.")
    ordenes = []
    for item in value:
        if isinstance(item, bool):
            raise IncidenciaError("El identificador de la orden de trabajo no es válido.")
        orden = _entero_positivo(item, "El identificador de la orden de trabajo")
        if orden not in ordenes:
            ordenes.append(orden)
    return ordenes


def actualizar_ordenes_trabajo(id_incidencia, data, token, ip="unknown"):
    if not isinstance(data, dict) or "ordenes" not in data:
        raise IncidenciaError("El campo ordenes es obligatorio.")
    ordenes = _lista_ordenes(data.get("ordenes"))

    detalle = _incidencia_accesible(id_incidencia, token)
    estado_actual = detalle["estado"]
    if estado_actual == "CERRADA":
        raise IncidenciaError("No se pueden modificar las órdenes de trabajo de una incidencia cerrada.")

    id_empresa_real = incidencia_repos.obtener_empresa_incidencia(id_incidencia)
    validas = incidencia_repos.filtrar_ordenes_de_obra(ordenes, detalle["id_obra"], id_empresa_real)
    invalidas = [o for o in ordenes if o not in validas]
    if invalidas:
        # Mensaje genérico: no se revela si la OT existe en otra obra/empresa.
        raise IncidenciaError(
            "Las siguientes órdenes de trabajo no existen o no pertenecen a la obra de la incidencia: "
            + ", ".join(_ot_label(o) for o in invalidas) + "."
        )

    id_usuario = token.get("nro_usuario")
    agregadas, quitadas = incidencia_repos.reemplazar_ordenes_trabajo(id_incidencia, ordenes, id_usuario)

    if agregadas or quitadas:
        partes = []
        if agregadas:
            partes.append("agregadas " + ", ".join(_ot_label(o) for o in agregadas))
        if quitadas:
            partes.append("quitadas " + ", ".join(_ot_label(o) for o in quitadas))
        detalle_cambio = "; ".join(partes)
        incidencia_repos.crear_seguimiento(
            id_incidencia, id_usuario, estado_actual, estado_actual,
            f"Órdenes de trabajo afectadas actualizadas: {detalle_cambio}."
        )
        _log(token, "VINCULAR_ORDENES_TRABAJO",
             f"Incidencia {id_incidencia}: OT afectadas {detalle_cambio}.", ip)

    return {
        "success": True,
        "message": "Órdenes de trabajo afectadas actualizadas exitosamente.",
        "agregadas": agregadas,
        "quitadas": quitadas,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Seguimiento
# ─────────────────────────────────────────────────────────────────────────────
def listar_seguimiento(id_incidencia, token):
    id_empresa = _empresa_id(token)
    data = incidencia_repos.listar_seguimiento(id_incidencia, id_empresa)
    if data is None:
        raise IncidenciaError("Incidencia no encontrada.", 404)
    return {"success": True, "data": data}


def registrar_seguimiento(id_incidencia, data, token, ip="unknown"):
    observacion = _texto(data.get("observacion"), "La observación", max_len=2000)

    id_empresa = _empresa_id(token)
    estado_actual, _ = incidencia_repos.obtener_estado_actual(id_incidencia, id_empresa)
    if estado_actual is None:
        raise IncidenciaError("Incidencia no encontrada.", 404)

    id_seguimiento = incidencia_repos.crear_seguimiento(
        id_incidencia, token.get("nro_usuario"), estado_actual, estado_actual, observacion
    )
    _log(token, "AGREGAR_SEGUIMIENTO", f"Comentario agregado a incidencia {id_incidencia}.", ip)
    return {
        "success": True,
        "id_seguimiento": id_seguimiento,
        "message": "Seguimiento registrado exitosamente.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# HU73 – Evidencias fotográficas
#
# No existía infraestructura previa de archivos en el backend (no hay
# UploadFile/multipart en uso, ni carpeta de uploads, ni integración con
# Cloudinary/S3). Se implementa la alternativa mínima coherente con la
# arquitectura actual: almacenamiento en disco local bajo backend/uploads/,
# con metadatos en obras.t_incidencia_evidencia y descarga solo a través de
# un endpoint autenticado que revalida el tenant (nunca se expone la carpeta
# como archivo estático público).
# ─────────────────────────────────────────────────────────────────────────────
def adjuntar_evidencia(id_incidencia, token, filename, content_type, contenido, ip="unknown"):
    if not contenido:
        raise IncidenciaError("El archivo está vacío.")
    if len(contenido) > MAX_EVIDENCIA_BYTES:
        raise IncidenciaError("El archivo supera el tamaño máximo permitido (10 MB).")

    tipo = (content_type or "").split(";")[0].strip().lower()
    if tipo not in ALLOWED_EVIDENCIA_MIME:
        raise IncidenciaError("Solo se permiten fotografías (JPEG, PNG, WEBP o GIF).")

    id_empresa = _empresa_id(token)
    estado_actual, _ = incidencia_repos.obtener_estado_actual(id_incidencia, id_empresa)
    if estado_actual is None:
        raise IncidenciaError("Incidencia no encontrada.", 404)
    if estado_actual == "CERRADA":
        raise IncidenciaError("No se pueden adjuntar evidencias a una incidencia cerrada.")

    ext = os.path.splitext(filename or "")[1][:10] or ".jpg"
    nombre_disco = f"{uuid.uuid4().hex}{ext}"
    carpeta = os.path.join(_upload_root(), str(id_incidencia))
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, nombre_disco), "wb") as f:
        f.write(contenido)

    ruta_relativa = os.path.join("uploads", "incidencias", str(id_incidencia), nombre_disco)
    id_evidencia = incidencia_repos.crear_evidencia(
        id_incidencia, token.get("nro_usuario"), ruta_relativa,
        os.path.basename(filename or nombre_disco), tipo, len(contenido)
    )
    _log(token, "ADJUNTAR_EVIDENCIA", f"Evidencia {id_evidencia} adjuntada a incidencia {id_incidencia}.", ip)
    return {"success": True, "id_evidencia": id_evidencia, "message": "Evidencia adjuntada exitosamente."}


def listar_evidencias(id_incidencia, token):
    id_empresa = _empresa_id(token)
    data = incidencia_repos.listar_evidencias(id_incidencia, id_empresa)
    if data is None:
        raise IncidenciaError("Incidencia no encontrada.", 404)
    return {"success": True, "data": data}


def obtener_ruta_evidencia(id_incidencia, id_evidencia, token):
    id_empresa = _empresa_id(token)
    ev = incidencia_repos.obtener_evidencia(id_incidencia, id_evidencia, id_empresa)
    if not ev:
        raise IncidenciaError("Evidencia no encontrada.", 404)

    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta_absoluta = os.path.join(backend_dir, ev["ruta_archivo"])
    if not os.path.isfile(ruta_absoluta):
        raise IncidenciaError("El archivo de evidencia no está disponible.", 404)
    return ruta_absoluta, ev["nombre_archivo"], ev["tipo_mime"]
