from datetime import date
from functools import wraps
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from app.repos import control_costos_repos, trabajadores_costos_repos
from app.services import control_costos_services as costos


def requiere_esquema_cu32(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            if trabajadores_costos_repos.falta_esquema_cu32(exc):
                raise costos.ControlCostosError(
                    'CU32 requiere instalar migration_cu32_mano_obra_trabajadores.sql en el entorno designado.', 503
                ) from exc
            raise
    return wrapped


def _id(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise costos.ControlCostosError(f"{label} debe ser un entero positivo.")
    return value


def _diario(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise costos.ControlCostosError("El salario diario debe ser un número válido.") from exc
    if not amount.is_finite() or amount <= 0:
        raise costos.ControlCostosError("El salario diario debe ser mayor que cero.")
    try:
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise costos.ControlCostosError("El salario diario excede el límite permitido.") from exc


def _dias(value):
    try:
        days = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise costos.ControlCostosError("Los días trabajados deben ser un número válido.") from exc
    if not days.is_finite() or days < 0 or days > 1:
        raise costos.ControlCostosError("Los días trabajados deben estar entre 0 y 1 por fecha.")
    return days.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@requiere_esquema_cu32
def listar_mano_obra(id_obra, token):
    empresa = costos._empresa(token)
    _id(id_obra, "La obra")
    if not control_costos_repos.obtener_obra(empresa, id_obra):
        raise costos.ControlCostosError(
            "La obra no existe o no pertenece a su empresa.", 404
        )
    obra = trabajadores_costos_repos.listar_trabajadores_obra(empresa, id_obra)
    jornadas = trabajadores_costos_repos.listar_jornadas_obra(empresa, id_obra)
    return {"success": True, "data": {"trabajadores": obra, "jornadas": jornadas}}


@requiere_esquema_cu32
def registrar_salario(id_obra, id_usuario, data, token):
    empresa = costos._empresa(token)
    obra = _id(id_obra, "La obra")
    trabajador = _id(id_usuario, "El trabajador")
    salario = _diario(data.get("salario_diario"))
    vigencia = data.get("fecha_vigencia")
    if not isinstance(vigencia, date):
        raise costos.ControlCostosError("La fecha de vigencia debe ser válida.")
    if vigencia < date.today():
        raise costos.ControlCostosError("No se permiten vigencias salariales retroactivas.")
    try:
        result = trabajadores_costos_repos.registrar_salario(
            empresa, obra, trabajador, salario, vigencia, costos._usuario(token)
        )
    except trabajadores_costos_repos.TrabajadoresCostosConflictError as exc:
        raise costos.ControlCostosError(str(exc), 409) from exc
    return {"success": True, "data": result}


@requiere_esquema_cu32
def registrar_jornada(id_obra, data, token):
    empresa = costos._empresa(token)
    obra = _id(id_obra, "La obra")
    trabajador = _id(data.get("id_usuario"), "El trabajador")
    fecha = data.get("fecha")
    if not isinstance(fecha, date) or fecha > date.today():
        raise costos.ControlCostosError("La fecha trabajada debe ser válida y no futura.")
    days = _dias(data.get("dias_trabajados"))
    try:
        result = trabajadores_costos_repos.registrar_jornada(
            empresa, obra, trabajador, fecha, days
        )
    except trabajadores_costos_repos.TrabajadoresCostosConflictError as exc:
        raise costos.ControlCostosError(str(exc), 409) from exc
    return {"success": True, "data": result}
