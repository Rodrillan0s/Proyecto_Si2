import asyncio
from datetime import datetime
import time
import anyio
from app.repos import notificaciones_repos, bitacora_repos
from app.classes.websocket_manager import manager
from app.utils.security import es_admin_sistema


class NotificacionesError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


ROLES_GESTION_ALERTAS = frozenset({
    "ADMINISTRADOR",
    "ADMINISTRADOR_EMPRESA",
    "JEFE DE OBRA",
})

ROLES_DESTINO_VALIDOS = (
    "ADMINISTRADOR_EMPRESA",
    "JEFE DE OBRA",
    "SUPERVISOR_OBRA",
    "CLIENTE",
    "ELECTRICO",
    "PLOMERO",
    "MAESTROALBAÑIL",
    "ALBAÑIL",
    "ADMINISTRADOR",
)

ROLES_DESTINO_DEFECTO = ["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"]

CATALOGO_EVENTOS_ALERTA = (
    {
        "tipo_evento": "AVANCE_OBRA",
        "nombre": "Avances de obra",
        "descripcion": "Se dispara al registrar avances físicos en unidades y obras.",
        "categoria": "Ejecución",
        "activo_por_defecto": True,
        "roles_por_defecto": ["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"],
    },
    {
        "tipo_evento": "INCIDENCIA",
        "nombre": "Incidencias de obra",
        "descripcion": "Se dispara al registrar, asignar, actualizar estado o adjuntar evidencias en incidencias.",
        "categoria": "Operación",
        "activo_por_defecto": True,
        "roles_por_defecto": ["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"],
    },
    {
        "tipo_evento": "ORDEN_TRABAJO",
        "nombre": "Órdenes de trabajo",
        "descripcion": "Se dispara al crear órdenes de trabajo, cambiar su estado o asignar responsables.",
        "categoria": "Operación",
        "activo_por_defecto": True,
        "roles_por_defecto": ["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"],
    },
    {
        "tipo_evento": "CONSULTA_TECNICA",
        "nombre": "Consultas técnicas (RFI)",
        "descripcion": "Se dispara al crear, asignar o responder consultas técnicas de obra.",
        "categoria": "Comunicación técnica",
        "activo_por_defecto": True,
        "roles_por_defecto": ["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"],
    },
    {
        "tipo_evento": "OBRA_ESTADO",
        "nombre": "Cambios de estado de obra",
        "descripcion": "Se dispara cuando un proyecto cambia de estado operativo (ej. en ejecución, pausado, finalizado).",
        "categoria": "Gestión de obra",
        "activo_por_defecto": True,
        "roles_por_defecto": ["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"],
    },
    {
        "tipo_evento": "ORDEN_CAMBIO",
        "nombre": "Órdenes de cambio y costos",
        "descripcion": "Se dispara al registrar, aprobar o rechazar órdenes de cambio en control de costos.",
        "categoria": "Costos",
        "activo_por_defecto": True,
        "roles_por_defecto": ["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"],
    },
    {
        "tipo_evento": "CRONOGRAMA",
        "nombre": "Cronogramas de obra",
        "descripcion": "Se dispara al crear o actualizar la planificación de un cronograma de obra.",
        "categoria": "Planificación",
        "activo_por_defecto": True,
        "roles_por_defecto": ["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"],
    },
    {
        "tipo_evento": "CRM_PROSPECTO",
        "nombre": "Prospectos comerciales",
        "descripcion": "Se dispara cuando se captura un nuevo contacto comercial desde el asistente.",
        "categoria": "Comercial",
        "activo_por_defecto": True,
        "roles_por_defecto": ["ADMINISTRADOR_EMPRESA", "JEFE DE OBRA"],
    },
)

_CATALOGO_POR_CODIGO = {item["tipo_evento"]: item for item in CATALOGO_EVENTOS_ALERTA}

_ALIASES_TIPO_EVENTO = {
    "ASIGNACION_RFI": "CONSULTA_TECNICA",
    "ALERTA_OBRA": "INCIDENCIA",
}

# Respaldo en memoria para idempotencia cuando la columna clave_evento aún no existe en BD.
_CLAVES_EMITIDAS_CACHE: dict[tuple[int, str], float] = {}
_CLAVES_TTL_SEGUNDOS = 300.0


def _normalizar_rol(rol: str) -> str:
    return str(rol or "").strip().upper()


def _normalizar_tipo_evento(tipo_referencia: str) -> str:
    codigo = str(tipo_referencia or "").strip().upper()
    return _ALIASES_TIPO_EVENTO.get(codigo, codigo)


def _registrar_clave_memoria(nro_usuario: int, clave_evento: str) -> bool:
    """
    Devuelve False si la pareja (nro_usuario, clave_evento) ya fue emitida
    recientemente en este proceso; True en caso contrario y la registra.
    """
    if not clave_evento:
        return True
    ahora = time.monotonic()
    # Limpieza perezosa cuando crece demasiado
    if len(_CLAVES_EMITIDAS_CACHE) > 2000:
        expiradas = [k for k, ts in _CLAVES_EMITIDAS_CACHE.items() if ahora - ts > _CLAVES_TTL_SEGUNDOS]
        for k in expiradas:
            _CLAVES_EMITIDAS_CACHE.pop(k, None)

    llave = (int(nro_usuario), str(clave_evento))
    prev = _CLAVES_EMITIDAS_CACHE.get(llave)
    if prev is not None and (ahora - prev) <= _CLAVES_TTL_SEGUNDOS:
        return False
    _CLAVES_EMITIDAS_CACHE[llave] = ahora
    return True


def _limpiar_cache_idempotencia():
    """Utilidad para pruebas unitarias."""
    _CLAVES_EMITIDAS_CACHE.clear()


def _despachar_ws_seguro(mensaje_push: dict, nro_usuario: int):
    """
    Envía un mensaje por WebSocket tanto desde contextos asíncronos (EventLoop activo)
    como desde hilos síncronos de FastAPI (worker thread de AnyIO).
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.send_personal_message(mensaje_push, int(nro_usuario)))
        return
    except RuntimeError:
        pass

    try:
        anyio.from_thread.run(manager.send_personal_message, mensaje_push, int(nro_usuario))
        return
    except Exception:
        pass

    try:
        asyncio.run(manager.send_personal_message(mensaje_push, int(nro_usuario)))
    except Exception:
        pass


def resolver_configuracion_evento(id_empresa: int, tipo_referencia: str, id_obra: int = None) -> dict:
    """
    Resuelve la regla efectiva para (id_empresa, id_obra, tipo_evento) con prioridad:
    1) Regla específica de obra
    2) Regla general de empresa
    3) Valor por defecto del catálogo
    """
    codigo = _normalizar_tipo_evento(tipo_referencia)
    base = _CATALOGO_POR_CODIGO.get(codigo)
    default_activo = base["activo_por_defecto"] if base else True
    default_roles = list(base["roles_por_defecto"]) if base else list(ROLES_DESTINO_DEFECTO)

    if not base or id_empresa is None:
        return {
            "tipo_evento": codigo,
            "activo": default_activo,
            "roles_destino": default_roles,
            "origen": "DEFAULT",
        }

    try:
        reglas = notificaciones_repos.obtener_configuraciones_alertas_db(
            id_empresa=int(id_empresa),
            id_obra=int(id_obra) if id_obra is not None else None,
        )
    except notificaciones_repos.NotificacionesSchemaMissing:
        return {
            "tipo_evento": codigo,
            "activo": default_activo,
            "roles_destino": default_roles,
            "origen": "DEFAULT",
        }

    regla_empresa = None
    regla_obra = None
    for r in reglas:
        if r.get("tipo_evento") != codigo:
            continue
        if id_obra is not None and r.get("id_obra") == int(id_obra):
            regla_obra = r
        elif r.get("id_obra") is None:
            regla_empresa = r

    elegida = regla_obra or regla_empresa
    if not elegida:
        return {
            "tipo_evento": codigo,
            "activo": default_activo,
            "roles_destino": default_roles,
            "origen": "DEFAULT",
        }

    return {
        "tipo_evento": codigo,
        "activo": bool(elegida["activo"]),
        "roles_destino": list(elegida.get("roles_destino") or []),
        "origen": "OBRA" if regla_obra else "EMPRESA",
    }


def _autorizar_contexto_alertas(token_data: dict, id_empresa_solicitada: int = None, id_obra: int = None) -> tuple[int, dict | None]:
    """
    Valida rol autorizado para HU141, empresa autorizada desde el JWT y pertenencia
    de la obra cuando se especifica.
    """
    if not token_data or not token_data.get("nro_usuario"):
        raise NotificacionesError("Sesión inválida o no autenticada.", 401)

    rol = _normalizar_rol(token_data.get("nombre_rol"))
    if rol not in ROLES_GESTION_ALERTAS:
        raise NotificacionesError(
            "Solo Administrador de Empresa, Jefe de Obra o Administrador pueden configurar alertas.",
            403,
        )

    es_global = es_admin_sistema(token_data)
    empresa_token = token_data.get("id_empresa")

    if es_global:
        id_empresa = id_empresa_solicitada if id_empresa_solicitada is not None else empresa_token
    else:
        if empresa_token is None:
            raise NotificacionesError("La sesión no tiene una empresa autorizada.", 400)
        if id_empresa_solicitada is not None and int(id_empresa_solicitada) != int(empresa_token):
            raise NotificacionesError("No tiene autorización para gestionar alertas de otra empresa.", 403)
        id_empresa = int(empresa_token)

    obra_info = None
    if id_obra is not None:
        obra_info = notificaciones_repos.validar_obra_empresa(int(id_obra))
        if not obra_info:
            raise NotificacionesError("La obra especificada no existe.", 404)
        if id_empresa is None:
            id_empresa = obra_info["id_empresa"]
        elif obra_info["id_empresa"] != int(id_empresa):
            raise NotificacionesError("La obra especificada no pertenece a su empresa.", 403)

    if id_empresa is None:
        raise NotificacionesError("Debe indicar una empresa válida para gestionar alertas.", 400)

    return int(id_empresa), obra_info


def obtener_configuracion_alertas(
    token_data: dict,
    id_obra: int = None,
    id_empresa_solicitada: int = None,
) -> dict:
    """
    HU141: Devuelve el catálogo de eventos con su configuración efectiva para la
    empresa (y sobrescritura de obra si se indicó id_obra).
    """
    id_empresa, obra_info = _autorizar_contexto_alertas(
        token_data=token_data,
        id_empresa_solicitada=id_empresa_solicitada,
        id_obra=id_obra,
    )

    migracion_pendiente = False
    reglas_db = []
    try:
        reglas_db = notificaciones_repos.obtener_configuraciones_alertas_db(
            id_empresa=id_empresa,
            id_obra=obra_info["id_obra"] if obra_info else None,
        )
    except notificaciones_repos.NotificacionesSchemaMissing:
        migracion_pendiente = True

    por_empresa = {}
    por_obra = {}
    for r in reglas_db:
        if r.get("id_obra") is None:
            por_empresa[r["tipo_evento"]] = r
        else:
            por_obra[r["tipo_evento"]] = r

    eventos = []
    for item in CATALOGO_EVENTOS_ALERTA:
        codigo = item["tipo_evento"]
        r_obra = por_obra.get(codigo) if obra_info else None
        r_emp = por_empresa.get(codigo)

        if r_obra:
            activo = bool(r_obra["activo"])
            roles_dest = list(r_obra["roles_destino"])
            origen = "OBRA"
            actualizado_en = r_obra.get("actualizado_en")
        elif r_emp:
            activo = bool(r_emp["activo"])
            roles_dest = list(r_emp["roles_destino"])
            origen = "EMPRESA"
            actualizado_en = r_emp.get("actualizado_en")
        else:
            activo = bool(item["activo_por_defecto"])
            roles_dest = list(item["roles_por_defecto"])
            origen = "DEFAULT"
            actualizado_en = None

        eventos.append({
            "tipo_evento": codigo,
            "nombre": item["nombre"],
            "descripcion": item["descripcion"],
            "categoria": item["categoria"],
            "activo": activo,
            "roles_destino": roles_dest,
            "origen": origen,
            "heredado_de_empresa": bool(obra_info and origen != "OBRA"),
            "actualizado_en": actualizado_en,
        })

    return {
        "success": True,
        "id_empresa": id_empresa,
        "id_obra": obra_info["id_obra"] if obra_info else None,
        "nombre_obra": obra_info["nombre"] if obra_info else None,
        "migracion_pendiente": migracion_pendiente,
        "roles_disponibles": list(ROLES_DESTINO_VALIDOS),
        "data": eventos,
    }


def actualizar_configuracion_alertas(
    token_data: dict,
    data: dict,
    client_ip: str = "unknown",
) -> dict:
    """
    HU141: Persiste la configuración de alertas por tipo de evento para una
    empresa o una obra específica, validando roles y pertenencia de tenant.
    """
    payload = data or {}
    id_obra = payload.get("id_obra")
    id_empresa_solicitada = payload.get("id_empresa")
    restablecer_obra = bool(payload.get("restablecer_obra", False))

    id_empresa, obra_info = _autorizar_contexto_alertas(
        token_data=token_data,
        id_empresa_solicitada=id_empresa_solicitada,
        id_obra=id_obra,
    )

    if restablecer_obra:
        if not obra_info:
            raise NotificacionesError("Debe indicar una obra válida para restablecer su configuración.", 400)
        try:
            eliminadas = notificaciones_repos.eliminar_configuraciones_obra_db(
                id_empresa=id_empresa,
                id_obra=obra_info["id_obra"],
            )
        except notificaciones_repos.NotificacionesSchemaMissing as exc:
            raise NotificacionesError(str(exc), 503) from exc

        try:
            bitacora_repos.registrar_bitacora(
                id_usuario=token_data.get("nro_usuario"),
                modulo="NOTIFICACIONES",
                accion="RESTABLECER_ALERTAS_OBRA",
                descripcion=f"Alertas de obra #{obra_info['id_obra']} restablecidas a valores de empresa #{id_empresa} ({eliminadas} reglas).",
                ip=client_ip,
                estado="EXITOSO",
            )
        except Exception:
            pass

        respuesta = obtener_configuracion_alertas(
            token_data=token_data,
            id_obra=obra_info["id_obra"],
            id_empresa_solicitada=id_empresa,
        )
        respuesta["message"] = "Configuración de la obra restablecida a los valores generales de la empresa."
        return respuesta

    items = payload.get("configuraciones")
    if not isinstance(items, list) or not items:
        raise NotificacionesError("Debe enviar al menos una configuración de evento válida.", 400)

    roles_validos_set = set(ROLES_DESTINO_VALIDOS)
    validados = []
    vistos = set()

    for raw in items:
        if not isinstance(raw, dict):
            raise NotificacionesError("Formato inválido en la lista de configuraciones.", 400)
        tipo_evento = _normalizar_tipo_evento(raw.get("tipo_evento"))
        if tipo_evento not in _CATALOGO_POR_CODIGO:
            raise NotificacionesError(f"Tipo de evento no soportado: {raw.get('tipo_evento')}", 400)
        if tipo_evento in vistos:
            raise NotificacionesError(f"Tipo de evento duplicado en la solicitud: {tipo_evento}", 400)
        vistos.add(tipo_evento)

        if "activo" not in raw or not isinstance(raw.get("activo"), bool):
            raise NotificacionesError(f"El campo 'activo' debe ser booleano para {tipo_evento}.", 400)

        roles_raw = raw.get("roles_destino")
        if roles_raw is None:
            roles_limpios = list(_CATALOGO_POR_CODIGO[tipo_evento]["roles_por_defecto"])
        else:
            if not isinstance(roles_raw, list):
                raise NotificacionesError(f"'roles_destino' debe ser una lista para {tipo_evento}.", 400)
            roles_limpios = []
            for r in roles_raw:
                rol_norm = _normalizar_rol(r)
                if rol_norm not in roles_validos_set:
                    raise NotificacionesError(f"Rol destinatario inválido: {r}", 400)
                if rol_norm not in roles_limpios:
                    roles_limpios.append(rol_norm)

        validados.append({
            "tipo_evento": tipo_evento,
            "activo": raw["activo"],
            "roles_destino": roles_limpios,
        })

    try:
        notificaciones_repos.guardar_configuraciones_alertas_db(
            id_empresa=id_empresa,
            configuraciones=validados,
            id_obra=obra_info["id_obra"] if obra_info else None,
            actualizado_por=token_data.get("nro_usuario"),
        )
    except notificaciones_repos.NotificacionesSchemaMissing as exc:
        raise NotificacionesError(str(exc), 503) from exc

    ambito = f"obra #{obra_info['id_obra']}" if obra_info else f"empresa #{id_empresa}"
    try:
        bitacora_repos.registrar_bitacora(
            id_usuario=token_data.get("nro_usuario"),
            modulo="NOTIFICACIONES",
            accion="CONFIGURAR_ALERTAS_EVENTO",
            descripcion=f"Actualizadas {len(validados)} reglas de alertas para {ambito}.",
            ip=client_ip,
            estado="EXITOSO",
        )
    except Exception:
        pass

    respuesta = obtener_configuracion_alertas(
        token_data=token_data,
        id_obra=obra_info["id_obra"] if obra_info else None,
        id_empresa_solicitada=id_empresa,
    )
    respuesta["message"] = "Configuración de alertas actualizada exitosamente."
    return respuesta


def emitir_notificacion_push_empresa(
    titulo: str,
    cuerpo: str,
    tipo_referencia: str = "OBRA",
    id_empresa: int = None,
    nro_referencia: int = None,
    roles_destino: list = None,
    usuarios_especificos: list = None,
    data_extra: dict = None,
    id_obra: int = None,
    clave_evento: str = None,
    omitir_configuracion: bool = False,
):
    """
    Evalúa preferencias de alertas (HU141), filtra destinatarios autorizados de la
    empresa, persiste la notificación con control de duplicados y la transmite por
    WebSocket. Nunca propaga excepciones hacia las transacciones principales.
    """
    try:
        roles_efectivos = roles_destino

        if not omitir_configuracion and id_empresa is not None:
            pref = resolver_configuracion_evento(
                id_empresa=int(id_empresa),
                tipo_referencia=tipo_referencia,
                id_obra=id_obra,
            )
            if not pref["activo"]:
                return 0
            # Si el llamador no fijó una lista explícita de roles (None), se usan los configurados.
            if roles_destino is None:
                roles_efectivos = pref["roles_destino"]

        destinatarios_ids = set()
        if usuarios_especificos:
            autorizados = notificaciones_repos.filtrar_usuarios_autorizados_empresa(
                usuarios_ids=usuarios_especificos,
                id_empresa=id_empresa,
            )
            destinatarios_ids.update(autorizados)

        if roles_efectivos:
            usuarios_bd = notificaciones_repos.obtener_usuarios_por_roles(
                roles=roles_efectivos,
                id_empresa=id_empresa,
            )
            for u in usuarios_bd:
                if u.get("nro_usuario"):
                    destinatarios_ids.add(int(u["nro_usuario"]))
        elif roles_efectivos is None and not destinatarios_ids:
            usuarios_bd = notificaciones_repos.obtener_usuarios_por_roles(
                roles=list(ROLES_DESTINO_DEFECTO),
                id_empresa=id_empresa,
            )
            for u in usuarios_bd:
                if u.get("nro_usuario"):
                    destinatarios_ids.add(int(u["nro_usuario"]))

        if not destinatarios_ids:
            return 0

        ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        enviadas = 0
        for nro_usu in sorted(destinatarios_ids):
            if clave_evento and not _registrar_clave_memoria(nro_usu, clave_evento):
                continue

            meta_db = notificaciones_repos.guardar_notificacion_db(
                titulo=titulo,
                cuerpo=cuerpo,
                tipo_referencia=tipo_referencia,
                nro_usuario=nro_usu,
                nro_emergencia=nro_referencia,
                id_empresa=id_empresa,
                id_obra=id_obra,
                clave_evento=clave_evento,
            )
            if meta_db.get("duplicada"):
                continue

            id_notif = meta_db.get("id_notificacion")
            fecha_creacion = meta_db.get("fecha_creacion") or ahora_str
            payload_extra = dict(data_extra) if isinstance(data_extra, dict) else {"nro_referencia": nro_referencia}
            if id_obra is not None and "id_obra" not in payload_extra:
                payload_extra["id_obra"] = id_obra

            mensaje_push = {
                "id_notificacion": id_notif,
                "tipo_alerta": tipo_referencia,
                "tipo_referencia": tipo_referencia,
                "tipo": tipo_referencia,
                "titulo": titulo,
                "cuerpo": cuerpo,
                "mensaje": cuerpo,
                "leido": False,
                "fecha_creacion": fecha_creacion,
                "created_at": fecha_creacion,
                "nro_emergencia": nro_referencia,
                "id_obra": id_obra,
                "data": payload_extra,
            }
            _despachar_ws_seguro(mensaje_push, nro_usu)
            enviadas += 1
        return enviadas
    except Exception as exc:
        print(f"[WARN] No se pudo emitir notificación push: {exc}")
        return 0


# ALERTA A TODOS LOS TALLERES (COMPATIBILIDAD)
async def enviar_push_nueva_emergencia(nro_emergencia: int, tipo_emergencia: str):
    roles_destino = ['ADMINISTRADOR', 'ADMINISTRADOR_EMPRESA', 'JEFE DE OBRA']
    usuarios_destino = notificaciones_repos.obtener_usuarios_por_roles(roles_destino)

    titulo = "¡Nueva Alerta Reportada!"
    cuerpo = f"Se requiere atención en obra: {tipo_emergencia}"
    tipo_ref = "ALERTA_OBRA"

    for u in usuarios_destino:
        nro_usu = u['nro_usuario']
        meta_db = notificaciones_repos.guardar_notificacion_db(titulo, cuerpo, tipo_ref, nro_usu, nro_emergencia)
        mensaje_push = {
            "id_notificacion": meta_db.get("id_notificacion"),
            "tipo_alerta": tipo_ref,
            "tipo_referencia": tipo_ref,
            "tipo": tipo_ref,
            "titulo": titulo,
            "cuerpo": cuerpo,
            "mensaje": cuerpo,
            "leido": False,
            "fecha_creacion": meta_db.get("fecha_creacion"),
            "created_at": meta_db.get("fecha_creacion"),
            "data": {"nro_emergencia": nro_emergencia},
        }
        await manager.send_personal_message(mensaje_push, nro_usu)


async def enviar_push_nueva_oferta(nro_emergencia: int, id_oferta: int, nro_usuario_cliente: int, precio: float):
    titulo = "¡Nueva Propuesta Recibida!"
    cuerpo = f"Se registró una cotización por Bs. {precio}."
    tipo_ref = "NUEVA_OFERTA"

    meta_db = notificaciones_repos.guardar_notificacion_db(titulo, cuerpo, tipo_ref, nro_usuario_cliente, nro_emergencia)
    mensaje_push = {
        "id_notificacion": meta_db.get("id_notificacion"),
        "tipo_alerta": tipo_ref,
        "tipo_referencia": tipo_ref,
        "tipo": tipo_ref,
        "titulo": titulo,
        "cuerpo": cuerpo,
        "mensaje": cuerpo,
        "leido": False,
        "fecha_creacion": meta_db.get("fecha_creacion"),
        "created_at": meta_db.get("fecha_creacion"),
        "data": {"nro_emergencia": nro_emergencia, "id_oferta": id_oferta},
    }
    await manager.send_personal_message(mensaje_push, nro_usuario_cliente)


async def enviar_push_respuesta_oferta(nro_emergencia: int, id_oferta: int, estado_respuesta: str, nro_taller: int):
    usuarios_taller = notificaciones_repos.obtener_usuarios_por_taller(nro_taller)

    if estado_respuesta == 'ACEPTADA':
        titulo = "¡Cotización Aceptada!"
        cuerpo = "El cliente aprobó la propuesta."
    else:
        titulo = "Cotización Rechazada"
        cuerpo = "El cliente ha declinado la propuesta."

    tipo_ref = "RESPUESTA_OFERTA"

    for u in usuarios_taller:
        nro_usu = u['nro_usuario']
        meta_db = notificaciones_repos.guardar_notificacion_db(titulo, cuerpo, tipo_ref, nro_usu, nro_emergencia)
        mensaje_push = {
            "id_notificacion": meta_db.get("id_notificacion"),
            "tipo_alerta": tipo_ref,
            "tipo_referencia": tipo_ref,
            "tipo": tipo_ref,
            "titulo": titulo,
            "cuerpo": cuerpo,
            "mensaje": cuerpo,
            "leido": False,
            "fecha_creacion": meta_db.get("fecha_creacion"),
            "created_at": meta_db.get("fecha_creacion"),
            "data": {"nro_emergencia": nro_emergencia, "id_oferta": id_oferta},
        }
        await manager.send_personal_message(mensaje_push, nro_usu)


def listar_mis_notificaciones(
    nro_usuario: int,
    solo_no_leidas: bool = False,
    tipo: str = None,
):
    if not nro_usuario:
        raise ValueError("No se pudo identificar al usuario de la sesión.")

    alertas = notificaciones_repos.obtener_notificaciones_por_usuario_db(
        int(nro_usuario),
        solo_no_leidas=bool(solo_no_leidas),
        tipo=tipo,
    )
    no_leidas = sum(1 for a in alertas if not a.get("leido"))
    return {
        "success": True,
        "message": "Bandeja de notificaciones recuperada exitosamente.",
        "no_leidas": no_leidas,
        "data": alertas,
    }


def cambiar_estado_leido(nro_usuario: int, id_notificacion: int = None, marcar_todo: bool = False):
    if not nro_usuario:
        raise ValueError("Operación no autorizada. Sesión inválida.")

    if marcar_todo:
        total_actualizadas = notificaciones_repos.marcar_todas_las_notificaciones_leidas_db(int(nro_usuario))
        return {
            "success": True,
            "message": f"Todas las notificaciones fueron marcadas como leídas. ({total_actualizadas} alertas afectadas)",
            "actualizadas": total_actualizadas,
        }

    if id_notificacion:
        exito = notificaciones_repos.marcar_notificacion_leida_db(int(id_notificacion), int(nro_usuario))
        if not exito:
            raise ValueError("No se encontró la notificación seleccionada o no te pertenece.")
        return {
            "success": True,
            "message": "Notificación marcada como leída exitosamente.",
        }

    raise ValueError("Parámetros insuficientes para procesar la lectura de alertas.")
