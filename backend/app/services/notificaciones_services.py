import asyncio
from datetime import datetime
import anyio
from app.repos import notificaciones_repos
from app.classes.websocket_manager import manager


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


def emitir_notificacion_push_empresa(
    titulo: str,
    cuerpo: str,
    tipo_referencia: str = "OBRA",
    id_empresa: int = None,
    nro_referencia: int = None,
    roles_destino: list = None,
    usuarios_especificos: list = None,
    data_extra: dict = None,
):
    """
    Guarda la notificación en BD y la transmite en tiempo real por WebSocket
    a los destinatarios activos de la empresa correspondiente.
    Nunca propaga excepciones hacia las transacciones principales de negocio.
    """
    try:
        destinatarios_ids = set()
        if usuarios_especificos:
            for uid in usuarios_especificos:
                try:
                    if uid is not None and int(uid) > 0:
                        destinatarios_ids.add(int(uid))
                except (TypeError, ValueError):
                    continue

        if roles_destino or not destinatarios_ids:
            roles = roles_destino or [
                "ADMINISTRADOR",
                "ADMINISTRADOR_EMPRESA",
                "JEFE DE OBRA",
                "SUPERVISOR_OBRA",
            ]
            usuarios_bd = notificaciones_repos.obtener_usuarios_por_roles(
                roles=roles,
                id_empresa=id_empresa,
            )
            for u in usuarios_bd:
                if u.get("nro_usuario"):
                    destinatarios_ids.add(int(u["nro_usuario"]))

        ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        enviadas = 0
        for nro_usu in destinatarios_ids:
            meta_db = notificaciones_repos.guardar_notificacion_db(
                titulo=titulo,
                cuerpo=cuerpo,
                tipo_referencia=tipo_referencia,
                nro_usuario=nro_usu,
                nro_emergencia=nro_referencia,
            )
            id_notif = meta_db.get("id_notificacion")
            fecha_creacion = meta_db.get("fecha_creacion") or ahora_str
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
                "data": data_extra or {"nro_referencia": nro_referencia},
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


def listar_mis_notificaciones(nro_usuario: int):
    if not nro_usuario:
        raise ValueError("No se pudo identificar al usuario de la sesión.")

    alertas = notificaciones_repos.obtener_notificaciones_por_usuario_db(int(nro_usuario))
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
