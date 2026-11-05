"""
Servicios CU23 – Gestionar consultas técnicas de obra (RFI)
Lógica de negocio, reglas de transición de estados y aislamiento multitenant.
"""
from app.repos import consulta_tecnica_repos as repo


class ConsultaTecnicaError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _empresa_id(token) -> int | None:
    """Devuelve el ID de la empresa del token, o None si es Super Administrador global."""
    if token.get("nombre_rol") == "ADMINISTRADOR":
        return None
    emp = token.get("id_empresa")
    if not emp:
        raise ConsultaTecnicaError("Contexto de empresa no identificado en el token de autenticación.", 403)
    return int(emp)


def _usuario_id(token) -> int:
    uid = token.get("nro_usuario") or token.get("id_usuario")
    if not uid:
        raise ConsultaTecnicaError("Identificador de usuario no válido en el token.", 401)
    return int(uid)


def autorizar_acceso_obra(id_obra: int, token) -> dict:
    """Valida que la obra exista y pertenezca al tenant del usuario."""
    id_emp = _empresa_id(token)
    obra = repo.obtener_obra(id_obra, id_emp)
    if not obra:
        raise ConsultaTecnicaError(f"La obra con ID {id_obra} no existe o no pertenece a su empresa.", 404)
    return obra


def listar_consultas(id_obra: int = None, token=None, estado: str = None, id_responsable: int = None,
                     busqueda: str = None, page: int = 1, limit: int = 20) -> dict:
    if id_obra is not None:
        autorizar_acceso_obra(id_obra, token)
    id_emp = _empresa_id(token)
    return repo.listar_consultas(
        id_obra=id_obra,
        id_empresa=id_emp,
        estado=estado,
        id_responsable=id_responsable,
        busqueda=busqueda,
        page=page,
        limit=limit
    )


def registrar_consulta(id_obra: int, data: dict, token) -> dict:
    obra = autorizar_acceso_obra(id_obra, token)
    id_emp = obra["id_empresa"]
    creado_por = _usuario_id(token)

    asunto = str(data.get("asunto") or "").strip()
    if len(asunto) < 3 or len(asunto) > 200:
        raise ConsultaTecnicaError("El asunto de la consulta técnica debe tener entre 3 y 200 caracteres.", 422)

    descripcion = str(data.get("descripcion") or "").strip()
    if len(descripcion) < 5:
        raise ConsultaTecnicaError("La descripción técnica debe tener al menos 5 caracteres detallando la consulta.", 422)

    referencia_tecnica = str(data.get("referencia_tecnica") or "").strip() or None

    asignado_a = data.get("asignado_a")
    if asignado_a is not None:
        try:
            asignado_a = int(asignado_a)
        except (ValueError, TypeError):
            raise ConsultaTecnicaError("El identificador del responsable asignado debe ser un número entero.", 422)

    codigo = repo.generar_siguiente_codigo(id_obra, id_emp)

    id_ct = repo.crear_consulta(
        id_empresa=id_emp,
        id_obra=id_obra,
        codigo=codigo,
        asunto=asunto,
        descripcion=descripcion,
        referencia_tecnica=referencia_tecnica,
        creado_por=creado_por,
        asignado_a=asignado_a
    )
    if not id_ct:
        raise ConsultaTecnicaError("No se pudo registrar la consulta técnica en base de datos.", 500)

    return {
        "success": True,
        "id_consulta_tecnica": id_ct,
        "codigo": codigo,
        "message": "Consulta técnica registrada correctamente."
    }


def obtener_detalle(id_consulta_tecnica: int, token) -> dict:
    id_emp = _empresa_id(token)
    consulta = repo.obtener_por_id(id_consulta_tecnica, id_emp)
    if not consulta:
        raise ConsultaTecnicaError(f"Consulta técnica #{id_consulta_tecnica} no encontrada o sin acceso.", 404)

    respuestas = repo.obtener_respuestas(id_consulta_tecnica)
    historial = repo.obtener_historial(id_consulta_tecnica)

    consulta["respuestas"] = respuestas
    consulta["historial"] = historial
    return consulta


def asignar_responsable(id_consulta_tecnica: int, data: dict, token) -> dict:
    id_emp = _empresa_id(token)
    consulta = repo.obtener_por_id(id_consulta_tecnica, id_emp)
    if not consulta:
        raise ConsultaTecnicaError(f"Consulta técnica #{id_consulta_tecnica} no encontrada o sin acceso.", 404)

    if consulta["estado"] == "CERRADA":
        raise ConsultaTecnicaError("No es posible asignar responsable a una consulta técnica que ya está CERRADA.", 400)

    asignado_a = data.get("asignado_a")
    if not asignado_a:
        raise ConsultaTecnicaError("Debe especificar el usuario responsable para la asignación.", 422)
    try:
        asignado_a = int(asignado_a)
    except (ValueError, TypeError):
        raise ConsultaTecnicaError("El identificador del responsable debe ser numérico.", 422)

    actor_id = _usuario_id(token)
    ok = repo.asignar_responsable(id_consulta_tecnica, asignado_a, actor_id)
    if not ok:
        raise ConsultaTecnicaError("Error al procesar la asignación en base de datos.", 500)

    return {
        "success": True,
        "message": "Responsable asignado exitosamente."
    }


def registrar_respuesta(id_consulta_tecnica: int, data: dict, token) -> dict:
    id_emp = _empresa_id(token)
    consulta = repo.obtener_por_id(id_consulta_tecnica, id_emp)
    if not consulta:
        raise ConsultaTecnicaError(f"Consulta técnica #{id_consulta_tecnica} no encontrada o sin acceso.", 404)

    if consulta["estado"] == "CERRADA":
        raise ConsultaTecnicaError("No se puede registrar una respuesta en una consulta técnica CERRADA. Debe reabrirse primero.", 400)

    contenido = str(data.get("contenido") or "").strip()
    if len(contenido) < 3:
        raise ConsultaTecnicaError("El contenido de la respuesta técnica debe tener al menos 3 caracteres.", 422)

    autor_id = _usuario_id(token)
    id_resp = repo.registrar_respuesta(id_consulta_tecnica, autor_id, contenido)
    if not id_resp:
        raise ConsultaTecnicaError("No se pudo registrar la respuesta técnica.", 500)

    return {
        "success": True,
        "id_consulta_tecnica_respuesta": id_resp,
        "message": "Respuesta técnica registrada exitosamente."
    }


def cambiar_estado(id_consulta_tecnica: int, data: dict, token) -> dict:
    id_emp = _empresa_id(token)
    consulta = repo.obtener_por_id(id_consulta_tecnica, id_emp)
    if not consulta:
        raise ConsultaTecnicaError(f"Consulta técnica #{id_consulta_tecnica} no encontrada o sin acceso.", 404)

    nuevo_estado = str(data.get("estado") or "").strip().upper()
    motivo = str(data.get("motivo") or "").strip()
    actor_id = _usuario_id(token)

    if nuevo_estado == "CERRADA":
        if consulta["estado"] == "CERRADA":
            raise ConsultaTecnicaError("La consulta técnica ya se encuentra cerrada.", 400)
        if not motivo:
            motivo = "Cierre formal de la consulta técnica tras revisión."
        ok = repo.cerrar_consulta(id_consulta_tecnica, actor_id, motivo)
        if not ok:
            raise ConsultaTecnicaError("No se pudo cerrar la consulta técnica.", 500)
        return {"success": True, "message": "Consulta técnica cerrada correctamente."}

    elif nuevo_estado == "ABIERTA" and consulta["estado"] == "CERRADA":
        if not motivo:
            raise ConsultaTecnicaError("Debe indicar el motivo de reapertura de la consulta técnica.", 422)
        ok = repo.reabrir_consulta(id_consulta_tecnica, actor_id, motivo)
        if not ok:
            raise ConsultaTecnicaError("No se pudo reabrir la consulta técnica.", 500)
        return {"success": True, "message": "Consulta técnica reabierta correctamente."}

    else:
        raise ConsultaTecnicaError(f"Transición de estado no permitida: {consulta['estado']} -> {nuevo_estado}.", 400)


def obtener_usuarios_asignables(id_obra: int, token) -> list:
    obra = autorizar_acceso_obra(id_obra, token)
    id_emp = obra["id_empresa"]
    return repo.obtener_usuarios_asignables(id_obra, id_emp)
