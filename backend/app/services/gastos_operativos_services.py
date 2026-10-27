"""CU32: consolidacion calculada de CU17, sin registrar ni persistir gastos."""
from contextlib import contextmanager
from decimal import Decimal

from app.classes.postgres import PostgreSQL
from app.repos import control_costos_repos, obra_repos, trabajadores_costos_repos
from app.services import control_costos_services as costos


@contextmanager
def _transaccion():
    db = PostgreSQL()
    try:
        db.create_connection()
        if db.conn is None or db.cur is None:
            raise RuntimeError("No hay conexion para calcular los gastos finales.")
        # create_connection prueba la conexion con SELECT 1. Empezar una
        # transaccion nueva para que todas las lecturas compartan un snapshot.
        db.conn.rollback()
        db.execute_query("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        yield db
    except Exception as exc:
        if db.conn is not None:
            db.conn.rollback()
        if trabajadores_costos_repos.falta_esquema_cu32(exc):
            raise costos.ControlCostosError(
                'CU32 requiere instalar migration_cu32_mano_obra_trabajadores.sql en el entorno designado.', 503
            ) from exc
        raise
    finally:
        db.close_connection()


def _obra(id_obra, token, db, bloquear=False):
    if isinstance(id_obra, bool) or not isinstance(id_obra, int) or id_obra <= 0:
        raise costos.ControlCostosError("La obra debe ser valida.")
    obra = control_costos_repos.obtener_obra(
        costos._empresa(token), id_obra, db=db, bloquear=bloquear
    )
    if not obra:
        raise costos.ControlCostosError("La obra no existe o no pertenece a su empresa.", 404)
    return obra


def _resumen(obra, token, db):
    if obra["estado_obra"] != "FINALIZADO":
        raise costos.ControlCostosError(
            "El resumen economico final requiere una obra FINALIZADO.", 409
        )
    response = costos.obtener_resumen(obra["id_obra"], token, db=db)
    data = response["data"]
    if data["linea_base"]["presupuesto_estado"] != "APROBADA":
        raise costos.ControlCostosError("El presupuesto de la linea base no esta APROBADA.", 409)
    registrados = control_costos_repos.listar_costos(
        costos._empresa(token), id_obra=obra["id_obra"],
        id_control_costo=data["linea_base"]["id_control_costo"],
        estado="REGISTRADO", db=db,
    )
    categorias = {categoria: Decimal("0.00") for categoria in sorted(costos.CATEGORIAS_COSTO)}
    for registro in registrados:
        # Defensa adicional; las consultas de CU17 tambien filtran el estado.
        if registro["estado"] == "REGISTRADO":
            categorias[registro["categoria"]] += Decimal(registro["monto"])
    categorias = {key: value.quantize(costos.CENTAVOS) for key, value in categorias.items()}
    if sum(categorias.values(), Decimal("0.00")) != data["resumen"]["costo_ejecutado"]:
        raise costos.ControlCostosError(
            "El desglose de costos no coincide con la comparacion de CU17.", 409
        )

    mano_obra = trabajadores_costos_repos.listar_cierre_mano_obra(
        costos._empresa(token), obra["id_obra"], db=db
    )
    costo_mano_obra = sum(
        (Decimal(item["costo_calculado"]) for item in mano_obra), Decimal("0.00")
    ).quantize(costos.CENTAVOS)
    if costo_mano_obra and categorias["MANO_OBRA"]:
        raise costos.ControlCostosError(
            "El cierre contiene MANO_OBRA manual y calculada. Revise los registros para evitar duplicación.",
            409,
        )
    categorias["MANO_OBRA"] = (categorias["MANO_OBRA"] + costo_mano_obra).quantize(
        costos.CENTAVOS
    )
    resumen = data["resumen"]
    resumen["costo_ejecutado"] = (
        Decimal(resumen["costo_ejecutado"]) + costo_mano_obra
    ).quantize(costos.CENTAVOS)
    resumen["variacion_original"] = (
        resumen["costo_ejecutado"] - resumen["costo_presupuestado_original"]
    ).quantize(costos.CENTAVOS)
    resumen["variacion_original_porcentaje"] = costos._porcentaje(
        resumen["variacion_original"], resumen["costo_presupuestado_original"]
    )
    resumen["variacion_revisada"] = (
        resumen["costo_ejecutado"] - resumen["presupuesto_revisado"]
    ).quantize(costos.CENTAVOS)
    resumen["variacion_revisada_porcentaje"] = costos._porcentaje(
        resumen["variacion_revisada"], resumen["presupuesto_revisado"]
    )
    resumen["costo_mano_obra_calculado"] = costo_mano_obra
    resumen["total_trabajadores_con_costo"] = len({
        item["id_usuario"] for item in mano_obra
        if Decimal(item["costo_calculado"]) > 0
    })
    resumen["total_jornadas_trabajadas"] = len(mano_obra)
    data["obra"] = obra
    resumen["costo_final_registrado"] = resumen["costo_ejecutado"]
    data["desglose_por_categoria"] = categorias
    data["mano_obra_trabajadores"] = mano_obra
    return response


def obtener_resumen_final(id_obra, token):
    """HU137: consulta recalculable; no crea una fotografia historica."""
    costos._empresa(token)
    with _transaccion() as db:
        return _resumen(_obra(id_obra, token, db), token, db)


def finalizar_obra(id_obra, token):
    """HU135/HU136: estado y calculo se confirman en la misma transaccion."""
    empresa = costos._empresa(token)
    with _transaccion() as db:
        _obra(id_obra, token, db, bloquear=True)
        result = obra_repos.actualizar_estado_obra_sp(
            id_obra, empresa, "FINALIZADO", db=db
        )
        if not result.get("success"):
            raise costos.ControlCostosError(
                result.get("error") or "No se pudo finalizar la obra.", 409
            )
        try:
            trabajadores_costos_repos.cerrar_mano_obra(empresa, id_obra, db)
        except trabajadores_costos_repos.TrabajadoresCostosConflictError as exc:
            raise costos.ControlCostosError(str(exc), 409) from exc
        resumen = _resumen(_obra(id_obra, token, db), token, db)
        db.conn.commit()
        return {**result, "resumen_economico_final": resumen["data"]}
