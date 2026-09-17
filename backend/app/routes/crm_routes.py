from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from app.services import crm_services
from app.utils.security import exigir_permiso


router = APIRouter(tags=["CRM"])


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _raise(exc):
    raise HTTPException(status_code=exc.status_code, detail=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/clientes
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/clientes")
def get_clientes(
    tipo_cliente: str = None,
    estado: str = None,
    q: str = None,
    id_usuario_asignado: int = None,
    page: int = 1,
    limit: int = Query(20, le=100),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    try:
        return crm_services.listar(
            token=token,
            tipo_cliente=tipo_cliente,
            estado=estado,
            q=q,
            id_usuario_asignado=id_usuario_asignado,
            page=page,
            limit=limit,
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/clientes/metricas
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/clientes/metricas")
def get_metricas(
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    try:
        return crm_services.obtener_metricas(token=token, id_empresa_solicitada=id_empresa)
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/clientes/unidades-disponibles
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/clientes/unidades-disponibles")
def get_unidades_disponibles(
    id_obra: int = None,
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    try:
        return crm_services.listar_unidades_disponibles(
            token=token, id_obra=id_obra, id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/crm/clientes
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/clientes", status_code=201)
def post_cliente(
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Registrar_clientes")),
):
    try:
        return crm_services.registrar(
            data=data,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/crm/clientes/{id_cliente}
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/clientes/{id_cliente}")
def get_cliente_detalle(
    id_cliente: int,
    id_empresa: int = None,
    token=Depends(exigir_permiso("Visualizar_clientes")),
):
    try:
        return crm_services.obtener_detalle_historial(
            id_cliente=id_cliente,
            token=token,
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/crm/clientes/{id_cliente}
# ─────────────────────────────────────────────────────────────────────────────
@router.put("/clientes/{id_cliente}")
def put_cliente(
    id_cliente: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        return crm_services.actualizar(
            id_cliente=id_cliente,
            data=data,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/crm/clientes/{id_cliente}/clasificacion
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/clientes/{id_cliente}/clasificacion")
def patch_clasificacion(
    id_cliente: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        nuevo_estado = data.get("estado")
        return crm_services.clasificar_prospecto(
            id_cliente=id_cliente,
            nuevo_estado=nuevo_estado,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/crm/clientes/{id_cliente}/interacciones
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/clientes/{id_cliente}/interacciones", status_code=201)
def post_interaccion(
    id_cliente: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        return crm_services.registrar_interaccion(
            id_cliente=id_cliente,
            data=data,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/crm/clientes/{id_cliente}/unidades
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/clientes/{id_cliente}/unidades", status_code=201)
def post_asociar_unidad(
    id_cliente: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        return crm_services.asociar_unidad(
            id_cliente=id_cliente,
            data=data,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/crm/asociaciones/{id_cliente_unidad}/estado
# ─────────────────────────────────────────────────────────────────────────────
@router.patch("/asociaciones/{id_cliente_unidad}/estado")
def patch_estado_asociacion(
    id_cliente_unidad: int,
    request: Request,
    data: dict = Body(...),
    id_empresa: int = None,
    token=Depends(exigir_permiso("Modificar_clientes")),
):
    try:
        nuevo_estado = data.get("estado_asociacion")
        observaciones = data.get("observaciones")
        return crm_services.cambiar_estado_asociacion(
            id_cliente_unidad=id_cliente_unidad,
            nuevo_estado=nuevo_estado,
            observaciones=observaciones,
            token=token,
            ip=_ip(request),
            id_empresa_solicitada=id_empresa
        )
    except crm_services.CrmError as exc:
        _raise(exc)
