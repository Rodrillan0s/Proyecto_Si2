"""
Servicio CU18 – Avances de Obra
Lógica de negocio: validaciones, mapeo de roles y orquestación
de los repositorios de avances.
"""
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from app.repos import avance_repos, bitacora_repos, crm_repos
from app.services import sync_offline_services


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _id_empresa(token_data: dict):
    """Devuelve None si es ADMINISTRADOR global, el id de empresa del token si no."""
    return None if token_data.get("nombre_rol") == "ADMINISTRADOR" else token_data.get("id_empresa")


def _validar_porcentaje(valor) -> float:
    """Valida y convierte el porcentaje de avance."""
    if valor is None:
        raise ValueError("El porcentaje de avance es obligatorio.")
    try:
        pct = Decimal(str(valor))
        if not pct.is_finite():
            raise InvalidOperation()
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("El porcentaje de avance debe ser un número válido.")
    pct_float = float(pct)
    if pct_float < 0 or pct_float > 100:
        raise ValueError("El porcentaje de avance debe estar entre 0 y 100.")
    return pct_float


def _validar_fecha(fecha_str) -> date:
    """Valida y convierte la fecha de registro."""
    if not fecha_str:
        return date.today()
    if isinstance(fecha_str, date):
        return fecha_str
    try:
        return datetime.strptime(str(fecha_str), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Formato de fecha incorrecto. Debe ser YYYY-MM-DD.")


# ---------------------------------------------------------------------------
# Operaciones principales
# ---------------------------------------------------------------------------

def registrar_avance(
    id_obra: int,
    data: dict,
    token_data: dict,
    client_ip: str = "unknown",
    idempotency_key: str | None = None,
) -> dict:
    """
    Registra un nuevo avance de obra.
    Roles autorizados (definidos por permiso 'Registrar_avances'):
      - ADMINISTRADOR (global)
      - ADMINISTRADOR_EMPRESA (Supervisor)
      - JEFE DE OBRA (Responsable del Proyecto)
    """
    id_empresa = _id_empresa(token_data)
    id_usuario = token_data.get("nro_usuario")
    clave_idemp = sync_offline_services.extraer_clave_idempotencia(data, idempotency_key)
    fecha_ocurrencia_local = sync_offline_services.parsear_fecha_ocurrencia_local(
        data.get("fecha_ocurrencia_local")
    )

    # Validar unidad
    id_unidad = data.get("id_unidad")
    if not id_unidad:
        raise ValueError("La unidad de construcción es obligatoria.")
    try:
        id_unidad = int(id_unidad)
        if id_unidad <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError("El identificador de la unidad de construcción es inválido.")

    # Validar porcentaje
    porcentaje = _validar_porcentaje(data.get("porcentaje_avance"))

    # Validar fecha (si llega fecha_ocurrencia_local y no fecha_registro, derivar fecha de ocurrencia)
    fecha_raw = data.get("fecha_registro")
    if not fecha_raw and fecha_ocurrencia_local is not None:
        fecha_raw = fecha_ocurrencia_local.date()
    fecha = _validar_fecha(fecha_raw)

    # Observación opcional
    observacion = str(data.get("observacion") or "").strip()

    def _ejecutar():
        res = avance_repos.registrar_avance_fn(
            id_obra=id_obra,
            id_unidad=id_unidad,
            id_empresa=id_empresa,
            porcentaje=porcentaje,
            fecha_registro=fecha,
            observacion=observacion,
            id_usuario=id_usuario,
        )

        if not res.get("success"):
            raise ValueError(res.get("error", "No se pudo registrar el avance."))

        bitacora_repos.registrar_bitacora(
            id_usuario=id_usuario,
            modulo="AVANCES_OBRA",
            accion="REGISTRAR_AVANCE",
            descripcion=(
                f"Avance de {porcentaje}% registrado en unidad {id_unidad} "
                f"del proyecto {id_obra}. Observacion: {observacion or 'Ninguna'}"
            ),
            ip=client_ip,
            estado="EXITOSO",
        )

        try:
            from app.services import notificaciones_services
            notificaciones_services.emitir_notificacion_push_empresa(
                titulo=f"Avance registrado ({porcentaje}%)",
                cuerpo=f"Se registró un avance del {porcentaje}% en la unidad #{id_unidad} de la obra #{id_obra}.",
                tipo_referencia="AVANCE_OBRA",
                id_empresa=token_data.get("id_empresa"),
                id_obra=id_obra,
                nro_referencia=id_obra,
                clave_evento=f"AVANCE_OBRA:{id_obra}:{id_unidad}:{res.get('id_avance') or porcentaje}",
            )
        except Exception:
            pass

        return res

    return sync_offline_services.ejecutar_con_idempotencia(
        id_empresa=token_data.get("id_empresa"),
        id_usuario=id_usuario,
        tipo_operacion="AVANCE_OBRA",
        id_obra=id_obra,
        client_operation_id=clave_idemp,
        fecha_ocurrencia_local=fecha_ocurrencia_local,
        fn_ejecutar=_ejecutar,
        fn_extraer_id=lambda r: r.get("id_avance") if isinstance(r, dict) else None,
        tabla_recurso="t_avance_obra",
        columna_pk="id_avance",
    )


def listar_avances(id_obra: int, token_data: dict, estado: str = None) -> dict:
    """
    Lista la bitácora de órdenes de trabajo de la obra, con filtro opcional por estado (FINALIZADO / PENDIENTE).
    Requiere permiso 'Visualizar_avances'.
    """
    id_empresa = _id_empresa(token_data)
    res = avance_repos.listar_avances_fn(id_obra=id_obra, id_empresa=id_empresa, estado=estado)
    if not res.get("success"):
        raise ValueError(res.get("error", "Error al obtener la bitácora de avances de obra."))
    return res


def consultar_avance_fisico_unidad_cliente(
    id_obra: int,
    id_unidad: int,
    token_data: dict,
) -> dict:
    if token_data.get("nombre_rol") != "CLIENTE":
        raise PermissionError("No tiene permisos para consultar el avance de esta unidad.")

    try:
        id_usuario = int(token_data.get("nro_usuario"))
        id_empresa = int(token_data.get("id_empresa"))
    except (TypeError, ValueError):
        raise PermissionError("No se pudo validar el cliente autenticado.")

    id_cliente = crm_repos.obtener_id_cliente_por_usuario_empresa(id_usuario, id_empresa)
    if id_cliente is None:
        raise PermissionError("No se pudo validar el cliente autenticado.")

    unidades = crm_repos.listar_unidades_cliente_cu30(id_cliente, id_empresa)
    unidad_autorizada = any(
        unidad.get("id_unidad") == id_unidad and unidad.get("id_obra") == id_obra
        for unidad in unidades
    )
    if not unidad_autorizada:
        raise PermissionError("La unidad no está asociada al cliente autenticado.")

    res = avance_repos.listar_avance_fisico_unidad_cliente(
        id_cliente=id_cliente,
        id_unidad=id_unidad,
        id_obra=id_obra,
        id_empresa=id_empresa,
    )
    if not res.get("success"):
        raise ValueError(res.get("error", "Error al obtener el avance físico de la unidad."))
    return res


def resumen_avances(id_obra: int, token_data: dict) -> dict:
    """
    Devuelve el resumen de avance global del proyecto calculado como:
      (Órdenes FINALIZADAS / Total de Órdenes) * 100%
    y el desglose por cuadrillas.
    Requiere permiso 'Visualizar_avances'.
    """
    id_empresa = _id_empresa(token_data)
    res = avance_repos.resumen_avances_fn(id_obra=id_obra, id_empresa=id_empresa)
    if not res.get("success"):
        raise ValueError(res.get("error", "Error al calcular el resumen de avances."))
    return res


def eliminar_avance(id_obra: int, id_avance: int, token_data: dict, client_ip: str = "unknown") -> dict:
    """
    Elimina un registro de avance.
    Requiere permiso 'Registrar_avances' (misma capa de permisos que el registro).
    """
    id_empresa = _id_empresa(token_data)
    res = avance_repos.eliminar_avance_fn(id_avance=id_avance, id_obra=id_obra, id_empresa=id_empresa)
    if not res.get("success"):
        raise ValueError(res.get("error", "No se pudo eliminar el avance."))

    bitacora_repos.registrar_bitacora(
        id_usuario=token_data.get("nro_usuario"),
        modulo="AVANCES_OBRA",
        accion="ELIMINAR_AVANCE",
        descripcion=f"Avance {id_avance} eliminado del proyecto {id_obra}.",
        ip=client_ip,
        estado="EXITOSO",
    )
    return res
