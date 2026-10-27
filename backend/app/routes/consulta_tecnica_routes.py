"""
Rutas API para CU23 – Gestionar consultas técnicas de obra (RFI)
HU138, HU139, HU140
Prefijos: /proyectos/{id_obra}/consultas-tecnicas y /consultas-tecnicas/{id}
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from app.services import consulta_tecnica_services as service
from app.utils.security import exigir_permiso, verificar_token


router = APIRouter(tags=["Consultas Técnicas"])


def _raise(exc: service.ConsultaTecnicaError):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# 1. LISTADO Y REGISTRO POR PROYECTO
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/consultas-tecnicas")
def listar_consultas_empresa(
    id_obra: int = Query(None, description="Filtro opcional por ID de obra"),
    estado: str = Query(None, description="Filtro por estado: ABIERTA, ASIGNADA, RESPONDIDA, CERRADA"),
    id_responsable: int = Query(None, description="Filtro por ID de usuario asignado"),
    busqueda: str = Query(None, description="Búsqueda por asunto, código, referencia o descripción"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    token=Depends(exigir_permiso("Visualizar_consultas_tecnicas"))
):
    try:
        return service.listar_consultas(
            id_obra=id_obra,
            token=token,
            estado=estado,
            id_responsable=id_responsable,
            busqueda=busqueda,
            page=page,
            limit=limit
        )
    except service.ConsultaTecnicaError as exc:
        _raise(exc)


@router.get("/proyectos/{id_obra}/consultas-tecnicas")
def listar_consultas_obra(
    id_obra: int,
    estado: str = Query(None, description="Filtro por estado: ABIERTA, ASIGNADA, RESPONDIDA, CERRADA"),
    id_responsable: int = Query(None, description="Filtro por ID de usuario asignado"),
    busqueda: str = Query(None, description="Búsqueda por asunto, código, referencia o descripción"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    token=Depends(exigir_permiso("Visualizar_consultas_tecnicas"))
):
    try:
        return service.listar_consultas(
            id_obra=id_obra,
            token=token,
            estado=estado,
            id_responsable=id_responsable,
            busqueda=busqueda,
            page=page,
            limit=limit
        )
    except service.ConsultaTecnicaError as exc:
        _raise(exc)


@router.post("/proyectos/{id_obra}/consultas-tecnicas", status_code=201)
def registrar_consulta_obra(
    id_obra: int,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Registrar_consultas_tecnicas"))
):
    try:
        return service.registrar_consulta(id_obra=id_obra, data=data, token=token)
    except service.ConsultaTecnicaError as exc:
        _raise(exc)


@router.get("/proyectos/{id_obra}/consultas-tecnicas/usuarios-asignables")
def get_usuarios_asignables(
    id_obra: int,
    token=Depends(exigir_permiso("Visualizar_consultas_tecnicas"))
):
    try:
        return service.obtener_usuarios_asignables(id_obra=id_obra, token=token)
    except service.ConsultaTecnicaError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# 2. DETALLE, ASIGNACIÓN, RESPUESTAS Y ESTADO DE CONSULTA
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/consultas-tecnicas/{id_consulta_tecnica}")
def get_detalle_consulta(
    id_consulta_tecnica: int,
    token=Depends(exigir_permiso("Visualizar_consultas_tecnicas"))
):
    try:
        return service.obtener_detalle(id_consulta_tecnica=id_consulta_tecnica, token=token)
    except service.ConsultaTecnicaError as exc:
        _raise(exc)


@router.patch("/consultas-tecnicas/{id_consulta_tecnica}/asignacion")
def asignar_responsable_consulta(
    id_consulta_tecnica: int,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Asignar_consultas_tecnicas"))
):
    try:
        return service.asignar_responsable(id_consulta_tecnica=id_consulta_tecnica, data=data, token=token)
    except service.ConsultaTecnicaError as exc:
        _raise(exc)


@router.post("/consultas-tecnicas/{id_consulta_tecnica}/respuestas", status_code=201)
def responder_consulta_tecnica(
    id_consulta_tecnica: int,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Responder_consultas_tecnicas"))
):
    try:
        return service.registrar_respuesta(id_consulta_tecnica=id_consulta_tecnica, data=data, token=token)
    except service.ConsultaTecnicaError as exc:
        _raise(exc)


@router.patch("/consultas-tecnicas/{id_consulta_tecnica}/estado")
def cambiar_estado_consulta(
    id_consulta_tecnica: int,
    data: dict = Body(...),
    token=Depends(exigir_permiso("Cerrar_consultas_tecnicas"))
):
    try:
        return service.cambiar_estado(id_consulta_tecnica=id_consulta_tecnica, data=data, token=token)
    except service.ConsultaTecnicaError as exc:
        _raise(exc)


@router.get("/consultas-tecnicas/{id_consulta_tecnica}/historial")
def get_historial_consulta(
    id_consulta_tecnica: int,
    token=Depends(exigir_permiso("Visualizar_consultas_tecnicas"))
):
    try:
        detalle = service.obtener_detalle(id_consulta_tecnica=id_consulta_tecnica, token=token)
        return detalle.get("historial", [])
    except service.ConsultaTecnicaError as exc:
        _raise(exc)
