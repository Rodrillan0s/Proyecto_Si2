"""
Servicio CU41 – Soporte transversal de idempotencia y marcas temporales offline
para los flujos existentes de CU18 (avances) y CU19 (incidencias).
"""
from datetime import datetime, timezone

from app.repos import sync_offline_repos


class SyncConflictError(ValueError):
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


def extraer_clave_idempotencia(data: dict | None, header_key: str | None = None) -> str | None:
    raw = header_key
    if (raw is None or not str(raw).strip()) and isinstance(data, dict):
        raw = data.get("client_operation_id")
    if raw is None:
        return None
    clave = str(raw).strip()
    if not clave:
        return None
    if len(clave) > 100:
        raise ValueError("La clave de idempotencia no puede superar 100 caracteres.")
    return clave


def parsear_fecha_ocurrencia_local(valor) -> datetime | None:
    if valor is None or str(valor).strip() == "":
        return None
    if isinstance(valor, datetime):
        return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)
    texto = str(valor).strip()
    if texto.endswith("Z"):
        texto = texto[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(texto)
    except ValueError:
        raise ValueError("Formato inválido para fecha_ocurrencia_local (use ISO-8601).")
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def ejecutar_con_idempotencia(
    *,
    id_empresa: int | None,
    id_usuario: int | None,
    tipo_operacion: str,
    id_obra: int,
    client_operation_id: str | None,
    fecha_ocurrencia_local: datetime | None,
    fn_ejecutar,
    fn_extraer_id,
    tabla_recurso: str | None = None,
    columna_pk: str | None = None,
) -> dict:
    """
    Si no se proporciona client_operation_id, delega directamente en fn_ejecutar()
    conservando 100% el contrato online existente.
    Si se proporciona, garantiza ejecución única por (id_empresa, id_usuario,
    tipo_operacion, client_operation_id).
    """
    if not client_operation_id:
        return fn_ejecutar()

    if not id_empresa or not id_usuario:
        raise ValueError("El contexto autenticado no identifica empresa y usuario para sincronización offline.")

    ocurrencia = fecha_ocurrencia_local or datetime.now(timezone.utc)
    reserva = sync_offline_repos.reservar_operacion(
        id_empresa=int(id_empresa),
        id_usuario=int(id_usuario),
        tipo_operacion=tipo_operacion,
        id_obra=int(id_obra),
        client_operation_id=client_operation_id,
        fecha_ocurrencia_local=ocurrencia,
    )

    if reserva.get("estado") == "EXISTENTE":
        if reserva.get("estado_op") == "PROCESADO" and isinstance(reserva.get("respuesta_json"), dict):
            respuesta = dict(reserva["respuesta_json"])
            respuesta["duplicado_idempotente"] = True
            respuesta["client_operation_id"] = client_operation_id
            if reserva.get("fecha_ocurrencia_local"):
                respuesta["fecha_ocurrencia_local"] = reserva["fecha_ocurrencia_local"]
            if reserva.get("fecha_sincronizacion"):
                respuesta["fecha_sincronizacion"] = reserva["fecha_sincronizacion"]
            return respuesta
        raise SyncConflictError(
            "La operación offline ya se encuentra en proceso de sincronización. Reintente en unos segundos.",
            409,
        )

    id_sync = reserva.get("id_sync")
    try:
        resultado = fn_ejecutar()
    except Exception:
        sync_offline_repos.liberar_operacion_fallida(id_sync)
        raise

    id_recurso = fn_extraer_id(resultado) if callable(fn_extraer_id) else None
    if tabla_recurso and columna_pk and id_recurso:
        try:
            sync_offline_repos.registrar_marcas_temporales_recurso(
                tabla_recurso, columna_pk, id_recurso, ocurrencia
            )
        except Exception:
            # Si la columna opcional aún no fue migrada en la BD destino, no revertir el recurso creado
            pass

    meta = sync_offline_repos.completar_operacion(id_sync, id_recurso, resultado)
    respuesta_final = dict(resultado)
    respuesta_final["client_operation_id"] = client_operation_id
    respuesta_final["fecha_ocurrencia_local"] = ocurrencia.isoformat()
    respuesta_final["fecha_sincronizacion"] = meta.get("fecha_sincronizacion") or datetime.now(timezone.utc).isoformat()
    respuesta_final["duplicado_idempotente"] = False
    return respuesta_final
