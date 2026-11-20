from fastapi import APIRouter, Body, Depends, HTTPException, Request
from app.services import presupuesto_services
from app.services.presupuesto_services import PresupuestoError
from app.utils.security import exigir_permiso


router_proyectos = APIRouter(prefix="/api/proyectos/{id_obra}/presupuestos", tags=["Presupuestos de Obra"])
router_apus = APIRouter(prefix="/api/apus", tags=["Catálogo de APU"])
router_costos = APIRouter(prefix="/api/proyectos/{id_obra}/costos-ejecutados", tags=["Costos Ejecutados"])


def _ip(request: Request):
    return request.client.host if request.client else "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# RUTAS DE PRESUPUESTO POR OBRA (HU53, HU54, HU57)
# ─────────────────────────────────────────────────────────────────────────────

@router_proyectos.get("/")
def get_presupuestos_obra(
    id_obra: int,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return presupuesto_services.listar_presupuestos(id_obra, token_data)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.post("/")
def post_presupuesto_obra(
    id_obra: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Registrar_presupuesto"))
):
    try:
        return presupuesto_services.crear_presupuesto(id_obra, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.get("/comparativa")
def get_comparativa_presupuesto(
    id_obra: int,
    id_presupuesto: int = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    """
    HU60: Obtiene la comparativa detallada y global entre lo presupuestado
    y lo realmente ejecutado en la obra.
    """
    try:
        return presupuesto_services.obtener_comparativa(id_obra, id_presupuesto=id_presupuesto, token=token_data)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.get("/{id_presupuesto}")
def get_presupuesto_detalle(
    id_obra: int,
    id_presupuesto: int,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return presupuesto_services.obtener_detalle_presupuesto(id_obra, id_presupuesto, token_data)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.put("/{id_presupuesto}")
def put_presupuesto_obra(
    id_obra: int,
    id_presupuesto: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return presupuesto_services.actualizar_presupuesto(id_obra, id_presupuesto, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.delete("/{id_presupuesto}")
def delete_presupuesto_obra(
    id_obra: int,
    id_presupuesto: int,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return presupuesto_services.eliminar_presupuesto(id_obra, id_presupuesto, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# RUTAS DE CONSOLIDADO, APROBACIÓN Y VERSIONADO (HU58)
# ─────────────────────────────────────────────────────────────────────────────

@router_proyectos.get("/{id_presupuesto}/consolidado")
def get_presupuesto_consolidado(
    id_obra: int,
    id_presupuesto: int,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    """
    HU58: Obtiene el presupuesto consolidado analítico, con incidencias,
    desglose por tipo de recurso y métricas paramétricas.
    """
    try:
        return presupuesto_services.obtener_consolidado(id_obra, id_presupuesto, token_data)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.post("/{id_presupuesto}/aprobar")
def post_aprobar_presupuesto(
    id_obra: int,
    id_presupuesto: int,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Aprobar_presupuesto"))
):
    """
    HU58: Aprueba la línea base del presupuesto de obra de forma transaccional,
    desmarcando versiones vigentes anteriores y congelando su valor para control.
    """
    try:
        return presupuesto_services.aprobar_presupuesto(id_obra, id_presupuesto, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.patch("/{id_presupuesto}/estado")
def patch_estado_presupuesto(
    id_obra: int,
    id_presupuesto: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    """
    HU58: Cambia el estado del presupuesto (BORRADOR, EN_REVISION, CERRADO).
    """
    try:
        nuevo_estado = data.get("estado")
        return presupuesto_services.cambiar_estado(id_obra, id_presupuesto, nuevo_estado, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.post("/{id_presupuesto}/versionar")
def post_versionar_presupuesto(
    id_obra: int,
    id_presupuesto: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Registrar_presupuesto"))
):
    """
    HU58: Genera una nueva versión borrador del presupuesto clonando las partidas históricas.
    """
    try:
        return presupuesto_services.versionar_presupuesto(id_obra, id_presupuesto, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# RUTAS DE PARTIDAS (HU54 & HU57)
# ─────────────────────────────────────────────────────────────────────────────

@router_proyectos.get("/{id_presupuesto}/partidas/siguiente-codigo")
def get_siguiente_codigo_partida(
    id_obra: int,
    id_presupuesto: int,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return presupuesto_services.sugerir_codigo_partida(id_presupuesto, token_data)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.post("/{id_presupuesto}/partidas")
def post_partida(
    id_obra: int,
    id_presupuesto: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Registrar_presupuesto"))
):
    try:
        return presupuesto_services.crear_partida(id_obra, id_presupuesto, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.put("/{id_presupuesto}/partidas/{id_partida}")
def put_partida(
    id_obra: int,
    id_presupuesto: int,
    id_partida: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return presupuesto_services.actualizar_partida(id_obra, id_presupuesto, id_partida, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.delete("/{id_presupuesto}/partidas/{id_partida}")
def delete_partida(
    id_obra: int,
    id_presupuesto: int,
    id_partida: int,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return presupuesto_services.eliminar_partida(id_obra, id_presupuesto, id_partida, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_proyectos.post("/{id_presupuesto}/partidas/{id_partida}/asociar-apu")
def post_asociar_apu_partida(
    id_obra: int,
    id_presupuesto: int,
    id_partida: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    """
    HU57: Asocia un APU a la partida congelando (snapshot) su precio unitario.
    """
    try:
        return presupuesto_services.asociar_apu_a_partida(id_obra, id_presupuesto, id_partida, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# RUTAS DE APU Y COMPONENTES (HU55 & HU56)
# ─────────────────────────────────────────────────────────────────────────────

@router_apus.get("/")
def get_apus(
    id_obra: int = None,
    q: str = None,
    id_empresa: int = None,
    solo_vigentes: bool = False,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return presupuesto_services.listar_apus(token_data, id_obra=id_obra, q=q, id_empresa=id_empresa, solo_vigentes=solo_vigentes)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_apus.get("/siguiente-codigo")
def get_siguiente_codigo_apu(
    id_empresa: int = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return presupuesto_services.sugerir_codigo_apu(token_data, id_empresa)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_apus.get("/recursos/equipos")
def get_recursos_equipos(
    id_empresa: int = None,
    q: str = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return presupuesto_services.listar_equipos_catalogo(token_data, id_empresa, q)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_apus.get("/recursos/mano-obra")
def get_recursos_mano_obra(
    id_empresa: int = None,
    q: str = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return presupuesto_services.listar_mano_obra_catalogo(token_data, id_empresa, q)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_apus.post("/")
def post_apu(
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Registrar_presupuesto"))
):
    try:
        return presupuesto_services.crear_apu(data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_apus.get("/{id_apu}")
def get_apu_detalle(
    id_apu: int,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    try:
        return presupuesto_services.obtener_detalle_apu(id_apu, token_data)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_apus.put("/{id_apu}")
def put_apu(
    id_apu: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return presupuesto_services.actualizar_apu(id_apu, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_apus.post("/{id_apu}/componentes")
def post_componente_apu(
    id_apu: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return presupuesto_services.agregar_componente_apu(id_apu, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_apus.put("/{id_apu}/componentes/{id_componente}")
def put_componente_apu(
    id_apu: int,
    id_componente: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return presupuesto_services.actualizar_componente_apu(id_apu, id_componente, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_apus.delete("/{id_apu}/componentes/{id_componente}")
def delete_componente_apu(
    id_apu: int,
    id_componente: int,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Modificar_presupuesto"))
):
    try:
        return presupuesto_services.eliminar_componente_apu(id_apu, id_componente, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# RUTAS DE COSTOS EJECUTADOS (HU59)
# ─────────────────────────────────────────────────────────────────────────────

@router_costos.get("/")
def get_costos_ejecutados(
    id_obra: int,
    id_partida: int = None,
    tipo_recurso: str = None,
    origen_costo: str = None,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    token_data: dict = Depends(exigir_permiso("Visualizar_presupuesto"))
):
    """
    HU59: Lista los costos ejecutados reales de la obra.
    """
    try:
        filters = {
            "id_partida": id_partida,
            "tipo_recurso": tipo_recurso,
            "origen_costo": origen_costo,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        }
        return presupuesto_services.listar_costos_ejecutados(id_obra, filters, token_data)
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_costos.post("/")
def post_costo_ejecutado(
    id_obra: int,
    request: Request,
    data: dict = Body(...),
    token_data: dict = Depends(exigir_permiso("Registrar_costo_ejecutado"))
):
    """
    HU59: Registra un costo ejecutado real en la obra (sin mutar el presupuesto).
    """
    try:
        return presupuesto_services.registrar_costo_ejecutado(id_obra, data, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router_costos.delete("/{id_costo_ejecutado}")
def delete_costo_ejecutado(
    id_obra: int,
    id_costo_ejecutado: int,
    request: Request,
    token_data: dict = Depends(exigir_permiso("Registrar_costo_ejecutado"))
):
    """
    HU59: Elimina un registro de costo ejecutado.
    """
    try:
        return presupuesto_services.eliminar_costo_ejecutado(id_obra, id_costo_ejecutado, token_data, _ip(request))
    except PresupuestoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
