"""
Servicio CU18 – Avances de Obra
Lógica de negocio: validaciones, mapeo de roles y orquestación
de los repositorios de avances.
"""
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

from app.repos import avance_repos, bitacora_repos


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

def registrar_avance(id_obra: int, data: dict, token_data: dict, client_ip: str = "unknown") -> dict:
    """
    Registra un nuevo avance de obra.
    Roles autorizados (definidos por permiso 'Registrar_avances'):
      - ADMINISTRADOR (global)
      - ADMINISTRADOR_EMPRESA (Supervisor)
      - JEFE DE OBRA (Responsable del Proyecto)
    """
    id_empresa = _id_empresa(token_data)
    id_usuario = token_data.get("nro_usuario")

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

    # Validar fecha
    fecha = _validar_fecha(data.get("fecha_registro"))

    # Observación opcional
    observacion = str(data.get("observacion") or "").strip()

    # Llamar al repositorio
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

    # Registrar en bitácora
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

    return res


def listar_avances(id_obra: int, token_data: dict, id_unidad: int = None) -> dict:
    """
    Lista el historial de avances de un proyecto, con filtro opcional por unidad.
    Requiere permiso 'Visualizar_avances'.
    """
    id_empresa = _id_empresa(token_data)
    res = avance_repos.listar_avances_fn(id_obra=id_obra, id_empresa=id_empresa, id_unidad=id_unidad)
    if not res.get("success"):
        raise ValueError(res.get("error", "Error al obtener los avances."))
    return res


def resumen_avances(id_obra: int, token_data: dict) -> dict:
    """
    Devuelve el resumen de avance global del proyecto y el último avance
    registrado por unidad.
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
